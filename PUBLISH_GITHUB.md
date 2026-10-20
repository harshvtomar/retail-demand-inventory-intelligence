# Publish SupplyPulse on GitHub — Session 1 Task 5

## Status

**Prepared, not yet published.** No `retail-demand-inventory-intelligence` repository was visible in the connected `harshvtomar` GitHub account when this package was prepared. Repository creation is not supported by the available GitHub write actions in this chat. Do not claim a commit SHA or successful GitHub Actions run until verified.

## Step 1: Create an empty GitHub repository

1. Open **https://github.com/new?name=retail-demand-inventory-intelligence** while signed into `harshvtomar`.
2. Repository name: `retail-demand-inventory-intelligence`. Select **Public** if you want a publicly viewable portfolio.
3. **Do not** tick *Add a README*, *.gitignore*, or *Choose a license*; this package already contains its own files and the dataset rights do not grant an automatic license to redistribute the source data.
4. Click **Create repository**.

## Step 2: Publish the prepared project

Use a terminal on the Mac after extracting the release ZIP:

```bash
cd ~/Downloads/retail-demand-inventory-intelligence
python3 -m pytest -q
bash scripts/publish_github.sh --check
bash scripts/publish_github.sh --publish
```

If your extracted folder is elsewhere, change the `cd` path. Git must be installed and configured with your identity (run `git config --global user.name` and `git config --global user.email` to check); GitHub authentication may be required by the credential helper, browser, or GitHub Desktop. **Do not put a password, PAT, or Kaggle credentials into the repository or chat.**

The script commits only Git-eligible files and refuses to stage raw M5 CSVs, the local SQLite database, credentials, or unexpectedly large files. It refuses to push to a mismatched `origin` remote.

**Alternative:** In GitHub Desktop, choose **File → Add Local Repository** and select the extracted project folder. If it is not yet a Git repository, use the create-local-repository option. Publish the repository as `retail-demand-inventory-intelligence`, with the public/private setting appropriate for your portfolio. Inspect the staged files and make sure `data/raw` and `data/processed` are not included.

## Step 3: Verify the published repository

1. Visit **https://github.com/harshvtomar/retail-demand-inventory-intelligence**.
2. Check `README.md`, `.github/workflows/ci.yml`, `src/`, `sql/`, `tests/`, `notebooks/`, `reports/` and `docs/` appear.
3. Confirm that **no** original `sales_train_validation.csv`, `sell_prices.csv`, `calendar.csv`, large `.sqlite` files, `.env`, authentication tokens, or `source_manifest.json` were committed.
4. Open the **Actions** tab and check whether the fixture-based tests run. **CI verification is Session 1 Task 6, not Task 5.**
5. Record the public URL and the actual commit SHA in `PROJECT_STATE.md` only after GitHub confirms them.

## What is included

- 12 SQL report outputs and independent Python/SQL reconciliation.
- Executed exploratory notebook, six visuals and accompanying business review.
- Full-source audit summaries and tests (but not the source CSVs).
- `.github/workflows/ci.yml` and Session 2 handoff notes.

## Known limitations

The warehouse in the project was built using a **210-series nonrandom subset**, not the full Walmart M5 time series. Raw Kaggle CSVs remain in a separate, locally ignored directory. All data-driven results are sample-specific and do not establish causal effects, inventory availability, lost sales, or true unconstrained demand.


## Additional verification — 20 October 2026

Before publication, the unit-test GitHub Actions workflow was corrected to install `requirements-ci.txt` (pytest, pandas and matplotlib). Local tests pass (51 passed). `requirements-ci.txt` is needed for fixture-based CI and **does not** make private Kaggle data available to Actions.

If GitHub has been created, you can also just reply **"Repository created"** in the ChatGPT conversation; the GitHub connector can then attempt to commit approved text files. For a large batch of project files, publishing locally with `scripts/publish_github.sh` may be more efficient. Any GitHub Actions status must be confirmed after an actual remote push.
