"""Run the 12 read-only exploratory SQL statements and export results."""
import argparse,csv,sqlite3
from pathlib import Path
from src.metrics import metrics

def run(db_path,out='reports/tables'):
    db=sqlite3.connect(db_path); out=Path(out);out.mkdir(parents=True,exist_ok=True)
    try:
        queries=(Path(__file__).resolve().parents[1]/'sql'/'exploratory_queries.sql').read_text().split(';')
        n=0
        for q in queries:
            if not q.strip():continue
            cursor=db.execute(q);n+=1
            with (out/f'query_{n:02d}.csv').open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow([c[0] for c in cursor.description]);writer.writerows(cursor.fetchall())
        return {'queries_executed':n,'metrics':metrics(db)}
    finally:db.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--out',default='reports/tables');a=p.parse_args()
    print(run(a.database,a.out))
