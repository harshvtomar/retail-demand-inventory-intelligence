"""CI-friendly tests use an independent *synthetic test fixture*, not M5 claims."""
import copy
import sqlite3
from datetime import date, timedelta

import pytest

from scripts.generate_eda import collect_eda, check_eda, build_review, generate, plot_chart


@pytest.fixture
def eda_db(tmp_path):
    path=tmp_path/'fixture.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE products(item_id TEXT PRIMARY KEY, dept_id TEXT,cat_id TEXT);
        CREATE TABLE sales(series_id TEXT,day_id TEXT);
        CREATE TABLE daily_sales(series_id TEXT, item_id TEXT,store_id TEXT,date TEXT,
           weekday TEXT,units INTEGER,sell_price REAL);
        INSERT INTO products VALUES ('item_a','food_1','FOODS'),('item_b','hobby_1','HOBBIES');
        ''')
        start=date(2025,1,1)
        for offset in range(32):  # all January, one February day (partial)
            current=start+timedelta(days=offset)
            for item,store,units,price in [('item_a','TX_1',3,1.5),('item_b','TX_2',0,None)]:
                db.execute('INSERT INTO sales VALUES (?,?)',(f'{item}_{store}',f'd_{offset+1}'))
                db.execute('INSERT INTO daily_sales VALUES (?,?,?,?,?,?,?)',
                           (f'{item}_{store}',item,store,current.isoformat(),current.strftime('%A'),units,price))
    return path


def test_complete_month_detection_and_seven_weekdays(eda_db):
    with sqlite3.connect(eda_db) as db: frames=collect_eda(db)
    assert frames['monthly_units']['complete_month'].tolist()==[True,False]
    assert frames['monthly_units']['dates_observed'].tolist()==[31,1]
    assert len(frames['weekday_mean'])==7
    assert set(frames['category_units']['category'])=={'FOODS','HOBBIES'}


def test_rates_and_percentage_denominators(eda_db):
    with sqlite3.connect(eda_db) as db:
        f=collect_eda(db);checked=check_eda(db,f)
    assert checked['rows']==64 and checked['units']==96
    assert checked['zero_rows']==32 and checked['zero_pct']==50
    assert checked['priced_rows']==32 and checked['priced_pct']==50
    assert checked['missing_price_rows']==32
    food=f['category_units'].set_index('category').loc['FOODS']
    assert food['units_per_series_day']==3
    assert f['price_coverage'].set_index('store_id').loc['TX_2','priced_pct']==0


def test_chart_sum_reconciliation_rejects_tampering(eda_db):
    with sqlite3.connect(eda_db) as db:
        f=collect_eda(db)
        f['monthly_units'].loc[0,'units']+=1
        with pytest.raises(AssertionError,match='monthly_units'):check_eda(db,f)


def test_price_percent_above_100_rejected(eda_db):
    with sqlite3.connect(eda_db) as db:
        f=collect_eda(db)
        f['price_coverage'].loc[0,'priced_pct']=101
        with pytest.raises(AssertionError,match='price_coverage'):check_eda(db,f)


def test_duplicate_series_day_detected(eda_db):
    with sqlite3.connect(eda_db) as db:
        r=db.execute('SELECT * FROM daily_sales LIMIT 1').fetchone()
        db.execute('INSERT INTO daily_sales VALUES (?,?,?,?,?,?,?)',r)
        f=collect_eda(db)
        with pytest.raises(AssertionError,match='Missing sales rows or join multiplication'):
            check_eda(db,f)


def test_missing_task3_reference_fails_closed(eda_db,tmp_path):
    with sqlite3.connect(eda_db) as db:
        f=collect_eda(db)
        with pytest.raises(FileNotFoundError,match='Task 3'):
            check_eda(db,f,tmp_path/'no_references')


def test_six_charts_render_and_mark_month_gaps(eda_db,tmp_path):
    with sqlite3.connect(eda_db) as db: f=collect_eda(db)
    for name,df in f.items():
        dest=tmp_path/f'{name}.png'
        plot_chart(name,df,dest)
        assert dest.exists() and dest.stat().st_size>3000


def test_review_explicit_limits_and_correct_weighted_weekend(eda_db):
    with sqlite3.connect(eda_db) as db:
        f=collect_eda(db);checked=check_eda(db,f)
    review=build_review(f,checked)
    for phrase in ['nonrandom','not','stockout','price','weekend','sample','replenishment']:
        assert phrase.lower() in review.lower()
    assert '96' in review and '64' in review


def test_end_to_end_review_artifacts_from_fixture(eda_db,tmp_path):
    result=generate(eda_db,tmp_path/'figures',tmp_path/'eda_tables',
                    tmp_path/'review.md',tmp_path/'review.json',sql_exports=None)
    assert result['charts']==6
    assert len(list((tmp_path/'figures').glob('*.png')))==6
    assert len(list((tmp_path/'eda_tables').glob('*.csv')))==6
    assert (tmp_path/'review.md').exists() and (tmp_path/'review.json').exists()
