"""Tab 2: Assembly Line Starvation Horizon, BOM Deficit Matrix & Warehouse True ATP."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_ACCENT,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_CHART_ACCENT,
    COLOR_CHART_MUTED,
    COLOR_CHART_PRIMARY,
    COLOR_CHART_SECONDARY,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    apply_mangrove_theme,
    format_inr_crore_lakh,
    safe_float,
)


def render_bom_horizon_tab(
    marts: dict,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Tab 2: Unified Inventory & Assembly Line Starvation Horizon.

    Reconciles physical warehouse True ATP against central ERP book stock,
    and maps the resulting component shortages to assembly line starvation hours.
    """
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")
    bom_df: pd.DataFrame = marts["bom_risk_mart"].copy()
    bom_df["line_component_label"] = bom_df["assembly_line_id"] + " | " + bom_df["component_part_num"]

    inv_df: pd.DataFrame = marts["inventory_mart"].copy().sort_values(
        "phantom_inventory_value_inr", ascending=False
    )

    # 1. Perspective Banner
    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.82rem;">🚨 TRADITIONAL ERP BLIND SPOT: ZERO PHANTOM VISIBILITY &amp; ALL 4 LINES IN RED ZONE</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Traditional ERP assumes 100% of book inventory is usable (<code>Naive ATP = Book On-Hand</code>), ignoring damaged bins and quality holds. Concurrently, 13 dispatches are quarantined, leading the ERP to predict line halts within 4.2 hours across all 4 assembly lines.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem;">🟢 MANGROVE UNIFIED BUFFER: 13,855 PHANTOM UNITS (₹1.18 CR) DEDUCTED &amp; 3 OF 4 LINES SECURED</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    In-DB True ATP deducts damaged stock in RAM before pickers reach shelves: <code>ATP = max(0, Q_wms - Q_allocated - Q_hold)</code>. Harmonization confirms Lines 1, 2, and 4 maintain &gt;48h buffer, isolating the genuine deficit strictly to Line 3.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # SECTION 1: 48-Hour Assembly Station Starvation Horizon
    # -------------------------------------------------------------------------
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
            marker_color=COLOR_CHART_SECONDARY,
        )
    )
    if is_mangrove:
        fig.add_trace(
            go.Bar(
                y=chart_df["line_component_label"],
                x=chart_df["hours_to_starvation_harmonized"],
                name="Exasol In-DB Harmonized + Overrides",
                orientation="h",
                marker_color=COLOR_CHART_PRIMARY,
            )
        )
    fig.add_vline(
        x=48.0,
        line_dash="dash",
        line_color=COLOR_CHART_ACCENT,
        annotation_text="48h Target Run Buffer",
        annotation_position="top left",
        annotation_font=dict(size=9.5, color=COLOR_CHART_ACCENT),
    )
    fig = apply_mangrove_theme(fig, height=460)
    fig.update_layout(
        barmode="group",
        xaxis_title="Hours Until Station Starvation (Max 48h)",
        yaxis_title="Assembly Line & Component SKU",
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------------
    # SECTION 2: BOM Explosion & Component Deficit Matrix
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
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

    # -------------------------------------------------------------------------
    # SECTION 3: Warehouse True ATP & Phantom Inventory Audit
    # -------------------------------------------------------------------------
    st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #D5E2D3;'>", unsafe_allow_html=True)
    st.subheader("Warehouse Phantom Inventory Audit (`VW_INVENTORY_TRUE_ATP`)")
    st.caption(
        "Reconciles Central ERP ledger balances against physical WMS cycle counts and quality-hold quarantine bins "
        "at Chakan Plant-1 Stores (`CHAKAN-PLT1-STORE`)."
    )

    st.markdown(
        f"""
        <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-top: 1rem; margin-bottom: 2px;">
            Component Stock Breakdown: True Pickable ATP vs. Phantom Ledger Drift
        </div>
        <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 8px;">
            Physical warehouse stock reconciled against phantom inventory and quality-hold quarantine bins
        </div>
        """,
        unsafe_allow_html=True,
    )

    rename_map = {
        "true_pickable_atp_qty": "True Pickable ATP",
        "phantom_inventory_qty": "Phantom Stock",
        "allocated_to_prod_qty": "Allocated to Prod",
        "quality_hold_qty": "Quality Hold",
    }
    plot_df = inv_df.rename(columns=rename_map)

    fig_inv = px.bar(
        plot_df,
        x="internal_part_num",
        y=list(rename_map.values()),
        labels={"value": "Units in Base UOM", "internal_part_num": "Component SKU", "variable": "Category"},
        color_discrete_map={
            "True Pickable ATP": COLOR_CHART_PRIMARY,
            "Allocated to Prod": COLOR_CHART_SECONDARY,
            "Quality Hold": COLOR_CHART_MUTED,
            "Phantom Stock": COLOR_CHART_ACCENT,
        },
        barmode="group",
        height=390,
    )
    fig_inv = apply_mangrove_theme(fig_inv, height=390)
    fig_inv.update_layout(
        title=None,
        margin=dict(l=36, r=16, t=28, b=85),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            title=None,
            font=dict(size=10, color=COLOR_TEXT_SECONDARY),
        ),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9, color=COLOR_TEXT_SECONDARY),
            title=None,
        ),
        yaxis=dict(
            title=dict(text="Units in Base UOM", font=dict(size=10, color=COLOR_TEXT_SECONDARY)),
            tickfont=dict(size=10, color=COLOR_TEXT_SECONDARY),
        ),
    )
    st.plotly_chart(fig_inv, use_container_width=True)

    inv_table = pd.DataFrame(
        {
            "Storage Bin": inv_df["storage_bin_id"],
            "Component SKU": inv_df["internal_part_num"],
            "Part Description": inv_df["part_description"],
            "UOM": inv_df["base_uom"],
            "ERP On-Hand (Ledger)": inv_df["erp_system_on_hand_qty"],
            "WMS Physical Count": inv_df["wms_physical_counted_qty"],
            "Allocated to Prod": inv_df["allocated_to_prod_qty"],
            "Quality Hold": inv_df["quality_hold_qty"],
            "True Pickable ATP": inv_df["true_pickable_atp_qty"] if is_mangrove else inv_df["erp_system_on_hand_qty"],
            "Phantom Inventory Qty": inv_df["phantom_inventory_qty"] if is_mangrove else ["0 (Unreported)"] * len(inv_df),
            "Phantom Capital Distortion": inv_df["phantom_inventory_value_inr"].apply(format_inr_crore_lakh) if is_mangrove else ["Rs 0.00 (Blind Spot)"] * len(inv_df),
        }
    )
    st.dataframe(inv_table, use_container_width=True, hide_index=True)
