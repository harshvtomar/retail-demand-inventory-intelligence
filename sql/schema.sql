PRAGMA foreign_keys=ON;
CREATE TABLE products(item_id TEXT PRIMARY KEY,dept_id TEXT NOT NULL,cat_id TEXT NOT NULL);
CREATE TABLE stores(store_id TEXT PRIMARY KEY,state_id TEXT NOT NULL);
CREATE TABLE calendar(day_id TEXT PRIMARY KEY,date TEXT NOT NULL UNIQUE,wm_yr_wk INTEGER NOT NULL,weekday TEXT NOT NULL,event_name TEXT,event_type TEXT);
CREATE TABLE prices(store_id TEXT NOT NULL,item_id TEXT NOT NULL,wm_yr_wk INTEGER NOT NULL,sell_price REAL NOT NULL CHECK(sell_price>0),PRIMARY KEY(store_id,item_id,wm_yr_wk));
CREATE TABLE sales(series_id TEXT NOT NULL,item_id TEXT NOT NULL,store_id TEXT NOT NULL,day_id TEXT NOT NULL,units INTEGER NOT NULL CHECK(units>=0),PRIMARY KEY(series_id,day_id),FOREIGN KEY(day_id) REFERENCES calendar(day_id));
