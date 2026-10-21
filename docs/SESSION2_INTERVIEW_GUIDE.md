# SupplyPulse Session 2 — interview preparation

**Q: What is the business question?** Understand which observed sales series contribute volume, how variability/intermittency differs, and how to construct defensible forecasts without using the future.

**Q: Why ABC/XYZ together?** ABC describes unit-contribution concentration; XYZ describes variation in complete-week units. Their intersection is a useful diagnostic shortlist, but neither tells us actual inventory levels or true service-level requirements.

**Q: Why didn't you calculate safety stock now?** M5 lacks supplier lead times, inventory positions and known lost-sales demand. Session 4 will use clearly documented hypothetical parameters and report simulated rather than actual effects.

**Q: What can go wrong with daily CV?** Sparse per-day unit counts have many zeros; weekly aggregation better matches replenishment planning time frames but can obscure within-week patterns. Thresholds are assumption-dependent.

**Q: How did you prevent target leakage?** Lag and rolling features shift prior to their window, use item/store grouping, test future perturbations, and distinguish one-day target dates from 28-day forecast origins. A model must still recompute any class or scaler strictly before each origin.

**Q: What is the test window?** Last 28 calendar days of the available historical sample (2016-03-28 through 2016-04-24), with origin 2016-03-27; earlier folds are chronological. Never shuffle time series across future boundaries.

**Q: How were the SQL results checked?** Original M5 wide-format CSVs were independently reselected and reshaped in pandas, and all 14 reports were compared by business keys with numerical tolerances. 985,600 numeric cells reconciled in the local real-data execution.

**Q: Biggest limitation?** The current sample takes the first three series per store/department rather than a probability sample, so all figures are sample-specific and cannot be extrapolated to the retailer or all M5 items. Observed zero sales are not proof of no underlying demand or of inventory stockouts.
