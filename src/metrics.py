"""Canonical base metrics (not a demand or inventory estimate)."""
def metrics(db):
    row=db.execute('''SELECT COUNT(*),COALESCE(SUM(units),0),COUNT(DISTINCT item_id || '|' || store_id),
       COALESCE(SUM(CASE WHEN units=0 THEN 1 ELSE 0 END),0),
       COALESCE(SUM(priced_revenue),0),
       COALESCE(SUM(CASE WHEN sell_price IS NULL THEN 1 ELSE 0 END),0)
       FROM daily_sales''').fetchone()
    n,u,series,zeros,revenue,missing=row
    return {'rows':n,'units':u,'series':series,'zero_share':zeros/n if n else None,'priced_revenue':revenue,'missing_price_rows':missing}
