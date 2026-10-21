-- Session 2 independent advanced analyses. Only real M5 sampled rows.
-- Q01 daily store rolling 7/28 calendar-day sales units
WITH store_day AS (
 SELECT store_id,date,SUM(units) units FROM daily_sales GROUP BY store_id,date
) SELECT store_id,date,units,
 AVG(units * 1.0) OVER (PARTITION BY store_id ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) avg_units_7d,
 AVG(units * 1.0) OVER (PARTITION BY store_id ORDER BY date ROWS BETWEEN 27 PRECEDING AND CURRENT ROW) avg_units_28d
 FROM store_day ORDER BY store_id,date;
-- Q02 store/category normalized sales per observed product-day
SELECT d.store_id,p.cat_id,COUNT(*) observed_series_days,SUM(d.units) units,
 ROUND(AVG(d.units * 1.0),8) mean_units_per_series_day
 FROM daily_sales d JOIN products p USING(item_id)
 GROUP BY d.store_id,p.cat_id ORDER BY 1,2;
-- Q03 store-month exposure corrected
SELECT store_id,substr(date,1,7) month,COUNT(*) series_days,SUM(units) units,
 ROUND(AVG(units*1.0),8) mean_units_per_series_day
 FROM daily_sales GROUP BY store_id,substr(date,1,7) ORDER BY store_id,month;
-- Q04 zero / positive observed sales by series
SELECT store_id,item_id,COUNT(*) days_observed, SUM(CASE WHEN units=0 THEN 1 ELSE 0 END) zero_days,
 SUM(CASE WHEN units>0 THEN 1 ELSE 0 END) positive_days, SUM(units) units
 FROM daily_sales GROUP BY store_id,item_id ORDER BY 1,2;
-- Q05 observed event association by category
SELECT p.cat_id,COALESCE(d.event_type,'No event') event_type,
 COUNT(*) series_days,SUM(d.units) units,ROUND(AVG(d.units*1.0),8) avg_units
 FROM daily_sales d JOIN products p USING(item_id)
 GROUP BY p.cat_id,COALESCE(d.event_type,'No event') ORDER BY 1,2;
-- Q06 weekend observed units normalized
SELECT store_id, CASE WHEN CAST(strftime('%w',date) AS INTEGER) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END day_type,
 COUNT(*) series_days,SUM(units) units,ROUND(AVG(units*1.0),8) mean_units
 FROM daily_sales GROUP BY store_id,day_type ORDER BY 1,2;
-- Q07 price-matching coverage by department
SELECT p.dept_id,COUNT(*) series_days,
 SUM(CASE WHEN d.sell_price IS NOT NULL THEN 1 ELSE 0 END) priced_days,
 SUM(CASE WHEN d.sell_price IS NULL THEN 1 ELSE 0 END) missing_price_days,
 SUM(d.priced_revenue) observed_priced_revenue
 FROM daily_sales d JOIN products p USING(item_id) GROUP BY p.dept_id ORDER BY 1;
-- Q08 seasonality across calendar month (descriptive)
SELECT substr(date,6,2) month_of_year,COUNT(*) series_days,SUM(units) units,
 ROUND(AVG(units*1.0),8) mean_units
 FROM daily_sales GROUP BY substr(date,6,2) ORDER BY 1;
-- Q09 top series contribution (all series incl zero unit)
WITH total AS (SELECT SUM(units) total_units FROM daily_sales),
 grouped AS (SELECT store_id,item_id,SUM(units) units FROM daily_sales GROUP BY store_id,item_id)
SELECT store_id,item_id,units,ROUND(1.0*units/NULLIF(total_units,0),10) share
 FROM grouped CROSS JOIN total ORDER BY units DESC,store_id,item_id;
-- Q10 weekly demand and coverage (Mon-Sun)
WITH weeks AS (SELECT store_id,item_id,
 date(date, printf('-%d days', (CAST(strftime('%w',date) AS INTEGER)+6)%7)) week_start,
 COUNT(*) observed_days,SUM(units) weekly_units FROM daily_sales GROUP BY 1,2,3)
SELECT store_id,item_id,week_start,observed_days,weekly_units FROM weeks
ORDER BY store_id,item_id,week_start;
-- Q11 daily product-store level volatility: population variance
SELECT store_id,item_id,COUNT(*) series_days,ROUND(AVG(units*1.0),8) mean_daily,
 ROUND(AVG(units*units*1.0)-AVG(units*1.0)*AVG(units*1.0),8) pop_variance
FROM daily_sales GROUP BY 1,2 ORDER BY 1,2;
-- Q12 department contribution share in the nonrandom sample
WITH dept AS (SELECT p.dept_id,SUM(d.units) units,COUNT(*) series_days FROM daily_sales d JOIN products p USING(item_id) GROUP BY 1)
SELECT dept_id,units,series_days,ROUND(1.0*units/NULLIF(SUM(units) OVER (),0),10) unit_share
FROM dept ORDER BY units DESC,dept_id;
-- Q13 week-over-week store-level demand (not a demand forecast)
WITH w AS (SELECT store_id,strftime('%Y-%W',date) calendar_week,SUM(units) units
 FROM daily_sales GROUP BY 1,2)
SELECT store_id,calendar_week,units,
 LAG(units) OVER (PARTITION BY store_id ORDER BY calendar_week) previous_week_units
FROM w ORDER BY store_id,calendar_week;
-- Q14 recent prior 28-day mean of observed daily units, excluding target day
SELECT store_id,item_id,date,units,
 CASE WHEN ROW_NUMBER() OVER (PARTITION BY store_id,item_id ORDER BY date)>28
 THEN ROUND(AVG(units*1.0) OVER (PARTITION BY store_id,item_id ORDER BY date
 ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING),8) ELSE NULL END trailing_28_before_today
FROM daily_sales ORDER BY store_id,item_id,date;
