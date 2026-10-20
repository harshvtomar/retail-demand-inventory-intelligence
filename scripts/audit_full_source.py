"""Streaming, full-file source integrity audit for authorized M5 CSVs.

No raw M5 records are written to the report. Handles all 30,490 series, all
historical day columns, and all sell-price records without materializing a
58-million-row dataset in memory. This is input validation, not a full warehouse.
"""
import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import re


def audit(raw):
    raw = Path(raw)
    with (raw / 'calendar.csv').open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        needed = {'d', 'date', 'wm_yr_wk', 'weekday'}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError('Calendar schema missing expected fields')
        calendar = {}
        dates = set()
        weeks = set()
        for row in reader:
            k = row['d']
            when = date.fromisoformat(row['date'])
            if k in calendar or when in dates or not re.fullmatch(r'd_[1-9]\d*', k):
                raise ValueError(f'Duplicate or malformed calendar day: {k}')
            week = int(row['wm_yr_wk'])
            if not row['weekday'] or week <= 0:
                raise ValueError(f'Invalid calendar details: {k}')
            calendar[k] = when
            dates.add(when)
            weeks.add(week)
    if not calendar:
        raise ValueError('Calendar is empty')
    day_numbers = {int(k[2:]) for k in calendar}
    if day_numbers != set(range(1, len(calendar) + 1)):
        raise ValueError('Calendar day IDs have gaps')
    if max(dates) - min(dates) != timedelta(days=len(dates)-1):
        raise ValueError('Calendar dates have gaps')

    seen_series, seen_pairs, stores, depts, states = set(), set(), set(), set(), set()
    stratum_counts = {}
    observed = 0
    zero_units = 0
    total_units = 0
    with (raw / 'sales_train_validation.csv').open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        needed = {'id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id'}
        day_cols = [k for k in fields if re.fullmatch(r'd_[1-9]\d*', k)]
        if not needed.issubset(fields) or not day_cols or len(day_cols) != len(set(day_cols)):
            raise ValueError('Sales file schema is invalid')
        if [int(k[2:]) for k in day_cols] != list(range(1,len(day_cols)+1)):
            raise ValueError('Sales day columns out of order or missing')
        if any(k not in calendar for k in day_cols):
            raise ValueError('Sales dates absent from calendar')
        for row in reader:
            if None in row or any(not row[k] for k in needed):
                raise ValueError('Missing sales identifiers or malformed row')
            series = row['id']
            pair = (row['item_id'], row['store_id'])
            if series in seen_series or pair in seen_pairs:
                raise ValueError(f'Duplicate series or store-item: {series}')
            seen_series.add(series)
            seen_pairs.add(pair)
            stores.add(row['store_id'])
            states.add(row['state_id'])
            depts.add(row['dept_id'])
            stratum = (row['store_id'], row['dept_id'])
            stratum_counts[stratum] = stratum_counts.get(stratum, 0) + 1
            vals = [row[k] for k in day_cols]
            if any(not v.isdecimal() for v in vals):
                raise ValueError(f'Invalid/negative daily sales in series {series}')
            total_units += sum(map(int, vals))
            zero_units += vals.count('0')
            observed += len(vals)
    if not seen_series:
        raise ValueError('Sales source empty')
    price_rows = 0
    min_price, max_price = None, None
    with (raw / 'sell_prices.csv').open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'store_id','item_id','wm_yr_wk','sell_price'} <= set(reader.fieldnames or []):
            raise ValueError('Price schema invalid')
        for row in reader:
            if None in row or not all(row.get(k) for k in ('store_id','item_id','wm_yr_wk','sell_price')):
                raise ValueError('Incomplete price record')
            p = float(row['sell_price'])
            if not 0 < p < float('inf'):
                raise ValueError('Invalid nonpositive/nonfinite price')
            if row['store_id'] not in stores:
                raise ValueError('Unknown store in price records')
            if int(row['wm_yr_wk']) not in weeks:
                raise ValueError('Unknown calendar week in price records')
            min_price = p if min_price is None else min(min_price,p)
            max_price = p if max_price is None else max(max_price,p)
            price_rows += 1
    if price_rows == 0:
        raise ValueError('Price file empty')
    return {
        'audit_scope': 'ALL original calendar, sales and sell-price CSV records (not only warehouse sample)',
        'calendar_rows': len(calendar),
        'calendar_min_date': min(dates).isoformat(),
        'calendar_max_date': max(dates).isoformat(),
        'historical_sales_days': len(day_cols),
        'historical_sales_min_date': calendar[day_cols[0]].isoformat(),
        'historical_sales_max_date': calendar[day_cols[-1]].isoformat(),
        'unique_series': len(seen_series),
        'unique_item_store_pairs': len(seen_pairs),
        'stores': len(stores),
        'states': len(states),
        'departments': len(depts),
        'store_department_groups': len(stratum_counts),
        'total_original_daily_values': observed,
        'total_original_sales_units': total_units,
        'zero_unit_days': zero_units,
        'sell_price_records_checked': price_rows,
        'min_positive_selling_price': min_price,
        'max_positive_selling_price': max_price,
        'calendar_sales_price_schema_valid': True,
        'no_duplicate_sales_series_or_item_store': True,
        'every_daily_sales_value_nonnegative_integer': True,
        'price_values_finite_positive_and_calendar_weeks_valid': True,
        'note': 'Price-key uniqueness separately enforced by the SQLite warehouse PRIMARY KEY for the full price file; revenue coverage and sales join reconciliation are measured on the explicitly nonrepresentative 210-series warehouse sample.'
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--raw', default='data/raw')
    p.add_argument('--out', default='reports/full_source_audit.json')
    args = p.parse_args()
    result = audit(args.raw)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
