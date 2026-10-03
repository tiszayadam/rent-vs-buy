"""Yearly line chart: click a point, then move it with the slider.

Streamlit/Plotly cannot drag scatter points natively. A custom component could,
but it requires PyArrow/pandas, which is blocked in some Windows environments.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def yearly_drag_chart(
    *,
    years: list[int],
    values: list[float],
    y_label: str,
    y_min: float,
    y_max: float,
    y_suffix: str = "",
    key: str,
) -> list[float]:
    selected_key = f"{key}_selected_idx"
    if selected_key not in st.session_state:
        st.session_state[selected_key] = 0
    selected = int(st.session_state[selected_key])
    selected = max(0, min(len(years) - 1, selected))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=values,
            mode="lines+markers",
            name=y_label,
            hovertemplate="%{x}: %{y:.1f}" + y_suffix + "<extra></extra>",
            marker=dict(size=10),
            line=dict(width=2, color="#1c83e1"),
        )
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
    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=y_label,
        yaxis=dict(range=[y_min, y_max]),
        margin=dict(t=24, b=40, l=40, r=16),
        height=320,
        hovermode="closest",
        showlegend=False,
    )
    fig.update_xaxes(dtick=2)

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
        if pt.get("curve_number", 0) != 0:
            continue
        if "point_index" in pt:
            st.session_state[selected_key] = int(pt["point_index"])
            selected = st.session_state[selected_key]
            break
        if "x" in pt and pt["x"] in years:
            st.session_state[selected_key] = years.index(int(pt["x"]))
            selected = st.session_state[selected_key]
            break

    year = years[selected]
    slider_label = f"Move {year}"
    if y_suffix:
        slider_label += f" ({y_suffix})"
    new_val = st.slider(
        slider_label,
        min_value=float(y_min),
        max_value=float(y_max),
        value=float(values[selected]),
        step=0.1,
        key=f"{key}_slider_{year}",
    )
    updated = [float(v) for v in values]
    updated[selected] = float(new_val)
    return updated
