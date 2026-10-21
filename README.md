# SupplyPulse Intelligence
### Retail Demand Forecasting & Inventory Optimization — Session 1 data/SQL foundation

**Real historical M5 dataset · Python · SQLite · 12 SQL analyses · 6 audited EDA charts · executable notebook · QA**

SupplyPulse is an end-to-end retail analytics portfolio project. **Only the Session 1 analytical foundation exists so far**: authenticated-by-user M5 CSV import, strict file checks and hash logging, a reproducible relational warehouse, real-data exploratory reports, and automated tests. Future demand forecasting, replenishment simulations, Power BI, and deployment are **not yet built**.

## Actual validated results (20 October 2026)
The genuine-format data was supplied by the user in `m5-forecasting-accuracy.zip` after accepting Kaggle access terms. Its five ZIP members passed archive CRC checks. The importer recorded checksums and schema/row counts for three required CSVs.

| Source file | Observed records |
|---|---:|
| `calendar.csv` | 1,969 calendar rows |
| `sales_train_validation.csv` | 30,490 product-store series |
| `sell_prices.csv` | 6,841,121 weekly item-store price rows |

A **full streaming source-data audit** independently checked all **58,327,370 original daily sales values** across 30,490 unique product-store series, and all **6,841,121** selling-price records. It found 65,695,409 total original sales units and 39,777,094 zero-unit observations, with valid original date identifiers, unique sales series and store-item keys, nonnegative integer daily counts, and finite positive prices. Details: `reports/full_source_audit.json`. This is input validation, **not** a full-data warehouse or forecasting run.

The **verified analysis sample is only 210 of the 30,490 product-store series**, first **3 per store and department** (all 10 stores and all 7 departments); this is deterministic but neither random nor statistically representative. Its 401,730 product-store-day observations span **2011-01-29 through 2016-04-24** (1,913 days).

- Observed units (sample only): **210,786**.
- Zero-unit days (sample only): **299,476** (74.55%).
- Days with no observed matched weekly price: **71,421** (17.78%); these days are included in unit KPIs and excluded from calculated priced revenue.
- Six Task 4 EDA charts regenerated with defensible per-series-day rates and properly labelled percentages; the notebook was re-executed with all 8 code cells successful. Monthly trend excludes the two partial months (2011-01, 2016-04). Read `reports/eda_business_review.md` for specific findings and limitations.
- **12/12 SQL queries executed** against the real-data SQLite warehouse and **all 12 independently reconciled** with pandas calculations rebuilt from original M5 CSVs (1,222 numeric output values checked).
- Raw source units and zero counts **independently reconciled** against the SQL fact table, with no change in joined row cardinality.
- **51 automated unit/fixture tests passed** locally, including five tests for the full-source audit and five dedicated independent SQL reconciliation tests. These tests are distinct from the real-data validation above.

Do not generalize these sample findings to the full M5 dataset or treat observed sales as unconstrained demand. No true inventory, lead-time, or stockout data is present. No real-world revenue uplift, company outcomes, or inventory savings are claimed.

## Acquire the source data yourself
Source: [M5 Forecasting — Accuracy (Kaggle)](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data). Follow the competition's access and redistribution rules. The original raw CSVs **are intentionally NOT included** in this repository/package.

After downloading the competition ZIP (or exporting the required files), run from project root:

```bash
python3 -m pip install -r requirements.txt
python3 -m scripts.download_m5 --archive ~/Downloads/m5-forecasting-accuracy.zip
```

Alternative authenticated CLI: `python3 -m pip install kaggle && kaggle auth login && python3 -m scripts.download_m5` (subject to competition permissions). No Kaggle credentials should be stored in the repository.

The importer writes validated files to gitignored `data/raw/` and records SHA-256 fingerprints and import provenance in `data/raw/source_manifest.json`.

## Reproduce real-data analysis

```bash
# deterministic, diverse *prefix* sample: first 3 product series per store/department
python3 -m src.pipeline --sample-per-store-dept 3
python3 -m src.analysis --database data/processed/m5.sqlite
python3 -m scripts.verify_real_m5
python3 -m scripts.reconcile_sql --database data/processed/m5.sqlite
python3 -m scripts.audit_full_source
python3 -m scripts.generate_eda
python3 -m pytest -q
# Jupyter: open notebooks/01_exploratory_analysis.ipynb and run all cells
```

For a smaller but biased first-in-file sample: `python3 -m src.pipeline --limit-series 100`. For a bigger prefix sample raise `--sample-per-store-dept`, bearing in mind SQLite currently imports all 6.8 million price records and occupies significant disk space. Avoid scaling to the full 58 million daily observations without first assessing memory, time, and disk needs. The local derived SQLite database is gitignored and excluded from this ZIP.

## Architecture
Original M5 CSVs (private, gitignored) → strict import + manifest → streaming wide-to-long transformation → normalized products, stores, calendar, weekly prices and unit sales tables → materialized `daily_sales` analytical table with a **left price join**, generated once per pipeline run → SQL and Python KPIs → independent raw-to-SQL reconciliation → executed charts/notebook.

- `src/pipeline.py`: streaming M5 loader, optional stratified prefix sampling, SQL warehouse construction.
- `src/analysis.py`: execute and export 12 real-data SQL queries.
- `scripts/reconcile_sql.py`: independently recreate each report in pandas directly from the three raw CSVs; check 1,222 output numeric cells and core SQL totals, including matched-price revenue. No SQL tables are used to build the expected results.
- `reports/sql_python_reconciliation.json`: committed summary of all 12 completed cross-checks.
- `src/metrics.py`: canonical SQL-derived KPIs.
- `scripts/download_m5.py`: user-authorized download/ZIP import, strict checks, SHA-256 provenance.
- `scripts/verify_real_m5.py`: independent reconciliation of the exact selected raw series against the database.
- `scripts/audit_full_source.py`: streaming full-input audit of all three original source CSVs, without publishing source data.
- `scripts/generate_eda.py`: regenerate 6 sample-specific PNG charts, export their plotting tables, cross-check five plotted datasets against the independently reconciled Task 3 SQL outputs, and create a machine-readable and written business review.
- `scripts/build_eda_notebook.py`: regenerate the reproducible, notebook-based narrative (then execute in Jupyter).
- `reports/eda_business_review.md`: Task 4 evidence-based business interpretation, sample limitations, and interview-safe statements.
- `reports/eda_review.json` and `reports/eda_tables/`: verified chart counts, scope, and six plotting-input datasets.
- `reports/figures/`: 6 actual sample charts; `reports/tables/`: 12 query exports.
- `notebooks/`: executed exploratory notebook with figures and analysis.
- `tests/`: fixture-only tests plus test coverage of sampling, ingest and metrics.
- `.github/workflows/ci.yml`: **verified on GitHub; 51 tests passed**.

See `PROJECT_STATE.md`, `SESSION_LOG.md`, `docs/METHODOLOGY.md`, and `docs/DATA_PROVENANCE.md` for evidence, assumptions, and Session 1 completion status.

## Verified publication and CI (20 October 2026)

The Session 1 foundation is published at [harshvtomar/retail-demand-inventory-intelligence](https://github.com/harshvtomar/retail-demand-inventory-intelligence) on `main`, with all 70 approved source/report files. The first complete publication commit is [`6a0507a2`](https://github.com/harshvtomar/retail-demand-inventory-intelligence/commit/6a0507a2246600c8b0674bf3eaf030094f23d7df). The [hosted GitHub Actions run](https://github.com/harshvtomar/retail-demand-inventory-intelligence/actions/runs/39381480268) completed successfully: **51 tests passed in 3.63 seconds**.

The fixture-based CI does **not** download private/restricted M5 CSVs; real-data integration and independent SQL/EDA checks were performed locally using the user-authorized dataset. The complete source files (30,490 sales series / 58,327,370 observed product-days) were audited; the analytical warehouse remains a **210-series, nonrandom sample**, and its findings cannot be extrapolated to all Walmart stores or customers.

**Session 1 tasks 1–7 are complete at the foundation level.** Actual demand forecasting models, inventory optimization, Power BI and live dashboards belong to future sessions. See [PROJECT_STATE.md](PROJECT_STATE.md), [SESSION_LOG.md](SESSION_LOG.md), [NEXT_SESSION_PROMPT.md](NEXT_SESSION_PROMPT.md), and [release verification](reports/RELEASE_READINESS.md).

## Session 2 — Advanced analytics and leakage-aware demand features (October 2026)

Session 2 adds 14 advanced SQL reports, independently validated source-data reconstruction (985,600 checked numeric cells in the local real-data report), unit-based ABC analysis, complete-week CV-based XYZ segmentation, intermittent-demand diagnostics, leakage-safe historical lag/rolling features, and 28-day end-of-day forecast-origin labels. The original analysis covers **210 nonrandom sampled series and 401,730 product-store-day rows**, not the complete retail population. **69 fixture tests passed** independently in the local publication review; see GitHub Actions for the current hosted run.

Six published vector charts are under **reports/session2/figures/** (SVG). Their underlying data are documented in **reports/session2/**; original ZIP PNG renderings remain in the local source archive, not on GitHub. No actual inventory positions, stockouts, causal impacts, forecast model performance, or financial savings are asserted.

To run safely:

~~~bash
python -m pip install -r requirements-ci.txt
python -m pytest -q
~~~

For optional real-M5 reproduction, obtain the competition CSVs lawfully and follow the existing README instructions for importing into gitignored **data/raw/**. Then run **python -m src.advanced_sql**, **python -m scripts.reconcile_session2**, and **python -m src.session2** against the sampled warehouse. For Session 3 instructions, read NEXT_SESSION_PROMPT.md.

