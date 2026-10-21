"""Independent fixture tests; private original M5 files not required."""
import sqlite3
import numpy as np
import pandas as pd
import pytest
from src.session2 import (abc_segment,xyz_segment,intermittent_segment,
                          daily_features,rolling_origins_28,max_zero_streak)
from src.advanced_sql import run as run_advanced
from scripts.reconcile_session2 import compare_report


def fixture(days=125):
    dt=pd.date_range('2020-01-01',periods=days)
    rows=[]
    for store,item,mul in [('CA_1','FOODS_1_001',1),('TX_1','HOBBIES_1_001',2)]:
        for i,d in enumerate(dt):
            rows.append((store,item,d,int((i%9==0)*mul*(1+i%3))))
    return pd.DataFrame(rows,columns=['store_id','item_id','date','units'])

def test_abc_sort_and_ties():
    f=pd.DataFrame([('S','b',60),('S','a',60),('S','c',20)],columns=['store_id','item_id','units'])
    r=abc_segment(f)
    assert list(r.item_id)==['a','b','c']
    assert list(r.abc_class)==['A','A','B']
    assert r.unit_share.sum()==pytest.approx(1)


def test_abc_zero_and_custom_thresholds():
    f=pd.DataFrame([('S','a',0),('S','b',0)],columns=['store_id','item_id','units'])
    assert set(abc_segment(f).abc_class)=={'U'}
    with pytest.raises(ValueError):abc_segment(f,.95,.8)


def test_abc_zero_volume_does_not_inflate_last_tier():
    f=pd.DataFrame([('S','a',10),('S','b',0)],columns=['store_id','item_id','units'])
    assert abc_segment(f).set_index('item_id').abc_class.loc['b']=='U'


def test_xyz_zero_weekly_variability_is_x():
    dt=pd.date_range('2023-01-02',periods=28)
    f=pd.DataFrame({'store_id':['S']*28,'item_id':['A']*28,'date':dt,'units':[2]*28})
    r=xyz_segment(f)
    assert r.xyz_class.iloc[0]=='X'
    assert r.weekly_cv.iloc[0]==0
    assert r.complete_weeks.iloc[0]==4


def test_xyz_week_boundaries_ignore_partial_weeks():
    dt=pd.date_range('2023-01-04',periods=12)
    f=pd.DataFrame({'store_id':['S']*12,'item_id':['A']*12,'date':dt,'units':[1]*12})
    r=xyz_segment(f)
    assert r.complete_weeks.iloc[0]==1


def test_xyz_undefined_zero_mean_and_threshold_validation():
    f=fixture(28);f.units=0
    assert set(xyz_segment(f).xyz_class)=={'U'}
    with pytest.raises(ValueError):xyz_segment(f,.7,.2)


def test_intermittent_no_observations_and_one_positive():
    f=fixture(70);f.units=0
    r=intermittent_segment(f)
    assert set(r.demand_pattern)=={'U'}
    f.loc[0,'units']=2
    r=intermittent_segment(f).set_index(['store_id','item_id'])
    assert r.loc[('CA_1','FOODS_1_001'),'demand_pattern']=='U'
    assert np.isnan(r.loc[('CA_1','FOODS_1_001'),'cv2_positive_size'])


def test_streak_counts():
    assert max_zero_streak([0,0,1,0,0,0,3])==3
    assert max_zero_streak([2,3])==0
    assert max_zero_streak([0,0])==2


def test_intermit_smooth():
    f=fixture(70);f.units=1
    r=intermittent_segment(f)
    assert set(r.demand_pattern)=={'Smooth'}
    assert (r.adi==1).all()
    assert (r.cv2_positive_size==0).all()


def test_intermit_lumpy_and_intermittent():
    f=fixture(100)
    v=np.zeros(100,dtype=int);v[::10]=1
    f.loc[f.item_id=='FOODS_1_001','units']=v
    r=intermittent_segment(f)
    assert r.set_index('item_id').loc['FOODS_1_001','demand_pattern']=='Intermittent'
    v[::20]=12
    f.loc[f.item_id=='FOODS_1_001','units']=v
    r=intermittent_segment(f)
    assert r.set_index('item_id').loc['FOODS_1_001','demand_pattern']=='Lumpy'


def test_lags_and_rolling_exclude_target():
    f=fixture(95)
    p=daily_features(f).query("store_id == 'CA_1'").reset_index(drop=True)
    assert np.isnan(p.lag_1.iloc[0])
    assert np.isnan(p.rolling_mean_28.iloc[27])
    assert np.isnan(p.prior_zero_share_28.iloc[27])
    assert p.lag_1.iloc[28]==f.query("store_id == 'CA_1'").units.iloc[27]
    assert p.rolling_mean_28.iloc[28]==pytest.approx(f.query("store_id == 'CA_1'").units.iloc[:28].mean())
    assert p.prior_zero_share_28.iloc[28]==pytest.approx((f.query("store_id == 'CA_1'").units.iloc[:28]==0).mean())


def test_perturb_today_and_future_does_not_change_current_features():
    f=fixture(95)
    baseline=daily_features(f)
    altered=f.copy()
    altered.loc[altered.date>=pd.Timestamp('2020-03-01'),'units']=999
    changed=daily_features(altered)
    fields=[c for c in baseline if c.startswith('rolling_') or c.startswith('lag_') or c.startswith('prior_zero')]
    # At first perturbed date, the target is changed but no feature can depend on it.
    mask=baseline.date==pd.Timestamp('2020-03-01')
    pd.testing.assert_frame_equal(baseline.loc[mask,fields],changed.loc[mask,fields])


def test_future_28day_supervised_labels_and_origin_separation():
    f=fixture(125)
    o=rolling_origins_28(f,origin_stride=28)
    assert len(o)>0
    assert o.target_end_date.max()==f.date.max()
    for _,r in o.iterrows():
        subset=f[(f.store_id==r.store_id)&(f.item_id==r.item_id)&
                 (f.date>r.forecast_origin_date)&(f.date<=r.target_end_date)]
        assert len(subset)==28
        assert int(subset.units.sum())==int(r.future_28d_units)
    assert 'target_day_units' not in o


def test_forecast_origin_rejects_missing_day():
    f=fixture(125)
    f=f.drop(f[(f.store_id=='CA_1')&(f.date==pd.Timestamp('2020-02-01'))].index)
    with pytest.raises(ValueError,match='consecutive'):rolling_origins_28(f)


def test_validates_origins():
    with pytest.raises(ValueError):rolling_origins_28(fixture(90),origin_stride=0)
    with pytest.raises(ValueError):rolling_origins_28(fixture(90),history=10)


def test_advanced_queries_end_to_end_fixture(tmp_path):
    db=tmp_path/'fixture.sqlite'
    with sqlite3.connect(db) as con:
        con.executescript('''CREATE TABLE products(item_id TEXT,cat_id TEXT,dept_id TEXT);
            CREATE TABLE daily_sales(store_id TEXT,item_id TEXT,date TEXT,units INT,
            sell_price REAL,priced_revenue REAL,event_type TEXT);''')
        con.execute("INSERT INTO products VALUES ('A','FOODS','FOODS_1')")
        dt=pd.date_range('2023-01-01',periods=70)
        con.executemany('INSERT INTO daily_sales VALUES (?,?,?,?,?,?,?)',
            [('S','A',d.strftime('%Y-%m-%d'),int(d.day%3),2.0,int(d.day%3)*2.,None) for d in dt])
    result=run_advanced(db,tmp_path/'sql')
    assert len(result)==14
    assert result[13]['rows']==70
    assert result[3]['rows']==1


def test_reconciliation_detects_tampered_sql(tmp_path):
    f=tmp_path/'out.csv'
    f.write_text('store_id,item_id,days_observed,zero_days,positive_days,units\nS,A,2,0,2,88\n')
    expected=pd.DataFrame([dict(store_id='S',item_id='A',days_observed=2,zero_days=0,positive_days=2,units=3)])
    with pytest.raises(AssertionError,match='mismatch'):
        compare_report(4,f,expected)


def test_reconciliation_good_data(tmp_path):
    f=tmp_path/'out.csv'
    f.write_text('store_id,item_id,days_observed,zero_days,positive_days,units\nS,A,2,0,2,3\n')
    expected=pd.DataFrame([dict(store_id='S',item_id='A',days_observed=2,zero_days=0,positive_days=2,units=3)])
    assert compare_report(4,f,expected)['numeric_cells']==4
