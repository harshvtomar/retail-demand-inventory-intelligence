-- Each SELECT is independently executable against the generated SQLite warehouse.
-- 01 monthly units
SELECT substr(date,1,7) month, SUM(units) units FROM daily_sales GROUP BY 1 ORDER BY 1;
-- 02 store units
SELECT store_id,SUM(units) units FROM daily_sales GROUP BY 1 ORDER BY 2 DESC,1 ASC;
-- 03 state units
SELECT st.state_id,SUM(s.units) units FROM daily_sales s JOIN stores st USING(store_id) GROUP BY 1 ORDER BY 2 DESC,1 ASC;
-- 04 top items
SELECT item_id,SUM(units) units FROM daily_sales GROUP BY 1 ORDER BY 2 DESC,1 ASC LIMIT 20;
-- 05 category monthly
SELECT p.cat_id,substr(d.date,1,7) month,SUM(d.units) units FROM daily_sales d JOIN products p USING(item_id) GROUP BY 1,2 ORDER BY 1,2;
-- 06 department monthly
SELECT p.dept_id,substr(d.date,1,7) month,SUM(d.units) units FROM daily_sales d JOIN products p USING(item_id) GROUP BY 1,2 ORDER BY 1,2;
-- 07 weekday sales
SELECT weekday,SUM(units) units,AVG(units) mean_product_day_units FROM daily_sales GROUP BY 1 ORDER BY 1;
-- 08 month-of-year seasonality
SELECT substr(date,6,2) month_of_year,ROUND(AVG(units),4) mean_series_day_units FROM daily_sales GROUP BY 1 ORDER BY 1;
-- 09 event association (descriptive only)
SELECT COALESCE(event_type,'No event') event_type,ROUND(AVG(units),4) mean_series_day_units FROM daily_sales GROUP BY 1 ORDER BY 1;
-- 10 demand volatility
SELECT item_id,store_id,ROUND(AVG(units),4) mean_units,ROUND(AVG(units*units)-AVG(units)*AVG(units),4) population_variance FROM daily_sales GROUP BY 1,2 ORDER BY 1,2;
-- 11 zero-sale days
SELECT store_id,COUNT(*) observed_days,SUM(CASE WHEN units=0 THEN 1 ELSE 0 END) zero_days,ROUND(1.0*SUM(CASE WHEN units=0 THEN 1 ELSE 0 END)/COUNT(*),4) zero_share FROM daily_sales GROUP BY 1 ORDER BY 1;
-- 12 units by observed price band, excludes missing prices
SELECT CASE WHEN sell_price<5 THEN 'below 5' WHEN sell_price<15 THEN '5-15' ELSE '15+' END price_band,COUNT(*) priced_rows,SUM(units) units FROM daily_sales WHERE sell_price IS NOT NULL GROUP BY 1 ORDER BY 1;
