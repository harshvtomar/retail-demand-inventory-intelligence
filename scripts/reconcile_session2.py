"""Independent Session 2 SQL reconciliation from original M5 CSVs (not SQLite)."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.reconcile_sql import source_frame

KEY=['store_id','item_id']

def independent_reports(df):
    d=df.copy()
    d['date']=pd.to_datetime(d.date)
    d['series_days']=1
    result={}
    storeday=d.groupby(['store_id','date'],as_index=False).units.sum().sort_values(['store_id','date'])
    gg=storeday.groupby('store_id',sort=False).units
    for n in (7,28):
        storeday[f'avg_units_{n}d']=gg.transform(lambda s:s.rolling(n,min_periods=1).mean())
    result[1]=storeday
    result[2]=d.groupby(['store_id','cat_id'],as_index=False).agg(observed_series_days=('units','size'),units=('units','sum'),mean_units_per_series_day=('units','mean'))
    d['month']=d.date.dt.strftime('%Y-%m')
    result[3]=d.groupby(['store_id','month'],as_index=False).agg(series_days=('units','size'),units=('units','sum'),mean_units_per_series_day=('units','mean'))
    d['zero']=(d.units==0).astype(int)
    d['positive']=(d.units>0).astype(int)
    result[4]=d.groupby(KEY,as_index=False).agg(days_observed=('units','size'),zero_days=('zero','sum'),positive_days=('positive','sum'),units=('units','sum'))
    result[5]=d.groupby(['cat_id','event_type'],as_index=False).agg(series_days=('units','size'),units=('units','sum'),avg_units=('units','mean'))
    d['day_type']=np.where(d.date.dt.dayofweek>=5,'Weekend','Weekday')
    result[6]=d.groupby(['store_id','day_type'],as_index=False).agg(series_days=('units','size'),units=('units','sum'),mean_units=('units','mean'))
    d['priced']=(d.sell_price.notna()).astype(int)
    d['missing']=(d.sell_price.isna()).astype(int)
    d['priced_revenue']=d.units*d.sell_price
    result[7]=d.groupby('dept_id',as_index=False).agg(series_days=('units','size'),priced_days=('priced','sum'),missing_price_days=('missing','sum'),observed_priced_revenue=('priced_revenue','sum'))
    d['month_of_year']=d.date.dt.strftime('%m')
    result[8]=d.groupby('month_of_year',as_index=False).agg(series_days=('units','size'),units=('units','sum'),mean_units=('units','mean'))
    result[9]=d.groupby(KEY,as_index=False).units.sum().sort_values(['units','store_id','item_id'],ascending=[False,True,True])
    result[9]['share']=result[9].units/result[9].units.sum()
    d['week_start']=d.date.dt.to_period('W-SUN').dt.start_time
    result[10]=d.groupby(KEY+['week_start'],as_index=False).agg(observed_days=('units','size'),weekly_units=('units','sum'))
    result[10]['week_start']=result[10].week_start.dt.strftime('%Y-%m-%d')
    d['sq_units']=d.units.astype('float64')**2
    result[11]=d.groupby(KEY,as_index=False).agg(series_days=('units','size'),mean_daily=('units','mean'),sq_mean=('sq_units','mean'))
    result[11]['pop_variance']=result[11].sq_mean-result[11].mean_daily**2
    result[11]=result[11].drop(columns=['sq_mean'])
    result[12]=d.groupby('dept_id',as_index=False).agg(units=('units','sum'),series_days=('units','size'))
    result[12]['unit_share']=result[12].units/result[12].units.sum()
    d['calendar_week']=d.date.dt.strftime('%Y-%W')
    result[13]=d.groupby(['store_id','calendar_week'],as_index=False).units.sum().sort_values(['store_id','calendar_week'])
    result[13]['previous_week_units']=result[13].groupby('store_id').units.shift(1)
    daily=d.sort_values(KEY+['date'])[['store_id','item_id','date','units']].copy()
    previous=daily.groupby(KEY,sort=False).units.shift(1)
    daily['trailing_28_before_today']=previous.groupby([daily.store_id,daily.item_id],sort=False).transform(lambda s:s.rolling(28,min_periods=28).mean())
    daily['date']=daily.date.dt.strftime('%Y-%m-%d')
    result[14]=daily
    result[1]['date']=result[1].date.dt.strftime('%Y-%m-%d')
    return result

IDENTITIES={
    1:['store_id','date'],2:['store_id','cat_id'],3:['store_id','month'],
    4:['store_id','item_id'],5:['cat_id','event_type'],6:['store_id','day_type'],
    7:['dept_id'],8:['month_of_year'],9:['store_id','item_id'],
    10:['store_id','item_id','week_start'],11:['store_id','item_id'],
    12:['dept_id'],13:['store_id','calendar_week'],14:['store_id','item_id','date']
}

def compare_report(number, actual, expected):
    path=Path(actual)
    if not path.is_file():raise AssertionError(f'Missing SQL export: {path}')
    actual=pd.read_csv(path,dtype={k:str for k in IDENTITIES[number]},keep_default_na=True)
    expected=expected.copy()
    keys=IDENTITIES[number]
    if set(actual.columns)!=set(expected.columns):
        raise AssertionError(f'SQL query {number}: columns disagree: {set(actual.columns)^set(expected.columns)}')
    if actual.duplicated(keys).any() or expected.duplicated(keys).any():
        raise AssertionError(f'SQL query {number}: duplicate keys')
    for k in keys:
        actual[k]=actual[k].astype(str)
        expected[k]=expected[k].astype(str)
    joined=expected.merge(actual,on=keys,how='outer',suffixes=('_py','_sql'),indicator=True,validate='one_to_one')
    if len(joined)!=len(expected) or not joined._merge.eq('both').all():
        raise AssertionError(f'SQL query {number}: row keys differ')
    numeric=[x for x in expected.columns if x not in keys]
    errors={}
    for col in numeric:
        v1=pd.to_numeric(joined[f'{col}_py'],errors='coerce').to_numpy(float)
        v2=pd.to_numeric(joined[f'{col}_sql'],errors='coerce').to_numpy(float)
        if not np.allclose(v1,v2,rtol=0,atol=1e-6,equal_nan=True):
            index=np.flatnonzero(~np.isclose(v1,v2,rtol=0,atol=1e-6,equal_nan=True))[:3]
            raise AssertionError(f'SQL query {number}: {col} mismatch at {index.tolist()}: {v1[index]} vs {v2[index]}')
        errors[col]=float(np.nanmax(abs(v1-v2))) if np.isfinite(v1-v2).any() else 0.0
    return {"query":number,"rows":len(expected),"numeric_cells":len(expected)*len(numeric),"max_difference":max(errors.values(),default=0.)}

def reconcile(raw='data/raw',sql_dir='data/processed/session2_sql',report='reports/session2/sql_reconciliation.json'):
    reference=independent_reports(source_frame(raw,3))
    checks=[compare_report(i,Path(sql_dir)/f'advanced_{i:02d}.csv',reference[i]) for i in range(1,15)]
    obj={'method':'Independent raw M5 CSV reconstruction, not derived SQLite warehouse',
         'source_sample':'210 nonrandom prefix series; all 10 stores, seven departments',
         'queries_verified':len(checks),'numeric_cells_verified':sum(c['numeric_cells'] for c in checks),
         'results':checks}
    if report:
        path=Path(report);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(obj,indent=2))
    return obj
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',default='data/raw');p.add_argument('--sql-dir',default='data/processed/session2_sql')
    a=p.parse_args();print(json.dumps(reconcile(a.raw,a.sql_dir),indent=2))
