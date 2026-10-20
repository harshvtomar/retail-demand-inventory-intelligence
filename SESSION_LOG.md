# Session 1 execution log — 20 October 2026

- User uploaded authorized downloaded Kaggle ZIP. ZIP archive integrity check: all entries valid.
- Verified three required M5 CSV headers, exact row counts and SHA-256; imported into `data/raw/` with `scripts.download_m5`.
- Ran existing original first-100-series pipeline: 191,300 rows, 12 SQL queries executed; found that the sample covered only early series, so broadened it.
- Added deterministic first-N-per-store/department sampling (`--sample-per-store-dept 3`), sampling tests and guarded mutually exclusive sample arguments.
- Rebuilt SQLite: 210 series, 10 stores, 7 departments, 401,730 rows. SQL query exports regenerated (12).
- Independent raw CSV versus SQL reconciliation confirmed 210,786 units, 299,476 zero-unit days, preserved left-join cardinality, zero duplicate series/day keys.
- Generated 6 PNG reports; executed exploratory Jupyter notebook (8 code cells, 6 chart outputs).
- Updated local test suite: 37 passed, 0 failed. No GitHub CI yet.
- Updated project README, data methodology, state and follow-up instructions. Raw M5 files and SQLite data remain excluded from distributable code/archive.

**No GitHub repository creation or CI launch claimed.**

- Task 2 follow-up: ran `scripts/audit_full_source.py` against all supplied M5 inputs (58,327,370 nonnegative integer daily values; 6,841,121 positive finite price rows). Wrote `reports/full_source_audit.json`; added 5 regression tests for source corruption/invalid inputs. Reverified 210-series SQLite sample reconciliation and `PRAGMA integrity_check=ok`. No full-series warehouse build performed.

## 20 October 2026 — Task 3 SQL reconciliation completed
- Re-extracted the user's original authorized Kaggle archive and confirmed the original three source file SHA-256 values match the prior Task 2 checkpoint.
- Rebuilt the sampled real-data warehouse, executed twelve exploratory SQL queries, and exported all twelve CSV reports.
- Optimized repeated querying by materializing the immutable `daily_sales` analytical table once during ingestion, preserving the left-price-join and grain verification semantics.
- Implemented `scripts/reconcile_sql.py`: independent source-to-pandas/NumPy reconstruction across every query, with exact row keys and 1,222 numeric result comparisons. All twelve outputs reconciled. Core SQLite priced revenue ($778,107.05), units, zero days, rows and price coverage independently matched.
- Added five fixture regression tests including deliberate query tampering detection; 42/42 pytest checks passed (0 failed).
- Updated README, methodology, data model, project state, and machine-readable reconciliation report. GitHub publication and CI remain unverified/pending.

## 20 October 2026 — Task 4 EDA business review completed
- Rebuilt charting to use complete-month unit-per-series-day trends and rate-based store/category comparisons; changed zero-unit and weekly-price-share charts to correctly labelled percentages.
- Audited six datasets against warehouse row/aggregate invariants and matching Task 3 SQL exports (five independent source-to-SQL report mappings).
- Regenerated `reports/figures/*.png`, `reports/eda_tables/*.csv`, `reports/eda_review.json`, and `reports/eda_business_review.md`.
- Rebuilt and executed the 16-cell Jupyter notebook: all eight code cells successful, six chart outputs. Reviewed sample-specific interpretations and limitations.
- Added nine synthetic fixture regression tests; full local test run 51 passed, zero failed.
- Repository publication and hosted GitHub CI remain outstanding; do not claim Session 1 release is complete.

## Task 5 publication preflight
- Target remote repository absent from connected GitHub list; no repository-creation tool available.
- Prepared publish instructions and a git-based safe publish script; no GitHub push or CI run has been performed.
- Re-ran `python3 -m pytest -q`: 51 passed.


## 20 October 2026 — Publication blocker and CI repair
- Confirmed remote repository still absent (`get_repo` 404; not in owned repo listing). Repository creation cannot be executed with the current GitHub connector. No remote modifications made.
- Corrected `.github/workflows/ci.yml`: all Python test imports (pandas, matplotlib and pytest) now available through `requirements-ci.txt`. The former workflow installed only pytest and risked missing dependency errors.
- Improved publish preflight to test ignore patterns within a temporary Git repository. Added ignore exclusions for typical generated and secret files.
- Locally ran 51 fixture tests successfully. Uploaded or pushed nothing to GitHub; hosted CI still unverified.
