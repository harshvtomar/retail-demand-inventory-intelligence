# SUPPLYPULSE INTELLIGENCE — WORK SESSION 2 (DO NOT RESTART)

**Repository:** https://github.com/harshvtomar/retail-demand-inventory-intelligence
**Verified Session 1 foundation commit:** `6a0507a2246600c8b0674bf3eaf030094f23d7df`
**Hosted CI:** https://github.com/harshvtomar/retail-demand-inventory-intelligence/actions/runs/39381480268 — successful, 51 fixture tests passed.
**Execution:** ChatGPT Work, GPT-6 Medium thinking (if available), one focused five-hour session.

## Mandatory recovery
1. Inspect the latest remote `main`, README.md, PROJECT_STATE.md, SESSION_LOG.md, reports/RELEASE_READINESS.md, and methodology. Preserve working code and verified artifacts.
2. Run `python -m pip install -r requirements-ci.txt` and `python -m pytest -q` in a fresh clone. Verify GitHub Actions after any new commits.
3. The original Walmart M5 competition data must be acquired by the user under authorized Kaggle access. Raw CSVs and credentials are gitignored and must not be redistributed or committed.
4. The 30,490-series / 58,327,370-observation original source was **audited**, not loaded into a full warehouse. Real SQL and EDA findings use a deterministic, nonrandom sample of **210 series / 401,730 store-product-day rows** across ten stores and seven departments. Do not generalize sample KPIs or claim real stockouts or savings.
5. Preserve the 12/12 independently reconciled SQL reports (1,222 numeric comparisons), six verified EDA figures, executed notebook and 51 passing tests.

## Session 2 objective
Develop advanced SQL analytics for store, category, seasonality and intermittent-demand patterns; defensible ABC/XYZ segmentation; and strictly historical, leakage-free forecast-ready features. Create independent SQL/Python reconciliations and meaningful regression tests. Consider expanding the sample only when justified by resources and reproducibility.

## Expected deliverables
Working code and executed reports; reproducible analytics and unit tests; clear metric definitions and caveats; updated README and checkpoint documents; meaningful committed changes to the **existing** repository; and verified hosted CI status. Do not claim future forecasting, inventory policies or live dashboards are already built.
