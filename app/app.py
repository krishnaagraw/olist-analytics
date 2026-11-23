"""Olist Marketplace Analytics dashboard (Streamlit)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from insights import brl, compute_insights  # noqa: E402

DATA = HERE / "data"
NAMES = ["state_month", "category_year", "delivery_vs_review", "repeat_customers",
         "cohort_retention", "rfm_segments", "seller_summary", "payment_mix", "meta"]

st.set_page_config(page_title="Olist Marketplace Analytics", page_icon="📦", layout="wide")

if not all((DATA / f"{n}.parquet").exists() for n in NAMES):
    st.error("Data files not found. Run `python run.py` (or `python pipeline/build_data.py`) first.")
    st.stop()


@st.cache_data
def load_all():
    return {n: pd.read_parquet(DATA / f"{n}.parquet") for n in NAMES}


D = load_all()
sm = D["state_month"].copy()
sm["year"] = sm["ym"].str[:4]
meta = D["meta"].iloc[0]

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
all_years = sorted(sm["year"].unique())
all_states = sorted(sm["state"].unique())
sel_years = st.sidebar.multiselect("Year", all_years, default=all_years)
sel_states = st.sidebar.multiselect("State", all_states, default=all_states)
st.sidebar.caption("Filters apply to the Overview and Delivery tabs. "
                   "The category chart responds to Year only.")

f = sm[sm["year"].isin(sel_years) & sm["state"].isin(sel_states)]

st.title("📦 Olist Marketplace Analytics")
st.caption(f"Brazilian e-commerce, {meta['first_order']} to {meta['last_order']}. "
           "Data: Olist public dataset (Kaggle). Built with SQL (DuckDB), Python and Streamlit.")

tab_find, tab_over, tab_cust, tab_ops, tab_about = st.tabs(
    ["Key findings", "Overview", "Customers", "Delivery & Sellers,About"])

# ---------------- Key findings ----------------
with tab_find:
    st.subheader("What the data says")
    st.caption("Calculated from the full dataset (filters do not change this tab).")
    for title, text in compute_insights(D):
        st.info(f"**{title}.** {text}")

# ---------------- Overview ----------------
with tab_over:
    if f.empty:
        st.warning("No data for the selected filters.")
    else:
        revenue, orders = f["revenue"].sum(), f["orders"].sum()
        delivered = f["delivered_orders"].sum()
        late_pct = f["late_orders"].sum() / delivered * 100 if delivered else 0
        review = f["review_sum"].sum() / f["review_n"].sum() if f["review_n"].sum() else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Revenue", brl(revenue))
        c2.metric("Orders", f"{int(orders):,}")
        c3.metric("Avg order value", f"R$ {revenue / orders:,.0f}")
        c4.metric("Avg review", f"{review:.2f} / 5")
        c5.metric("Late deliveries", f"{late_pct:.1f}%")

        monthly = (f.groupby("ym", as_index=False)[["revenue", "orders"]].sum()
                   .sort_values("ym"))
        monthly["3-month average"] = monthly["revenue"].rolling(3).mean()
        monthly = monthly.rename(columns={"revenue": "Monthly revenue"})
        fig = px.line(monthly, x="ym", y=["Monthly revenue", "3-month average"], markers=True,
                      title="Revenue by month, with 3-month rolling average",
                      labels={"ym": "Month", "value": "Revenue (BRL)", "variable": ""})
        st.plotly_chart(fig, use_container_width=True)

        left, right = st.columns(2)
        by_state = (f.groupby("state", as_index=False)["revenue"].sum()
                    .sort_values("revenue", ascending=False).head(10))
        left.plotly_chart(
            px.bar(by_state, x="state", y="revenue", title="Top 10 states by revenue",
                   labels={"revenue": "Revenue (BRL)", "state": "State"}),
            use_container_width=True)

        cats = D["category_year"]
        cats = cats[cats["year"].isin(sel_years)]
        top = (cats.groupby("category", as_index=False)["revenue"].sum()
               .sort_values("revenue", ascending=False).head(10).sort_values("revenue"))
        right.plotly_chart(
            px.bar(top, x="revenue", y="category", orientation="h",
                   title="Top 10 categories by revenue",
                   labels={"revenue": "Revenue (BRL)", "category": ""}),
            use_container_width=True)

        pm = D["payment_mix"]
        a, b = st.columns(2)
        a.plotly_chart(px.pie(pm, names="payment_type", values="total_value", hole=0.5,
                              title="Payment method share (by value)"),
                       use_container_width=True)
        b.dataframe(pm.rename(columns={"payment_type": "Payment type", "orders": "Orders",
                                       "total_value": "Total value",
                                       "avg_installments": "Avg installments"}),
                    use_container_width=True, hide_index=True)

# ---------------- Customers ----------------
with tab_cust:
    rp = D["repeat_customers"]
    total = rp["customers"].sum()
    repeat = rp.loc[rp["order_group"] != "1 order", "customers"].sum()
    st.metric("Customers who ordered more than once", f"{repeat / total * 100:.1f}%")

    l, r = st.columns(2)
    l.plotly_chart(px.pie(rp, names="order_group", values="customers", hole=0.5,
                          title="Orders per customer"), use_container_width=True)
    rfm = D["rfm_segments"]
    r.plotly_chart(px.bar(rfm, x="segment", y="total_spend", title="Total spend by customer segment",
                          labels={"total_spend": "Total spend (BRL)", "segment": ""}),
                   use_container_width=True)

    st.subheader("Cohort retention")
    st.caption("Cohort = month of a customer's first order. Each cell = % of that cohort ordering again "
               "N months later. Small early cohorts are hidden.")
    co = D["cohort_retention"]
    pv = co.pivot(index="cohort_month", columns="month_number", values="customers")
    if 0 in pv.columns:
        pv = pv[pv[0] >= 100] if (pv[0] >= 100).sum() >= 3 else pv
        ret = pv.div(pv[0], axis=0).mul(100).round(1)
        ret = ret.loc[:, [c for c in ret.columns if c <= 12]]
        fig = px.imshow(ret, text_auto=".1f", aspect="auto", color_continuous_scale="Blues",
                        labels=dict(x="Months since first order", y="Cohort", color="% retained"))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("RFM segments")
    st.dataframe(rfm.rename(columns={"segment": "Segment", "customers": "Customers",
                                     "avg_spend": "Avg spend", "total_spend": "Total spend"}),
                 use_container_width=True, hide_index=True)

# ---------------- Delivery & Sellers ----------------
with tab_ops:
    dv = D["delivery_vs_review"].sort_values("delivery_group")
    l, r = st.columns(2)
    l.plotly_chart(px.bar(dv, x="delivery_group", y="avg_review", text="avg_review",
                          title="Late deliveries get lower review scores",
                          labels={"delivery_group": "", "avg_review": "Average review (1-5)"},
                          range_y=[0, 5]), use_container_width=True)

    if not f.empty:
        st_late = f.groupby("state")[["delivered_orders", "late_orders"]].sum()
        st_late = st_late[st_late["delivered_orders"] > 0]
        st_late["late_rate_pct"] = st_late["late_orders"] / st_late["delivered_orders"] * 100
        st_late = st_late.reset_index().sort_values("late_rate_pct", ascending=False)
        r.plotly_chart(px.bar(st_late, x="state", y="late_rate_pct",
                              title="Late delivery rate by state (%)",
                              labels={"late_rate_pct": "Late deliveries (%)", "state": "State"}),
                       use_container_width=True)

    st.subheader("Seller concentration (Pareto)")
    sellers = D["seller_summary"].sort_values("revenue", ascending=False).reset_index(drop=True)
    sellers["cum_revenue_pct"] = sellers["revenue"].cumsum() / sellers["revenue"].sum() * 100
    sellers["sellers_pct"] = (sellers.index + 1) / len(sellers) * 100
    fig = go.Figure(go.Scatter(x=sellers["sellers_pct"], y=sellers["cum_revenue_pct"], mode="lines"))
    fig.update_layout(title="Share of revenue earned by the top X% of sellers",
                      xaxis_title="Top % of sellers", yaxis_title="Cumulative % of revenue")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 20 sellers")
    top = sellers.head(20).copy()
    top["seller_id"] = top["seller_id"].str[:8]
    st.dataframe(top[["seller_id", "state", "revenue", "orders", "avg_review", "cum_revenue_pct"]]
                 .round(1), use_container_width=True, hide_index=True)

    st.subheader("Freight cost as % of product price (top 15 categories by revenue)")
    cat = (D["category_year"][D["category_year"]["year"].isin(sel_years)]
           .groupby("category")[["revenue", "freight"]].sum()
           .sort_values("revenue", ascending=False).head(15))
    cat["freight_pct"] = cat["freight"] / cat["revenue"] * 100
    st.plotly_chart(px.bar(cat.reset_index().sort_values("freight_pct"), x="freight_pct",
                           y="category", orientation="h",
                           labels={"freight_pct": "Freight % of price", "category": ""}),
                    use_container_width=True)

# ---------------- About ----------------
with tab_about:
    st.markdown("""
### How this project works
`CSV files -> SQL (DuckDB) -> small Parquet files -> this Streamlit app`

The SQL lives in the `sql/` folder of the GitHub repo. It is run once by `pipeline/build_data.py`,
so this dashboard only reads small summary files and stays fast.

### Assumptions
- Revenue = product price (freight excluded). Canceled and unavailable orders are excluded.
- Customers are counted with `customer_unique_id` because `customer_id` changes on every order.
- Payments, items and reviews have several rows per order, so each is summed/averaged **per order first**
  before joining. Otherwise revenue would be double-counted.
- An order is *late* if it was delivered on a later calendar date than the estimated date.
- Repeat, cohort and RFM analysis use delivered orders only.
- RFM: frequency is not split into 5 groups because almost all customers ordered once.
  Anyone with 2+ orders is a "Repeat buyer"; one-time buyers are split by recency and spend.
- 2016 and late 2018 have very few orders, so growth figures compare only full overlapping months.

### Data source
Olist Brazilian E-Commerce Public Dataset (Kaggle), licensed CC BY-NC-SA 4.0 for non-commercial use.
""")
