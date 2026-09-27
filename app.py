"""Streamlit UI: set rent vs buy parameters and plot wealth over the mortgage."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from model import WealthModel
from parameters import (
    MIN_DOWN_PAYMENT_RATE,
    BuyingParameters,
    RentingParameters,
    Scenario,
    TRANSFER_DUTY_RATE,
)

MILLION = 1_000_000
THOUSAND = 1_000


def _huf_display(value: float) -> str:
    if abs(value) >= MILLION:
        return f"{value / MILLION:.2f} million HUF"
    if abs(value) >= THOUSAND:
        return f"{value / THOUSAND:.1f} thousand HUF"
    return f"{value:.0f} HUF"


st.set_page_config(page_title="Rent vs buy", layout="wide")
st.title("Rent vs buy")
st.caption("Wealth from origination through the last mortgage payment.")

with st.sidebar:
    st.header("Buying")
    purchase_million = st.number_input(
        "Purchase price (million HUF)",
        min_value=0.0,
        value=70.0,
        step=1.0,
        format="%.2f",
    )
    purchase_price = purchase_million * MILLION
    min_down_million = MIN_DOWN_PAYMENT_RATE * purchase_million
    down_million = st.number_input(
        "Down payment (million HUF)",
        min_value=float(min_down_million),
        max_value=float(purchase_million) if purchase_million > 0 else 0.0,
        value=max(15.0, min_down_million),
        step=1.0,
        format="%.2f",
    )
    down_payment = down_million * MILLION
    st.caption(
        f"Minimum {MIN_DOWN_PAYMENT_RATE:.0%} of purchase price "
        f"({min_down_million:.2f} million HUF)."
    )
    mortgage_years = st.number_input("Mortgage length (years)", min_value=0, value=25, step=1)
    mortgage_rate_pct = st.number_input(
        "Fixed mortgage interest rate (% / year)",
        min_value=0.0,
        value=3.0,
        step=0.1,
        format="%.1f",
    )
    amort_pct = st.number_input(
        "Amortization + repairs (% of home value / year)",
        min_value=0.0,
        value=1.0,
        step=0.1,
        format="%.1f",
    )
    appreciation_pct = st.number_input(
        "House value appreciation (% / year)",
        min_value=-20.0,
        value=3.0,
        step=0.1,
        format="%.1f",
    )
    st.caption(
        f"Transfer duty is fixed at {TRANSFER_DUTY_RATE:.0%} of purchase price "
        f"({purchase_million * TRANSFER_DUTY_RATE:.2f} million HUF)."
    )

    st.header("Renting")
    deposit_thousand = st.number_input(
        "Deposit (thousand HUF)",
        min_value=0.0,
        value=500.0,
        step=10.0,
        format="%.2f",
    )
    deposit = deposit_thousand * THOUSAND
    rent_thousand = st.number_input(
        "Current monthly rent (thousand HUF)",
        min_value=0.0,
        value=250.0,
        step=10.0,
        format="%.2f",
    )
    current_rent = rent_thousand * THOUSAND
    rent_increase_pct = st.number_input(
        "Yearly rent increase (% / year)",
        min_value=-20.0,
        value=3.0,
        step=0.1,
        format="%.1f",
    )

    st.header("Investment")
    investment_pct = st.number_input(
        "Investment return on leftover cash (% / year, HUF)",
        min_value=-50.0,
        value=8.0,
        step=0.1,
        format="%.1f",
    )
    st.caption("Return is in HUF.")

try:
    scenario = Scenario(
        buying=BuyingParameters(
            purchase_price=purchase_price,
            down_payment=down_payment,
            mortgage_length_years=int(mortgage_years),
            mortgage_interest_rate=mortgage_rate_pct / 100,
            amortization_and_repairs_rate=amort_pct / 100,
            appreciation_rate=appreciation_pct / 100,
        ),
        renting=RentingParameters(
            deposit=deposit,
            current_rent=current_rent,
            yearly_rent_increase=rent_increase_pct / 100,
        ),
        investment_return=investment_pct / 100,
    )
    model = WealthModel(scenario)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

points = model.timeline()
end = points[-1]
years = [p.month / 12 for p in points]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=years,
        y=[p.buying_wealth / MILLION for p in points],
        name="Buying",
        mode="lines",
    )
)
fig.add_trace(
    go.Scatter(
        x=years,
        y=[p.renting_wealth / MILLION for p in points],
        name="Renting",
        mode="lines",
    )
)
fig.update_layout(
    xaxis_title="Years",
    yaxis_title="Wealth (million HUF)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=40, b=40),
    hovermode="x unified",
    height=520,
)
st.plotly_chart(fig, width="stretch")

m1, m2, m3 = st.columns(3)
m1.metric("Buying wealth at end", _huf_display(end.buying_wealth))
m2.metric("Renting wealth at end", _huf_display(end.renting_wealth))
m3.metric("Monthly mortgage instalment", _huf_display(model.mortgage.monthly_payment()))
