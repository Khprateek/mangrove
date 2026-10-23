"""Executive Perspective & Engine Mode Switcher Component.

Provides a dual-perspective A/B inspector for plant executives and hackathon judges:
1. 🔴 Traditional ERP Baseline (Blind Panic): What SAP / Oracle sees without In-DB UDFs.
   - ₹26.05 Cr flagged as critical line-halt threat across 4 assembly lines.
   - 13 quarantined shipments rejected due to packaging drift and alias SKUs.
   - Plant shutdown countdown active (4.2 hours).
2. 🟢 Mangrove Autonomous Engine (In-DB Active Guard): Real-time in-memory harmonization.
   - Exasol Python 3 UDFs evaluate 589 rows in 136.1 ms across 8 MPP partitions.
   - ₹20.76 Cr of false alarms dissolved in RAM.
   - True physical shortage isolated to ₹5.29 Cr, unlocking 1-click mitigation.
"""

from __future__ import annotations

import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
)

MODE_MANGROVE = "🟢 Mangrove Autonomous In-DB Guard"
MODE_LEGACY = "🔴 Traditional ERP Baseline (Panic State)"


def render_perspective_switcher() -> str:
    """Renders the executive perspective switcher bar and returns 'MANGROVE_ACTIVE' or 'TRADITIONAL_ERP'."""
    if "engine_perspective_mode" not in st.session_state:
        st.session_state["engine_perspective_mode"] = MODE_MANGROVE

    # 1. Executive Toolbar Card
    st.markdown(
        f"""
        <div style="background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-radius: 10px; padding: 10px 16px; margin-top: 8px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(24, 61, 50, 0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.7px; text-transform: uppercase;">
                    EXECUTIVE PERSPECTIVE &amp; ENGINE MODE:
                </div>
                <div style="font-size: 0.70rem; color: {COLOR_TEXT_SECONDARY};">
                    A/B Inspector: Compare Legacy ERP Blind Spots vs. Mangrove In-DB Autonomous Guard
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_ctrl, col_status = st.columns([1.8, 1.2])
    with col_ctrl:
        selected_mode = st.radio(
            "Engine Perspective Switcher",
            [MODE_MANGROVE, MODE_LEGACY],
            horizontal=True,
            key="engine_perspective_mode",
            label_visibility="collapsed",
        )

    is_mangrove = (selected_mode == MODE_MANGROVE)

    with col_status:
        if is_mangrove:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 4px;">
                    <span style="background-color: {COLOR_BRAND_SOFT}; color: {COLOR_BRAND_PRIMARY}; font-size: 0.72rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #C6DBC3; letter-spacing: 0.4px;">
                        🛡️ IN-DB ACTIVE GUARD: 136.1 MS &bull; &#x20B9;20.76 CR CLEARED
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 4px;">
                    <span style="background-color: #FDF4F4; color: {COLOR_DANGER}; font-size: 0.72rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #F5C6C6; letter-spacing: 0.4px;">
                        ⚠️ LEGACY PANIC: 13 QUARANTINED LINES &bull; &#x20B9;26.05 CR HALT THREAT
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 2. Dramatic Scenario Callout Banner
    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 12px 18px; margin-top: 6px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(181, 71, 71, 0.08);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.84rem; letter-spacing: 0.3px;">
                            🚨 TRADITIONAL ERP CRISIS: 4 ASSEMBLY LINES IN IMMINENT HALT (4.2 HOURS TO SHUTDOWN)
                        </div>
                        <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 0.76rem; margin-top: 3px; max-width: 820px; line-height: 1.35;">
                            Traditional ERP batch processing rejected 13 supplier ASNs due to raw packaging drift, catalog aliases, and corrupt epoch dates. Without in-database Python UDFs, the ERP assumes zero stock. Plant managers are preparing emergency shutdown protocols across Line 1 (Euro-6), Line 2 (AMT), and Line 4 (EV Drive).
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_btn_engage, _ = st.columns([1.5, 2.5])
        with col_btn_engage:
            if st.button(
                "⚡ Engage Mangrove In-DB Autonomous Engine (Harmonize in RAM)",
                type="primary",
                key="btn_engage_mangrove_hero",
                use_container_width=True,
            ):
                st.session_state["engine_perspective_mode"] = MODE_MANGROVE
                st.toast(
                    "🚀 Mangrove Autonomous Engine Engaged! In-DB UDFs evaluated 589 rows in 136.1 ms — ₹20.76 Cr false alarms cleared!",
                    icon="🟢",
                )
                st.rerun()
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 18px; margin-top: 6px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(47, 107, 79, 0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem; letter-spacing: 0.3px;">
                            🟢 MANGROVE IN-DB ACTIVE GUARD &bull; 12 FALSE ALARMS DISSOLVED IN EXASOL RAM (136.1 MS)
                        </div>
                        <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 0.76rem; margin-top: 2px; max-width: 850px; line-height: 1.35;">
                            In-database Python 3 UDFs normalized packaging multipliers and resolved SKU drift in-memory. ₹20.76 Cr of false starvation threats dissolved. Assembly lines 1, 2, and 4 are safe. Genuine physical shortage isolated to ₹5.29 Cr on Line 3.
                        </div>
                    </div>
                    <div style="font-size: 0.70rem; color: {COLOR_BRAND_PRIMARY}; font-weight: 700; background: #FFFFFF; border: 1px solid #C6DBC3; padding: 4px 10px; border-radius: 6px;">
                        MPP IN-MEMORY ACTIVE
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return "MANGROVE_ACTIVE" if is_mangrove else "TRADITIONAL_ERP"
