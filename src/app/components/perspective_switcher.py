"""Executive Perspective & Engine Mode Switcher Component.

Provides a dual-perspective A/B inspector for plant executives and hackathon judges:
1. ERP Baseline (Panic State) [DEFAULT]:
   - What SAP / Oracle sees without In-DB UDFs.
   - 13 inbound ASNs rejected at factory gate due to raw packaging and SKU drift.
   - ₹26.05 Cr flagged as critical line-halt threat across 4 assembly lines.
   - Completely blind to Phantom Inventory (assumes book stock is usable).
   - Zero concept of 'Cleared Exposure' (all 13 lines in shutdown alert).
2. Mangrove Guard (Exasol Active Guard):
   - In-database Python 3 UDFs evaluate 589 rows in 136.1 ms across 8 MPP partitions.
   - ₹20.76 Cr of false alarms dissolved in RAM.
   - True physical shortage isolated to ₹5.29 Cr on Line 3.
   - True ATP algorithm isolates ₹1.18 Cr phantom stock locked in damaged bins.
"""

from __future__ import annotations

import streamlit as st

from src.app.theme import (
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_TEXT_SECONDARY,
)

MODE_LEGACY = "ERP Baseline"
MODE_MANGROVE = "Mangrove Guard"


def activate_mangrove_mode() -> None:
    """Streamlit on_click callback to engage Mangrove before script execution."""
    st.session_state["engine_perspective_mode"] = MODE_MANGROVE


def activate_legacy_mode() -> None:
    """Streamlit on_click callback to engage Traditional ERP before script execution."""
    st.session_state["engine_perspective_mode"] = MODE_LEGACY


def render_perspective_switcher() -> str:
    """Renders the executive perspective switcher bar matching the Mangrove design spec.

    Defaults to ERP Baseline so viewers immediately witness the legacy crisis
    before turning ON Mangrove Guard.
    Returns: 'TRADITIONAL_ERP' or 'MANGROVE_ACTIVE'.
    """
    if "engine_perspective_mode" not in st.session_state:
        st.session_state["engine_perspective_mode"] = MODE_LEGACY

    current_val = st.session_state.get("engine_perspective_mode", MODE_LEGACY)
    is_mangrove = (current_val == MODE_MANGROVE)

    # Server-rendered CSS fallback based on current perspective mode
    css_server_fallback = """
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label {
            background-color: #23533F !important;
            box-shadow: 0 2px 8px rgba(35, 83, 63, 0.28) !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label [data-testid="stMarkdownContainer"] p {
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label [data-testid="stMarkdownContainer"] p::before {
            background-color: #4ECA8B !important;
            box-shadow: 0 0 5px rgba(78, 202, 139, 0.65) !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label {
            background-color: transparent !important;
            box-shadow: none !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label [data-testid="stMarkdownContainer"] p {
            color: #4A5850 !important;
            font-weight: 500 !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label [data-testid="stMarkdownContainer"] p::before {
            background-color: #9AA59D !important;
            box-shadow: none !important;
        }
    """ if is_mangrove else """
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label {
            background-color: #FFFFFF !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label [data-testid="stMarkdownContainer"] p {
            color: #26332C !important;
            font-weight: 700 !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label [data-testid="stMarkdownContainer"] p::before {
            background-color: #B54747 !important;
            box-shadow: 0 0 3px rgba(181, 71, 71, 0.45) !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label {
            background-color: transparent !important;
            box-shadow: none !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label [data-testid="stMarkdownContainer"] p {
            color: #4A5850 !important;
            font-weight: 500 !important;
        }
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label [data-testid="stMarkdownContainer"] p::before {
            background-color: #9AA59D !important;
            box-shadow: none !important;
        }
    """

    st.markdown(
        f"""
        <style>
        /* Scoped Execution Mode Segmented Pill */
        .st-key-engine_perspective_mode {{
            margin-top: 0px !important;
            margin-bottom: 0px !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadio"] {{
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadio"] > label {{
            display: none !important;
        }}
        /* Outer capsule track */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] {{
            display: inline-flex !important;
            flex-direction: row !important;
            align-items: center !important;
            background-color: #E6ECE5 !important;
            border-radius: 9999px !important;
            padding: 4px !important;
            gap: 4px !important;
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            width: fit-content !important;
            box-sizing: border-box !important;
        }}
        /* Hide default Streamlit radio circles and inputs completely */
        .st-key-engine_perspective_mode [data-testid="stRadioOption"] > *:first-child,
        .st-key-engine_perspective_mode [data-testid="stRadio"] input[type="radio"],
        .st-key-engine_perspective_mode [data-testid="stRadio"] [role="radiogroup"] label > div:first-child,
        .st-key-engine_perspective_mode [data-testid="stRadio"] [role="radiogroup"] label > span:first-child {{
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        /* Pill segments */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] label {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            padding: 7px 20px !important;
            border-radius: 9999px !important;
            cursor: pointer !important;
            background-color: transparent !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            user-select: none !important;
            min-height: 34px !important;
        }}
        /* Text inside segment */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] label [data-testid="stMarkdownContainer"] p {{
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            margin: 0 !important;
            line-height: 1.2 !important;
            white-space: nowrap !important;
            display: inline-flex !important;
            align-items: center !important;
            letter-spacing: 0.15px !important;
            transition: color 0.18s ease !important;
        }}
        /* Dot indicator before label */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] label [data-testid="stMarkdownContainer"] p::before {{
            content: "" !important;
            display: inline-block !important;
            width: 7px !important;
            height: 7px !important;
            border-radius: 50% !important;
            margin-right: 8px !important;
            background-color: #9AA59D !important;
            transition: all 0.18s ease !important;
        }}

        /* --- Client-side dynamic state via :has() --- */
        /* Left: ERP Baseline Active */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label:has(input:checked) {{
            background-color: #FFFFFF !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label:has(input:checked) [data-testid="stMarkdownContainer"] p {{
            color: #26332C !important;
            font-weight: 700 !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:first-child label:has(input:checked) [data-testid="stMarkdownContainer"] p::before {{
            background-color: #B54747 !important;
            box-shadow: 0 0 3px rgba(181, 71, 71, 0.45) !important;
        }}

        /* Right: Mangrove Guard Active */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label:has(input:checked) {{
            background-color: #23533F !important;
            box-shadow: 0 2px 8px rgba(35, 83, 63, 0.28) !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label:has(input:checked) [data-testid="stMarkdownContainer"] p {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] > *:last-child label:has(input:checked) [data-testid="stMarkdownContainer"] p::before {{
            background-color: #4ECA8B !important;
            box-shadow: 0 0 5px rgba(78, 202, 139, 0.65) !important;
        }}

        /* Inactive states hover */
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] label:not(:has(input:checked)) [data-testid="stMarkdownContainer"] p {{
            color: #4A5850 !important;
            font-weight: 500 !important;
        }}
        .st-key-engine_perspective_mode [data-testid="stRadioGroup"] label:not(:has(input:checked)):hover {{
            background-color: rgba(255, 255, 255, 0.5) !important;
        }}

        {css_server_fallback}
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_ctrl, col_status = st.columns([1.6, 1.4])
    with col_ctrl:
        st.markdown(
            """
            <div style="font-size: 0.70rem; font-weight: 700; letter-spacing: 0.8px; color: #68756B; text-transform: uppercase; margin-bottom: 6px;">
                EXECUTION MODE
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_mode = st.radio(
            "Execution Mode",
            [MODE_LEGACY, MODE_MANGROVE],
            key="engine_perspective_mode",
            label_visibility="collapsed",
            horizontal=True,
        )

    is_mangrove = (selected_mode == MODE_MANGROVE)

    with col_status:
        if is_mangrove:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 24px;">
                    <span style="background-color: {COLOR_BRAND_SOFT}; color: {COLOR_BRAND_PRIMARY}; font-size: 0.72rem; font-weight: 700; padding: 6px 12px; border-radius: 6px; border: 1px solid #C6DBC3; letter-spacing: 0.4px;">
                        🛡️ MANGROVE ACTIVE: 136.1 MS &bull; &#x20B9;20.76 CR CLEARED
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 24px;">
                    <span style="background-color: #FDF4F4; color: {COLOR_DANGER}; font-size: 0.72rem; font-weight: 700; padding: 6px 12px; border-radius: 6px; border: 1px solid #F5C6C6; letter-spacing: 0.4px;">
                        ⚠️ TRADITIONAL ERP: 13 REJECTED ASNs &bull; &#x20B9;26.05 CR HALT THREAT
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Informational Scenario Callout Banner (Mode controlled via the Execution Mode toggle above)
    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 12px 18px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(181, 71, 71, 0.08);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.84rem; letter-spacing: 0.3px;">
                            🚨 TRADITIONAL ERP CRISIS: 4 ASSEMBLY LINES IN IMMINENT HALT (4.2 HOURS TO SHUTDOWN)
                        </div>
                        <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 0.76rem; margin-top: 3px; max-width: 820px; line-height: 1.35;">
                            Traditional ERP batch processing rejected 13 supplier ASNs due to raw packaging drift, catalog aliases, and corrupt epoch dates. Without in-database Python UDFs, the ERP assumes zero stock. Plant managers are preparing emergency shutdown protocols across Line 1 (Euro-6), Line 2 (AMT), and Line 4 (EV Drive). Toggle to <b>Mangrove Guard</b> above to engage Exasol in-memory defense.
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 18px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(47, 107, 79, 0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <div style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem; letter-spacing: 0.3px;">
                            🟢 MANGROVE IN-DB ACTIVE GUARD &bull; 12 FALSE ALARMS DISSOLVED IN EXASOL RAM (136.1 MS)
                        </div>
                        <div style="color: {COLOR_TEXT_SECONDARY}; font-size: 0.76rem; margin-top: 2px; max-width: 850px; line-height: 1.35;">
                            In-database Python 3 UDFs normalized packaging multipliers and resolved SKU drift in-memory. &#x20B9;20.76 Cr of false starvation threats dissolved. Assembly lines 1, 2, and 4 are safe. Genuine physical shortage isolated to &#x20B9;5.29 Cr on Line 3.
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
