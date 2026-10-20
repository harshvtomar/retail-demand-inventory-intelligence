"""Regression tests: independent pandas reference must catch corrupt SQL exports."""
import csv
import sqlite3

import pytest

from scripts.reconcile_sql import reconcile, source_frame
from src.pipeline import run as build
from src.analysis import run as analyze


def csv_write(path, header, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(header);writer.writerows(rows)


@pytest.fixture
def fixture_project(tmp_path):
    raw=tmp_path/'raw';raw.mkdir()
    csv_write(raw/'calendar.csv',
        ['d','date','wm_yr_wk','weekday','event_name_1','event_type_1'],
        [['d_1','2011-01-29',11101,'Saturday','',''],
         ['d_2','2011-02-05',11102,'Saturday','Event','Cultural'],
         ['d_3','2011-02-06',11102,'Sunday','','']])
    csv_write(raw/'sell_prices.csv',['store_id','item_id','wm_yr_wk','sell_price'],
              [['CA_1','FOODS_1_001',11101,'2.50'],
               ['CA_1','FOODS_1_001',11102,'6.00'],
               ['TX_1','HOBBIES_1_001',11101,'20.00']])
    csv_write(raw/'sales_train_validation.csv',
             ['id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_2','d_3'],
             [['FOODS_1_001_CA_1_validation','FOODS_1_001','FOODS_1','FOODS','CA_1','CA','0','3','4'],
              ['HOBBIES_1_001_TX_1_validation','HOBBIES_1_001','HOBBIES_1','HOBBIES','TX_1','TX','2','0','1']])
    database=tmp_path/'m5.sqlite'; tables=tmp_path/'tables'
    build(raw,database,sample_per_store_dept=1)
    analyze(database,tables)
    return raw,database,tables


def test_all_twelve_independent_sql_aggregates(fixture_project):
    raw,db,tables=fixture_project
    result=reconcile(raw,tables,sample_per_store_dept=1,database=db)
    assert result['all_queries_reconciled'] and result['queries_checked']==12
    assert result['daily_observations']==6
    assert result['observed_units']==10
    assert result['missing_price_observations']==2
    assert result['priced_revenue_observed_only']==82.0


def test_corrupted_sql_export_detected(fixture_project):
    raw,db,tables=fixture_project
    target=tables/'query_12.csv'
    content=target.read_text()
    target.write_text(content.replace('5-15,2,7','5-15,2,700'))
    if target.read_text()==content:  # Handles any formatting/layout differences.
        lines=content.splitlines()
        vals=lines[1].split(','); vals[-1]='99999';lines[1]=','.join(vals)
        target.write_text('\n'.join(lines)+'\n')
    with pytest.raises(AssertionError,match='Query 12'):
        reconcile(raw,tables,sample_per_store_dept=1,database=db)


def test_priced_revenue_not_filled_for_missing_prices(fixture_project):
    raw,db,tables=fixture_project
    frame=source_frame(raw,sample_per_store_dept=1)
    assert frame['sell_price'].isna().sum()==2
    assert frame['units'].sum()==10
    with sqlite3.connect(db) as connection:
        count,price_rows=connection.execute('SELECT COUNT(*),COUNT(sell_price) FROM daily_sales').fetchone()
        assert count==6 and price_rows==4


def test_missing_query_export_fails(fixture_project):
    raw,db,tables=fixture_project
    (tables/'query_05.csv').unlink()
    with pytest.raises(FileNotFoundError):
        reconcile(raw,tables,sample_per_store_dept=1,database=db)


def test_warehouse_core_value_tampering_detected(fixture_project):
    raw,db,tables=fixture_project
    with sqlite3.connect(db) as connection:
        connection.execute('UPDATE daily_sales SET priced_revenue=12345 WHERE rowid=1')
    with pytest.raises(AssertionError,match='priced revenue'):
        reconcile(raw,tables,sample_per_store_dept=1,database=db)
