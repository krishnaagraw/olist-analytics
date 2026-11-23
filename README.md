# Olist Marketplace Analytics

**Business question:** Where is this online marketplace losing customers and money, and what should it do about it?

**Live demo:** _add your Streamlit link here after deploying_

An end-to-end analytics project on ~100K real orders (Brazilian e-commerce, 2016-2018):
raw CSVs -> SQL (DuckDB) -> summary tables -> interactive Streamlit dashboard.

## Key findings
_Paste the numbers from `docs/findings.md` here after you run the project on the real data._

## What is inside
| Folder / file | Purpose |
|---|---|
| `sql/` | All SQL: CTEs, window functions (NTILE), cohort and RFM analysis |
| `pipeline/build_data.py` | Loads CSVs, runs the SQL, saves small Parquet files, writes `docs/findings.md` |
| `app/app.py` | Streamlit dashboard (filters, KPIs, cohort heatmap, Pareto, seller table) |
| `run.py` | One command that does everything |

## How to run
1. Install Python 3.10+.
2. Download the dataset from Kaggle and put the 8 CSV files in `data/raw/` (see the note file in that folder).
3. Windows: double-click `run.bat`. Mac/Linux: `bash run.sh`. Or: `pip install -r requirements-dev.txt` then `python run.py`.
4. Open http://localhost:8501.

Test the setup first without the Kaggle data: `python run.py --demo` (fake data, never use its numbers publicly).
Export Power BI files: `python run.py --powerbi` (CSV star-schema files appear in `exports/`).

## Assumptions
- Revenue = product price, excluding freight; canceled and unavailable orders excluded.
- Customers identified by `customer_unique_id` (`customer_id` changes per order).
- Items, payments and reviews have several rows per order, so each is aggregated per order before joining (prevents double-counted revenue).
- Late = delivered on a later calendar date than the estimate.
- Repeat, cohort and RFM analysis use delivered orders only.

## Deploy for free (Streamlit Community Cloud)
1. Run `python run.py --no-app` with the REAL data so `app/data/*.parquet` holds real results.
2. Push to a public GitHub repo (`app/data` must be included, `data/raw` is ignored automatically).
3. On share.streamlit.io: New app -> pick the repo -> main file `app/app.py` -> Deploy.

## Data
Olist Brazilian E-Commerce Public Dataset (Kaggle), CC BY-NC-SA 4.0, non-commercial use.
