"""Streamlit UI: set parameters and plot wealth over the mortgage."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from indices.tab import render_expected_indices_tab
from model import WealthModel
from parameters import (
    MIN_DOWN_PAYMENT_RATE,
    MODE_LET_VS_INVEST,
    MODE_RENT_VS_BUY,
    BuyingParameters,
    LettingParameters,
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


RENT_VS_BUY_DESCRIPTION = """
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

LET_VS_INVEST_DESCRIPTION = """
This is a static, month-by-month comparison of two *investment* paths — **buying a house and renting it out**, versus **keeping the money in an investment account**. You already have somewhere to live; this is not a decision about where to live.

The two paths face the same cash choice at each stage. Whoever has the smaller net outflow (or the larger net inflow) invests the difference. Both investment accounts grow at the same annual return, compounded monthly.

**Horizon and timing**

- Horizon is the mortgage length in months.
- Month 0 is the upfront cash outlay only (no mortgage instalment and no rent received yet).
- Months 1 through $N$ are the monthly cashflows. After $N$ payments the loan principal is zero.

**Buy-to-let cashflows**

- **Upfront:** down payment plus transfer duty (*vagyonszerzési illeték*). Transfer duty is a fixed 4% of purchase price. Down payment must be at least 10% of purchase price.
- **Loan:** purchase price minus down payment.
- **Each month:** the constant fully amortizing mortgage instalment *minus* rent received. Rent received starts at the initial monthly rent and increases once per year (months 1–12 at the starting rent, then stepped up each following year). If rent exceeds the instalment, that month is a net inflow.

House value at month $m$ is

$$
\\text{purchase price} \\times (1 + \\text{appreciation} - \\text{amortization and repairs})^{m/12}.
$$

Amortization and repairs reduce house *value*; they are not a separate cash outflow.

**Investment-account cashflows**

- **Every stage:** zero. There is no purchase, no mortgage, and no rent paid.

**Leftover cash**

At every stage, net cashflows are compared (outflow is positive):

- if buy-to-let has the larger net outflow, the investment account receives the difference;
- if buy-to-let has a smaller outflow or a net inflow, the landlord invests the difference.

Existing investment balances then grow one month at a time at

$$
(1 + \\text{investment return})^{1/12} - 1
$$

before that month’s leftover (if any) is added.

**Wealth**

- **Buy-to-let:** investment account + house value − remaining mortgage principal.
- **Investment account:** investment account only.

The chart below plots these two wealth series over the mortgage.
"""


def render_wealth_tab() -> None:
    mode = st.radio(
        "Comparison",
        options=(MODE_RENT_VS_BUY, MODE_LET_VS_INVEST),
        format_func=lambda m: (
            "Rent vs buy" if m == MODE_RENT_VS_BUY else "Buy-to-let vs invest"
        ),
        horizontal=True,
    )

    if mode == MODE_LET_VS_INVEST:
        st.caption("Wealth from origination through the last mortgage payment — as an investment.")
        st.markdown(LET_VS_INVEST_DESCRIPTION)
    else:
        st.caption("Wealth from origination through the last mortgage payment.")
        st.markdown(RENT_VS_BUY_DESCRIPTION)

    buy_col, mid_col, inv_col = st.columns(3)

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

    with mid_col:
        if mode == MODE_LET_VS_INVEST:
            st.header("Letting")
            initial_rent = st.number_input(
                "Initial monthly rent (HUF)",
                min_value=0.0,
                value=250_000.0,
                step=10_000.0,
                format="%.0f",
            )
            let_increase_pct = st.number_input(
                "Yearly rent increase (% / year)",
                min_value=-20.0,
                value=3.0,
                step=0.1,
                format="%.1f",
                key="let_yearly_rent_increase",
            )
        else:
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
                key="rent_yearly_rent_increase",
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
        buying = BuyingParameters(
            purchase_price=purchase_price,
            down_payment=down_payment,
            mortgage_length_years=int(mortgage_years),
            mortgage_interest_rate=mortgage_rate_pct / 100,
            amortization_and_repairs_rate=amort_pct / 100,
            appreciation_rate=appreciation_pct / 100,
        )
        if mode == MODE_LET_VS_INVEST:
            scenario = Scenario(
                buying=buying,
                investment_return=investment_pct / 100,
                letting=LettingParameters(
                    initial_rent=initial_rent,
                    yearly_rent_increase=let_increase_pct / 100,
                ),
            )
        else:
            scenario = Scenario(
                buying=buying,
                investment_return=investment_pct / 100,
                renting=RentingParameters(
                    deposit=deposit,
                    current_rent=current_rent,
                    yearly_rent_increase=rent_increase_pct / 100,
                ),
            )
        model = WealthModel(scenario)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    points = model.timeline()
    end = points[-1]
    years = [p.month / 12 for p in points]

    if mode == MODE_LET_VS_INVEST:
        house_label = "Buy-to-let"
        other_label = "Investment account"
    else:
        house_label = "Buying"
        other_label = "Renting"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=[p.buying_wealth for p in points],
            name=house_label,
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=[p.renting_wealth for p in points],
            name=other_label,
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
    m1.metric(f"{house_label} wealth at end", f"{format_grouped(end.buying_wealth)} HUF")
    m2.metric(f"{other_label} wealth at end", f"{format_grouped(end.renting_wealth)} HUF")
    m3.metric("Monthly mortgage instalment", f"{format_grouped(model.mortgage.monthly_payment())} HUF")
    if mode == MODE_LET_VS_INVEST:
        net_month_one = model.at(1).buying_cashflow
        st.caption(
            f"Month-1 net buy-to-let cashflow (instalment − rent): "
            f"{format_grouped(net_month_one)} HUF "
            f"({'outflow' if net_month_one >= 0 else 'inflow'})."
        )


st.set_page_config(page_title="Rent vs buy", layout="wide")
st.title("Rent vs buy")
wealth_tab, indices_tab = st.tabs(["Wealth comparison", "Expected indices"])
with wealth_tab:
    render_wealth_tab()
with indices_tab:
    render_expected_indices_tab()
