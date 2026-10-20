# Session 1 — Real M5 subset results (20 Oct 2026)

**Dataset import status: complete.** ZIP and all three required original CSVs passed integrity and schema/record-count validation. The original data remains local and is not included in the downloadable project source ZIP.

**Executed analysis:** 210 product-store series, 10 stores, 7 departments, 401,730 product-store-day rows, 2011-01-29 through 2016-04-24. Sample method: first three series per store and department, **not random or representative**.

Independent source-versus-database results:

| Check | Verified sample result |
|---|---:|
| Daily observations | 401,730 |
| Product-store series | 210 |
| Observed unit sales | 210,786 |
| Zero-unit days | 299,476 |
| Days with observed matched selling price | 330,309 |
| Days without matched price | 71,421 |
| Join duplication or loss | 0 rows |
| Executed SQL queries | 12 |
| Generated EDA charts | 6 |
| Executed notebook code cells | 8 |
| Local automated tests | 51 passed, 0 failed |

The 71,421 missing-price matches do not indicate zero price and are excluded from `priced_revenue`. A zero-unit day does not demonstrate a stockout. Observed sample results should never be presented as entire-Walmart results.

**Remaining Session 1:** publish GitHub repository and verify actual CI; review/check limitations and final repository metadata.

## Task 2: Full source input audit (not an expanded warehouse)

All 30,490 original series, 58,327,370 daily unit observations, and 6,841,121 price records were checked in a streaming audit. Found 65,695,409 original unit sales and 39,777,094 zero-unit observations, no duplicated original sales series or store-item combinations, no negative/malformed daily unit counts, and no nonpositive/nonfinite prices. Full report: `reports/full_source_audit.json`. The separately analyzed 210-series SQL warehouse is a small nonrepresentative subset; neither its priced revenue nor its demand metrics should be extrapolated.

## Task 3: Independent SQL/Python reconciliation — completed
All twelve SQL outputs were reexecuted on the real 210-series M5 warehouse, then independently recomputed from the original M5 sales, calendar, and weekly price CSVs in pandas and NumPy. **12/12 reports and 1,222 numeric result values reconciled**; core dataset and available-price revenue checks reconciled separately. Full machine-readable result: `reports/sql_python_reconciliation.json`. Final test run: **42 passed, 0 failed**.

Examples of strictly sample-specific descriptive findings: WI_2 recorded 30,370 units (highest among the 10 sampled stores); 36,425 units were observed on Saturdays and 35,851 on Sundays. Observed revenue, computed only where prices are present, was **$778,107.05**. None of these figures represents all Walmart stores or supports a causal conclusion.

## Task 4: Final exploratory analysis review — completed

- Regenerated six plots and exported the six chart-source tables directly from the original M5 sample warehouse.
- Excluded two partial boundary months from the normalized monthly trend (2011-01: 3 days; 2016-04: 24 days).
- Compared store/category/weekday rates per product-store-day, not uneven raw category/month totals; zero-day and price-match indicators use percentages.
- Verified the five chart datasets with matching independently checked SQL exports; the sixth price-coverage dataset reconciled with priced and unpriced warehouse counts.
- Executed all eight notebook code cells and checked their outputs. Added `reports/eda_business_review.md` with six findings, reasoning, and explicit limitations.
- Added 9 more regression tests; **51/51 passed** locally, zero failures.
- Sample-only findings: FOODS 0.799 observed units per series-day; WI_2 0.756; Saturday/Sunday combined 0.628 versus weekdays 0.483; zero-unit share 74.55%; price match coverage 82.22%. None proves stockouts, demand causation or full-store demand.

**Still required for Session 1 release:** GitHub repository publication and a real GitHub Actions CI run.
