"""Session 2 retail analytics and strictly historical forecast features.

This module does not claim inventory balances, stockouts, causal impacts, or
unconstrained demand. Source is the user's authorized M5 sample warehouse.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

KEY = ["store_id", "item_id"]
CV_BOUNDS = (0.5, 1.0)

def load_daily(database: str | Path) -> pd.DataFrame:
    with sqlite3.connect(database) as db:
        frame = pd.read_sql_query("""SELECT d.store_id,d.item_id,p.dept_id,p.cat_id,
           d.date,d.units,d.sell_price,d.priced_revenue,d.event_type
           FROM daily_sales d JOIN products p USING(item_id)
           ORDER BY d.store_id,d.item_id,d.date""", db, parse_dates=["date"])
    if frame.empty:
        raise ValueError("No daily sales data")
    if frame[KEY + ["date"]].duplicated().any():
        raise ValueError("Duplicate product-store-day grain")
    if frame[KEY + ["date"]].isna().any().any() or (frame.units < 0).any():
        raise ValueError("Invalid sales identity or units")
    return frame

def abc_segment(frame: pd.DataFrame, a: float=0.8, b: float=0.95) -> pd.DataFrame:
    """Classify by historical units; crossing item belongs to its starting tier."""
    if not 0 < a < b < 1:
        raise ValueError("ABC boundaries must satisfy 0 < a < b < 1")
    scores=(frame.groupby(KEY,as_index=False).agg(total_units=("units","sum"),
            observations=("units","size"))
            .sort_values(["total_units","store_id","item_id"],ascending=[False,True,True])
            .reset_index(drop=True))
    grand=scores.total_units.sum()
    if grand == 0:
        scores["unit_share"]=0.0
        scores["previous_cumulative_share"]=0.0
        scores["cumulative_share"]=0.0
        scores["abc_class"]="U"
    else:
        scores["unit_share"]=scores.total_units/grand
        scores["previous_cumulative_share"]=(scores.total_units.cumsum()-scores.total_units)/grand
        scores["cumulative_share"]=scores.total_units.cumsum()/grand
        scores["abc_class"]=np.select(
            [scores.previous_cumulative_share < a,scores.previous_cumulative_share < b],
            ["A","B"],default="C")
        scores.loc[scores.total_units==0,"abc_class"]="U"
    return scores

def xyz_segment(frame: pd.DataFrame, x: float=.5, y: float=1.) -> pd.DataFrame:
    """Weekly population CV, excluding first/last incomplete calendar weeks."""
    if not 0 <= x < y:
        raise ValueError("XYZ boundaries require 0 <= x < y")
    tmp=frame[KEY+["date","units"]].copy()
    tmp["week_start"]=tmp.date.dt.to_period("W-SUN").dt.start_time
    weekly=(tmp.groupby(KEY+["week_start"],as_index=False)
              .agg(weekly_units=("units","sum"),days_observed=("units","size")))
    # Missing days are not zero demand: a complete week must have seven rows.
    weekly=weekly[weekly.days_observed.eq(7)]
    stats=(weekly.groupby(KEY,as_index=False).agg(complete_weeks=("weekly_units","size"),
                 mean_weekly_units=("weekly_units","mean"),
                 weekly_variance=("weekly_units",lambda s: float(np.var(s,ddof=0)))))
    stats["weekly_cv"]=np.where(stats.mean_weekly_units>0,
                  np.sqrt(stats.weekly_variance)/stats.mean_weekly_units,np.nan)
    stats["xyz_class"]=np.select([stats.weekly_cv<=x,stats.weekly_cv<=y,
                                   stats.weekly_cv>y],["X","Y","Z"],default="U")
    return stats

def max_zero_streak(values: np.ndarray) -> int:
    z=np.asarray(values)==0
    if not z.any(): return 0
    boundaries=np.diff(np.concatenate(([0],z.astype(int),[0])))
    return int((np.where(boundaries==-1)[0]-np.where(boundaries==1)[0]).max())

def intermittent_segment(frame: pd.DataFrame, adi_threshold:float=1.32,cv2_threshold:float=.49) -> pd.DataFrame:
    """ADI=count(all observed days)/count(nonzero days); CV² on nonzero sizes.
    Less than two nonzero observations -> undefined CV² and U classification.
    """
    rows=[]
    for (store,item),group in frame.groupby(KEY,sort=True):
        units=group.units.to_numpy()
        positive=units[units>0]
        n=len(positive)
        adi=len(units)/n if n else np.nan
        cv2=float(np.var(positive,ddof=0)/np.mean(positive)**2) if n>=2 else np.nan
        if n<2: category="U"
        elif adi<=adi_threshold: category="Smooth" if cv2<=cv2_threshold else "Erratic"
        else: category="Intermittent" if cv2<=cv2_threshold else "Lumpy"
        rows.append((store,item,len(units),n,adi,cv2,max_zero_streak(units),category))
    return pd.DataFrame(rows,columns=KEY+["observed_days","positive_days","adi","cv2_positive_size","max_zero_streak","demand_pattern"])

def daily_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Features for target day t only use observed sales strictly before t."""
    base=frame[KEY+["date","units"]].sort_values(KEY+["date"]).copy()
    g=base.groupby(KEY,sort=False)["units"]
    for lag in (1,7,14,28,56):
        base[f"lag_{lag}"]=g.shift(lag)
    past=g.shift(1)
    for window in (7,28,56):
        groups=past.groupby([base.store_id,base.item_id],sort=False)
        base[f"rolling_mean_{window}"]=groups.transform(lambda s:s.rolling(window,min_periods=window).mean())
    for window in (7,28):
        groups=past.groupby([base.store_id,base.item_id],sort=False)
        base[f"rolling_std_{window}"]=groups.transform(lambda s:s.rolling(window,min_periods=window).std(ddof=0))
    groups=past.groupby([base.store_id,base.item_id],sort=False)
    base["prior_zero_share_28"]=groups.transform(lambda s:s.eq(0).where(s.notna()).rolling(28,min_periods=28).mean())
    base["weekday"]=base.date.dt.dayofweek
    base["month"]=base.date.dt.month
    base["is_weekend"]=base.weekday>=5
    base["target_day_units"]=base.pop("units")
    return base

def rolling_origins_28(frame: pd.DataFrame, origin_stride:int=28, history:int=56) -> pd.DataFrame:
    """At origin t predict sum of subsequent 28 days; predictors stop at t.

    Target is retrospective for supervised development, never a predictor.
    The final 28 days form a held-out evaluation window. No train/test split
    is performed here; Session 3 must freeze origins before model selection.
    """
    if origin_stride<1 or history<56: raise ValueError("Invalid origin configuration")
    daily=daily_features(frame)
    result=[]
    for (store,item),g in daily.groupby(KEY,sort=True):
        g=g.reset_index(drop=True)
        if not g.date.diff().iloc[1:].eq(pd.Timedelta(days=1)).all():
            raise ValueError("Forecast-origin records require consecutive daily observations")
        target=g.target_day_units.to_numpy(dtype=np.int64)
        cum=np.r_[0,np.cumsum(target)]
        # Indices i correspond to observed forecast origins. 28 future rows exist.
        eligible=list(range(len(g)-29,history-2,-origin_stride))[::-1]
        subset=g.iloc[eligible].copy()
        if subset.empty:continue
        loc=np.array(eligible)
        subset["future_28d_units"]=cum[loc+29]-cum[loc+1]
        subset["origin_units_known"]=subset.target_day_units
        subset=subset.drop(columns=["target_day_units"])
        subset=subset.rename(columns={"date":"forecast_origin_date"})
        subset["target_end_date"]=g.date.iloc[loc+28].to_numpy()
        result.append(subset)
    return pd.concat(result,ignore_index=True) if result else pd.DataFrame()

def run(db_path:str|Path, output:str|Path="reports/session2", feature_output:str|Path="data/processed/session2_features") -> dict:
    frame=load_daily(db_path)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    feature_output=Path(feature_output);feature_output.mkdir(parents=True,exist_ok=True)
    abc=abc_segment(frame);xyz=xyz_segment(frame);intermittent=intermittent_segment(frame)
    classes=(abc.merge(xyz,on=KEY,validate="one_to_one")
                .merge(intermittent,on=KEY,validate="one_to_one"))
    classes.to_csv(feature_output/"abc_xyz_intermittent.csv",index=False)
    matrix=pd.crosstab(classes.abc_class,classes.xyz_class)
    matrix.to_csv(output/"abc_xyz_matrix.csv")
    monthly=frame.assign(month=frame.date.dt.to_period("M").astype(str)).groupby("month",as_index=False).agg(
        units=("units","sum"),observations=("units","size"))
    monthly["per_series_day"]=monthly.units/monthly.observations
    monthly.to_csv(output/"monthly_rates.csv",index=False)
    daily=daily_features(frame)
    origins=rolling_origins_28(frame)
    daily.to_csv(feature_output/"one_day_features.csv.gz",index=False,compression="gzip")
    origins.to_csv(feature_output/"origin_28day_features.csv.gz",index=False,compression="gzip")
    report={"source":"M5 sampled warehouse (not population representative)",
        "series":len(classes),"daily_rows":len(frame),"time_start":str(frame.date.min().date()),
        "time_end":str(frame.date.max().date()),"units":int(frame.units.sum()),
        "abc_counts":{k:int(v) for k,v in classes.abc_class.value_counts().items()},
        "xyz_counts":{k:int(v) for k,v in classes.xyz_class.value_counts().items()},
        "intermittent_counts":{k:int(v) for k,v in classes.demand_pattern.value_counts().items()},
        "one_day_feature_rows":len(daily),"rolling_origin_rows":len(origins),
        "classification_metric":"unit-based ABC; CV of complete-week sales for XYZ",
        "notes":["Nonrandom 210-series prefix sample; not representative of M5 population",
        "Sales are observed units, not unconstrained demand or confirmed inventory availability",
        "Full-horizon segmentation is descriptive; recompute on training history for forecasting",
        "Price is never an input to modeled features without known-in-advance proof",
        "Forecast origin at end of t predicts units t+1 through t+28; future label is evaluation-only"]}
    (output/"verification_summary.json").write_text(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--database",default="data/processed/m5.sqlite")
    parser.add_argument("--output",default="reports/session2")
    parser.add_argument("--features",default="data/processed/session2_features")
    args=parser.parse_args()
    print(json.dumps(run(args.database,args.output,args.features),indent=2))
