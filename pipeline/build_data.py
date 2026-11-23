"""
Build step: raw Olist CSVs  ->  SQL (DuckDB)  ->  small Parquet files for the dashboard.

Usage (from the project folder):
    python pipeline/build_data.py                  # uses data/raw
    python pipeline/build_data.py --raw data/demo_raw
    python pipeline/build_data.py --powerbi        # also exports CSVs for Power BI
"""
import argparse
import re
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
from insights import compute_insights, insights_to_markdown  # noqa: E402

# table name -> (csv file, columns that hold dates)
TABLES = {
    "customers": ("olist_customers_dataset.csv", []),
    "orders": ("olist_orders_dataset.csv", [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"]),
    "order_items": ("olist_order_items_dataset.csv", ["shipping_limit_date"]),
    "order_payments": ("olist_order_payments_dataset.csv", []),
    "order_reviews": ("olist_order_reviews_dataset.csv",
                      ["review_creation_date", "review_answer_timestamp"]),
    "products": ("olist_products_dataset.csv", []),
    "sellers": ("olist_sellers_dataset.csv", []),
    "category_translation": ("product_category_name_translation.csv", []),
}


def split_statements(sql_text: str):
    """Split a .sql file into single statements (comment lines removed)."""
    lines = [ln for ln in sql_text.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def load_raw(con, raw_dir: Path):
    missing = [f for f, _ in TABLES.values() if not (raw_dir / f).exists()]
    if missing:
        print(f"\nERROR: these files were not found in {raw_dir}:")
        for m in missing:
            print("  -", m)
        print("\nDownload the 'Brazilian E-Commerce Public Dataset by Olist' from Kaggle,")
        print("unzip it, and copy the CSV files into that folder. Then run again.")
        sys.exit(1)
    print(f"Loading CSV files from {raw_dir} ...")
    for table, (fname, date_cols) in TABLES.items():
        df = pd.read_csv(raw_dir / fname, parse_dates=date_cols)
        con.register("tmp_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM tmp_df")
        con.unregister("tmp_df")
        print(f"  {table:22s} {len(df):>8,} rows")


def export_powerbi(con, out_dir: Path):
    out_dir.mkdir(exist_ok=True)
    exports = {
        "fact_sales": """
            SELECT oi.order_id, oi.order_item_id, oi.product_id, oi.seller_id,
                   ob.customer_unique_id, CAST(ob.purchased_at AS DATE) AS order_date,
                   oi.price, oi.freight_value, ob.order_status,
                   ob.delivery_days, ob.delay_days, ob.is_late
            FROM order_items oi JOIN order_base ob ON oi.order_id = ob.order_id""",
        "fact_reviews": "SELECT order_id, review_score FROM review_per_order",
        "dim_product": """
            SELECT p.product_id,
                   COALESCE(t.product_category_name_english, p.product_category_name, 'unknown') AS category
            FROM products p
            LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name""",
        "dim_seller": "SELECT seller_id, seller_city, seller_state FROM sellers",
        "dim_customer": """
            SELECT customer_unique_id, MAX(customer_city) AS customer_city,
                   MAX(customer_state) AS customer_state
            FROM customers GROUP BY customer_unique_id""",
    }
    for name, sql in exports.items():
        con.execute(sql).df().to_csv(out_dir / f"{name}.csv", index=False)
        print(f"  Power BI export: {name}.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--powerbi", action="store_true", help="also write CSVs for Power BI")
    args = ap.parse_args()

    out_dir = ROOT / "app" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()          # temporary in-memory database

    load_raw(con, Path(args.raw))

    sql_dir = ROOT / "sql"
    print("\nCreating base views ...")
    for stmt in split_statements((sql_dir / "00_base_views.sql").read_text(encoding="utf-8")):
        con.execute(stmt)

    print("\nRunning SQL files and saving results ...")
    marts = {}
    for f in sorted(sql_dir.glob("[0-9][0-9]_*.sql")):
        if f.name.startswith("00_"):
            continue
        name = re.sub(r"^\d+_", "", f.stem)
        df = con.execute(f.read_text(encoding="utf-8")).df()
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
        marts[name] = df
        print(f"  {f.name:28s} -> {name}.parquet  ({len(df):,} rows)")

    # Auto-written findings with the real numbers from your data
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    findings = compute_insights(marts)
    (docs / "findings.md").write_text(insights_to_markdown(findings), encoding="utf-8")
    print("\nWrote docs/findings.md (your real numbers for README and resume)")

    if args.powerbi:
        print("\nExporting Power BI files ...")
        export_powerbi(con, ROOT / "exports")

    print("\nDone. Start the dashboard with:  streamlit run app/app.py")
