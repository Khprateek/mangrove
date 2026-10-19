"""Tab 2: Assembly Line Starvation Horizon & BOM Deficit Matrix."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_PRIMARY,
    COLOR_DANGER,
    apply_mangrove_theme,
    format_inr_crore_lakh,
    safe_float,
)


def render_bom_horizon_tab(marts: dict) -> None:
    """Tab 2: Assembly Line Starvation Horizon & BOM Deficit Matrix."""
    bom_df: pd.DataFrame = marts["bom_risk_mart"].copy()
    bom_df["line_component_label"] = bom_df["assembly_line_id"] + " | " + bom_df["component_part_num"]

    st.subheader("48-Hour Assembly Station Starvation Horizon (Legacy ETL vs. Exasol Harmonization)")
    st.caption(
        "Components falling below the 48-hour scheduled window trigger impending assembly line starvation."
    )

    chart_df = bom_df.sort_values("hours_to_starvation_legacy", ascending=True)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=chart_df["line_component_label"],
            x=chart_df["hours_to_starvation_legacy"],
            name="Legacy ETL (Quarantined ASNs = 0 Stock)",
            orientation="h",
            marker_color=COLOR_DANGER,
        )
    )
    fig.add_trace(
        go.Bar(
            y=chart_df["line_component_label"],
            x=chart_df["hours_to_starvation_harmonized"],
            name="Exasol In-DB Harmonized + Overrides",
            orientation="h",
            marker_color=COLOR_BRAND_PRIMARY,
        )
    )
    fig.add_vline(
        x=48.0,
        line_dash="dash",
        line_color=COLOR_BRAND_PRIMARY,
        annotation_text="48h Target Run Buffer",
        annotation_position="top left",
    )
    fig = apply_mangrove_theme(fig, height=480)
    fig.update_layout(
        barmode="group",
        xaxis_title="Hours Until Station Starvation (Max 48h)",
        yaxis_title="Assembly Line & Component SKU",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("BOM Explosion & Component Deficit Matrix")
    st.caption("Quantitative bill of materials tracking across all 4 production lines at Chakan Plant-1.")

    def format_bom_status(row: pd.Series) -> str:
        h = row["hours_to_starvation_harmonized"]
        deficit = row["true_net_deficit_qty"]
        if deficit <= 0 or h >= 48.0:
            return "🟢 SECURED (48h+)"
        if h < 16.0:
            return "🔴 HALT IMMINENT"
        return "🟠 DEFICIT AT RISK"

    bom_table = pd.DataFrame(
        {
            "Status": bom_df.apply(format_bom_status, axis=1),
            "Assembly Line": bom_df["assembly_line_id"],
            "Component SKU": bom_df["component_part_num"],
            "Description": bom_df["part_description"],
            "Station": bom_df["assembly_station_code"],
            "48h Gross Req": bom_df["gross_required_qty"].apply(lambda v: f"{safe_float(v):,.0f}"),
            "Pickable ATP": bom_df["true_pickable_atp_qty"].apply(lambda v: f"{safe_float(v):,.0f}"),
            "Inbound Harmonized": bom_df["harmonized_inbound_qty"].apply(lambda v: f"{safe_float(v):,.0f}"),
            "Net Line Deficit": bom_df["true_net_deficit_qty"].apply(
                lambda v: f"{safe_float(v):,.0f}" if safe_float(v) > 0 else "0 (Balanced)"
            ),
            "Hrs to Halt (Legacy)": bom_df["hours_to_starvation_legacy"].apply(lambda v: f"{safe_float(v):.1f}h"),
            "Hrs to Halt (Harmonized)": bom_df["hours_to_starvation_harmonized"].apply(lambda v: f"{safe_float(v):.1f}h"),
            "Net Revenue at Risk": bom_df["revenue_at_risk_net_inr"].apply(format_inr_crore_lakh),
        }
    )
    st.dataframe(bom_table, use_container_width=True, hide_index=True)
