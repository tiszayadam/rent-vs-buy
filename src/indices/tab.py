"""Independent expected-index graphs: inflation, real rent, real house prices."""

from __future__ import annotations

import streamlit as st

from indices.drag_chart import yearly_drag_chart
from indices.historical import house_history, implied_inflation_pct, rent_history, vwce_return_history
from indices.series import (
    DEFAULT_EQUITY_RETURN_PCT,
    default_equity_return_pct,
    default_inflation_pct,
    default_real_index,
    inflation_deflator,
    interpolate_from_knots,
    nominal_index,
    years,
)


def ensure_index_state() -> None:
    yrs = years()
    if "expected_inflation_pct" not in st.session_state:
        st.session_state.expected_inflation_pct = default_inflation_pct()
    if "expected_real_rent_index" not in st.session_state:
        st.session_state.expected_real_rent_index = default_real_index()
    if "expected_real_house_index" not in st.session_state:
        st.session_state.expected_real_house_index = default_real_index()
    if "expected_equity_return_pct" not in st.session_state:
        st.session_state.expected_equity_return_pct = default_equity_return_pct()
    n = len(yrs)
    fills = {
        "expected_inflation_pct": 3.0,
        "expected_real_rent_index": 100.0,
        "expected_real_house_index": 100.0,
        "expected_equity_return_pct": DEFAULT_EQUITY_RETURN_PCT,
    }
    for key, fill in fills.items():
        series = list(st.session_state[key])
        if len(series) != n:
            series = (series + [fill] * n)[:n]
        st.session_state[key] = interpolate_from_knots(series, yrs)


def current_nominal_paths() -> tuple[list[float], list[float]]:
    """Nominal house and rent indices from the Expected indices tab (session state)."""
    ensure_index_state()
    inflation = st.session_state.expected_inflation_pct
    house = nominal_index(st.session_state.expected_real_house_index, inflation)
    rent = nominal_index(st.session_state.expected_real_rent_index, inflation)
    return house, rent


def current_price_deflator() -> list[float]:
    """Cumulative CPI deflator, 100 in the first expected year (2027)."""
    ensure_index_state()
    return inflation_deflator(st.session_state.expected_inflation_pct)


def current_equity_return_pct() -> list[float]:
    """Expected yearly nominal HUF equity returns (percent) for leftover cash."""
    ensure_index_state()
    return list(st.session_state.expected_equity_return_pct)


def _load_history() -> dict[str, object] | None:
    try:
        rent_years, rent_nom, rent_real = rent_history()
        house_years, house_nom, house_real = house_history()
        inf_years, inf_pct = implied_inflation_pct(rent_years, rent_nom, rent_real)
        equity_years, equity_pct = vwce_return_history()
    except FileNotFoundError as exc:
        st.warning(f"Historical index files not found: {exc}")
        return None
    return {
        "rent_years": rent_years,
        "rent_nom": rent_nom,
        "rent_real": rent_real,
        "house_years": house_years,
        "house_nom": house_nom,
        "house_real": house_real,
        "inf_years": inf_years,
        "inf_pct": inf_pct,
        "equity_years": equity_years,
        "equity_pct": equity_pct,
    }


def render_expected_indices_tab() -> None:
    ensure_index_state()
    yrs = years()
    history = _load_history()

    st.subheader("Expected indices")
    st.caption(
        "Grey history is realized KSH data through 2026 (2026 = 100) and cannot be edited. "
        "Only the next five expected years, then every fifth year, are editable knots "
        "(2027–2031, 2036, …, 2056); years in between are linear interpolations. "
        "Click a knot, then use the slider or +/− beside the chart to move the expected real series. "
        "Nominal = real × cumulative inflation deflator / 100 (deflator = 100 in 2027). "
        "Streamlit cannot drag points on the plot itself. The wealth comparison uses the "
        "expected (post-2026) nominal rent, house, and equity-return series. "
        "Equity returns are calendar-year HUF total returns (VWCE); a 2026 house/rent "
        "index level lines up with the 2025 realized stock return, so history starts in 2015. "
        "2026 YTD equity return is 12%; expected years default to 8%."
    )

    if st.button("Reset expected path to defaults"):
        st.session_state.expected_inflation_pct = default_inflation_pct()
        st.session_state.expected_real_rent_index = default_real_index()
        st.session_state.expected_real_house_index = default_real_index()
        st.session_state.expected_equity_return_pct = default_equity_return_pct()
        st.rerun()

    inf_hist_years = history["inf_years"] if history else None
    inf_hist_vals = history["inf_pct"] if history else None

    st.markdown("**Inflation** (% / year; history implied from KSH rent, locked)")
    st.session_state.expected_inflation_pct = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_inflation_pct,
        y_label="% / year",
        y_min=-5.0,
        y_max=15.0,
        y_suffix="%",
        key="chart_expected_inflation",
        history_years=inf_hist_years,
        history_values=inf_hist_vals,
    )

    st.markdown("**Rent index** (history locked; expected real editable)")
    rent_hist_kwargs = {}
    if history:
        rent_hist_kwargs = {
            "history_years": history["rent_years"],
            "history_values": history["rent_real"],
            "history_overlays": [("Nominal", history["rent_nom"])],
        }
    st.session_state.expected_real_rent_index = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_real_rent_index,
        y_label="Index",
        y_min=50.0,
        y_max=200.0,
        key="chart_expected_real_rent",
        overlays=[
            (
                "Nominal",
                nominal_index(
                    st.session_state.expected_real_rent_index,
                    st.session_state.expected_inflation_pct,
                ),
            )
        ],
        **rent_hist_kwargs,
    )

    st.markdown("**House price index** (Budapest history locked; expected real editable)")
    house_hist_kwargs = {}
    if history:
        house_hist_kwargs = {
            "history_years": history["house_years"],
            "history_values": history["house_real"],
            "history_overlays": [("Nominal", history["house_nom"])],
        }
    st.session_state.expected_real_house_index = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_real_house_index,
        y_label="Index",
        y_min=50.0,
        y_max=200.0,
        key="chart_expected_real_house",
        overlays=[
            (
                "Nominal",
                nominal_index(
                    st.session_state.expected_real_house_index,
                    st.session_state.expected_inflation_pct,
                ),
            )
        ],
        **house_hist_kwargs,
    )

    st.markdown("**Equity return** (nominal % / year, HUF; VWCE history locked; expected editable)")
    equity_hist_kwargs = {}
    if history:
        equity_hist_kwargs = {
            "history_years": history["equity_years"],
            "history_values": history["equity_pct"],
        }
    st.session_state.expected_equity_return_pct = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_equity_return_pct,
        y_label="% / year",
        y_min=-20.0,
        y_max=40.0,
        y_suffix="%",
        key="chart_expected_equity_return",
        **equity_hist_kwargs,
    )
