"""Tab 2: Assembly Line Starvation Horizon & BOM Deficit Matrix."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    apply_mangrove_theme,
    format_inr_crore_lakh,
    safe_float,
)


def render_bom_horizon_tab(
    marts: dict,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Tab 2: Assembly Line Starvation Horizon & BOM Deficit Matrix

    dynamically highlights the starvation delta between Traditional ERP and Mangrove.
    """
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")
    bom_df: pd.DataFrame = marts["bom_risk_mart"].copy()
    bom_df["line_component_label"] = bom_df["assembly_line_id"] + " | " + bom_df["component_part_num"]

    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.82rem;">🚨 TRADITIONAL ERP STARVATION VIEW: ALL 4 ASSEMBLY LINES IN RED ZONE</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Traditional ERP quarantined 13 dispatches, assuming zero stock. Station starvation curves plummet into shutdown at 4.2 hours across Line 1, 2, 3, and 4.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem;">🟢 MANGROVE BUFFER RESTORATION: 3 OF 4 ASSEMBLY LINES SECURED ABOVE 48-HOUR BUFFER</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    In-DB harmonization reveals that Line 1 (Euro-6), Line 2 (AMT), and Line 4 (EV Drive) have adequate physical stock. Only Line 3 has a genuine physical deficit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
    if is_mangrove:
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
        if not is_mangrove:
            h_leg = row["hours_to_starvation_legacy"]
            if h_leg < 16.0:
                return "🔴 HALT IMMINENT (0 Stock)"
            if h_leg < 48.0:
                return "🟠 STARVATION RISK"
            return "🟢 SECURED"
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
            "Part Description": bom_df["part_description"],
            "Planned Output": bom_df["planned_output_units"].map(lambda x: f"{x:,.0f} units"),
            "True Net Shortage": bom_df["revenue_at_risk_net_inr"].map(format_inr_crore_lakh) if is_mangrove else bom_df["revenue_at_risk_legacy_inr"].map(format_inr_crore_lakh),
            "Hours to Halt (Legacy)": bom_df["hours_to_starvation_legacy"].map(lambda x: f"{x:.1f}h"),
            "Hours to Halt (In-DB)": bom_df["hours_to_starvation_harmonized"].map(lambda x: f"{x:.1f}h") if is_mangrove else ["N/A (Disabled)"] * len(bom_df),
        }
    )
    st.dataframe(bom_table, use_container_width=True, hide_index=True)
