# KPI definitions
- Sales units: sum of nonnegative observed daily `units` at product-store-day grain.
- Zero-sales share: product-store-day rows with zero units divided by all included product-store-day rows. Not a stockout rate.
- Historical priced revenue: `SUM(units * sell_price)` over rows with non-null weekly item-store selling price; coverage must be reported separately.
- Active product-store combinations: unique `(item_id, store_id)` present in the selected raw M5 series; this does not guarantee positive unit sales.
- Temporal comparisons must explicitly acknowledge varying observed date coverage.
