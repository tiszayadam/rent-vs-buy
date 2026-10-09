"""Streamlit UI: set parameters and plot wealth over the mortgage."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from indices.series import real_huf
from indices.tab import current_nominal_paths, current_price_deflator, render_expected_indices_tab
from model import WealthModel
from parameters import (
    MIN_DOWN_PAYMENT_RATE,
    MODE_HOUSE_VS_HOUSE,
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

House value at month $m$ follows the **nominal house index** $H$ from the Expected indices tab (linearly interpolated between yearly points), with amortization and repairs as a value haircut:

$$
\\text{purchase price} \\times \\frac{H_m}{H_0} \\times (1 - \\text{amortization and repairs})^{m/12}.
$$

Amortization and repairs reduce house *value*; they are not a separate cash outflow.

**Renting cashflows**

- **Upfront:** the rental deposit, held at face value (it does not earn the investment return).
- **Each month:** current monthly rent scaled by the **nominal rent index** $R$ (months 1–12 use year 0, then one step per year): $\\text{current rent} \\times R_y / R_0$ with $y = \\lfloor (m-1)/12 \\rfloor$.

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

The chart and end-of-horizon figures are in **real 2027 HUF** (nominal wealth divided by the cumulative inflation deflator from Expected indices). Cashflows and the mortgage instalment stay nominal.
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
- **Each month:** the constant fully amortizing mortgage instalment *minus* rent received. Rent received starts at the initial monthly rent and then follows the **nominal rent index** $R$ (months 1–12 use year 0, then one step per year). If rent exceeds the instalment, that month is a net inflow.

House value at month $m$ follows the **nominal house index** $H$ from the Expected indices tab (linearly interpolated between yearly points), with amortization and repairs as a value haircut:

$$
\\text{purchase price} \\times \\frac{H_m}{H_0} \\times (1 - \\text{amortization and repairs})^{m/12}.
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

The chart and end-of-horizon figures are in **real 2027 HUF** (nominal wealth divided by the cumulative inflation deflator from Expected indices). Cashflows and the mortgage instalment stay nominal.
"""


HOUSE_VS_HOUSE_DESCRIPTION = """
This is a static, month-by-month comparison of two *investment* houses — **house A** versus **house B**. You already have somewhere to live; both properties are bought and rented out.

The two paths face the same cash choice at each stage. Whoever has the smaller net outflow (or the larger net inflow) invests the difference. Both leftover investment accounts grow at the same annual return, compounded monthly.

**Horizon and timing**

- Horizon is the longer of the two mortgages, in months. After a loan is repaid, that house still receives rent and its value still follows the house index.
- Month 0 is the upfront cash outlay only (no mortgage instalment and no rent received yet).
- Months 1 through $N$ are the monthly cashflows.

**Each house’s cashflows**

- **Upfront:** down payment plus transfer duty (*vagyonszerzési illeték*). Transfer duty is a fixed 4% of that house’s purchase price. Down payment must be at least 10% of purchase price.
- **Loan:** purchase price minus down payment.
- **Each month (while the mortgage runs):** the constant fully amortizing instalment *minus* rent received. Rent received starts at that house’s initial monthly rent and then follows the **nominal rent index** $R$. If rent exceeds the instalment, that month is a net inflow.
- **Each month (after that house’s mortgage ends):** minus rent received (a net inflow).

House value at month $m$ follows the shared **nominal house index** $H$ from the Expected indices tab:

$$
\\text{purchase price} \\times \\frac{H_m}{H_0} \\times (1 - \\text{amortization and repairs})^{m/12}.
$$

Amortization and repairs reduce house *value*; they are not a separate cash outflow. Each house has its own purchase price, mortgage, rent, and amortization rate.

**Leftover cash**

At every stage, net cashflows are compared (outflow is positive):

- if house A has the larger net outflow, house B’s investment account receives the difference;
- if house B has the larger net outflow (or A has a net inflow relative to B), house A invests the difference.

Existing investment balances then grow one month at a time at

$$
(1 + \\text{investment return})^{1/12} - 1
$$

before that month’s leftover (if any) is added.

**Wealth**

- **Each house:** that house’s investment account + house value − remaining mortgage principal.

The chart and end-of-horizon figures are in **real 2027 HUF** (nominal wealth divided by the cumulative inflation deflator from Expected indices). Cashflows and the mortgage instalment stay nominal.
"""


def render_investment_house_inputs(
    header: str,
    *,
    key_prefix: str,
    default_price: float,
    default_down: float,
    default_years: int,
    default_rate_pct: float,
    default_amort_pct: float,
    default_rent: float,
) -> tuple[float, float, int, float, float, float]:
    st.header(header)
    purchase_price = st.number_input(
        "Purchase price (HUF)",
        min_value=0.0,
        value=default_price,
        step=1_000_000.0,
        format="%.0f",
        key=f"{key_prefix}_purchase",
    )
    min_down = MIN_DOWN_PAYMENT_RATE * purchase_price
    down_payment = st.number_input(
        "Down payment (HUF)",
        min_value=float(min_down),
        max_value=float(purchase_price) if purchase_price > 0 else 0.0,
        value=max(default_down, min_down),
        step=1_000_000.0,
        format="%.0f",
        key=f"{key_prefix}_down",
    )
    st.caption(
        f"Minimum {MIN_DOWN_PAYMENT_RATE:.0%} of purchase price "
        f"({format_grouped(min_down)} HUF)."
    )
    mortgage_years = st.number_input(
        "Mortgage length (years)",
        min_value=0,
        value=default_years,
        step=1,
        key=f"{key_prefix}_years",
    )
    mortgage_rate_pct = st.number_input(
        "Fixed mortgage interest rate (% / year)",
        min_value=0.0,
        value=default_rate_pct,
        step=0.1,
        format="%.1f",
        key=f"{key_prefix}_rate",
    )
    amort_pct = st.number_input(
        "Amortization + repairs (% of home value / year)",
        min_value=0.0,
        value=default_amort_pct,
        step=0.1,
        format="%.1f",
        key=f"{key_prefix}_amort",
    )
    initial_rent = st.number_input(
        "Initial monthly rent (HUF)",
        min_value=0.0,
        value=default_rent,
        step=10_000.0,
        format="%.0f",
        key=f"{key_prefix}_rent",
    )
    st.caption(
        f"Transfer duty (vagyonszerzési illeték) is fixed at {TRANSFER_DUTY_RATE:.0%} of purchase price "
        f"({format_grouped(purchase_price * TRANSFER_DUTY_RATE)} HUF)."
    )
    st.caption("House value and rent follow the nominal indices on the Expected indices tab.")
    return (
        purchase_price,
        down_payment,
        int(mortgage_years),
        mortgage_rate_pct,
        amort_pct,
        initial_rent,
    )


def render_wealth_tab() -> None:
    mode = st.radio(
        "Comparison",
        options=(MODE_RENT_VS_BUY, MODE_LET_VS_INVEST, MODE_HOUSE_VS_HOUSE),
        format_func=lambda m: {
            MODE_RENT_VS_BUY: "Rent vs buy",
            MODE_LET_VS_INVEST: "Buy-to-let vs invest",
            MODE_HOUSE_VS_HOUSE: "House A vs house B",
        }[m],
        horizontal=True,
    )

    if mode == MODE_LET_VS_INVEST:
        st.caption("Wealth from origination through the last mortgage payment — as an investment.")
        st.markdown(LET_VS_INVEST_DESCRIPTION)
    elif mode == MODE_HOUSE_VS_HOUSE:
        st.caption("Wealth from origination through the longer mortgage — two houses as investments.")
        st.markdown(HOUSE_VS_HOUSE_DESCRIPTION)
    else:
        st.caption("Wealth from origination through the last mortgage payment.")
        st.markdown(RENT_VS_BUY_DESCRIPTION)

    if mode == MODE_HOUSE_VS_HOUSE:
        col_a, col_b, inv_col = st.columns(3)
        with col_a:
            (
                purchase_a,
                down_a,
                years_a,
                rate_a_pct,
                amort_a_pct,
                rent_a,
            ) = render_investment_house_inputs(
                "House A",
                key_prefix="house_a",
                default_price=70_000_000.0,
                default_down=15_000_000.0,
                default_years=25,
                default_rate_pct=3.0,
                default_amort_pct=1.0,
                default_rent=250_000.0,
            )
        with col_b:
            (
                purchase_b,
                down_b,
                years_b,
                rate_b_pct,
                amort_b_pct,
                rent_b,
            ) = render_investment_house_inputs(
                "House B",
                key_prefix="house_b",
                default_price=55_000_000.0,
                default_down=12_000_000.0,
                default_years=20,
                default_rate_pct=4.5,
                default_amort_pct=1.0,
                default_rent=220_000.0,
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
            st.caption("Return is in HUF. Shared leftover account for both houses.")
    else:
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
            st.caption(
                f"Transfer duty (vagyonszerzési illeték) is fixed at {TRANSFER_DUTY_RATE:.0%} of purchase price "
                f"({format_grouped(purchase_price * TRANSFER_DUTY_RATE)} HUF)."
            )
            st.caption("House value follows the nominal house index on the Expected indices tab.")

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
                st.caption("Rent received follows the nominal rent index on the Expected indices tab.")
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
                st.caption("Rent follows the nominal rent index on the Expected indices tab.")

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
        house_index, rent_index = current_nominal_paths()
        if mode == MODE_HOUSE_VS_HOUSE:
            scenario = Scenario(
                buying=BuyingParameters(
                    purchase_price=purchase_a,
                    down_payment=down_a,
                    mortgage_length_years=years_a,
                    mortgage_interest_rate=rate_a_pct / 100,
                    amortization_and_repairs_rate=amort_a_pct / 100,
                ),
                investment_return=investment_pct / 100,
                nominal_house_index=house_index,
                nominal_rent_index=rent_index,
                letting=LettingParameters(initial_rent=rent_a),
                buying_b=BuyingParameters(
                    purchase_price=purchase_b,
                    down_payment=down_b,
                    mortgage_length_years=years_b,
                    mortgage_interest_rate=rate_b_pct / 100,
                    amortization_and_repairs_rate=amort_b_pct / 100,
                ),
                letting_b=LettingParameters(initial_rent=rent_b),
            )
        else:
            buying = BuyingParameters(
                purchase_price=purchase_price,
                down_payment=down_payment,
                mortgage_length_years=int(mortgage_years),
                mortgage_interest_rate=mortgage_rate_pct / 100,
                amortization_and_repairs_rate=amort_pct / 100,
            )
            if mode == MODE_LET_VS_INVEST:
                scenario = Scenario(
                    buying=buying,
                    investment_return=investment_pct / 100,
                    nominal_house_index=house_index,
                    nominal_rent_index=rent_index,
                    letting=LettingParameters(initial_rent=initial_rent),
                )
            else:
                scenario = Scenario(
                    buying=buying,
                    investment_return=investment_pct / 100,
                    nominal_house_index=house_index,
                    nominal_rent_index=rent_index,
                    renting=RentingParameters(
                        deposit=deposit,
                        current_rent=current_rent,
                    ),
                )
        model = WealthModel(scenario)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    points = model.timeline()
    deflator = current_price_deflator()
    real_buying = [real_huf(p.buying_wealth, deflator, p.month) for p in points]
    real_other = [real_huf(p.renting_wealth, deflator, p.month) for p in points]
    years = [p.month / 12 for p in points]

    if mode == MODE_HOUSE_VS_HOUSE:
        house_label = "House A"
        other_label = "House B"
    elif mode == MODE_LET_VS_INVEST:
        house_label = "Buy-to-let"
        other_label = "Investment account"
    else:
        house_label = "Buying"
        other_label = "Renting"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=real_buying,
            name=house_label,
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=years,
            y=real_other,
            name=other_label,
            mode="lines",
        )
    )
    fig.update_layout(
        xaxis_title="Years",
        yaxis_title="Real wealth (2027 HUF)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=40, b=40),
        hovermode="x unified",
        height=520,
        separators=". ",
        yaxis=dict(tickformat=",.0f"),
    )
    st.plotly_chart(fig, width="stretch")

    m1, m2, m3 = st.columns(3)
    m1.metric(
        f"{house_label} real wealth at end",
        f"{format_grouped(real_buying[-1])} HUF",
    )
    m2.metric(
        f"{other_label} real wealth at end",
        f"{format_grouped(real_other[-1])} HUF",
    )
    if mode == MODE_HOUSE_VS_HOUSE:
        assert model.mortgage_b is not None
        m3.metric(
            "Monthly instalments A / B",
            f"{format_grouped(model.mortgage.monthly_payment())} / "
            f"{format_grouped(model.mortgage_b.monthly_payment())} HUF",
        )
        p1 = model.at(1)
        def _flow_word(cashflow: float) -> str:
            return "outflow" if cashflow >= 0 else "inflow"

        st.caption(
            f"Month-1 net cashflow (instalment − rent): "
            f"house A {format_grouped(p1.buying_cashflow)} HUF ({_flow_word(p1.buying_cashflow)}), "
            f"house B {format_grouped(p1.renting_cashflow)} HUF ({_flow_word(p1.renting_cashflow)})."
        )
    else:
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
# Index widgets first so a slider edit is visible to the wealth model on the same rerun.
with indices_tab:
    render_expected_indices_tab()
with wealth_tab:
    render_wealth_tab()
