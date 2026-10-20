"""Verified M5 CSV -> SQLite warehouse, streaming sales to bound memory."""
import argparse, csv, hashlib, json, re, sqlite3
from pathlib import Path
from datetime import date

SCHEMA = Path(__file__).resolve().parents[1] / 'sql' / 'schema.sql'
FIELDS = ('id','item_id','dept_id','cat_id','store_id','state_id')

def sha256(path):
    digest=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

def read_calendar(path):
    with open(path,newline='') as f:
        rows=list(csv.DictReader(f))
    if not rows or not {'d','date','wm_yr_wk','weekday','event_name_1','event_type_1'} <= rows[0].keys():
        raise ValueError('Calendar missing required M5 columns')
    out={}
    for r in rows:
        date.fromisoformat(r['date'])
        key=r['d']
        if key in out:raise ValueError('Duplicate calendar day')
        out[key]=(r['date'],int(r['wm_yr_wk']),r['weekday'],r['event_name_1'] or None,r['event_type_1'] or None)
    return out

def load_prices(db,path):
    n=0
    with open(path,newline='') as f:
        reader=csv.DictReader(f)
        if not {'store_id','item_id','wm_yr_wk','sell_price'} <= set(reader.fieldnames or []):
            raise ValueError('Missing price columns')
        batch=[]
        for r in reader:
            price=float(r['sell_price'])
            if price<=0:raise ValueError('Non-positive price')
            batch.append((r['store_id'],r['item_id'],int(r['wm_yr_wk']),price));n+=1
            if len(batch)==10000:
                db.executemany('INSERT INTO prices VALUES(?,?,?,?)',batch);batch=[]
        if batch:db.executemany('INSERT INTO prices VALUES(?,?,?,?)',batch)
    return n

def run(raw, output, limit_series=None, sample_per_store_dept=None):
    """Build the warehouse; optionally select first N series per store and department.

    Stratified prefix selection ensures a small sample spans stores/departments,
    but is not a random or statistically representative sample.
    """
    if sample_per_store_dept is not None and sample_per_store_dept <= 0:
        raise ValueError("sample_per_store_dept must be positive")
    if sample_per_store_dept is not None and limit_series is not None:
        raise ValueError("Choose either series limit or store/department sampling")
    raw=Path(raw); output=Path(output)
    files={k:raw/k for k in ('calendar.csv','sell_prices.csv','sales_train_validation.csv')}
    for p in files.values():
        if not p.is_file():raise FileNotFoundError(f'Real M5 file required: {p}; see docs/DATA_PROVENANCE.md')
    calendar=read_calendar(files['calendar.csv'])
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():output.unlink()
    db=sqlite3.connect(output)
    try:
        db.executescript(SCHEMA.read_text())
        db.executemany('INSERT INTO calendar VALUES(?,?,?,?,?,?)',[(k,*v) for k,v in calendar.items()])
        pn=load_prices(db,files['sell_prices.csv'])
        total=0;series=0;missing_prices=0;priced_sales=0
        seen=set(); selected_counts={}
        with open(files['sales_train_validation.csv'],newline='') as f:
            reader=csv.DictReader(f)
            days=[k for k in reader.fieldnames or [] if re.fullmatch(r'd_\d+',k)]
            if not set(FIELDS)<=set(reader.fieldnames or []) or not days:raise ValueError('Invalid wide sales schema')
            if any(day not in calendar for day in days):raise ValueError('Calendar lacks observed sales day')
            for row in reader:
                if limit_series is not None and series>=limit_series:break
                if sample_per_store_dept is not None:
                    stratum=(row["store_id"],row["dept_id"])
                    if selected_counts.get(stratum, 0) >= sample_per_store_dept:
                        continue
                    selected_counts[stratum]=selected_counts.get(stratum, 0)+1
                identity=tuple(row[k] for k in FIELDS)
                if not all(identity):raise ValueError('Missing identifier')
                if identity[0] in seen:raise ValueError('Duplicate series id')
                seen.add(identity[0]);series+=1
                db.execute('INSERT OR IGNORE INTO products VALUES (?,?,?)',(row['item_id'],row['dept_id'],row['cat_id']))
                db.execute('INSERT OR IGNORE INTO stores VALUES (?,?)',(row['store_id'],row['state_id']))
                batch=[]
                for day in days:
                    val=row[day]
                    if not re.fullmatch(r'\d+',val):raise ValueError(f'Invalid daily sales {row["id"]} {day}: {val!r}')
                    units=int(val)
                    batch.append((row['id'],row['item_id'],row['store_id'],day,units))
                db.executemany('INSERT INTO sales VALUES (?,?,?,?,?)',batch)
                total+=len(batch)
        db.executescript('''CREATE INDEX ix_sales_day ON sales(day_id);
          CREATE INDEX ix_sales_store_item ON sales(store_id,item_id);
          -- Materialize the immutable analytical dataset once; avoids repeated
          -- multi-million-row price lookups across twelve reports.
          CREATE TABLE daily_sales AS
          SELECT s.series_id,s.item_id,s.store_id,c.date,c.weekday,c.event_name,c.event_type,
            c.wm_yr_wk,s.units,p.sell_price,
            CASE WHEN p.sell_price IS NULL THEN NULL ELSE s.units*p.sell_price END AS priced_revenue
          FROM sales s JOIN calendar c ON c.day_id=s.day_id
          LEFT JOIN prices p ON p.store_id=s.store_id AND p.item_id=s.item_id AND p.wm_yr_wk=c.wm_yr_wk;''')
        db.execute('CREATE INDEX ix_daily_sales_date ON daily_sales(date)')
        db.execute('CREATE INDEX ix_daily_sales_store ON daily_sales(store_id)')
        missing_prices,priced_sales=db.execute('SELECT SUM(CASE WHEN sell_price IS NULL THEN 1 ELSE 0 END),SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END) FROM daily_sales').fetchone()
        actual=db.execute('SELECT COUNT(*) FROM daily_sales').fetchone()[0]
        if actual!=total:raise AssertionError('Join changed sales grain')
        db.commit()
        summary={'dataset':'Real M5 input (user-provided)','series':series,'daily_observations':total,'calendar_days':len(calendar),'weekly_prices':pn,'missing_price_observations':missing_prices,'priced_observations':priced_sales,'subset_series_limit':limit_series,'sample_per_store_dept':sample_per_store_dept,'stores_sampled':db.execute('SELECT COUNT(*) FROM stores').fetchone()[0],'departments_sampled':db.execute('SELECT COUNT(DISTINCT dept_id) FROM products').fetchone()[0],'file_sha256':{k:sha256(v) for k,v in files.items()},'sqlite_database':str(output)}
        output.with_suffix('.quality.json').write_text(json.dumps(summary,indent=2))
        return summary
    finally:db.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw',default='data/raw');parser.add_argument('--output',default='data/processed/m5.sqlite')
    parser.add_argument('--limit-series',type=int,default=None)
    parser.add_argument('--sample-per-store-dept',type=int,default=None,help='Take first N series in each store/department; spans all stores')
    a=parser.parse_args()
    limit = 100 if a.limit_series is None and a.sample_per_store_dept is None else a.limit_series
    print(json.dumps(run(a.raw,a.output,limit,a.sample_per_store_dept),indent=2))
