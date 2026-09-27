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


def format_grouped(value: float) -> str:
    negative = value < 0
    magnitude = abs(value)
    if abs(magnitude - round(magnitude)) < 1e-9:
        body = f"{int(round(magnitude)):,}".replace(",", " ")
    else:
        int_part, frac_part = f"{magnitude:.2f}".split(".")
        body = f"{int(int_part):,}".replace(",", " ") + "." + frac_part
    return f"-{body}" if negative else body


st.set_page_config(page_title="Rent vs buy", layout="wide")
st.title("Rent vs buy")
st.caption("Wealth from origination through the last mortgage payment.")

st.markdown(
    """
This is a static, month-by-month comparison of two housing paths — **buying** and **renting** — from origination (month 0) through the last mortgage payment.

The two paths are assumed to face the same choice of housing spend at each stage. Whoever spends less invests the difference. Both investment accounts grow at the same annual return, compounded monthly.

**Horizon and timing**

- Horizon is the mortgage length in months.
- Month 0 is the upfront cash outlay only (no mortgage instalment and no rent yet).
- Months 1 through $N$ are the monthly cashflows. After $N$ payments the loan principal is zero.

**Buying cashflows**

- **Upfront:** down payment plus transfer duty (*vagyonszerzési illeték*). Transfer duty is a fixed 4% of purchase price. Down payment must be at least 10% of purchase price.
- **Loan:** purchase price minus down payment.
- **Each month:** a constant instalment on a fully amortizing mortgage (equal monthly payments, fixed annual rate, monthly rate = annual rate / 12). The instalment covers principal and interest, not interest only.

House value at month $m$ is

$$
\\text{purchase price} \\times (1 + \\text{appreciation} - \\text{amortization and repairs})^{m/12}.
$$

Amortization and repairs reduce house *value*; they are not a separate cash outflow.

**Renting cashflows**

- **Upfront:** the rental deposit, held at face value (it does not earn the investment return).
- **Each month:** current monthly rent, increased once per year by the yearly rent increase (months 1–12 at the starting rent, then stepped up each following year).

**Leftover cash**

At every stage, outgoing cashflows are compared:

- if buying costs more, the renter invests the difference;
- if renting costs more, the buyer invests the difference.

Existing investment balances then grow one month at a time at

$$
(1 + \\text{investment return})^{1/12} - 1
$$

before that month’s leftover (if any) is added.

**Wealth**

- **Buying:** investment account + house value − remaining mortgage principal.
- **Renting:** deposit + investment account.

The chart below plots these two wealth series over the mortgage.
"""
)

buy_col, rent_col, inv_col = st.columns(3)

with buy_col:
    st.header("Buying")
    purchase_price = st.number_input(
        "Purchase price (HUF)",
        min_value=0.0,
        value=70_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )
    min_down = MIN_DOWN_PAYMENT_RATE * purchase_price
    down_payment = st.number_input(
        "Down payment (HUF)",
        min_value=float(min_down),
        max_value=float(purchase_price) if purchase_price > 0 else 0.0,
        value=max(15_000_000.0, min_down),
        step=1_000_000.0,
        format="%.0f",
    )
    st.caption(
        f"Minimum {MIN_DOWN_PAYMENT_RATE:.0%} of purchase price "
        f"({format_grouped(min_down)} HUF)."
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
        f"Transfer duty (vagyonszerzési illeték) is fixed at {TRANSFER_DUTY_RATE:.0%} of purchase price "
        f"({format_grouped(purchase_price * TRANSFER_DUTY_RATE)} HUF)."
    )

with rent_col:
    st.header("Renting")
    deposit = st.number_input(
        "Deposit (HUF)",
        min_value=0.0,
        value=500_000.0,
        step=10_000.0,
        format="%.0f",
    )
    current_rent = st.number_input(
        "Current monthly rent (HUF)",
        min_value=0.0,
        value=250_000.0,
        step=10_000.0,
        format="%.0f",
    )
    rent_increase_pct = st.number_input(
        "Yearly rent increase (% / year)",
        min_value=-20.0,
        value=3.0,
        step=0.1,
        format="%.1f",
    )

with inv_col:
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
        y=[p.buying_wealth for p in points],
        name="Buying",
        mode="lines",
    )
)
fig.add_trace(
    go.Scatter(
        x=years,
        y=[p.renting_wealth for p in points],
        name="Renting",
        mode="lines",
    )
)
fig.update_layout(
    xaxis_title="Years",
    yaxis_title="Wealth (HUF)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(t=40, b=40),
    hovermode="x unified",
    height=520,
    separators=". ",
    yaxis=dict(tickformat=",.0f"),
)
st.plotly_chart(fig, width="stretch")

m1, m2, m3 = st.columns(3)
m1.metric("Buying wealth at end", f"{format_grouped(end.buying_wealth)} HUF")
m2.metric("Renting wealth at end", f"{format_grouped(end.renting_wealth)} HUF")
m3.metric("Monthly mortgage instalment", f"{format_grouped(model.mortgage.monthly_payment())} HUF")
