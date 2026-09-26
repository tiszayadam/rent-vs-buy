"""Streamlit UI: set rent vs buy parameters and plot wealth over the mortgage."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from model import WealthModel
from parameters import BuyingParameters, RentingParameters, Scenario, TRANSFER_DUTY_RATE


def _huf(value: float) -> str:
    return f"{value:,.0f} Ft".replace(",", " ")


st.set_page_config(page_title="Rent vs buy", layout="wide")
st.title("Rent vs buy")
st.caption("Wealth from origination through the last mortgage payment.")

with st.sidebar:
    st.header("Buying")
    purchase_price = st.number_input("Purchase price (HUF)", min_value=0.0, value=80_000_000.0, step=1_000_000.0, format="%.0f")
    down_payment = st.number_input("Down payment (HUF)", min_value=0.0, value=16_000_000.0, step=500_000.0, format="%.0f")
    mortgage_years = st.number_input("Mortgage length (years)", min_value=0, value=20, step=1)
    mortgage_rate_pct = st.number_input("Fixed mortgage interest rate (% / year)", min_value=0.0, value=6.5, step=0.1, format="%.2f")
    amort_pct = st.number_input("Amortization + repairs (% of home value / year)", min_value=0.0, value=1.0, step=0.1, format="%.2f")
    appreciation_pct = st.number_input("House value appreciation (% / year)", min_value=-20.0, value=3.0, step=0.1, format="%.2f")
    buy_stock_pct = st.number_input("Stock return on leftover cash, buying (% / year)", min_value=-50.0, value=7.0, step=0.1, format="%.2f", key="buy_stock")
    st.caption(f"Transfer duty is fixed at {TRANSFER_DUTY_RATE:.0%} of purchase price ({_huf(purchase_price * TRANSFER_DUTY_RATE)}).")

    st.header("Renting")
    deposit = st.number_input("Deposit (HUF)", min_value=0.0, value=1_200_000.0, step=100_000.0, format="%.0f")
    current_rent = st.number_input("Current monthly rent (HUF)", min_value=0.0, value=350_000.0, step=10_000.0, format="%.0f")
    rent_increase_pct = st.number_input("Yearly rent increase (% / year)", min_value=-20.0, value=5.0, step=0.1, format="%.2f")
    rent_stock_pct = st.number_input("Stock return on leftover cash, renting (% / year)", min_value=-50.0, value=7.0, step=0.1, format="%.2f", key="rent_stock")

try:
    scenario = Scenario(
        buying=BuyingParameters(
            purchase_price=purchase_price,
            down_payment=down_payment,
            mortgage_length_years=int(mortgage_years),
            mortgage_interest_rate=mortgage_rate_pct / 100,
            amortization_and_repairs_rate=amort_pct / 100,
            appreciation_rate=appreciation_pct / 100,
            stock_return=buy_stock_pct / 100,
        ),
        renting=RentingParameters(
            deposit=deposit,
            current_rent=current_rent,
            yearly_rent_increase=rent_increase_pct / 100,
            stock_return=rent_stock_pct / 100,
        ),
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
    go.Scatter(x=years, y=[p.buying_wealth for p in points], name="Buying", mode="lines")
)
fig.add_trace(
    go.Scatter(x=years, y=[p.renting_wealth for p in points], name="Renting", mode="lines")
)
fig.update_layout(
    xaxis_title="Years",
    yaxis_title="Wealth (HUF)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=40, b=40),
    hovermode="x unified",
    height=520,
)
st.plotly_chart(fig, width="stretch")

m1, m2, m3 = st.columns(3)
m1.metric("Buying wealth at end", _huf(end.buying_wealth))
m2.metric("Renting wealth at end", _huf(end.renting_wealth))
m3.metric("Monthly mortgage instalment", _huf(model.mortgage.monthly_payment()))
