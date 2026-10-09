"""Independent expected-index graphs: inflation, real rent, real house prices."""

from __future__ import annotations

import streamlit as st

from indices.drag_chart import yearly_drag_chart
from indices.historical import house_history, implied_inflation_pct, rent_history
from indices.series import (
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
    n = len(yrs)
    for key in (
        "expected_inflation_pct",
        "expected_real_rent_index",
        "expected_real_house_index",
    ):
        series = list(st.session_state[key])
        if len(series) != n:
            fill = 3.0 if key.endswith("pct") else 100.0
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


def _load_history() -> dict[str, object] | None:
    try:
        rent_years, rent_nom, rent_real = rent_history()
        house_years, house_nom, house_real = house_history()
        inf_years, inf_pct = implied_inflation_pct(rent_years, rent_nom, rent_real)
    except FileNotFoundError as exc:
        st.warning(f"Historical KSH files not found: {exc}")
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
        "expected (post-2026) nominal rent and house series."
    )

    if st.button("Reset expected path to defaults"):
        st.session_state.expected_inflation_pct = default_inflation_pct()
        st.session_state.expected_real_rent_index = default_real_index()
        st.session_state.expected_real_house_index = default_real_index()
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
