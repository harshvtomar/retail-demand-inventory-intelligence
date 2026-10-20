"""Independent pandas/NumPy reconciliation of all 12 SQL reports using original M5 CSVs.

The reference calculation never reads the SQLite database or its derived tables.
It reselects documented source series, joins raw source calendar/weekly prices,
then checks exact integer aggregates and bounded floating-point measures.
The deterministic prefix sample is not representative of full M5 demand.
"""
import argparse
import csv
import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED = {
  1: (['month'], ['units']),
  2: (['store_id'], ['units']),
  3: (['state_id'], ['units']),
  4: (['item_id'], ['units']),
  5: (['cat_id', 'month'], ['units']),
  6: (['dept_id', 'month'], ['units']),
  7: (['weekday'], ['units', 'mean_product_day_units']),
  8: (['month_of_year'], ['mean_series_day_units']),
  9: (['event_type'], ['mean_series_day_units']),
  10: (['item_id', 'store_id'], ['mean_units', 'population_variance']),
  11: (['store_id'], ['observed_days', 'zero_days', 'zero_share']),
  12: (['price_band'], ['priced_rows', 'units']),
}
FLOAT_COLS = {'mean_product_day_units','mean_series_day_units','mean_units','population_variance','zero_share'}


def source_frame(raw, sample_per_store_dept=3):
    """Reconstruct a sample strictly from independent original wide-format source CSVs."""
    raw = Path(raw)
    if sample_per_store_dept < 1:
        raise ValueError('sample_per_store_dept must be >=1')
    with (raw / 'calendar.csv').open(newline='', encoding='utf-8') as f:
        calendar = {r['d']: r for r in csv.DictReader(f)}

    chosen=[]; series_units=[]; selection={}
    with (raw / 'sales_train_validation.csv').open(newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f)
        days=[k for k in reader.fieldnames or [] if k.startswith('d_') and k[2:].isdigit()]
        if not days or any(day not in calendar for day in days):
            raise ValueError('Missing required source dates or calendar records')
        for r in reader:
            key=(r['store_id'],r['dept_id'])
            if selection.get(key,0)>=sample_per_store_dept: continue
            selection[key]=selection.get(key,0)+1
            chosen.append({k:r[k] for k in ('id','item_id','dept_id','cat_id','store_id','state_id')})
            series_units.append(np.array([int(r[day]) for day in days],dtype=np.int64))
    if not chosen: raise ValueError('No source series selected')
    n=len(days)
    vals=np.concatenate(series_units)
    cols={k:np.repeat([r[k] for r in chosen],n) for k in ('id','item_id','dept_id','cat_id','store_id','state_id')}
    cols.update({
        'day_id':np.tile(days,len(chosen)),
        'date':np.tile([calendar[d]['date'] for d in days],len(chosen)),
        'wm_yr_wk':np.tile([int(calendar[d]['wm_yr_wk']) for d in days],len(chosen)),
        'weekday':np.tile([calendar[d]['weekday'] for d in days],len(chosen)),
        'event_type':np.tile([(calendar[d]['event_type_1'] or 'No event') for d in days],len(chosen)),
        'units':vals,
    })
    frame=pd.DataFrame(cols)
    keys={(r['store_id'],r['item_id']) for r in chosen}
    prices=[]
    with (raw/'sell_prices.csv').open(newline='', encoding='utf-8') as f:
        for p in csv.DictReader(f):
            if (p['store_id'],p['item_id']) in keys:
                prices.append((p['store_id'],p['item_id'],int(p['wm_yr_wk']),float(p['sell_price'])))
    pframe=pd.DataFrame(prices,columns=['store_id','item_id','wm_yr_wk','sell_price'])
    frame=frame.merge(pframe,on=['store_id','item_id','wm_yr_wk'],how='left',validate='many_to_one')
    frame['month']=frame['date'].str[:7]
    frame['month_of_year']=frame['date'].str[5:7]
    return frame


def expected_reports(df):
    """Pandas implementation, independent from exploratory SQL definitions."""
    outputs={}
    def units(keys): return df.groupby(keys,as_index=False)['units'].sum()
    outputs[1]=units(['month'])
    outputs[2]=units(['store_id'])
    outputs[3]=units(['state_id'])
    outputs[4]=units(['item_id']).sort_values(['units','item_id'],ascending=[False,True]).head(20)
    outputs[5]=units(['cat_id','month'])
    outputs[6]=units(['dept_id','month'])
    outputs[7]=df.groupby(['weekday'],as_index=False).agg(units=('units','sum'),mean_product_day_units=('units','mean'))
    outputs[8]=df.groupby(['month_of_year'],as_index=False).agg(mean_series_day_units=('units','mean'))
    outputs[8]['mean_series_day_units']=outputs[8]['mean_series_day_units'].round(4)
    outputs[9]=df.groupby(['event_type'],as_index=False).agg(mean_series_day_units=('units','mean'))
    outputs[9]['mean_series_day_units']=outputs[9]['mean_series_day_units'].round(4)
    work=df.assign(squared_units=df['units'].to_numpy(dtype=np.float64)**2)
    outputs[10]=work.groupby(['item_id','store_id'],as_index=False).agg(mean_units=('units','mean'),squared_mean=('squared_units','mean'))
    outputs[10]['population_variance']=(outputs[10]['squared_mean']-outputs[10]['mean_units']**2).round(4)
    outputs[10]['mean_units']=outputs[10]['mean_units'].round(4)
    outputs[10]=outputs[10].drop(columns=['squared_mean'])
    work=df.assign(zero=(df['units']==0).astype('int64'))
    outputs[11]=work.groupby(['store_id'],as_index=False).agg(observed_days=('units','size'),zero_days=('zero','sum'))
    outputs[11]['zero_share']=(outputs[11]['zero_days']/outputs[11]['observed_days']).round(4)
    observed=df.loc[df['sell_price'].notna(),['sell_price','units']].copy()
    observed['price_band']=np.select([observed['sell_price']<5, observed['sell_price']<15],['below 5','5-15'],default='15+')
    outputs[12]=observed.groupby(['price_band'],as_index=False).agg(priced_rows=('units','size'),units=('units','sum'))
    return outputs


def compare_report(number, actual_path, expected):
    keys, values=EXPECTED[number]
    with Path(actual_path).open(newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames != keys+values:
            raise AssertionError(f'Query {number}: unexpected columns {reader.fieldnames}, expected {keys+values}')
        actual=list(reader)
    rows={tuple(str(r[k]) for k in keys):r for r in expected.to_dict(orient='records')}
    found={}
    for r in actual:
        key=tuple(r[k] for k in keys)
        if key in found:raise AssertionError(f'Query {number}: duplicate output key {key}')
        found[key]=r
    if rows.keys()!=found.keys():
        raise AssertionError(f'Query {number}: missing {list(rows.keys()-found.keys())[:3]}, unexpected {list(found.keys()-rows.keys())[:3]}')
    max_abs=0.0
    for key,r in rows.items():
        for v in values:
            measured=float(found[key][v]); wanted=float(r[v])
            tol=0.00011 if v in FLOAT_COLS else 0.0
            if not math.isfinite(measured) or abs(measured-wanted)>tol:
                raise AssertionError(f'Query {number}: {key} {v} SQL={measured} Python={wanted} tol={tol}')
            max_abs=max(max_abs,abs(measured-wanted))
    return {'query':number,'verified':True,'result_rows':len(rows),'numeric_fields_checked':len(rows)*len(values),'max_absolute_difference':round(max_abs,10)}


def reconcile(raw, tables, sample_per_store_dept=3, report_path=None, database=None):
    df=source_frame(raw,sample_per_store_dept)
    expected=expected_reports(df)
    results=[compare_report(i,Path(tables)/f'query_{i:02d}.csv',expected[i]) for i in range(1,13)]
    available=df[df['sell_price'].notna()]
    report={
        'source':'Expected values derived from original M5 CSVs without reading the SQL database; optional final metrics compared to SQLite',
        'sample_method':f'First {sample_per_store_dept} series per store-department in source order; nonrandom/nonrepresentative',
        'series':int(df['id'].nunique()),'stores':int(df['store_id'].nunique()),'departments':int(df['dept_id'].nunique()),
        'daily_observations':len(df),'observed_units':int(df['units'].sum()),
        'zero_unit_observations':int((df['units']==0).sum()),
        'missing_price_observations':int(df['sell_price'].isna().sum()),
        'priced_observations':len(available),
        'priced_revenue_observed_only':round(float((available['sell_price']*available['units']).sum()),2),
        'queries_checked':len(results),'numeric_values_checked':sum(r['numeric_fields_checked'] for r in results),
        'all_queries_reconciled':all(r['verified'] for r in results),'results':results,
        'limitations':'Not total Walmart revenue; unpriced observations excluded; zero sales not confirmed stockouts; no causal claims'
    }
    if database is not None:
        with sqlite3.connect(database) as connection:
            row=connection.execute('''SELECT COUNT(*), SUM(units),
                SUM(CASE WHEN units=0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN sell_price IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END),
                SUM(priced_revenue) FROM daily_sales''').fetchone()
        reference=(len(df),int(df['units'].sum()),int((df['units']==0).sum()),
                   int(df['sell_price'].isna().sum()),len(available))
        if tuple(row[:5])!=reference:
            raise AssertionError(f'Warehouse core metrics disagree: SQL {row[:5]} versus source {reference}')
        if row[5] is None or abs(float(row[5])-report['priced_revenue_observed_only'])>0.005:
            raise AssertionError(f'Warehouse priced revenue differs: SQL={row[5]}, source={report["priced_revenue_observed_only"]}')
        report['warehouse_core_metrics_reconciled']=True
    if report_path:
        p=Path(report_path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--raw',default='data/raw')
    p.add_argument('--tables',default='reports/tables')
    p.add_argument('--sample-per-store-dept',type=int,default=3)
    p.add_argument('--out',default='reports/sql_python_reconciliation.json')
    p.add_argument('--database',default='data/processed/m5.sqlite')
    a=p.parse_args()
    r=reconcile(a.raw,a.tables,a.sample_per_store_dept,a.out,database=a.database)
    print(json.dumps({k:v for k,v in r.items() if k!='results'},indent=2))
