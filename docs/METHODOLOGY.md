# Session 1 analytic methodology and limitations

## Ingestion and source controls
`calendar.csv`, `sales_train_validation.csv`, and `sell_prices.csv` are imported only after strict header and record-count checks. The importer records bytes, SHA-256 and acquisition metadata. Original Kaggle CSVs are kept locally and excluded from Git.

## Deterministic sampling, not random inference
For a computationally manageable yet cross-store subset, iterate `sales_train_validation.csv` in source file order and choose the first 3 series for every `(store_id, dept_id)` stratum. This yields 210 unique product-store series, covering 10 stores, 7 departments, 21 distinct product IDs, 1,913 observed dates, 401,730 daily rows. Because these are the earliest series in each stratum, they need not represent average item demand, sales or price coverage across the population. Store/category comparisons describe the sample only.

## Warehouse grain and price treatment
Fact `sales` has grain `(series_id, day_id)`. Weekly prices have grain `(store_id, item_id, wm_yr_wk)` with duplicate keys rejected. Dates and weekly price join through the calendar. The reproducibly materialized `daily_sales` analytical table uses a LEFT JOIN for price so no valid sales rows disappear if price is missing. Priced revenue only sums `units * sell_price` where observed prices exist; it is not full company revenue and does not imply unobserved sale-price values are zero.

## Independent reconciliation
The raw wide CSV is re-read independently and only selected rows are summed; the resulting 210,786 unit sales and 299,476 zero-unit days exactly equal the SQLite fact table. Both fact and joined view contain 401,730 rows, and duplicate `(series_id, day_id)` keys are zero. Price coverage: 330,309 priced observations; 71,421 with no matched weekly price.

## Business interpretation
Analysis covers observed daily sales, zero-unit day share, available price coverage, seasonal differences, and sample-specific store/category trends. A zero-unit day is not proof of a stockout. Event-day differences are associations, not causal effects. Inventory reorder points, demand forecasts, cost reductions and service-level improvements require later modeling, assumptions, and out-of-sample verification.

## Session 1 Task 3 — independent validation of all SQL reports
`src/analysis.py` runs twelve read-only exploratory SQL analyses and exports CSVs. `scripts/reconcile_sql.py` independently reconstructs the same 210-series sample **from the original sales, calendar, and price CSVs**, then derives each result with pandas and NumPy rather than reading the SQL warehouse. Every result key and 1,222 numerical fields were compared, allowing only 0.00011 absolute tolerance for rounded floating-point measures and requiring exact integer aggregates. A separate comparison verifies row count, unit totals, zero-unit days, price coverage, and available-price revenue ($778,107.05). All checks passed on 20 October 2026.

The joined daily analytical dataset is materialized once per ingestion run rather than executing an expensive price join for every analytical SQL query. This is a batch analytical snapshot, not an updatable view: **rerun the pipeline after changing raw files**. Unit tests explicitly detect tampered query exports, missing reports, and inconsistent priced revenue.

Query 12 provides descriptive observed price-band summaries; it is not a causal price elasticity model. Reported category/store differences and weekend/day-of-week figures concern only the nonrandom prefix sample.

## Session 1 Task 4 — EDA notebook and chart assurance (completed 20 October 2026)
The exploratory notebook was rebuilt with reusable chart-query definitions in `scripts/generate_eda.py` and executed (8/8 code cells). Six PNG figures and six plotting-input CSVs were regenerated from the authentic 210-series M5 warehouse. Chart totals and rates were cross-checked with warehouse counts and the **five corresponding Task 3 raw-source-reconciled SQL exports**; the sixth figure, weekly-price match coverage, was checked against the independently validated priced/unpriced-row totals.

Daily unit totals cannot meaningfully compare categories with unequal sample sizes: charts therefore use observed **units per product-store-day**. The monthly trend omits the incomplete first and last months and uses the same denominator. Zero-unit shares and price-match shares are explicitly labelled percentages with the correct denominator. The sample is not a probability sample; no statistical uncertainty intervals or full-retailer extrapolations are justified. The weekend contrast is merely an observational pattern, not a treatment effect.

Primary evidence: `reports/eda_business_review.md`, `reports/eda_review.json`, six files in `reports/eda_tables/`, six figures in `reports/figures/`, and executed `notebooks/01_exploratory_analysis.ipynb`. Nine additional fixture-based regression tests cover chart invariants, invalid percentages, incomplete month handling, export availability, and regenerating all files. Current local suite: **51 passed, 0 failed**.
