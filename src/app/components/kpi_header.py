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

    dynamically adjusted to the active executive perspective mode (MANGROVE_ACTIVE vs TRADITIONAL_ERP).
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

    # Dynamic metrics based on perspective
    if is_mangrove:
        cleared_val_disp = actual_cleared_val
        cleared_delta = "↗ Harmonized in RAM"
        net_risk_val_disp = actual_net_risk_val
        net_delta = "1 Actionable Deficit (Line 3)"
        card_styles = f"""
        <style>
        /* Card 3: Cleared Exposure (Green - Positive Cleared Outcome) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {{
            background-color: {COLOR_BRAND_SOFT} !important;
            border: 1px solid #C6DBC3 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] {{
            color: {COLOR_BRAND_PRIMARY} !important;
        }}

        /* Card 4: Net Shortage (Red - Confirmed Operational Deficit) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(4) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}
        </style>
        """
    else:
        # Traditional ERP mode: UDFs absent -> zero cleared -> 100% of quarantined inventory assumed missing!
        cleared_val_disp = 0.0
        cleared_delta = "0 Cr (Legacy ERP Blind)"
        net_risk_val_disp = legacy_risk_val
        net_delta = "13 Assembly Lines Threatened"
        card_styles = f"""
        <style>
        /* Card 2: Legacy Blind Spots (Red - Emergency Unmanaged Crisis) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(2) [data-testid="stMetric"] {{
            background-color: #FDF4F4 !important;
            border: 1px solid #F5C6C6 !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(2) [data-testid="stMetricValue"] {{
            color: {COLOR_DANGER} !important;
        }}

        /* Card 3: Cleared Exposure (Neutral Slate - Inactive in Legacy Mode) */
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetric"] {{
            background-color: {COLOR_SURFACE} !important;
            border: 1px solid {COLOR_BORDER} !important;
        }}
        [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"]:nth-child(3) [data-testid="stMetricValue"] {{
            color: {COLOR_TEXT_SECONDARY} !important;
        }}

        /* Card 4: Net Shortage (Red - Panic Level ₹26.05 Cr) */
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

    st.markdown("<div style='margin-top: 0.2rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Scheduled Exposure",
        format_inr_crore_lakh(total_scheduled_val),
        f"{int(sched_units.sum()):,} Units (4 Lines)",
    )
    c2.metric(
        "Legacy Blind Spots",
        format_inr_crore_lakh(legacy_risk_val),
        f"{len(triage_df)} Quarantined ASNs" if is_mangrove else f"{len(triage_df)} Rejected ASNs (ALL)",
        delta_color="inverse",
    )
    c3.metric(
        "Cleared Exposure",
        format_inr_crore_lakh(cleared_val_disp),
        cleared_delta,
    )
    c4.metric(
        "Net Shortage",
        format_inr_crore_lakh(net_risk_val_disp),
        net_delta,
        delta_color="inverse",
    )
    c5.metric(
        "Phantom Inventory",
        format_inr_crore_lakh(phantom_val),
        f"{phantom_units:,} Unpickable Units",
        delta_color="inverse",
    )

    roi = marts.get("financial_roi_mart", {})
    if roi:
        if is_mangrove:
            strip_border = COLOR_BRAND_PRIMARY
            strip_title = "BUSINESS DEFENSE &amp; ROI (MANGROVE ACTIVE GUARD)"
            stoppage_disp = format_inr_crore_lakh(roi.get("total_stoppage_exposure_inr", 0))
            freight_disp = format_inr_crore_lakh(roi.get("benchmark_freight_inr", 45000))
            roi_disp = f"{roi.get('headline_roi_x', 1175):,.0f}x"
            avoided_disp = format_inr_crore_lakh(roi.get("avoided_panic_freight_inr", 135000))
            roi_color = COLOR_BRAND_PRIMARY
        else:
            strip_border = COLOR_DANGER
            strip_title = "TRADITIONAL ERP PERSPECTIVE: UNMITIGATED LINE-STOP EXPOSURE"
            stoppage_disp = format_inr_crore_lakh(roi.get("total_stoppage_exposure_inr", 0))
            freight_disp = "Rs 5.85 L (13 Hot-Shots Ordered)"
            roi_disp = "0x (Unmanaged)"
            avoided_disp = "Rs 0.00 (Zero Saved)"
            roi_color = COLOR_DANGER

        st.markdown(
            f"""
            <div style="background-color: {COLOR_SURFACE}; border-left: 4px solid {strip_border}; border-top: 1px solid {COLOR_BORDER}; border-right: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; padding: 8px 16px; border-radius: 9px; margin-top: 10px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 0.78rem; box-shadow: 0 1px 3px rgba(24, 61, 50, 0.03);">
                <span style="font-weight: 700; color: {strip_border}; letter-spacing: 0.6px; font-size: 0.72rem;">{strip_title}</span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Total Stoppage Exposure: <b style="color: {COLOR_DANGER}; font-size: 0.82rem;">{stoppage_disp}</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Emergency Freight: <b style="color: {COLOR_TEXT_PRIMARY};">{freight_disp}</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Executive ROI: <b style="color: {roi_color}; font-size: 0.90rem;">{roi_disp}</b></span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Avoided Panic Freight: <b style="color: {roi_color}; font-weight: 700;">{avoided_disp}</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
