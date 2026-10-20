"""Fixture-only tests for authenticated download helper; do not imply real M5 access."""
import csv
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.download_m5 import acquire, describe_csv, REQUIRED


def csv_bytes(columns, rows):
    import io
    buff = io.StringIO()
    w=csv.writer(buff);w.writerow(columns);w.writerows(rows)
    return buff.getvalue().encode()


class DownloadHelperFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.files={
          'calendar.csv': csv_bytes(['date','wm_yr_wk','d','weekday','wday'],[['2011-01-29','11101','d_1','Saturday','1']]),
          'sales_train_validation.csv': csv_bytes(['id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_1913'],[['x','a','b','c','s','CA','0','3']]),
          'sell_prices.csv': csv_bytes(['store_id','item_id','wm_yr_wk','sell_price'],[['s','a','11101','2.5']]),
        }
    def test_archive_extract_manifest_fixture(self):
        path=self.root/'authorized_sample.zip'
        with zipfile.ZipFile(path,'w') as z:
            for name, content in self.files.items():z.writestr('m5-forecasting/'+name,content)
        raw=self.root/'raw'; manifest=acquire(raw,archive=path,strict=False)
        self.assertEqual(set(manifest['files']),set(REQUIRED))
        self.assertFalse(manifest['full_original_csv_validation'])
        self.assertTrue((raw/'source_manifest.json').is_file())
        self.assertEqual((raw/'calendar.csv').read_bytes(),self.files['calendar.csv'])
    def test_missing_archive_file_does_not_write_partial(self):
        archive=self.root/'missing.zip'
        with zipfile.ZipFile(archive,'w') as z:z.writestr('calendar.csv',self.files['calendar.csv'])
        with self.assertRaises(FileNotFoundError):acquire(self.root/'raw',archive=archive,strict=False)
        self.assertFalse((self.root/'raw'/'calendar.csv').exists())
    def test_wrong_csv_header_fails(self):
        path=self.root/'calendar.csv';path.write_text('foo,bar\n1,2\n')
        with self.assertRaisesRegex(ValueError,'expected M5 columns'):describe_csv(path,'calendar.csv',strict=False)
    def test_prevents_overwrite_without_force(self):
        raw=self.root/'raw';raw.mkdir();(raw/'calendar.csv').write_text('already present')
        with self.assertRaises(FileExistsError):acquire(raw,strict=False)
    def test_strict_rejects_tiny_fixture(self):
        path=self.root/'calendar.csv';path.write_bytes(self.files['calendar.csv'])
        with self.assertRaisesRegex(ValueError,'1969'):describe_csv(path,'calendar.csv',strict=True)

if __name__=='__main__':unittest.main()
