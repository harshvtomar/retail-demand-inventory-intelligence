# SupplyPulse Session 2 — verified descriptive business brief

**Input:** Authorized genuine Walmart M5 series; deterministic nonrandom prefix of **210** product/store series representing **10** stores and **7** departments over **1,913** days. **401,730** product-store-day rows and **210,786** observed units. Results are **not** estimates for all Walmart stores or products.

## Findings (sample only)

- **ABC by total observed units:** 97 A series account for **169,209** units (**80.28%** of this sample); 63 B series account for **31,191** (**14.80%**); 50 C series account for **10,386** (**4.93%**). The boundary-crossing series belongs to its starting cumulative class.
- **Weekly XYZ:** 2 series have CV ≤ 0.5 (X); 75 have 0.5 < CV ≤ 1 (Y); 133 have CV > 1 (Z). This shows substantial sampled variability; the boundaries are policy assumptions, not universal standards.
- **ABC–XYZ intersection:** among A series, 2 AX, 51 AY, 44 AZ. B: 24 BY and 39 BZ; C: 50 CZ. These classifications are descriptive and use full historical observations. They must be recomputed per training fold before use as predictive features.
- **Intermittency:** 180 series satisfy the intermittent rules and 30 satisfy lumpy rules under the selected ADI/CV² criteria. None in this selected subset are classified Smooth/Erratic. This should not be generalized to all M5 sales series.
- **Pricing caveat:** unmatched weekly prices were previously found for 71,421 sampled product-days (17.78%). Unit based measures include them; priced revenue measures do not silently assume a zero price.
- **Forecast readiness:** 401,730 one-day historical-feature rows and 13,860 end-of-day 28-day forecast-origin records generated locally; *models have not been trained*. The final 28-day label window ends 2016-04-24.

## How to interpret the figures

Six descriptive figures are saved to `reports/session2/figures/`: monthly demand rates (excluding boundary partial months), store daily unit rates, ABC class counts, weekly CV distribution, ABC–XYZ matrix, and intermittent-pattern counts. These charts illustrate sampled observations rather than causal intervention outcomes or savings.

## Verification

**14 of 14** new advanced SQL outputs agree with independent pandas calculations directly reconstructed from the original source CSVs, with **985,600** numeric cells checked (absolute tolerance ≤ 1e-6). Detailed exports remain gitignored in `data/processed/session2_sql/` to avoid republishing fine-grained M5 data. Fixture tests plus baseline tests: **69 passed**, 0 failed at local verification. GitHub CI for the new code is a separate publication check; do not claim it passed until an actual run succeeds.
