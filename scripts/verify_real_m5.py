"""Independently reconcile raw M5 selected series against the SQLite warehouse.

Runs against the locally authorized source files. This avoids interpreting
fixture-test success as proof of real-data integrity.
"""
import argparse
import csv
import json
from pathlib import Path
import sqlite3


def verify(raw, database, n_per_store_dept=3):
    raw=Path(raw); sales=raw/'sales_train_validation.csv'
    counts={}; nrows=0; total=0; zeros=0; names=set()
    with sales.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        days=[c for c in reader.fieldnames or [] if c.startswith('d_') and c[2:].isdigit()]
        for row in reader:
            key=(row['store_id'],row['dept_id'])
            if counts.get(key,0)>=n_per_store_dept:continue
            counts[key]=counts.get(key,0)+1
            names.add(row['id'])
            vals=[int(row[c]) for c in days]
            nrows+=len(vals);total+=sum(vals);zeros+=sum(v==0 for v in vals)
    with sqlite3.connect(database) as db:
        actual=db.execute('SELECT COUNT(*),SUM(units),SUM(CASE WHEN units=0 THEN 1 ELSE 0 END),COUNT(DISTINCT series_id) FROM sales').fetchone()
        check_names={row[0] for row in db.execute('SELECT DISTINCT series_id FROM sales')}
        stores=db.execute('SELECT COUNT(*) FROM stores').fetchone()[0]
        dept=db.execute('SELECT COUNT(DISTINCT dept_id) FROM products').fetchone()[0]
        no_duplicate=db.execute('SELECT COUNT(*) FROM (SELECT series_id,day_id FROM sales GROUP BY 1,2 HAVING COUNT(*)>1)').fetchone()[0]
        joined=db.execute('SELECT COUNT(*),SUM(units) FROM daily_sales').fetchone()
        null_prices=db.execute('SELECT COUNT(*) FROM daily_sales WHERE sell_price IS NULL').fetchone()[0]
        valid_price=db.execute('SELECT COUNT(*) FROM daily_sales WHERE sell_price IS NOT NULL').fetchone()[0]
    passed=(actual==(nrows,total,zeros,len(names)) and names==check_names and no_duplicate==0 and joined==(nrows,total) and null_prices+valid_price==nrows)
    report={
        'real_source':'User-provided original M5 competition ZIP, validated SHA-256 in data/raw/source_manifest.json',
        'sampling':'First 3 product series per store/department; not random or representative',
        'source_series':len(names),'source_days':len(days),'source_product_store_days':nrows,
        'source_total_units':total,'source_zero_unit_days':zeros,
        'database_series':actual[3], 'database_product_store_days':actual[0],
        'database_total_units':actual[1],'database_zero_unit_days':actual[2],
        'stores':stores,'departments':dept,'unique_series_day_keys':no_duplicate==0,
        'left_join_preserved_grain_and_units':joined==(nrows,total),
        'missing_price_days':null_prices,'priced_days':valid_price,
        'raw_vs_sql_reconciled':bool(passed)
    }
    if not passed:raise AssertionError(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--raw',default='data/raw')
    a.add_argument('--database',default='data/processed/m5.sqlite')
    a.add_argument('--sample-per-store-dept',default=3,type=int)
    a.add_argument('--out',default='reports/real_data_reconciliation.json')
    args=a.parse_args()
    result=verify(args.raw,args.database,args.sample_per_store_dept)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
