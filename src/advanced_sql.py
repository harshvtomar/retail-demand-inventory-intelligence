"""Execute 14 verified read-only Session 2 SQL analyses, without modifying Session 1 files."""
import argparse, csv, json, sqlite3
from pathlib import Path

SQL_PATH=Path(__file__).resolve().parents[1]/'sql'/'advanced_queries.sql'

def run(database='data/processed/m5.sqlite',output='data/processed/session2_sql'):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    pieces=[p.strip() for p in SQL_PATH.read_text().split(';') if p.strip()]
    # Inputs are static source-controlled SQL, never user-entered SQL.
    counts=[]
    with sqlite3.connect(f'file:{Path(database).resolve()}?mode=ro',uri=True) as db:
        for i,sql in enumerate(pieces,1):
            result=db.execute(sql)
            headers=[c[0] for c in result.description]
            if len(headers)!=len(set(headers)):
                raise ValueError(f'Duplicate column names in query {i}')
            filename=output/f'advanced_{i:02d}.csv'
            with filename.open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(headers)
                number=0
                for chunk in iter(lambda:result.fetchmany(5000),[]):
                    writer.writerows(chunk);number+=len(chunk)
            counts.append(dict(query=i,rows=number,columns=headers))
    (output/'run_manifest.json').write_text(json.dumps(counts,indent=2))
    return counts
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',default='data/processed/m5.sqlite')
    p.add_argument('--output',default='data/processed/session2_sql')
    a=p.parse_args()
    print(json.dumps(run(a.database,a.output),indent=2))
