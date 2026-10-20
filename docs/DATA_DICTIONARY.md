# Data dictionary (Session 1)

| Table / view | Field | Meaning |
|---|---|---|
| `products` | `item_id` (PK) | Original M5 item identifier |
| `products` | `dept_id`, `cat_id` | Department and product category |
| `stores` | `store_id` (PK), `state_id` | Store and state |
| `calendar` | `day_id` (PK), `date` | M5 `d_#` and actual calendar date |
| `calendar` | `wm_yr_wk` | Walmart calendar year/week used for price joins |
| `calendar` | `weekday`, `event_name`, `event_type` | Weekday and first named M5 event, if present |
| `prices` | `store_id`, `item_id`, `wm_yr_wk` (composite PK) | Unique weekly price observation per store and item |
| `prices` | `sell_price` | Positive observed selling price; units consistent with original dataset |
| `sales` | `series_id`, `day_id` (composite PK) | Original series-day sale record |
| `sales` | `item_id`, `store_id`, `units` | Item-store-day identifiers and nonnegative sales units |
| `daily_sales` | `sell_price` | Nullable joined observed weekly price |
| `daily_sales` | `priced_revenue` | Nullable `units * observed sell_price`; not full turnover if price missing |

`daily_sales` retains all daily fact rows, even when no price observation is available. The current analysis sample contains 210 series, 401,730 daily observations and a nonrandom store/department prefix selection.
