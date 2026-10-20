"""Reproduce six M5 exploratory charts and evidence-audited business findings.

Uses the *sampled* SQLite warehouse only. The selected 210 source series are
nonrandom; these outputs are NOT company-wide estimates or causal findings.
"""
from __future__ import annotations

import argparse
import calendar as monthcalendar
import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd

SQL = {
    'monthly_units': '''SELECT substr(date,1,7) month, COUNT(DISTINCT date) dates_observed,
        COUNT(*) series_days, SUM(units) units, AVG(units * 1.0) units_per_series_day
        FROM daily_sales GROUP BY 1 ORDER BY 1''',
    'store_units': '''SELECT store_id, COUNT(*) series_days, COUNT(DISTINCT item_id) item_count,
        SUM(units) units, AVG(units * 1.0) units_per_series_day
        FROM daily_sales GROUP BY 1 ORDER BY 1''',
    'category_units': '''SELECT p.cat_id category, COUNT(*) series_days,
        SUM(d.units) units, AVG(d.units * 1.0) units_per_series_day
        FROM daily_sales d JOIN products p USING(item_id) GROUP BY 1 ORDER BY 1''',
    'weekday_mean': '''SELECT weekday, COUNT(*) series_days, SUM(units) units,
        AVG(units * 1.0) units_per_series_day FROM daily_sales GROUP BY 1''',
    'zero_share': '''SELECT store_id, COUNT(*) series_days,
        SUM(CASE WHEN units = 0 THEN 1 ELSE 0 END) zero_days,
        100.0 * AVG(CASE WHEN units = 0 THEN 1.0 ELSE 0 END) zero_pct
        FROM daily_sales GROUP BY 1 ORDER BY 1''',
    'price_coverage': '''SELECT store_id, COUNT(*) series_days,
        SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END) priced_days,
        100.0 * AVG(CASE WHEN sell_price IS NOT NULL THEN 1.0 ELSE 0 END) priced_pct
        FROM daily_sales GROUP BY 1 ORDER BY 1''',
}
WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']


def collect_eda(db: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    """Return chart source data, with complete-month flag and ordered weekdays."""
    result = {name: pd.read_sql_query(query, db) for name,query in SQL.items()}
    for name,df in result.items():
        if df.empty:
            raise ValueError(f'No real warehouse data for chart {name}')
    monthly = result['monthly_units']
    monthly['complete_month'] = [
        int(days) == monthcalendar.monthrange(*map(int, month.split('-')))[1]
        for month, days in zip(monthly['month'], monthly['dates_observed'])
    ]
    weekdays = result['weekday_mean']
    if set(weekdays['weekday']) != set(WEEKDAYS):
        raise ValueError('Incomplete weekday coverage')
    result['weekday_mean'] = weekdays.set_index('weekday').loc[WEEKDAYS].reset_index()
    return result


def check_eda(db: sqlite3.Connection, frames: dict[str, pd.DataFrame], sql_exports: Path | None = None) -> dict:
    """Defend charts against double-counting, unit/percent mistakes and SQL drift."""
    rows, units, zeros, priced, first_date, last_date, series, stores = db.execute('''
        SELECT COUNT(*),SUM(units),SUM(CASE WHEN units=0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END),
        MIN(date),MAX(date),COUNT(DISTINCT series_id),COUNT(DISTINCT store_id)
        FROM daily_sales''').fetchone()
    if not rows or rows != db.execute('SELECT COUNT(*) FROM sales').fetchone()[0]:
        raise AssertionError('Missing sales rows or join multiplication')
    if db.execute('''SELECT COUNT(*) FROM (
        SELECT series_id,date FROM daily_sales GROUP BY 1,2 HAVING COUNT(*)>1
    )''').fetchone()[0]:
        raise AssertionError('Duplicate series-date rows in warehouse')
    for name in ('monthly_units', 'store_units','category_units','weekday_mean'):
        f=frames[name]
        if int(f['units'].sum())!=units or int(f['series_days'].sum())!=rows:
            raise AssertionError(f'{name}: total units or row counts do not reconcile')
    for name, count_col in [('zero_share','zero_days'),('price_coverage','priced_days')]:
        f=frames[name]
        expected = zeros if name == 'zero_share' else priced
        if int(f[count_col].sum())!=expected or int(f['series_days'].sum())!=rows:
            raise AssertionError(f'{name}: numerator or row counts do not reconcile')
        value_col = 'zero_pct' if name == 'zero_share' else 'priced_pct'
        if (f[value_col].lt(0) | f[value_col].gt(100)).any():
            raise AssertionError(f'{name}: invalid percentage')
    if int(frames['monthly_units']['dates_observed'].sum()) != db.execute('SELECT COUNT(DISTINCT date) FROM daily_sales').fetchone()[0]:
        raise AssertionError('Monthly dates incomplete')

    # Cross-check chart aggregates against the 12 SQL exports that were independently
    # reconstructed from original source CSVs in Task 3, when available.
    verified = []
    if sql_exports is not None:
        sql_exports = Path(sql_exports)
        def reference(n):
            f=sql_exports/f'query_{n:02d}.csv'
            if not f.exists(): raise FileNotFoundError(f'Missing Task 3 verified SQL reference: {f}')
            return pd.read_csv(f, dtype=str)
        def pairs_equal(observed, expected, label):
            a = dict(observed)
            b = dict(expected)
            if a != b: raise AssertionError(f'{label} does not match Task 3 verified SQL report')
            verified.append(label)
        pairs_equal(zip(frames['monthly_units']['month'], frames['monthly_units']['units'].astype(int)),
                    zip(reference(1)['month'], reference(1)['units'].astype(int)), 'monthly_units')
        pairs_equal(zip(frames['store_units']['store_id'], frames['store_units']['units'].astype(int)),
                    zip(reference(2)['store_id'], reference(2)['units'].astype(int)), 'store_units')
        category_ref = reference(5)
        cat_ref = category_ref.assign(units=category_ref['units'].astype(int)).groupby('cat_id')['units'].sum()
        pairs_equal(zip(frames['category_units']['category'],frames['category_units']['units'].astype(int)),
                    cat_ref.items(), 'category_units')
        pairs_equal(zip(frames['weekday_mean']['weekday'],frames['weekday_mean']['units'].astype(int)),
                    zip(reference(7)['weekday'],reference(7)['units'].astype(int)), 'weekday_mean')
        pairs_equal(zip(frames['zero_share']['store_id'],frames['zero_share']['zero_days'].astype(int)),
                    zip(reference(11)['store_id'],reference(11)['zero_days'].astype(int)), 'zero_share')

    return {'scope':'Nonrandom prefix sample: do not generalize to retailer',
            'rows':rows,'series':series,'stores':stores,'units':units,'zero_rows':zeros,
            'zero_pct':100*zeros/rows,'priced_rows':priced,'priced_pct':100*priced/rows,
            'missing_price_rows':rows-priced,'first_date':first_date,'last_date':last_date,
            'charts':len(frames),'references_reconciled':verified}


def plot_chart(name: str, df: pd.DataFrame, dest: Path) -> None:
    fig,ax=plt.subplots(figsize=(10,4.7))
    if name == 'monthly_units':
        x=df.loc[df['complete_month']]
        if x.empty: raise ValueError('No complete months: cannot plot monthly trend')
        ax.plot(range(len(x)), x['units_per_series_day'], linewidth=1.8)
        ticks=list(range(0,len(x),max(1,len(x)//9)))
        ax.set_xticks(ticks, [x['month'].iloc[i] for i in ticks],rotation=38)
        ax.set(title='Observed unit rate by complete month — sampled series',
               xlabel='Month (partial months excluded)',ylabel='Units per product-store-day')
    else:
        col,label,ylab = {
          'store_units': ('store_id','units_per_series_day','Units per product-store-day'),
          'category_units': ('category','units_per_series_day','Units per product-store-day'),
          'weekday_mean': ('weekday','units_per_series_day','Units per product-store-day'),
          'zero_share': ('store_id','zero_pct','Zero-unit product-store-days (%)'),
          'price_coverage': ('store_id','priced_pct','Days with matched weekly price (%)'),
        }[name]
        view=df.sort_values(label,ascending=False) if name in ['store_units','category_units'] else df
        ax.bar(view[col],view[label]);ax.tick_params(axis='x',rotation=36)
        if name == 'store_units': title='Observed unit rate by store — sampled items'
        elif name == 'category_units':title='Observed unit rate by category — sampled items'
        elif name == 'weekday_mean':title='Mean daily unit rate by weekday — sampled items'
        elif name == 'zero_share':title='Zero-unit day share by store (NOT observed stockouts)'
        else:title='Matched-price coverage by store (NOT completeness of sales)'
        ax.set(title=title,xlabel=col.replace('_',' ').title(),ylabel=ylab)
        if name in ['zero_share','price_coverage']:
            ax.set_ylim(0,100)
    ax.grid(axis='y',alpha=.18)
    fig.text(.01,.01,'Source: original M5 data; first 3 series per store/department, NONRANDOM SAMPLE',fontsize=8)
    fig.tight_layout(rect=(0,.035,1,1))
    fig.savefig(dest, dpi=145)
    plt.close(fig)


def build_review(frames:dict[str,pd.DataFrame], checked:dict) -> str:
    month=frames['monthly_units']
    incomplete=month.loc[~month['complete_month'],['month','dates_observed']]
    store=frames['store_units'].sort_values('units_per_series_day',ascending=False)
    category=frames['category_units'].sort_values('units_per_series_day',ascending=False)
    weekday=frames['weekday_mean']
    weekend=weekday.loc[weekday['weekday'].isin(['Saturday','Sunday'])]
    workweek=weekday.loc[~weekday['weekday'].isin(['Saturday','Sunday'])]
    wend=weekend['units'].sum()/weekend['series_days'].sum()
    wk=workweek['units'].sum()/workweek['series_days'].sum()
    zero=frames['zero_share'].sort_values('zero_pct',ascending=False)
    price=frames['price_coverage'].sort_values('priced_pct')
    lines=[
        '# SupplyPulse — Session 1, Task 4: Verified exploratory review',
        '',
        'All results below apply **only to the 210 deterministically chosen product-store series** in the local M5 sample (three first-listed series per store/department).',
        'This is a **nonrandom, nonrepresentative** sample; differences are descriptive and are **not** full-Walmart estimates or causal effects.',
        '',
        '## Scope and data integrity',
        '',
        f"- Observations: **{checked['rows']:,}** product-store-days, **{checked['series']}** series, **{checked['stores']}** stores, {checked['first_date']} to {checked['last_date']}.",
        f"- Observed unit sales: **{checked['units']:,}**; zero-unit days: **{checked['zero_rows']:,} ({checked['zero_pct']:.2f}%)**.",
        f"- Available weekly-price matches: **{checked['priced_rows']:,} ({checked['priced_pct']:.2f}%)**; unmatched-price days: **{checked['missing_price_rows']:,}**.",
        f"- All six plotted series sum correctly to the relevant warehouse totals; **{len(checked['references_reconciled'])} chart datasets** match independently reconciled Task 3 query exports.",
        '',
        '## Evidence-backed findings and limitations',
        '',
        '### 1. Monthly observed unit rate',
        '',
        f"- The trend chart uses **{int(month['complete_month'].sum())} complete months** and plots units per product-store-day to avoid mistaking different month lengths for changing demand.",
        '- Boundary months excluded from the line: '+', '.join(f"{r.month} ({int(r.dates_observed)} days)" for r in incomplete.itertuples())+'.',
        '- The series is descriptive, with possible product lifecycle, promotion, prices, and changing availability mixed together. It is **not** a forecast or isolated seasonal effect.',
        '',
        '### 2. Store comparison',
        '',
        f"- Largest observed sample rate: **{store.iloc[0]['store_id']}**, **{store.iloc[0]['units_per_series_day']:.3f}** units per product-store-day (**{int(store.iloc[0]['units']):,}** units).",
        f"- Smallest: **{store.iloc[-1]['store_id']}**, **{store.iloc[-1]['units_per_series_day']:.3f}** units per product-store-day (**{int(store.iloc[-1]['units']):,}** units).",
        '- Each store has the same number of sampled series, but this does not establish population-wide store rankings.',
        '',
        '### 3. Product category',
        '',
        f"- Highest observed per-series-day rate: **{category.iloc[0]['category']}**, **{category.iloc[0]['units_per_series_day']:.3f}** units. Lowest: **{category.iloc[-1]['category']}**, **{category.iloc[-1]['units_per_series_day']:.3f}** units.",
        '- Comparisons use *rates*, not category total units, since categories contain different numbers of sampled item-store series.',
        '',
        '### 4. Weekday pattern',
        '',
        f'- Weekend days averaged **{wend:.3f}** units per series-day; Monday–Friday averaged **{wk:.3f}** (**{(wend/wk-1)*100:.1f}% higher** in this sample).',
        '- This is an observed association, not evidence that weekend timing causes a sales lift.',
        '',
        '### 5. Zero-unit share',
        '',
        f"- The highest zero-day share was **{zero.iloc[0]['store_id']}** at **{zero.iloc[0]['zero_pct']:.2f}%**; the lowest was **{zero.iloc[-1]['store_id']}** at **{zero.iloc[-1]['zero_pct']:.2f}%**.",
        '- A zero sale can reflect no purchase demand, shelf absence, product lifecycle, or other factors. **Stockout frequency cannot be inferred** without inventory records.',
        '',
        '### 6. Weekly selling-price coverage',
        '',
        f"- Lowest observed weekly-price matching share: **{price.iloc[0]['store_id']}** at **{price.iloc[0]['priced_pct']:.2f}%**; highest: **{price.iloc[-1]['store_id']}** at **{price.iloc[-1]['priced_pct']:.2f}%**.",
        '- A missing weekly price is not evidence of a free sale, unavailable product, or data corruption. Revenue can be computed only for matched observations.',
        '',
        '## Business interpretation for an interview',
        '',
        '- Prioritize **investigating** store/category/day-of-week heterogeneity on a better-designed representative panel; do not roll out changes using sample ranks alone.',
        '- Before inventory policy modeling, obtain or explicitly simulate lead times, available stock, replenishment rules and costs. Never label simulated savings as achieved.',
        '- Forecasting work should establish chronological holdouts, a simple baseline, and leakage checks; avoid fitting models on the holdout interval.',
        '',
        '## Reproduction and evidence',
        '',
        '`python -m scripts.generate_eda --database data/processed/m5.sqlite --sql-exports reports/tables`',
        '',
        '- Six figure PNGs: `reports/figures/`.',
        '- Six plotting-input tables: `reports/eda_tables/`.',
        '- Machine-readable summary: `reports/eda_review.json`.',
        '- Interactive executed notebook: `notebooks/01_exploratory_analysis.ipynb`.',
        '- Task 3 source-to-SQL verification: `reports/sql_python_reconciliation.json`.',
    ]
    return '\n'.join(lines)+'\n'


def generate(database, output='reports/figures', tables='reports/eda_tables', review='reports/eda_business_review.md',
             summary='reports/eda_review.json', sql_exports='reports/tables') -> dict:
    output,tables,review,summary = map(Path, [output,tables,review,summary]);
    output.mkdir(parents=True, exist_ok=True);tables.mkdir(parents=True,exist_ok=True)
    review.parent.mkdir(parents=True,exist_ok=True);summary.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(database) as db:
        frames=collect_eda(db)
        checked=check_eda(db,frames,Path(sql_exports) if sql_exports else None)
    for name,frame in frames.items():
        frame.to_csv(tables/f'{name}.csv',index=False)
        plot_chart(name,frame,output/f'{name}.png')
    review.write_text(build_review(frames,checked),encoding='utf-8')
    summary.write_text(json.dumps(checked,indent=2)+'\n',encoding='utf-8')
    return checked

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--database',default='data/processed/m5.sqlite')
    parser.add_argument('--output',default='reports/figures')
    parser.add_argument('--tables',default='reports/eda_tables')
    parser.add_argument('--review',default='reports/eda_business_review.md')
    parser.add_argument('--summary',default='reports/eda_review.json')
    parser.add_argument('--sql-exports',default='reports/tables')
    args=parser.parse_args()
    print(json.dumps(generate(args.database,args.output,args.tables,args.review,args.summary,args.sql_exports),indent=2))
