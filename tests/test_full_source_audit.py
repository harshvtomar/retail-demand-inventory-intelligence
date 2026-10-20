"""Verify streaming full-source audit detects corrupt original CSVs."""
import csv
from pathlib import Path
import pytest
from scripts.audit_full_source import audit


def write_csv(p, cols, rows):
    with p.open('w', newline='') as f:
        w=csv.writer(f);w.writerow(cols);w.writerows(rows)


@pytest.fixture
def raw(tmp_path):
    write_csv(tmp_path/'calendar.csv',
              ['d','date','wm_yr_wk','weekday'],
              [['d_1','2011-01-29','11101','Saturday'],['d_2','2011-01-30','11101','Sunday']])
    write_csv(tmp_path/'sales_train_validation.csv',
              ['id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_2'],
              [['item_CA_1_validation','item','dept','cat','CA_1','CA','0','2']])
    write_csv(tmp_path/'sell_prices.csv',
              ['store_id','item_id','wm_yr_wk','sell_price'],
              [['CA_1','item','11101','3.1']])
    return tmp_path


def test_full_source_audit_valid(raw):
    result=audit(raw)
    assert result['total_original_daily_values']==2
    assert result['zero_unit_days']==1
    assert result['total_original_sales_units']==2
    assert result['unique_series']==1
    assert result['sell_price_records_checked']==1


def test_audit_duplicate_series(raw):
    p=raw/'sales_train_validation.csv'
    with p.open('a') as f:
        f.write('item_CA_1_validation,item,dept,cat,CA_1,CA,0,2\n')
    with pytest.raises(ValueError,match='Duplicate'):
        audit(raw)


def test_audit_rejects_negative_sales(raw):
    write_csv(raw/'sales_train_validation.csv',
              ['id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_2'],
              [['item_CA_1_validation','item','dept','cat','CA_1','CA','-1','2']])
    with pytest.raises(ValueError,match='Invalid/negative'):
        audit(raw)


def test_audit_rejects_invalid_price(raw):
    write_csv(raw/'sell_prices.csv',
              ['store_id','item_id','wm_yr_wk','sell_price'],
              [['CA_1','item','11101','0']])
    with pytest.raises(ValueError,match='Invalid nonpositive'):
        audit(raw)


def test_audit_rejects_calendar_gap(raw):
    write_csv(raw/'calendar.csv',
              ['d','date','wm_yr_wk','weekday'],
              [['d_1','2011-01-29','11101','Saturday'],['d_2','2011-01-31','11101','Monday']])
    with pytest.raises(ValueError,match='Calendar dates have gaps'):
        audit(raw)
