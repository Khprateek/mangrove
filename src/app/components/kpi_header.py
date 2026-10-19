"""Executive KPI Header & Business Defense Component."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    format_inr_crore_lakh,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_kpi_header(marts: dict, client: ChakanExasolClient) -> None:
    """Renders the top 5 operational KPI metrics cards and boardroom business defense strip."""
    sched_df = client.tables["PRODUCTION_SCHEDULES"]
    inv_df = marts["inventory_mart"]
    bom_df = marts["bom_risk_mart"]
    triage_df = marts["triage_queue"]

    # Defensive numeric coercion to strictly prevent string concatenation
    sched_units = pd.to_numeric(sched_df["planned_output_units"], errors="coerce").fillna(0.0)
    sched_val = pd.to_numeric(sched_df["finished_unit_value_inr"], errors="coerce").fillna(0.0)
    total_scheduled_val = float((sched_units * sched_val).sum())

    legacy_risk_val = float(pd.to_numeric(bom_df["revenue_at_risk_legacy_inr"], errors="coerce").fillna(0.0).sum())
    net_risk_val = float(pd.to_numeric(bom_df["revenue_at_risk_net_inr"], errors="coerce").fillna(0.0).sum())
    cleared_by_udf_val = max(0.0, legacy_risk_val - net_risk_val)

    phantom_val = float(pd.to_numeric(inv_df["phantom_inventory_value_inr"], errors="coerce").fillna(0.0).sum())
    phantom_units = int(pd.to_numeric(inv_df["phantom_inventory_qty"], errors="coerce").fillna(0.0).sum())
    pending_count = int((triage_df["harmonization_state"] == "UDF_HARMONIZED_PENDING_APPROVAL").sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "48h Scheduled Output",
        format_inr_crore_lakh(total_scheduled_val),
        f"{int(sched_units.sum()):,} Units (4 Lines)",
    )
    c2.metric(
        "Legacy Blind-Spot Risk",
        format_inr_crore_lakh(legacy_risk_val),
        f"{len(triage_df)} Quarantined ASNs",
        delta_color="inverse",
    )
    c3.metric(
        "Cleared by Exasol UDFs",
        format_inr_crore_lakh(cleared_by_udf_val),
        "↗ Harmonized in RAM",
    )
    c4.metric(
        "True Net Shortage",
        format_inr_crore_lakh(net_risk_val),
        f"{pending_count} Actionable Deficits",
        delta_color="inverse" if net_risk_val > 0 else "normal",
    )
    c5.metric(
        "Phantom Inventory",
        format_inr_crore_lakh(phantom_val),
        f"{phantom_units:,} Unpickable Units",
        delta_color="inverse",
    )

    roi = marts.get("financial_roi_mart", {})
    if roi:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_SURFACE}; border-left: 4px solid {COLOR_BRAND_PRIMARY}; border-top: 1px solid {COLOR_BORDER}; border-right: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; padding: 12px 18px; border-radius: 10px; margin-top: 16px; margin-bottom: 22px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; font-size: 0.80rem; box-shadow: 0 1px 4px rgba(24, 61, 50, 0.04);">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; letter-spacing: 0.6px; font-size: 0.74rem;">BUSINESS DEFENSE &amp; ROI</span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Total Stoppage Exposure: <b style="color: {COLOR_DANGER}; font-size: 0.85rem;">{format_inr_crore_lakh(roi.get('total_stoppage_exposure_inr', 0))}</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Emergency Freight: <b style="color: {COLOR_TEXT_PRIMARY};">{format_inr_crore_lakh(roi.get('benchmark_freight_inr', 45000))}</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Executive ROI: <b style="color: {COLOR_BRAND_PRIMARY}; font-size: 0.95rem;">{roi.get('headline_roi_x', 1175):,.0f}x</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Avoided Panic Freight: <b style="color: {COLOR_BRAND_PRIMARY}; font-weight: 700;">{format_inr_crore_lakh(roi.get('avoided_panic_freight_inr', 135000))}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
