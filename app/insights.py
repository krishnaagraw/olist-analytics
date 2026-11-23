"""Turns the summary tables into plain-English findings (all numbers come from the data)."""
import calendar
import math

import pandas as pd


def brl(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"R$ {x / 1_000_000:,.2f}M"
    return f"R$ {x:,.0f}"


def compute_insights(d: dict) -> list:
    """d = dict of DataFrames (state_month, repeat_customers, ...). Returns [(title, text), ...]."""
    out = []
    sm = d["state_month"].copy()
    meta = d["meta"].iloc[0]

    # 1. Scale
    out.append((
        "Scale of the data",
        f"{int(meta['total_orders']):,} orders from {int(meta['total_customers']):,} customers and "
        f"{int(meta['total_sellers']):,} sellers between {meta['first_order']} and {meta['last_order']}. "
        f"Revenue from valid (non-canceled) orders is {brl(sm['revenue'].sum())}."
    ))

    # 2. Year-over-year growth on months that exist in both years
    sm["year"] = sm["ym"].str[:4]
    sm["mm"] = sm["ym"].str[5:7]
    mon = sm.groupby(["year", "mm"], as_index=False)[["revenue", "orders"]].sum()
    years = sorted(mon["year"].unique())
    if len(years) >= 2:
        y_new, y_old = years[-1], years[-2]
        a_ = mon[mon.year == y_new].set_index("mm")
        b_ = mon[mon.year == y_old].set_index("mm")
        # only compare months that are well populated in BOTH years (early/late months are tiny)
        common = [m for m in sorted(set(a_.index) & set(b_.index))
                  if a_.loc[m, "orders"] >= 500 and b_.loc[m, "orders"] >= 500]
        if not common:
            common = [m for m in sorted(set(a_.index) & set(b_.index))
                      if a_.loc[m, "orders"] >= 50 and b_.loc[m, "orders"] >= 50]
        if common:
            new, old = a_.loc[common, "revenue"].sum(), b_.loc[common, "revenue"].sum()
            names = [calendar.month_abbr[int(m)] for m in common]
            span = names[0] if len(names) == 1 else f"{names[0]} to {names[-1]}"
            out.append((
                "Growth",
                f"Comparing the same months ({span}), revenue in {y_new} was {brl(new)} versus "
                f"{brl(old)} in {y_old}, a change of {(new / old - 1) * 100:+.0f}%."
            ))

    # 3. Repeat customers
    rp = d["repeat_customers"]
    total = rp["customers"].sum()
    repeat = rp.loc[rp["order_group"] != "1 order", "customers"].sum()
    out.append((
        "Very few customers come back",
        f"Only {repeat / total * 100:.1f}% of customers ({int(repeat):,} of {int(total):,}) placed more than one "
        f"delivered order. The business depends mostly on winning new customers. "
        f"Recommendation: a post-purchase campaign (coupon or reminder) to bring first-time buyers back."
    ))

    # 4. Late delivery and reviews
    dv = d["delivery_vs_review"].sort_values("delivery_group")
    late_rate = sm["late_orders"].sum() / max(sm["delivered_orders"].sum(), 1)
    if len(dv) >= 2:
        on = dv.iloc[0]["avg_review"]
        worst = dv.iloc[-1]["avg_review"]
        out.append((
            "Late deliveries hurt reviews",
            f"{late_rate * 100:.1f}% of delivered orders arrived after the promised date. On-time orders average "
            f"{on:.2f} stars, while the most delayed group averages {worst:.2f} "
            f"(a drop of {on - worst:.2f}). Recommendation: more realistic delivery estimates and tighter carrier SLAs."
        ))

    # 5. Worst state for late deliveries
    st = sm.groupby("state")[["delivered_orders", "late_orders"]].sum()
    big = st[st["delivered_orders"] >= 300]
    st = big if len(big) >= 3 else st
    st = st[st["delivered_orders"] > 0]
    if len(st):
        rate = st["late_orders"] / st["delivered_orders"]
        w = rate.idxmax()
        b = rate.idxmin()
        out.append((
            "Delivery performance differs by state",
            f"{w} has the highest late-delivery rate ({rate[w] * 100:.1f}%), while {b} has the lowest "
            f"({rate[b] * 100:.1f}%). Focus carrier improvements on the worst states first."
        ))

    # 6. Category concentration
    cat = d["category_year"].groupby("category")["revenue"].sum().sort_values(ascending=False)
    if len(cat) >= 3:
        top3 = cat.head(3)
        out.append((
            "A few categories drive revenue",
            f"The top 3 categories ({', '.join(top3.index)}) make up {top3.sum() / cat.sum() * 100:.1f}% of revenue."
        ))

    # 7. Seller concentration (Pareto)
    sellers = d["seller_summary"].sort_values("revenue", ascending=False)
    if len(sellers) >= 10:
        n = max(1, math.ceil(len(sellers) * 0.10))
        share = sellers.head(n)["revenue"].sum() / sellers["revenue"].sum() * 100
        out.append((
            "Seller concentration",
            f"The top 10% of sellers ({n:,} sellers) generate {share:.1f}% of delivered-order revenue. "
            f"Losing a few large sellers would hurt the marketplace, so keep them happy."
        ))

    # 8. Freight burden
    c = d["category_year"].groupby("category")[["revenue", "freight", "orders"]].sum()
    c2 = c[c["orders"] >= 100]
    c = c2 if len(c2) >= 3 else c
    c = c[c["revenue"] > 0]
    if len(c):
        pct = c["freight"] / c["revenue"] * 100
        out.append((
            "Shipping cost is heavy for some categories",
            f"Freight is {pct.mean():.0f}% of product price on average across categories, and as high as "
            f"{pct.max():.0f}% for '{pct.idxmax()}'. High shipping cost can reduce conversion."
        ))
    return out


def insights_to_markdown(insights: list) -> str:
    lines = ["# Key findings", "",
             "_Generated automatically from your data by `pipeline/build_data.py`._", ""]
    for i, (title, text) in enumerate(insights, 1):
        lines += [f"## {i}. {title}", text, ""]
    return "\n".join(lines)
