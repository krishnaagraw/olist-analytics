"""
Creates FAKE data shaped like the Olist dataset, only so you can test that the
project runs on your PC. Do NOT publish numbers from this data on your resume.
Output folder: data/demo_raw
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "demo_raw"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

N_ORD, N_SELL, N_PROD = 9000, 150, 600
STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "PE"]
STATE_P = [0.40, 0.13, 0.12, 0.06, 0.06, 0.05, 0.05, 0.04, 0.04, 0.05]
LATE_BASE = {"SP": .05, "RJ": .12, "MG": .07, "RS": .07, "PR": .06, "SC": .08,
             "BA": .15, "DF": .08, "GO": .09, "PE": .18}
CATS = ["bed_bath_table", "health_beauty", "sports_leisure", "computers_accessories",
        "furniture_decor", "watches_gifts", "housewares", "toys", "auto", "garden_tools"]
PT = ["cama_mesa_banho", "beleza_saude", "esporte_lazer", "informatica_acessorios",
      "moveis_decoracao", "relogios_presentes", "utilidades_domesticas", "brinquedos",
      "automotivo", "ferramentas_jardim"]


def ids(prefix, n):
    return [f"{prefix}{i:08x}{rng.integers(0, 16**8):08x}" for i in range(n)]


# customers: ~3% of orders come from a person who already ordered before (like the real data)
unique_ids = ids("u", N_ORD)
cust_state = rng.choice(STATES, N_ORD, p=STATE_P)
order_person = np.arange(N_ORD)
reuse = rng.choice(N_ORD, int(N_ORD * 0.03), replace=False)
order_person[reuse] = rng.integers(0, N_ORD, len(reuse))
customer_ids = ids("c", N_ORD)
customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_unique_id": [unique_ids[p] for p in order_person],
    "customer_zip_code_prefix": rng.integers(1000, 99999, N_ORD),
    "customer_city": "city",
    "customer_state": [cust_state[p] for p in order_person],
})

# orders
days = (pd.Timestamp("2018-08-31") - pd.Timestamp("2017-01-01")).days
growth = np.sqrt(rng.random(N_ORD))                 # more orders later in time
purchase = pd.Timestamp("2017-01-01") + pd.to_timedelta((growth * days * 86400).astype(int), unit="s")
estimated = purchase.normalize() + pd.to_timedelta(rng.integers(15, 30, N_ORD), unit="D")
late_p = customers["customer_state"].map(LATE_BASE).values
is_late = rng.random(N_ORD) < late_p
delay = np.where(is_late, rng.integers(1, 20, N_ORD), -rng.integers(0, 12, N_ORD))
delivered = estimated + pd.to_timedelta(delay, unit="D") + pd.to_timedelta(rng.integers(8, 20, N_ORD), unit="h")
status = rng.choice(["delivered", "shipped", "canceled", "unavailable"], N_ORD, p=[.965, .015, .015, .005])
deliv_col = pd.Series(delivered).where(status == "delivered")
orders = pd.DataFrame({
    "order_id": ids("o", N_ORD), "customer_id": customer_ids, "order_status": status,
    "order_purchase_timestamp": purchase, "order_approved_at": purchase + pd.Timedelta(hours=1),
    "order_delivered_carrier_date": purchase + pd.Timedelta(days=2),
    "order_delivered_customer_date": deliv_col,
    "order_estimated_delivery_date": estimated,
})

# sellers, products
sellers = pd.DataFrame({"seller_id": ids("s", N_SELL), "seller_zip_code_prefix": 1000,
                        "seller_city": "city", "seller_state": rng.choice(STATES, N_SELL, p=STATE_P)})
cat_idx = rng.integers(0, len(PT), N_PROD)
products = pd.DataFrame({"product_id": ids("p", N_PROD),
                         "product_category_name": [PT[i] for i in cat_idx]})
products.loc[rng.choice(N_PROD, 20, replace=False), "product_category_name"] = np.nan
translation = pd.DataFrame({"product_category_name": PT, "product_category_name_english": CATS})

# items (1-3 per order). Seller popularity is skewed so a few sellers dominate.
seller_w = rng.pareto(1.2, N_SELL) + 0.1
seller_w /= seller_w.sum()
rows = []
for oid in orders["order_id"]:
    for k in range(1, rng.choice([1, 2, 3], p=[.8, .15, .05]) + 1):
        price = float(np.round(rng.lognormal(4.3, 0.8), 2))
        rows.append((oid, k, products["product_id"].iloc[rng.integers(N_PROD)],
                     sellers["seller_id"].iloc[rng.choice(N_SELL, p=seller_w)],
                     price, float(np.round(price * rng.uniform(0.1, 0.4), 2))))
items = pd.DataFrame(rows, columns=["order_id", "order_item_id", "product_id", "seller_id",
                                    "price", "freight_value"])
items["shipping_limit_date"] = pd.Timestamp("2017-06-01")

# payments (some orders have 2 payment rows) and reviews (late orders get lower scores)
tot = items.groupby("order_id")[["price", "freight_value"]].sum().sum(axis=1)
pay = []
for oid, v in tot.items():
    if rng.random() < 0.05:
        pay.append((oid, 1, "credit_card", 1, round(v * 0.5, 2)))
        pay.append((oid, 2, "voucher", 1, round(v * 0.5, 2)))
    else:
        pay.append((oid, 1, rng.choice(["credit_card", "boleto", "debit_card"], p=[.75, .2, .05]),
                    int(rng.integers(1, 8)), round(v, 2)))
payments = pd.DataFrame(pay, columns=["order_id", "payment_sequential", "payment_type",
                                      "payment_installments", "payment_value"])
score = np.where(is_late, rng.choice([1, 2, 3, 4, 5], N_ORD, p=[.35, .2, .15, .15, .15]),
                 rng.choice([1, 2, 3, 4, 5], N_ORD, p=[.05, .03, .08, .27, .57]))
reviews = pd.DataFrame({"review_id": ids("r", N_ORD), "order_id": orders["order_id"],
                        "review_score": score, "review_comment_title": np.nan,
                        "review_comment_message": np.nan,
                        "review_creation_date": purchase + pd.Timedelta(days=20),
                        "review_answer_timestamp": purchase + pd.Timedelta(days=21)})
extra = reviews.sample(300, random_state=1).copy()       # a few orders have 2 reviews
extra["review_id"] = ids("x", len(extra))
reviews = pd.concat([reviews, extra])

for name, df in {
    "olist_customers_dataset": customers, "olist_orders_dataset": orders,
    "olist_order_items_dataset": items, "olist_order_payments_dataset": payments,
    "olist_order_reviews_dataset": reviews, "olist_products_dataset": products,
    "olist_sellers_dataset": sellers, "product_category_name_translation": translation,
}.items():
    df.to_csv(OUT / f"{name}.csv", index=False)
print("Demo data written to", OUT)
