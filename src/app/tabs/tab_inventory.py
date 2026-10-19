"""Phantom Inventory Audit Tab Module for Mangrove Cockpit."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_ACCENT,
    COLOR_BRAND_PRIMARY,
    COLOR_DANGER,
    COLOR_WARNING,
    apply_mangrove_theme,
    format_inr_crore_lakh,
)


def render_phantom_inventory_tab(marts: dict) -> None:
    """Render Tab 6: Warehouse Phantom Inventory Audit (VW_INVENTORY_TRUE_ATP)."""
    inv_df: pd.DataFrame = marts["inventory_mart"].copy().sort_values(
        "phantom_inventory_value_inr", ascending=False
    )

    st.subheader("Warehouse Phantom Inventory Audit (`VW_INVENTORY_TRUE_ATP`)")
    st.caption(
        "Reconciles Central ERP ledger balances against physical WMS cycle counts and quality-hold bins "
        "at Chakan Plant-1 Stores (`CHAKAN-PLT1-STORE`)."
    )

    fig_inv = px.bar(
        inv_df,
        x="internal_part_num",
        y=["true_pickable_atp_qty", "phantom_inventory_qty", "allocated_to_prod_qty", "quality_hold_qty"],
        title="Component Stock Breakdown: True Pickable ATP vs. Phantom Ledger Drift",
        labels={"value": "Units in Base UOM", "internal_part_num": "Component SKU", "variable": "Stock Category"},
        color_discrete_map={
            "true_pickable_atp_qty": COLOR_BRAND_PRIMARY,
            "phantom_inventory_qty": COLOR_DANGER,
            "allocated_to_prod_qty": COLOR_BRAND_ACCENT,
            "quality_hold_qty": COLOR_WARNING,
        },
        barmode="group",
        height=380,
    )
    fig_inv = apply_mangrove_theme(fig_inv, height=380)
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
            "True Pickable ATP": inv_df["true_pickable_atp_qty"],
            "Phantom Inventory Qty": inv_df["phantom_inventory_qty"],
            "Phantom Capital Distortion": inv_df["phantom_inventory_value_inr"].apply(format_inr_crore_lakh),
        }
    )
    st.dataframe(inv_table, use_container_width=True, hide_index=True)
