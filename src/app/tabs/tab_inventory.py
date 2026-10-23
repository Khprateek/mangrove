"""Phantom Inventory Audit Tab Module for Mangrove Cockpit."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_ACCENT,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    apply_mangrove_theme,
    format_inr_crore_lakh,
)


def render_phantom_inventory_tab(
    marts: dict,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Render Tab 6: Warehouse Phantom Inventory Audit (VW_INVENTORY_TRUE_ATP)

    dynamically highlights the visibility difference between Traditional ERP and Mangrove.
    """
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")
    inv_df: pd.DataFrame = marts["inventory_mart"].copy().sort_values(
        "phantom_inventory_value_inr", ascending=False
    )

    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.82rem;">⚠️ TRADITIONAL ERP BLIND SPOT: ZERO PHANTOM VISIBILITY</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Traditional ERP assumes 100% of book inventory is usable: <code>Naive ATP = Book On-Hand</code>. It is completely blind to damaged bins and quality-hold quarantine crates. When assembly lines run out of parts, the ERP is surprised because "the system says it's in stock."
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem;">🟢 MANGROVE TRUE ATP ENGINE: 13,855 PHANTOM UNITS (₹1.18 CR) DEDUCTED IN RAM</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Mangrove executes in-memory True ATP: <code>ATP = max(0, Q_wms - Q_allocated - Q_hold)</code>. Phantom units in damaged and QC-hold bins are quarantined before pickers reach the shelves.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Warehouse Phantom Inventory Audit (`VW_INVENTORY_TRUE_ATP`)")
    st.caption(
        "Reconciles Central ERP ledger balances against physical WMS cycle counts and quality-hold bins "
        "at Chakan Plant-1 Stores (`CHAKAN-PLT1-STORE`)."
    )

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-bottom: 2px;">
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
            "True Pickable ATP": COLOR_BRAND_PRIMARY,
            "Phantom Stock": COLOR_DANGER,
            "Allocated to Prod": COLOR_BRAND_ACCENT,
            "Quality Hold": COLOR_WARNING,
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

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
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
