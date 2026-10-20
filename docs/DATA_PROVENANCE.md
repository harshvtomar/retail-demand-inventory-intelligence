# Data source and provenance

**Source:** [Kaggle M5 Forecasting — Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data). The user supplied the original-named competition download ZIP on 20 October 2026 after being guided through Kaggle's access terms.

The ZIP contained: `calendar.csv`, `sales_train_evaluation.csv`, `sales_train_validation.csv`, `sample_submission.csv`, and `sell_prices.csv`. All members passed ZIP CRC validation. Only `calendar.csv`, `sales_train_validation.csv`, and `sell_prices.csv` were extracted. The project's authorized importer passed all strict source schema/row-count checks and computed SHA-256 hashes (see local `data/raw/source_manifest.json`).

| File | Records | SHA-256 |
|---|---:|---|
| calendar.csv | 1,969 | `d12b5914ef03e66649adf5dd9e996e6602251c22b7a6af8f1f7e3aa12f8860f5` |
| sales_train_validation.csv | 30,490 | `f368e66ed1dbecb48b2cc8fc589bf68b3deddbbb36bf5c88b4d6d0a09b9b6724` |
| sell_prices.csv | 6,841,121 | `9da3ad1f8b8ccacdbdc70612191dd375ec24a4ac6625c24b75b3bc60b0bed2ef` |

**Source confidence:** file structures/record counts match the expected competition dataset; import integrity is verified. SHA-256 allows rerun comparisons. It does not by itself prove the upload was fetched directly from Kaggle by this runtime (the user provided it).

**Permitted reuse:** Kaggle competition rules govern source-data use and sharing. Do not commit source CSVs to public GitHub or include them in distributed project ZIPs. This project emits a separately labeled, deterministic, nonrandom sample of source data for analysis and aggregate reports.

The sample covers 210 item-store series: first three per `(store_id, dept_id)` combination across 10 stores, 7 departments. It is not representative. Dates: 2011-01-29 to 2016-04-24 (1,913 days). Do not claim inventory, supplier lead times, stockouts, or lost sales from this dataset.
