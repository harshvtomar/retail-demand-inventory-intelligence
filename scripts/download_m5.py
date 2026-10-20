"""Acquire authorized original M5 CSVs without storing Kaggle credentials in this project.

Usage (from project root):
  python -m scripts.download_m5
  python -m scripts.download_m5 --archive ~/Downloads/m5-forecasting-accuracy.zip
  python -m scripts.download_m5 --from-dir ~/Downloads/m5

Requires accepted competition terms for Kaggle CLI downloads. No raw CSVs are committed.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

COMPETITION = 'm5-forecasting-accuracy'
REQUIRED = ('calendar.csv', 'sales_train_validation.csv', 'sell_prices.csv')
HEADERS = {
    'calendar.csv': {'date', 'wm_yr_wk', 'd', 'weekday', 'wday'},
    'sales_train_validation.csv': {'id','item_id','dept_id','cat_id','store_id','state_id','d_1','d_1913'},
    'sell_prices.csv': {'store_id','item_id','wm_yr_wk','sell_price'},
}


def describe_csv(path, name, strict=True):
    """Verify content type and basic schema; count rows and compute SHA-256."""
    digest = hashlib.sha256()
    rows_newline = 0
    last_byte = None
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(2 * 1024 * 1024), b''):
            digest.update(chunk)
            rows_newline += chunk.count(b'\n')
            last_byte = chunk[-1:]
    if last_byte is None:
        raise ValueError(f'{name} is empty')
    with open(path, encoding='utf-8-sig', newline='') as f:
        header = next(csv.reader(f), [])
    if not HEADERS[name].issubset(header):
        raise ValueError(f'{name}: expected M5 columns absent: {sorted(HEADERS[name] - set(header))}')
    lines = rows_newline + (last_byte != b'\n')
    rows = lines - 1
    if rows < 1:
        raise ValueError(f'{name} contains no data rows')
    if strict:
        if name == 'calendar.csv' and rows != 1969:
            raise ValueError(f'calendar.csv: expected 1969 records; found {rows}')
        if name == 'sales_train_validation.csv' and rows != 30490:
            raise ValueError(f'sales_train_validation.csv: expected 30490 records; found {rows}')
        if name == 'sell_prices.csv' and rows < 1000000:
            raise ValueError(f'sell_prices.csv: unexpectedly few records ({rows})')
    return {'bytes': path.stat().st_size, 'rows': int(rows), 'sha256': digest.hexdigest()}


def copy_csv(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(source, 'rb') as reader, open(dest, 'wb') as writer:
        shutil.copyfileobj(reader, writer, 2 * 1024 * 1024)


def extract_from_archive(archive, stage):
    with zipfile.ZipFile(archive, 'r') as zf:
        available = {}
        for info in zf.infolist():
            if not info.is_dir() and Path(info.filename).name in REQUIRED:
                name = Path(info.filename).name
                if name in available:
                    raise ValueError(f'Ambiguous duplicate {name} in archive')
                available[name] = info
        missing = set(REQUIRED) - set(available)
        if missing:
            raise FileNotFoundError(f'Archive missing: {sorted(missing)}')
        for name in REQUIRED:
            with zf.open(available[name]) as src, open(stage / name, 'wb') as dst:
                shutil.copyfileobj(src, dst, 2 * 1024 * 1024)


def download_using_kaggle_cli(stage):
    cli = shutil.which('kaggle')
    if not cli:
        raise RuntimeError('Kaggle CLI missing. Run: python3 -m pip install kaggle; then kaggle auth login. Accept the competition rules in browser.')
    for name in REQUIRED:
        print(f'Requesting {name} from official Kaggle competition...', flush=True)
        completed = subprocess.run([cli, 'competitions', 'download', COMPETITION,
                                    '-f', name, '-p', str(stage)], capture_output=True, text=True)
        if completed.returncode:
            # Avoid printing HTTP headers, tokens or other potentially sensitive text.
            raise RuntimeError(f'Official Kaggle download failed for {name} (code {completed.returncode}). '
                               'Check login and acceptance of competition rules at '
                               'https://www.kaggle.com/competitions/m5-forecasting-accuracy/data')
        if (stage / name).is_file():
            continue
        archives = list(stage.glob(f'{name}*.zip'))
        if len(archives) != 1:
            raise RuntimeError(f'Kaggle reported success but {name} was not found (or ambiguous archives)')
        with zipfile.ZipFile(archives[0]) as zf:
            matches = [x for x in zf.infolist() if Path(x.filename).name == name]
            if len(matches) != 1:
                raise RuntimeError(f'{archives[0].name} does not contain the expected CSV')
            with zf.open(matches[0]) as src, open(stage / name, 'wb') as dst:
                shutil.copyfileobj(src, dst, 2 * 1024 * 1024)
        archives[0].unlink()


def acquire(destination, archive=None, from_dir=None, force=False, strict=True):
    destination = Path(destination)
    if not force and any((destination / name).exists() for name in REQUIRED):
        raise FileExistsError('Some dataset files already exist. Nothing overwritten; use --force to replace all three.')
    with tempfile.TemporaryDirectory(prefix='m5_authorized_') as tmp:
        stage = Path(tmp)
        if archive:
            extract_from_archive(Path(archive).expanduser(), stage)
            source = f'User-provided archive: {Path(archive).expanduser().name}; user responsible for lawful dataset access'
        elif from_dir:
            directory = Path(from_dir).expanduser()
            for name in REQUIRED:
                copy_csv(directory / name, stage / name)
            source = 'User-provided directory; user responsible for lawful dataset access'
        else:
            download_using_kaggle_cli(stage)
            source = 'Authenticated Kaggle CLI / m5-forecasting-accuracy competition'
        checks = {name: describe_csv(stage / name, name, strict=strict) for name in REQUIRED}
        destination.mkdir(parents=True, exist_ok=True)
        for name in REQUIRED:
            # os.replace is atomic on a filesystem. Temp stage may be another filesystem,
            # so copy to a destination-side temporary file and then replace.
            temp_target = destination / (name + '.partial')
            copy_csv(stage / name, temp_target)
            temp_target.replace(destination / name)
        manifest = {
            'competition': COMPETITION,
            'original_url': 'https://www.kaggle.com/competitions/m5-forecasting-accuracy/data',
            'source_method': source,
            'retrieved_or_imported_utc': datetime.now(timezone.utc).isoformat(),
            'license_note': 'Subject to Competition Rules; raw CSVs must not be committed or redistributed',
            'full_original_csv_validation': bool(strict),
            'files': checks,
        }
        (destination / 'source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        return manifest


def main():
    parser = argparse.ArgumentParser(description='Download/verify original Kaggle M5 files; never store auth in repo')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--archive', help='Locally downloaded official Kaggle ZIP')
    source.add_argument('--from-dir', help='Folder containing the three authorized M5 CSVs')
    parser.add_argument('--destination', default='data/raw', help='Raw CSV destination; gitignored by default')
    parser.add_argument('--force', action='store_true', help='Replace any existing files after successful staged verification')
    args = parser.parse_args()
    try:
        result = acquire(args.destination, archive=args.archive, from_dir=args.from_dir, force=args.force)
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f'M5 acquisition not completed: {exc}', file=sys.stderr)
        raise SystemExit(2) from None
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
