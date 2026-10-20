"""Build a notebook whose figures and source tables reuse the tested EDA code.

Run notebook with Jupyter from either the repository root or notebooks/ folder.
This builder does not execute it; notebook execution is verified separately.
"""
from pathlib import Path
import nbformat as nbf

ROOT=Path(__file__).resolve().parents[1]
SECTIONS=[
('monthly_units','Monthly observed unit rate',
 'The chart uses **complete calendar months only** and a product-store-day denominator. The full detail table retains the partial boundary months; 2011-01 and 2016-04 are omitted from the trend. This prevents plotting partial months as artificial declines. Historical changes are not forecasts.'),
('store_units','Store-level observed unit rate',
 'Rates account for the same number of sampled series-days per store. The underlying items were **not selected randomly**, so the chart is not a ranking of all products or entire stores.'),
('category_units','Category-level observed unit rate',
 'Use per-series-day rates, **not raw unit totals**, because the seven departments belong to categories with different sample sizes. No causality or population representativeness is established.'),
('weekday_mean','Weekday and weekend patterns',
 'Averages use total observed product-store-days per weekday as the denominator. Saturdays and Sundays have different counts than some weekdays. Differences are descriptive, not causal effects.'),
('zero_share','Share of zero-unit sales days',
 'A zero-sales observation does **not** show a stockout. We lack on-hand inventory, product availability and replenishment records. The percentages are fractions of sampled product-store-days.'),
('price_coverage','Historical selling-price matching coverage',
 'A missing matched weekly price is **not zero revenue** or necessarily a data error. The plotted share is the proportion of sample product-store-days with an observed weekly sell price. Unmatched days must be excluded from priced-revenue estimates.'),
]

def build():
    cells=[nbf.v4.new_markdown_cell('''# SupplyPulse Intelligence — Session 1, Task 4: Exploratory analysis

**Historical M5 sales; reproducible, sampled analytics — NOT a demand forecast.**

- Original files: Kaggle M5 `sales_train_validation.csv`, `calendar.csv`, `sell_prices.csv`, provided by the user under the competition's access terms.
- Analysis subset: first three product-store series in every `(store_id, department)` group across ten stores and seven departments (**210 nonrandom series**).
- The following comparisons **must not be extrapolated** to full-Walmart sales, typical stores or true unconstrained demand. No observed inventory, supplier lead times, stockouts, or profit are contained in these inputs.
- Both the plots and their tables come from `scripts/generate_eda.py`, where they are reconciled with the previously independently checked Task 3 SQL outputs.

To rebuild: `python -m src.pipeline --sample-per-store-dept 3`, `python -m src.analysis --database data/processed/m5.sqlite`, `python -m scripts.generate_eda`, then execute this notebook.
'''),nbf.v4.new_code_cell('''from pathlib import Path
import json
import sqlite3
import sys
import pandas as pd
from IPython.display import Image, Markdown, display

root = Path.cwd().resolve()
if root.name == 'notebooks':
    root = root.parent
if not (root / 'scripts' / 'generate_eda.py').exists():
    raise FileNotFoundError('Open this notebook from the repository root or notebooks/ directory.')
sys.path.insert(0, str(root))
from scripts.generate_eda import collect_eda, check_eda, plot_chart, build_review

database = root / 'data' / 'processed' / 'm5.sqlite'
if not database.exists():
    raise FileNotFoundError('Missing local real-data warehouse; run the ingestion pipeline from README.md.')
with sqlite3.connect(database) as db:
    frames = collect_eda(db)
    checked = check_eda(db, frames, root / 'reports' / 'tables')
print('Nonrandom sample verification:',json.dumps(checked,indent=2))
''')]
    for tag,header,interpretation in SECTIONS:
        cells.append(nbf.v4.new_markdown_cell(f'## {header}\n\n{interpretation}\n\n**Read alongside:** `reports/eda_business_review.md` for measured results and limits.'))
        cells.append(nbf.v4.new_code_cell(f'''tag = '{tag}'
df = frames[tag].copy()
display(df.head(12))
plot = root / 'reports' / 'figures' / f'{{tag}}.png'
plot.parent.mkdir(parents=True, exist_ok=True)
plot_chart(tag, df, plot)
display(Image(filename=str(plot)))
'''))
    cells.append(nbf.v4.new_markdown_cell('''## Verified business interpretation

**Avoid overstating these associations.** The notebook does not demonstrate a causal weekend effect, confirmed stockouts, official financial performance, or inventory savings. Forecasting must be evaluated on a chronologically separated test window in a later session.'''))
    cells.append(nbf.v4.new_code_cell('''display(Markdown(build_review(frames, checked)))'''))
    note=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}})
    output=ROOT/'notebooks'/'01_exploratory_analysis.ipynb'
    nbf.write(note,output)
    print(f'Built {output} with {len(cells)} cells.')

if __name__=='__main__':build()
