# SupplyPulse — Session 1, Task 4: Verified exploratory review

All results below apply **only to the 210 deterministically chosen product-store series** in the local M5 sample (three first-listed series per store/department).
This is a **nonrandom, nonrepresentative** sample; differences are descriptive and are **not** full-Walmart estimates or causal effects.

## Scope and data integrity

- Observations: **401,730** product-store-days, **210** series, **10** stores, 2011-01-29 to 2016-04-24.
- Observed unit sales: **210,786**; zero-unit days: **299,476 (74.55%)**.
- Available weekly-price matches: **330,309 (82.22%)**; unmatched-price days: **71,421**.
- All six plotted series sum correctly to the relevant warehouse totals; **5 chart datasets** match independently reconciled Task 3 query exports.

## Evidence-backed findings and limitations

### 1. Monthly observed unit rate

- The trend chart uses **62 complete months** and plots units per product-store-day to avoid mistaking different month lengths for changing demand.
- Boundary months excluded from the line: 2011-01 (3 days), 2016-04 (24 days).
- The series is descriptive, with possible product lifecycle, promotion, prices, and changing availability mixed together. It is **not** a forecast or isolated seasonal effect.

### 2. Store comparison

- Largest observed sample rate: **WI_2**, **0.756** units per product-store-day (**30,370** units).
- Smallest: **CA_4**, **0.332** units per product-store-day (**13,331** units).
- Each store has the same number of sampled series, but this does not establish population-wide store rankings.

### 3. Product category

- Highest observed per-series-day rate: **FOODS**, **0.799** units. Lowest: **HOBBIES**, **0.194** units.
- Comparisons use *rates*, not category total units, since categories contain different numbers of sampled item-store series.

### 4. Weekday pattern

- Weekend days averaged **0.628** units per series-day; Monday–Friday averaged **0.483** (**30.0% higher** in this sample).
- This is an observed association, not evidence that weekend timing causes a sales lift.

### 5. Zero-unit share

- The highest zero-day share was **CA_4** at **79.79%**; the lowest was **CA_3** at **66.01%**.
- A zero sale can reflect no purchase demand, shelf absence, product lifecycle, or other factors. **Stockout frequency cannot be inferred** without inventory records.

### 6. Weekly selling-price coverage

- Lowest observed weekly-price matching share: **CA_2** at **75.10%**; highest: **TX_3** at **84.88%**.
- A missing weekly price is not evidence of a free sale, unavailable product, or data corruption. Revenue can be computed only for matched observations.

## Business interpretation for an interview

- Prioritize **investigating** store/category/day-of-week heterogeneity on a better-designed representative panel; do not roll out changes using sample ranks alone.
- Before inventory policy modeling, obtain or explicitly simulate lead times, available stock, replenishment rules and costs. Never label simulated savings as achieved.
- Forecasting work should establish chronological holdouts, a simple baseline, and leakage checks; avoid fitting models on the holdout interval.

## Reproduction and evidence

`python -m scripts.generate_eda --database data/processed/m5.sqlite --sql-exports reports/tables`

- Six figure PNGs: `reports/figures/`.
- Six plotting-input tables: `reports/eda_tables/`.
- Machine-readable summary: `reports/eda_review.json`.
- Interactive executed notebook: `notebooks/01_exploratory_analysis.ipynb`.
- Task 3 source-to-SQL verification: `reports/sql_python_reconciliation.json`.
