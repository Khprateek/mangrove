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


def render_kpi_header(
    marts: dict,
    client: ChakanExasolClient,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Renders the top 5 operational KPI metrics cards and boardroom business defense strip

    dynamically adjusted to the active executive perspective mode:
    - TRADITIONAL_ERP: Authentic legacy metrics (No 'Cleared Exposure' and No 'Phantom Inventory').
    - MANGROVE_ACTIVE: In-DB Harmonized metrics with Cleared Exposure, True Shortage, and Phantom Stock.
    """
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")
    sched_df = client.tables["PRODUCTION_SCHEDULES"]
    inv_df = marts["inventory_mart"]
    bom_df = marts["bom_risk_mart"]
    triage_df = marts["triage_queue"]

    # Defensive numeric coercion to strictly prevent string concatenation
    sched_units = pd.to_numeric(sched_df["planned_output_units"], errors="coerce").fillna(0.0)
    sched_val = pd.to_numeric(sched_df["finished_unit_value_inr"], errors="coerce").fillna(0.0)
    total_scheduled_val = float((sched_units * sched_val).sum())

    legacy_risk_val = float(pd.to_numeric(bom_df["revenue_at_risk_legacy_inr"], errors="coerce").fillna(0.0).sum())
    actual_net_risk_val = float(pd.to_numeric(bom_df["revenue_at_risk_net_inr"], errors="coerce").fillna(0.0).sum())
    actual_cleared_val = max(0.0, legacy_risk_val - actual_net_risk_val)

    phantom_val = float(pd.to_numeric(inv_df["phantom_inventory_value_inr"], errors="coerce").fillna(0.0).sum())
    phantom_units = int(pd.to_numeric(inv_df["phantom_inventory_qty"], errors="coerce").fillna(0.0).sum())

    st.markdown("<div style='margin-top: 0.75rem; margin-bottom: 0.4rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)

    if is_mangrove:
        # Dynamic CSS injection for Mangrove Mode
        card_styles = f"""
        <style>
        /* Card 3: Cleared in RAM (Green - Positive Cleared Outcome) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {{
            background-color: {COLOR_BRAND_SOFT} !important;
            border: 1px solid #C6DBC3 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] {{
            color: {COLOR_BRAND_PRIMARY} !important;
        }}

        /* Card 4: True Net Shortage (Red - Confirmed Operational Deficit) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}
        </style>
        """
        st.markdown(card_styles, unsafe_allow_html=True)

        c1.metric(
            "Scheduled Output",
            format_inr_crore_lakh(total_scheduled_val),
            f"{int(sched_units.sum()):,} Units (4 Lines)",
        )
        c2.metric(
            "Legacy Blind Spots",
            format_inr_crore_lakh(legacy_risk_val),
            f"{len(triage_df)} Quarantined ASNs",
            delta_color="inverse",
        )
        c3.metric(
            "Cleared in RAM",
            format_inr_crore_lakh(actual_cleared_val),
            "↗ Harmonized by Exasol UDFs",
        )
        c4.metric(
            "True Net Shortage",
            format_inr_crore_lakh(actual_net_risk_val),
            "1 Actionable Deficit (Line 3)",
            delta_color="inverse",
        )
        c5.metric(
            "Phantom Stock Isolated",
            format_inr_crore_lakh(phantom_val),
            f"{phantom_units:,} Unpickable Units",
            delta_color="inverse",
        )

        roi = marts.get("financial_roi_mart", {})
        if roi:
            st.markdown(
                f"""
                <div style="background-color: {COLOR_SURFACE}; border-left: 4px solid {COLOR_BRAND_PRIMARY}; border-top: 1px solid {COLOR_BORDER}; border-right: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; padding: 8px 16px; border-radius: 9px; margin-top: 10px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 0.78rem; box-shadow: 0 1px 3px rgba(24, 61, 50, 0.03);">
                    <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; letter-spacing: 0.6px; font-size: 0.72rem;">BUSINESS DEFENSE &amp; ROI (MANGROVE IN-DB ACTIVE GUARD)</span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Total Stoppage Exposure: <b style="color: {COLOR_DANGER}; font-size: 0.82rem;">{format_inr_crore_lakh(roi.get('total_stoppage_exposure_inr', 0))}</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Emergency Freight: <b style="color: {COLOR_TEXT_PRIMARY};">{format_inr_crore_lakh(roi.get('benchmark_freight_inr', 45000))}</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Executive ROI: <b style="color: {COLOR_BRAND_PRIMARY}; font-size: 0.90rem;">{roi.get('headline_roi_x', 177):,.0f}x</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Avoided Panic Freight: <b style="color: {COLOR_BRAND_PRIMARY}; font-weight: 700;">{format_inr_crore_lakh(roi.get('avoided_panic_freight_inr', 135000))}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        # Traditional ERP Mode: Realistic Legacy SAP/Oracle Metrics
        # - NO "Cleared Exposure" (Traditional ERP has no concept of in-DB UDF clearing)
        # - NO "Phantom Inventory" (Traditional ERP is completely blind to warehouse bin corruption)
        card_styles = f"""
        <style>
        /* Card 2: Quarantined ASNs (Red - High Defect Alarm) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(2) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(2) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}

        /* Card 3: Production Threatened (Red - Emergency Panic) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}

        /* Card 4: Assembly Lines Halting (Red - 4 of 4 Lines Halted) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}

        /* Card 5: Panic Freight Required (Warning Amber - 13 Emergency Couriers) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(5) [data-testid="stMetric"] {{
            background-color: #FFF8E6 !important;
            border: 1px solid #FFE49E !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(5) [data-testid="stMetricValue"] {{
            color: #A66B20 !important;
        }}
        </style>
        """
        st.markdown(card_styles, unsafe_allow_html=True)

        c1.metric(
            "Scheduled Output",
            format_inr_crore_lakh(total_scheduled_val),
            f"{int(sched_units.sum()):,} Units (4 Lines)",
        )
        c2.metric(
            "Quarantined ASNs",
            f"{len(triage_df)} Dispatches",
            "REJECTED AT FACTORY GATE",
            delta_color="inverse",
        )
        c3.metric(
            "Production Blocked",
            format_inr_crore_lakh(legacy_risk_val),
            "13 Dispatches Dropped (0 Stock)",
            delta_color="inverse",
        )
        c4.metric(
            "Assembly Lines Halting",
            "4 of 4 Lines",
            "Earliest Halt: 4.2 Hours",
            delta_color="inverse",
        )
        c5.metric(
            "Panic Freight Required",
            "Rs 5.85 L",
            "13 Emergency Courier Dispatches",
            delta_color="inverse",
        )

        roi = marts.get("financial_roi_mart", {})
        if roi:
            st.markdown(
                f"""
                <div style="background-color: {COLOR_SURFACE}; border-left: 4px solid {COLOR_DANGER}; border-top: 1px solid {COLOR_BORDER}; border-right: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; padding: 8px 16px; border-radius: 9px; margin-top: 10px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 0.78rem; box-shadow: 0 1px 3px rgba(181, 71, 71, 0.05);">
                    <span style="font-weight: 700; color: {COLOR_DANGER}; letter-spacing: 0.6px; font-size: 0.72rem;">TRADITIONAL ERP PERSPECTIVE: UNMITIGATED LINE-STOP EXPOSURE</span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Total Stoppage Exposure: <b style="color: {COLOR_DANGER}; font-size: 0.82rem;">{format_inr_crore_lakh(roi.get('total_stoppage_exposure_inr', 0))}</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Emergency Freight Required: <b style="color: {COLOR_DANGER};">Rs 5.85 L (13 Couriers)</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Executive ROI: <b style="color: {COLOR_DANGER}; font-size: 0.90rem;">0x (Unmitigated)</b></span>
                    <span style="color: {COLOR_TEXT_SECONDARY};">Avoided Panic Freight: <b style="color: {COLOR_DANGER}; font-weight: 700;">Rs 0.00 (Zero Saved)</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
