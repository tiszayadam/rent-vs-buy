"""Independent expected-index graphs: inflation, real rent, real house prices."""

from __future__ import annotations

import streamlit as st

from indices.drag_chart import yearly_drag_chart
from indices.series import default_inflation_pct, default_real_index, years


def _ensure_state() -> None:
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
            st.session_state[key] = (series + [fill] * n)[:n]


def render_expected_indices_tab() -> None:
    _ensure_state()
    yrs = years()

    st.subheader("Expected indices")
    st.caption(
        "Yearly series from 2027 through 2056. Click a point, then use the slider under the chart "
        "to move it. Streamlit cannot drag points on the plot itself. "
        "These graphs are not connected to the wealth comparison yet."
    )

    if st.button("Reset all to defaults"):
        st.session_state.expected_inflation_pct = default_inflation_pct()
        st.session_state.expected_real_rent_index = default_real_index()
        st.session_state.expected_real_house_index = default_real_index()
        st.rerun()

    st.markdown("**Expected inflation** (% / year)")
    st.session_state.expected_inflation_pct = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_inflation_pct,
        y_label="% / year",
        y_min=-5.0,
        y_max=15.0,
        y_suffix="%",
        key="chart_expected_inflation",
    )

    st.markdown("**Expected real rent index** (100 = no real change)")
    st.session_state.expected_real_rent_index = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_real_rent_index,
        y_label="Index",
        y_min=50.0,
        y_max=200.0,
        key="chart_expected_real_rent",
    )

    st.markdown("**Expected real house price index** (100 = no real change)")
    st.session_state.expected_real_house_index = yearly_drag_chart(
        years=yrs,
        values=st.session_state.expected_real_house_index,
        y_label="Index",
        y_min=50.0,
        y_max=200.0,
        key="chart_expected_real_house",
    )
