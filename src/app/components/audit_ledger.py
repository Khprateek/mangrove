"""Visual Cryptographic Merkle Audit Trail & 1-Click Rollback Explorer.

Provides automotive-grade IATF-16949 / ISO-9001 compliance, visualizes
the SHA-256 chained Merkle ledger, and offers instantaneous 1-click rollback
controls for plant materials overrides.
"""

from __future__ import annotations

import time
from typing import Any
import pandas as pd
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BORDER_LIGHT,
    COLOR_BRAND_DARK,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_SURFACE,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    safe_float,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_visual_audit_ledger(client: ChakanExasolClient) -> None:
    """Renders the visual cryptographic audit trail, verification badge, and 1-click rollback controls."""
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 24px; margin-bottom: 8px;">
            AUDIT &amp; GOVERNANCE: IATF-16949 / ISO-9001 CRYPTOGRAPHIC MERKLE LEDGER
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Fetch & Verify Cryptographic Audit Chain
    t0_verify = time.perf_counter()
    audit_df, is_chain_valid = client.get_verified_audit_ledger()
    verify_ms = (time.perf_counter() - t0_verify) * 1000.0

    total_blocks = len(audit_df) if audit_df is not None else 0
    active_overrides_df = client.tables.get("ASN_PLANNER_OVERRIDES", pd.DataFrame())
    active_count = len(active_overrides_df) if active_overrides_df is not None else 0

    # Determine status details
    if is_chain_valid:
        status_bg = COLOR_BRAND_SOFT
        status_border = "#C6DBC3"
        status_badge_color = COLOR_BRAND_PRIMARY
        status_title = "SHA-256 MERKLE CHAIN: 100% MATHEMATICALLY VERIFIED"
        status_sub = f"All {total_blocks} ledger blocks mathematically validated against cryptographic hash pointers in {verify_ms:.2f} ms. Zero tampering detected."
    else:
        status_bg = "#FDF4F4"
        status_border = "#F5C2C2"
        status_badge_color = COLOR_DANGER
        status_title = "CRYPTOGRAPHIC INTEGRITY ALERT: HASH CHAIN BROKEN"
        status_sub = "Hash pointer mismatch or block payload tampering detected. Check system event logs immediately."

    latest_hash = str(audit_df.iloc[-1]["sha256_hash"]) if total_blocks > 0 else "N/A"
    short_latest_hash = f"{latest_hash[:12]}...{latest_hash[-8:]}" if total_blocks > 0 else "N/A"

    # Status Bar Layout
    st.markdown(
        f"""
        <div style="background-color: {status_bg}; border: 1px solid {status_border}; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: {status_badge_color}; letter-spacing: 0.4px;">
                        {status_title}
                    </div>
                    <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 3px;">
                        {status_sub}
                    </div>
                </div>
                <div style="display: flex; gap: 14px; align-items: center; font-size: 0.75rem;">
                    <div style="background-color: #FFFFFF; border: 1px solid {status_border}; padding: 4px 10px; border-radius: 6px;">
                        <span style="color: {COLOR_TEXT_SECONDARY}; font-weight: 500;">Sealed Blocks:</span>
                        <strong style="color: {COLOR_TEXT_PRIMARY}; margin-left: 4px;">{total_blocks}</strong>
                    </div>
                    <div style="background-color: #FFFFFF; border: 1px solid {status_border}; padding: 4px 10px; border-radius: 6px;">
                        <span style="color: {COLOR_TEXT_SECONDARY}; font-weight: 500;">Active Overrides:</span>
                        <strong style="color: {COLOR_BRAND_PRIMARY if active_count == 0 else COLOR_WARNING}; margin-left: 4px;">{active_count}</strong>
                    </div>
                    <div style="background-color: #FFFFFF; border: 1px solid {status_border}; padding: 4px 10px; border-radius: 6px; font-family: monospace;">
                        <span style="color: {COLOR_TEXT_SECONDARY}; font-family: sans-serif;">Head:</span> {short_latest_hash}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Active Planner Overrides with 1-Click Rollback
    if active_count > 0:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 0.82rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY};">
                    Active Override Authorizations ({active_count})
                </span>
                <span style="font-size: 0.74rem; color: {COLOR_TEXT_SECONDARY};">
                    Click rollback to restore baseline ERP &amp; log an immutable reversal block
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for _, ov_row in active_overrides_df.iterrows():
            ov_asn = str(ov_row["asn_line_id"])
            ov_sku = str(ov_row.get("resolved_part_num", "UNKNOWN"))
            ov_qty = safe_float(ov_row.get("normalized_qty", 0))
            ov_uom = str(ov_row.get("normalized_uom", "EA"))
            ov_action = str(ov_row.get("resolution_action", "MANUAL_OVERRIDE"))
            ov_user = str(ov_row.get("resolved_by", "planner"))
            ov_time = str(ov_row.get("resolved_at", ""))

            col_card, col_btn = st.columns([4, 1.2])
            with col_card:
                st.markdown(
                    f"""
                    <div style="background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-left: 4px solid {COLOR_WARNING}; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 0.82rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY};">
                                Override: <code>{ov_asn}</code> &bull; Part: <code style="color: {COLOR_BRAND_PRIMARY}; font-weight: 700;">{ov_sku}</code>
                            </span>
                            <span style="font-size: 0.70rem; background-color: #FFF8E6; color: {COLOR_WARNING}; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid #FFE49E;">
                                ACTIVE OVERRIDE
                            </span>
                        </div>
                        <div style="font-size: 0.75rem; color: {COLOR_TEXT_SECONDARY}; display: flex; gap: 16px; flex-wrap: wrap;">
                            <span>Quantity: <strong style="color: {COLOR_TEXT_PRIMARY};">{ov_qty:,.0f} {ov_uom}</strong></span>
                            <span>Action: <strong style="color: {COLOR_TEXT_PRIMARY};">{ov_action}</strong></span>
                            <span>By: <strong style="color: {COLOR_TEXT_PRIMARY};">{ov_user}</strong></span>
                            <span>At: <strong style="color: {COLOR_TEXT_PRIMARY};">{ov_time}</strong></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_btn:
                st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
                if st.button(f"↩️ Rollback ({ov_asn})", key=f"btn_rollback_{ov_asn}", use_container_width=True):
                    rev_ms = client.revert_planner_override(ov_asn)
                    st.success(f"Rolled back override `{ov_asn}` and appended cryptographic reversal block in {rev_ms:.2f} ms.")
                    st.rerun()

        # Global Revert All Button
        c_spacer, c_reset = st.columns([3.5, 1.5])
        with c_reset:
            if st.button("🗑️ Revert All Overrides to Baseline", key="btn_reset_all_overrides", use_container_width=True):
                rst_ms = client.reset_planner_overrides()
                st.success(f"Restored plant baseline in {rst_ms:.2f} ms. Sealed reset block in audit ledger.")
                st.rerun()
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_SURFACE}; border: 1px dashed {COLOR_BORDER}; border-radius: 8px; padding: 10px 16px; margin-bottom: 14px; font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; display: flex; align-items: center; gap: 8px;">
                <span style="color: {COLOR_BRAND_PRIMARY}; font-size: 0.95rem;">✓</span>
                <span><strong>No active manual overrides.</strong> Factory assembly operations running strictly on automated In-DB harmonization rules.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Interactive Merkle Visualizer / Compliance Ledger View
    with st.expander("🛡️ Inspect Cryptographic Hash Chain & IATF-16949 Ledger", expanded=False):
        col_ctrl1, col_ctrl2 = st.columns([1.5, 1.0])
        with col_ctrl1:
            audit_view_mode = st.radio(
                "Audit Display Mode:",
                ["🧱 Merkle Block Chain (Visual)", "📋 IATF-16949 Compliance Ledger (Table)"],
                horizontal=True,
                label_visibility="collapsed",
                key="audit_display_mode_selector",
            )
        with col_ctrl2:
            st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
            if st.button("⚡ Re-Verify Hash Chain", key="btn_reverify_chain", use_container_width=False):
                t_chk = time.perf_counter()
                _, chk_valid = client.get_verified_audit_ledger()
                chk_ms = (time.perf_counter() - t_chk) * 1000.0
                if chk_valid:
                    st.toast(f"Cryptographic Chain 100% Valid ({total_blocks} blocks re-computed in {chk_ms:.2f} ms)", icon="🛡️")
                else:
                    st.error("Tampering detected during manual re-verification!")
            st.markdown("</div>", unsafe_allow_html=True)

        if total_blocks == 0 or audit_df is None or len(audit_df) == 0:
            st.info("No override audit blocks recorded yet. Approving or reverting overrides will append immutable cryptographic blocks here.")
            return

        if audit_view_mode == "🧱 Merkle Block Chain (Visual)":
            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
            # Display blocks in reverse chronological order (newest on top)
            for idx in reversed(range(total_blocks)):
                row = audit_df.iloc[idx]
                block_num = idx + 1
                ev_type = str(row.get("event_type", "EVENT"))
                ev_id = str(row.get("event_id", f"AUD-{block_num:04d}"))
                asn_id = str(row.get("asn_line_id", "N/A"))
                part_num = str(row.get("resolved_part_num", "N/A"))
                qty = safe_float(row.get("normalized_qty", 0))
                uom = str(row.get("normalized_uom", "EA"))
                action = str(row.get("action", ""))
                user = str(row.get("operator_id", "planner"))
                ts = str(row.get("timestamp", ""))
                curr_hash = str(row.get("sha256_hash", ""))
                prev_hash = str(row.get("prev_hash", ""))
                is_blk_valid = bool(row.get("chain_verified", True))

                # Color accents based on event type
                if ev_type == "OVERRIDE_APPROVED":
                    ev_color = COLOR_BRAND_PRIMARY
                    ev_bg = COLOR_BRAND_SOFT
                    ev_label = "OVERRIDE APPROVED"
                elif ev_type == "OVERRIDE_REVERTED":
                    ev_color = COLOR_WARNING
                    ev_bg = "#FFF8E6"
                    ev_label = "OVERRIDE REVERTED"
                elif ev_type == "ALL_OVERRIDES_RESET":
                    ev_color = "#3B5998"
                    ev_bg = "#EEF2FA"
                    ev_label = "SYSTEM RESET TO BASELINE"
                else:
                    ev_color = COLOR_TEXT_SECONDARY
                    ev_bg = COLOR_SURFACE_MUTED
                    ev_label = ev_type

                st.markdown(
                    f"""
                    <div style="background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-left: 5px solid {ev_color}; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(24, 61, 50, 0.04);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid {COLOR_BORDER_LIGHT}; padding-bottom: 6px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-weight: 700; font-size: 0.82rem; color: {COLOR_TEXT_PRIMARY};">
                                    Block #{block_num:04d} &bull; <span style="font-family: monospace; font-size: 0.78rem;">{ev_id}</span>
                                </span>
                                <span style="background-color: {ev_bg}; color: {ev_color}; font-size: 0.68rem; font-weight: 700; padding: 2px 7px; border-radius: 4px;">
                                    {ev_label}
                                </span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 10px; font-size: 0.72rem;">
                                <span style="color: {COLOR_TEXT_SECONDARY};">{ts}</span>
                                <span style="color: {COLOR_BRAND_PRIMARY if is_blk_valid else COLOR_DANGER}; font-weight: 700;">
                                    {'✓ SHA-256 Valid' if is_blk_valid else '✗ Tampered'}
                                </span>
                            </div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; font-size: 0.75rem; margin-bottom: 8px;">
                            <div><span style="color: {COLOR_TEXT_SECONDARY};">ASN Line:</span> <strong>{asn_id}</strong></div>
                            <div><span style="color: {COLOR_TEXT_SECONDARY};">Component Part:</span> <strong style="color: {COLOR_BRAND_PRIMARY};">{part_num}</strong></div>
                            <div><span style="color: {COLOR_TEXT_SECONDARY};">Authorized Qty:</span> <strong>{qty:,.0f} {uom}</strong></div>
                            <div><span style="color: {COLOR_TEXT_SECONDARY};">Operator:</span> <strong>{user}</strong></div>
                            <div><span style="color: {COLOR_TEXT_SECONDARY};">Resolution:</span> <code>{action}</code></div>
                        </div>

                        <div style="background-color: {COLOR_SURFACE_MUTED}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; padding: 6px 10px; font-family: monospace; font-size: 0.68rem; color: {COLOR_TEXT_SECONDARY}; line-height: 1.4;">
                            <div><span style="font-weight: 600; color: {COLOR_TEXT_PRIMARY};">PREV HASH:</span> {prev_hash}</div>
                            <div><span style="font-weight: 600; color: {ev_color};">THIS HASH:</span> {curr_hash}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Visual link indicator to previous block if not genesis
                if idx > 0:
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin: -6px 0 4px 0; color: {COLOR_BRAND_PRIMARY}; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;">
                            &uarr; SHA-256 Cryptographic Link Pointer &uarr;
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        else:
            # Compliance Ledger Table View
            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
            display_cols = [
                "event_id",
                "event_type",
                "asn_line_id",
                "resolved_part_num",
                "normalized_qty",
                "normalized_uom",
                "action",
                "operator_id",
                "timestamp",
                "sha256_hash",
                "chain_verified",
            ]
            valid_cols = [c for c in display_cols if c in audit_df.columns]
            audit_display_df = audit_df[valid_cols].copy()

            st.dataframe(audit_display_df, use_container_width=True, hide_index=True)

            # CSV Download Button
            csv_bytes = audit_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download IATF-16949 Cryptographic Audit Log (CSV)",
                data=csv_bytes,
                file_name="iatf16949_cryptographic_audit_ledger.csv",
                mime="text/csv",
                use_container_width=False,
            )
