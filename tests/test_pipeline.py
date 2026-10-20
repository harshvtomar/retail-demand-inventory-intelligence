import csv,sqlite3,tempfile,unittest
from pathlib import Path
from src.pipeline import run
from src.metrics import metrics

def write(path,fields,rows):
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(rows)
class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.raw=Path(self.tmp.name)/'raw';self.raw.mkdir()
        write(self.raw/'calendar.csv',['d','date','wm_yr_wk','weekday','event_name_1','event_type_1'],[['d_1','2011-01-29',11101,'Saturday','',''],['d_2','2011-01-30',11101,'Sunday','','']])
        write(self.raw/'sell_prices.csv',['store_id','item_id','wm_yr_wk','sell_price'],[['CA_1','FOODS_1_001',11101,'2.5']])
        self.headers=['id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_2']
        self.rows=[['FOODS_1_001_CA_1_validation','FOODS_1_001','FOODS_1','FOODS','CA_1','CA','0','3']]
        self.save()
    def save(self):write(self.raw/'sales_train_validation.csv',self.headers,self.rows)
    def go(self):return run(self.raw,Path(self.tmp.name)/'output.sqlite')
    def test_units_zero_and_revenue(self):
        summary=self.go();self.assertEqual(summary['daily_observations'],2)
        with sqlite3.connect(Path(self.tmp.name)/'output.sqlite') as db:
            m=metrics(db);self.assertEqual(m['units'],3);self.assertEqual(m['zero_share'],0.5);self.assertAlmostEqual(m['priced_revenue'],7.5)
    def test_missing_price_does_not_drop_units(self):
        write(self.raw/'sell_prices.csv',['store_id','item_id','wm_yr_wk','sell_price'],[])
        summary=self.go();self.assertEqual(summary['missing_price_observations'],2)
        with sqlite3.connect(Path(self.tmp.name)/'output.sqlite') as db:self.assertEqual(metrics(db)['units'],3)
    def test_negative_sales_rejected(self):
        self.rows[0][-1]='-1';self.save()
        with self.assertRaises(ValueError):self.go()
    def test_duplicate_series_rejected(self):
        self.rows.append(self.rows[0][:]);self.save()
        with self.assertRaises(ValueError):self.go()
    def test_calendar_missing_day_rejected(self):
        write(self.raw/'calendar.csv',['d','date','wm_yr_wk','weekday','event_name_1','event_type_1'],[['d_1','2011-01-29',11101,'Saturday','','']])
        with self.assertRaises(ValueError):self.go()
    def test_duplicate_weekly_price_rejected(self):
        write(self.raw/'sell_prices.csv',['store_id','item_id','wm_yr_wk','sell_price'],[['CA_1','FOODS_1_001',11101,'2.5'],['CA_1','FOODS_1_001',11101,'3']])
        with self.assertRaises(sqlite3.IntegrityError):self.go()
    def test_missing_source_files_fail(self):
        (self.raw/'calendar.csv').unlink()
        with self.assertRaises(FileNotFoundError):self.go()
    def test_repeatability(self):
        a=self.go();b=self.go();self.assertEqual(a['daily_observations'],b['daily_observations']);self.assertEqual(a['file_sha256'],b['file_sha256'])
if __name__=='__main__':unittest.main()

class AnalysisTest(PipelineTest):
    def test_twelve_sql_queries_execute(self):
        from src.analysis import run as analyze
        self.go()
        result=analyze(Path(self.tmp.name)/'output.sqlite',Path(self.tmp.name)/'tables')
        self.assertEqual(result['queries_executed'],12)
        self.assertEqual(result['metrics']['units'],3)
        self.assertEqual(len(list((Path(self.tmp.name)/'tables').glob('*.csv'))),12)


class SamplingTest(PipelineTest):
    def test_store_department_sampling(self):
        self.rows = [
            ['FOODS_1_001_CA_1_validation', 'FOODS_1_001', 'FOODS_1', 'FOODS', 'CA_1', 'CA', '0', '1'],
            ['FOODS_1_002_CA_1_validation', 'FOODS_1_002', 'FOODS_1', 'FOODS', 'CA_1', 'CA', '2', '0'],
            ['FOODS_1_001_TX_1_validation', 'FOODS_1_001', 'FOODS_1', 'FOODS', 'TX_1', 'TX', '1', '0'],
        ]
        self.save()
        summary=run(self.raw,Path(self.tmp.name)/'sample.sqlite',sample_per_store_dept=1)
        self.assertEqual(summary['series'],2)
        self.assertEqual(summary['stores_sampled'],2)
        self.assertEqual(summary['daily_observations'],4)
    def test_mutually_exclusive_sample_options(self):
        with self.assertRaises(ValueError):
            run(self.raw,Path(self.tmp.name)/'invalid.sqlite',limit_series=1,sample_per_store_dept=1)
