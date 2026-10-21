# SupplyPulse Intelligence — Session 2 publication checkpoint (22 October 2026)

This section supersedes earlier historical Session 1 and local Session 2 publication notes below, while preserving the original development record.

- **Source:** Genuine user-authorized Walmart M5 files; analytics use a deterministic **210-series nonrandom prefix sample** (401,730 series-day rows), not a representative retail-population sample. The complete source was audited in Session 1, not processed as a full-sized analytical warehouse.
- **Session 2 SQL:** 14 advanced read-only reports in sql/advanced_queries.sql; original-CSV independent numeric reconciliation report covers 985,600 numeric cells with reported absolute tolerance ≤ 1e-6. Detailed record-level exports and raw original CSV files remain absent from GitHub.
- **Analyses:** ABC unit-contribution classes 97 A / 63 B / 50 C; complete-week XYZ classes 2 X / 75 Y / 133 Z; intermittent categories 180 intermittent / 30 lumpy. These results are descriptive only and must be recomputed per training fold before predictive use.
- **Feature design:** 401,730 one-day historical feature rows and 13,860 28-day forecast-origin records were produced locally. No forecasting model has yet been fitted or evaluated.
- **Charts:** Six numerical SVG visualizations generated from verified aggregate data and the local historical histogram. The six original PNG renderings from the Session 2 ZIP have *not* been transferred to GitHub; SVGs are published instead.
- **Tests:** 69 passed, 0 failed on independently executed fixture tests in the current environment (22 October 2026). This is separate from GitHub Actions verification.
- **Verified GitHub Actions:** https://github.com/harshvtomar/retail-demand-inventory-intelligence/actions/runs/39677007872 — succeeded for source commit 61374a6b89f61a1ee7178308781b6fe44515a0c8; runner log: **69 passed in 3.70s, 0 failed** (fixture tests; original Kaggle M5 files are not used in public CI).
- **Next:** Session 3 — leakage-safe chronological validation, baseline and ML demand forecasting, with final 2016-03-28 through 2016-04-24 window untouched until test. Do not claim realized inventory savings or actual stockout observations.

---

# SupplyPulse Intelligence — Session 1 checkpoint
**As of 20 October 2026**

## Verified GitHub publication and hosted CI (CURRENT)

- Repository: [harshvtomar/retail-demand-inventory-intelligence](https://github.com/harshvtomar/retail-demand-inventory-intelligence), branch `main` (public).
- First complete 70-file publication commit: `6a0507a2246600c8b0674bf3eaf030094f23d7df`.
- [Actual GitHub Actions run](https://github.com/harshvtomar/retail-demand-inventory-intelligence/actions/runs/39381480268): **success, 51 passed in 3.63 seconds**, 0 failed. Workflow tests use fixtures without private Kaggle files.
- 30,490 genuine original sales series / 58,327,370 daily source values audited; SQL/EDA warehouse contains **210 nonrandom series**, 401,730 daily observations. SQL: 12/12 reports and 1,222 numeric values independently reconciled. EDA: 6 audited figures and 8 executed notebook code cells.
- Session 1 tasks 1–7 **complete**. No forecasting models, real inventory replenishment or live BI deployment exist yet.
- Historical pre-publication notes farther below are retained as a time-stamped development record; this section supersedes them.


## Completed and verified in this session
1. User-uploaded `m5-forecasting-accuracy.zip` checked by ZIP CRC (no corrupt entries); it contains all five official competition-named members.
2. Authorized-by-user archive importer extracted only 3 required M5 CSVs into gitignored `data/raw/`; source hashes recorded in `source_manifest.json`.
3. Strict CSV row count and required header verification: calendar 1,969; sales train validation 30,490 series; weekly prices 6,841,121 rows.
4. SQLite warehouse built on a **deterministic first-3-per-store/department prefix sample**, 210 product-store series, 10 stores, 7 departments, 401,730 product-store-day rows and 1,913 days (2011-01-29 to 2016-04-24).
5. Original raw source unit counts and zero days independently re-summed and matched warehouse: 210,786 units; 299,476 zero days. Join retains all 401,730 rows; no duplicate series-day keys. Missing matched prices: 71,421 rows.
6. All 12 SQL exploratory reports executed and exported; six historical-data figures generated; eight notebook cells executed with six charts.
7. `python -m pytest -q` locally: **42 passed, 0 failed** on fixtures. Independently, real-data integration validation and checks passed using the 210 series (not a full 30,490-series warehouse).

8. Task 2 independently reverified; added `scripts/audit_full_source.py` and `reports/full_source_audit.json`. Full original source audit: 30,490 distinct series, 58,327,370 daily cells, 65,695,409 units, 39,777,094 zero-unit observations, 6,841,121 price records, with all dates/keys/prices valid. This does **not** imply the 58-million-row warehouse was loaded.
9. Re-ran `PRAGMA integrity_check`: `ok`; real sampled warehouse remains independently reconciled.

## Task 3 completion (20 October 2026)
- Executed all 12 SQL analyses on the original M5 **sampled** warehouse.
- Created `scripts/reconcile_sql.py` to independently reconstruct all query results from **original** M5 sales, calendar and price CSVs using pandas/NumPy, not existing SQL tables. All **12/12** query result sets and **1,222** numeric values matched, with exact integer aggregations and bounded float tolerance.
- Matched core SQLite metrics against raw-source calculations: 401,730 rows; 210,786 units; 299,476 zero-unit rows; 330,309 priced and 71,421 missing-price days; available-price revenue **$778,107.05**.
- Added 5 regression tests for reconciliation: clean fixture, corrupted export, missing-price behavior, missing export, and tampered warehouse revenue; **42 passed, 0 failed** total.
- Materialized immutable daily sales analytical table once per load for substantially faster repeat SQL reporting; rerun pipeline to refresh.
- Verified results: `reports/sql_python_reconciliation.json`; sampled reports in `reports/tables/query_01.csv` through `query_12.csv`.

## Current limitations
- Sampling is prefix-based within each store/department, NOT random, so observed sample averages, unit totals, and priced revenue cannot be extrapolated to the full retailer.
- Historical sales are not true unconstrained demand; no observed inventory, supplier lead times, carrying costs or lost sales.
- A local SQLite warehouse exists at `data/processed/m5.sqlite` (~500 MB, gitignored) and raw CSVs (~324 MB, gitignored). Neither appears in distributable ZIP.
- Publication and hosted CI have been verified; see the current release summary at the beginning of this file.
- No forecast models, service level optimization, real Power BI artifacts, dashboards or deployment yet.
- Since competition access and redistribution conditions govern the original data, avoid committing the original Kaggle CSVs.

## Next Session 1 tasks
- Create `harshvtomar/retail-demand-inventory-intelligence` with proper permission; upload the source, derived summary artifacts, and documentation without restricted raw CSVs or the large SQLite database.
- Run GitHub CI and verify actual status/commit SHA.
- Finalize EDA business review/provenance sign-off and repository publication metadata; SQL/independent numeric reconciliation is complete.
- Optionally add an official-data integration run in CI if compatible with Kaggle authentication and terms; maintain fixture-based CI otherwise.

## Reproduction
Read README.md for exact local commands. When starting Session 2, inspect remote `main` and all checkpoint files; never overwrite verified Session 1 work.

## Session 1 Task 4 — completed 20 October 2026
- Reviewed and rebuilt **all six actual M5 charts** with correct axes, units, and sample-scope footnotes. Normalized monthly chart uses 62 complete months; incomplete boundary months 2011-01 and 2016-04 are excluded from the plotted trend rather than treated as a demand decline.
- Store and category charts use comparable units per product-store-day; weekday rates account for the proper observation denominators. Zero sales / missing price do not automatically imply stockouts / bad data.
- Ran and saved `notebooks/01_exploratory_analysis.ipynb` with eight executed code cells; six figures displayed.
- `scripts/generate_eda.py` now saves six PNG figures, six source CSVs, `reports/eda_review.json` and `reports/eda_business_review.md`. Chart unit/row totals and price coverage reconcile with the warehouse; five chart datasets cross-check with the Task 3 independently verified SQL results.
- Added nine new EDA regression tests (`tests/test_eda_review.py`): **51 passed, 0 failed** locally. All findings are limited to the 210-series, nonrandom sample.
- **Remaining before Session 1 release:** publish GitHub repository safely (no original M5 raw files or generated SQLite database), verify GitHub Actions CI and record commit SHA. No GitHub release or CI success claimed.

## Historical pre-publication work (superseded by current status above)

### Task 5 publication preparation (20 October 2026)
- Verified available GitHub account repositories: target `retail-demand-inventory-intelligence` not yet present; available connector has no create-repository action.
- Added `PUBLISH_GITHUB.md` and `scripts/publish_github.sh` for a safe, repeatable publication after user creates an empty repository.
- Confirmed 51 fixture-based pytest checks pass locally before packaging.
- **Publication remains blocked** on repository creation; no remote commit SHA and no GitHub Actions CI results are asserted.


## Pending-work continuation — 20 October 2026 (Task 5/6/7)
- Rechecked GitHub connector: target `harshvtomar/retail-demand-inventory-intelligence` still returns 404 and does not appear among 15 visible owned repositories. Available GitHub connector cannot create a repository. **No publication occurred.**
- Corrected GitHub Actions test workflow: previously installed only `pytest`; now installs a minimal `requirements-ci.txt` with pytest, pandas, and matplotlib, includes a headless plotting backend, least-privilege read permissions, and a workflow timeout. **Still not tested on GitHub** until the repository exists.
- Improved prepublication Git ignore checks with an actual temporary Git repository rather than assuming an outside-repo check succeeds; hardened `.gitignore` for common generated database / secret patterns.
- Re-ran full local fixture tests: **51 passed, 0 failed**. Independently, the real M5 full-source audit and sampled SQL/EDA verification described above remain unchanged.
- Release documentation and safe staging checks are ready. **Task 5 (publication) and Task 6 (GitHub CI) remain pending**; Task 7 documentation prepared locally but remote commit metadata and hosted CI sign-off cannot be completed until GitHub is accessible.
- To unblock: user must create the empty GitHub repository on their account, then the existing GitHub connector can write project files. Alternatively, follow `PUBLISH_GITHUB.md` locally on a GitHub-authenticated Mac.

## Release verification sign-off
The published Session 2 GitHub source, SQL code, unit tests, documentation, and six SVG charts are ready for Session 3 continuation. Exactly 90 tracked files were independently counted on the published commit (70 retained + 20 added); five existing documentation files were updated, none deleted. The ZIP's original six PNG figures were not copied to GitHub; available SVG equivalents preserve the aggregate findings. The 985,600 real-M5 comparison count is from the preserved local evidence report and is **not** a GitHub Actions execution. See the new CI run on this documentation-only checkpoint separately.
