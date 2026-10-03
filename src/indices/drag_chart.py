"""Yearly line chart: click a point, then move it with the slider.

Streamlit/Plotly cannot drag scatter points natively. A custom component could,
but it requires PyArrow/pandas, which is blocked in some Windows environments.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from indices.series import editable_years, interpolate_from_knots

CHART_HEIGHT = 320
_SLIDER_TRACK_PX = 260

_VERTICAL_SLIDER_CSS = f"""
<style>
div[data-testid="stHorizontalBlock"]:has([class*="_index_vslider"]),
div[data-testid="stHorizontalBlock"]:has([class*="_index_vslider"]) > div,
div[class*="_index_vslider"] {{
    overflow: visible !important;
}}
div[class*="_index_vslider"] {{
    height: {CHART_HEIGHT}px;
}}
div[class*="_index_vslider"] [data-testid="stSlider"] > div[role="group"] {{
    transform: rotate(-90deg);
    transform-origin: center center;
    width: {_SLIDER_TRACK_PX}px !important;
    margin-top: {(_SLIDER_TRACK_PX / 2) - 16}px;
    margin-left: -{(_SLIDER_TRACK_PX / 2) - 28}px;
}}
div[class*="_index_vslider"] [data-testid="stSliderThumbValue"] {{
    transform: rotate(90deg);
}}
div[class*="_index_vslider"] [data-testid="stSliderTickBar"] {{
    display: none;
}}
div[class*="_index_vbuttons"] {{
    height: {CHART_HEIGHT}px;
    display: flex !important;
    flex-direction: column;
    justify-content: space-between;
    padding-top: 24px;
    padding-bottom: 24px;
}}
div[class*="_index_vbuttons"] button {{
    min-height: 2.25rem;
    padding: 0 0.25rem !important;
}}
</style>
"""


def _nudge_slider(slider_key: str, delta: float, y_min: float, y_max: float) -> None:
    current = float(st.session_state.get(slider_key, 0.0))
    st.session_state[slider_key] = max(
        float(y_min),
        min(float(y_max), round(current + delta, 1)),
    )


HISTORY_REAL_COLOR = "#8b919a"
EXPECTED_REAL_COLOR = "#1c83e1"
HISTORY_OVERLAY_COLORS = ("#c47c4a", "#5f9e90", "#8a6bb5")
EXPECTED_OVERLAY_COLORS = ("#f77f00", "#2a9d8f", "#9b5de5")


def _add_expected_path(
    fig: go.Figure,
    years: list[int],
    values: list[float],
    knot_years: list[int],
    *,
    name: str,
    color: str,
    y_suffix: str,
    marker_size: int,
    showlegend: bool,
) -> None:
    fig.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines",
            name=name,
            hovertemplate="%{x}: %{y:.1f}" + y_suffix + f"<extra>{name}</extra>",
            line=dict(width=2, color=color),
            showlegend=showlegend,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=knot_years,
            y=[values[years.index(year)] for year in knot_years],
            mode="markers",
            name=name,
            hovertemplate="%{x}: %{y:.1f}" + y_suffix + f"<extra>{name}</extra>",
            marker=dict(size=marker_size, color=color),
            showlegend=False,
        )
    )


def yearly_drag_chart(
    *,
    years: list[int],
    values: list[float],
    y_label: str,
    y_min: float,
    y_max: float,
    y_suffix: str = "",
    key: str,
    overlays: list[tuple[str, list[float]]] | None = None,
    history_years: list[int] | None = None,
    history_values: list[float] | None = None,
    history_overlays: list[tuple[str, list[float]]] | None = None,
) -> list[float]:
    selected_key = f"{key}_selected_idx"
    knot_years = editable_years(years)
    knot_indices = [years.index(year) for year in knot_years]
    if selected_key not in st.session_state:
        st.session_state[selected_key] = knot_indices[0] if knot_indices else 0
    selected = int(st.session_state[selected_key])
    if selected not in knot_indices:
        selected = knot_indices[0] if knot_indices else 0
        st.session_state[selected_key] = selected
    values = interpolate_from_knots(values, years, knot_years)

    fig = go.Figure()
    primary_name = "Real" if overlays else y_label
    has_history = bool(history_years) and history_values is not None
    if has_history:
        fig.add_trace(
            go.Scatter(
                x=history_years,
                y=history_values,
                mode="lines+markers",
                name=f"{primary_name} (history)",
                hovertemplate="%{x}: %{y:.1f}" + y_suffix + f"<extra>{primary_name} (history)</extra>",
                marker=dict(size=8),
                line=dict(width=2, color=HISTORY_REAL_COLOR),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[history_years[-1], years[0]],
                y=[history_values[-1], values[0]],
                mode="lines",
                line=dict(width=2, color=EXPECTED_REAL_COLOR),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    _add_expected_path(
        fig,
        years,
        values,
        knot_years,
        name=primary_name,
        color=EXPECTED_REAL_COLOR,
        y_suffix=y_suffix,
        marker_size=10,
        showlegend=bool(overlays) or has_history,
    )
    for i, (name, series) in enumerate(overlays or []):
        color = EXPECTED_OVERLAY_COLORS[i % len(EXPECTED_OVERLAY_COLORS)]
        hist_overlay = None
        if history_overlays and i < len(history_overlays):
            hist_overlay = history_overlays[i]
        if has_history and hist_overlay is not None:
            h_name, h_series = hist_overlay
            fig.add_trace(
                go.Scatter(
                    x=history_years[: len(h_series)],
                    y=h_series,
                    mode="lines+markers",
                    name=f"{h_name} (history)",
                    hovertemplate="%{x}: %{y:.1f}" + y_suffix + f"<extra>{h_name} (history)</extra>",
                    marker=dict(size=7),
                    line=dict(width=2, color=HISTORY_OVERLAY_COLORS[i % len(HISTORY_OVERLAY_COLORS)]),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=[history_years[-1], years[0]],
                    y=[h_series[-1], series[0]],
                    mode="lines",
                    line=dict(width=2, color=color),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
        _add_expected_path(
            fig,
            years[: len(series)],
            series,
            [year for year in knot_years if year in years[: len(series)]],
            name=name,
            color=color,
            y_suffix=y_suffix,
            marker_size=8,
            showlegend=True,
        )
    fig.add_trace(
        go.Scatter(
            x=[years[selected]],
            y=[values[selected]],
            mode="markers",
            name="Selected",
            marker=dict(size=16, color="#ff4b4b"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    y_low = min(y_min, min(values) if values else y_min)
    y_high = max(y_max, max(values) if values else y_max)
    if has_history:
        y_low = min(y_low, min(history_values))
        y_high = max(y_high, max(history_values))
    for _, series in overlays or []:
        if series:
            y_low = min(y_low, min(series))
            y_high = max(y_high, max(series))
    for _, series in history_overlays or []:
        if series:
            y_low = min(y_low, min(series))
            y_high = max(y_high, max(series))
    pad = max(1.0, (y_high - y_low) * 0.05)
    x_all = list(history_years or []) + list(years)
    span = (max(x_all) - min(x_all)) if x_all else 0
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=y_label,
        yaxis=dict(range=[y_low - pad, y_high + pad]),
        margin=dict(t=24, b=40, l=40, r=16),
        height=CHART_HEIGHT,
        hovermode="closest",
        showlegend=bool(overlays) or has_history,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(dtick=5 if span > 25 else 2)

    st.markdown(_VERTICAL_SLIDER_CSS, unsafe_allow_html=True)

    with st.container(horizontal=True, wrap=False, vertical_alignment="center", gap="small"):
        event = st.plotly_chart(
            fig,
            key=f"{key}_plot",
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
            width="stretch",
        )
        points = getattr(getattr(event, "selection", None), "points", None) or []
        for pt in points:
            year_clicked = None
            if "x" in pt:
                try:
                    year_clicked = int(pt["x"])
                except (ValueError, TypeError):
                    year_clicked = None
            if year_clicked is None:
                continue
            if year_clicked in knot_years:
                selected = years.index(year_clicked)
                st.session_state[selected_key] = selected
                break

        year = years[selected]
        slider_label = f"{year}"
        if y_suffix:
            slider_label += f" ({y_suffix})"
        slider_key = f"{key}_slider_{year}"
        nudge_step = 0.1 if y_suffix == "%" else 1.0
        with st.container(key=f"{key}_index_vslider", width=96, height=CHART_HEIGHT):
            new_val = st.slider(
                slider_label,
                min_value=float(y_min),
                max_value=float(y_max),
                value=float(values[selected]),
                step=0.1,
                key=slider_key,
                help=f"Move the {year} knot; years in between are interpolated",
                label_visibility="collapsed",
            )
        with st.container(key=f"{key}_index_vbuttons", width=44, height=CHART_HEIGHT):
            st.button(
                "+",
                key=f"{key}_plus_{year}",
                help=f"Increase {year} by {nudge_step:g}",
                use_container_width=True,
                on_click=_nudge_slider,
                args=(slider_key, nudge_step, y_min, y_max),
            )
            st.button(
                "−",
                key=f"{key}_minus_{year}",
                help=f"Decrease {year} by {nudge_step:g}",
                use_container_width=True,
                on_click=_nudge_slider,
                args=(slider_key, -nudge_step, y_min, y_max),
            )
    updated = interpolate_from_knots(values, years, knot_years)
    updated[selected] = float(new_val)
    return interpolate_from_knots(updated, years, knot_years)
