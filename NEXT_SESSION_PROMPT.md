# SUPPLYPULSE INTELLIGENCE — SESSION 3 (DO NOT RESTART)

**Project:** SupplyPulse Intelligence — Retail Demand Forecasting & Inventory Optimization
**Repository:** https://github.com/harshvtomar/retail-demand-inventory-intelligence
**Environment:** ChatGPT Work, GPT-6 Astra Medium Reasoning if available, one focused five-hour session

## Recovery and safeguards

1. Inspect the latest remote main branch. Read README.md, PROJECT_STATE.md, SESSION_LOG.md, docs/SESSION2_METHODS.md, reports/session2/ANALYTICAL_BRIEF.md and tests before editing. Preserve Session 1 and 2; do not rebuild.
2. Install requirements-ci.txt, run python -m pytest -q, and inspect the GitHub Actions run for the published commit. Never assume a successful run.
3. Original M5 CSVs were obtained with user authorization and must stay outside GitHub. If absent, ask the user for their original m5-forecasting-accuracy.zip. Do not synthesize historical competition data.
4. Session 1 audited 30,490 series and 58,327,370 original sales observations, but all Session 1/2 analytical findings are based on a nonrandom **210-series / 401,730-row** sample. Do not extrapolate or claim real inventories, stockouts, lead times or profitability.
5. Session 2 added 14 independently reconciled SQL reports, ABC/XYZ and intermittent-demand diagnostics, historical lag features, and 28-day forecasting-origin labels. Recompute segmentation inside historical folds; never use the full-history retrospective classes as predictive input. Detailed feature rows under data/processed/ are private.
6. Six vector charts are in reports/session2/figures/; the original Session 2 PNGs are only in the local ZIP.

## Session 3 objective

**Train and rigorously evaluate demand forecasting models** under strict chronological and leakage-safe validation. Compare zero-demand, seasonal-naïve, trailing rolling-mean baselines and, only if justified, ML methods such as gradient boosted trees. Report MAE, RMSE, WAPE (with valid denominator), MASE (with valid seasonal scale), forecast bias, and per-series/store/department diagnostics.

Distinguish one-day-ahead forecasts from full 28-day-horizon predictions. The 28-day model must not condition on realized intermediate future demand unless implementing a separately labeled online-updating scenario.

## Train/validation/test plan

- Freeze held-out historical window **2016-03-28 through 2016-04-24**, forecast origin **2016-03-27**, until final model comparison.
- Use at least three earlier chronologically ordered rolling-origin validation folds.
- Fit preprocessing, missing-value rules, transformations, scalers, segmentation and tuning strictly within each fold's historical training window.
- Do not use future daily units, future unknown prices, or full-history ABC/XYZ class membership as predictors.

## Expected deliverables

Implement reproducible source-controlled training and evaluation code, independent checks, credible holdout metrics, baseline comparisons, per-segment diagnostics, error decomposition, labeled charts, updated documentation, tests and a business interpretation without unsupported causal claims. Update PROJECT_STATE.md, SESSION_LOG.md and NEXT_SESSION_PROMPT.md for Session 4 inventory-policy simulations. Commit only safe source and aggregate results to the existing repository; check that GitHub Actions succeeds.

**Begin by inspecting the latest remote main, not by starting a new repository.**
