"""Tab 1: Actionable Shortage-Risk Queue & 1-Click Fast-Resolution Workbench."""

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
    safe_float,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_triage_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Tab 1: Actionable Shortage-Risk Queue & 1-Click Fast-Resolution Workbench."""
    triage_df: pd.DataFrame = marts["triage_queue"].copy()

    for col_name in [
        "downtime_burn_rate_inr_hr",
        "expedited_freight_cost_inr",
        "mitigation_roi_x",
        "revenue_at_risk_net_inr",
        "revenue_at_risk_legacy_inr",
        "true_net_deficit_qty",
        "harmonized_shipped_qty",
        "po_ordered_qty",
        "raw_shipped_qty",
        "min_hours_to_stop_harmonized",
        "min_hours_to_stop_legacy",
        "total_stoppage_exposure_inr",
        "sku_confidence",
    ]:
        if col_name in triage_df.columns:
            triage_df[col_name] = pd.to_numeric(triage_df[col_name], errors="coerce").fillna(0.0)

    # Sort triage_df so highest true net risk is first
    triage_df = triage_df.sort_values(
        by=["revenue_at_risk_net_inr", "min_hours_to_stop_harmonized"],
        ascending=[False, True],
    )

    # 1. Actionable Queue Header & Urgency Filter
    col_t_title, col_t_filter = st.columns([1.1, 1.0])
    with col_t_title:
        st.markdown(
            f"""
            <div style="margin-bottom: 6px;">
                <span style="font-size: 1.15rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; letter-spacing: -0.2px;">Actionable Shortage-Risk Queue &amp; Fast Triage</span>
                <div style="font-size: 0.80rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 2px;">
                    Ranked by plant halt urgency and net revenue threatened over the next 48 hours.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_t_filter:
        urgency_filter = st.radio(
            "Filter Stream:",
            ["🔴 Active Line Threats", "All Quarantined", "🟢 Cleared by UDFs"],
            horizontal=True,
            label_visibility="collapsed",
        )

    # Apply quick filter
    if urgency_filter == "🔴 Active Line Threats":
        filtered_df = triage_df[triage_df["revenue_at_risk_net_inr"] > 0]
    elif urgency_filter == "🟢 Cleared by UDFs":
        filtered_df = triage_df[
            triage_df["operational_verdict"].isin(
                ["FALSE_STARVATION_CLEARED_BY_UDF", "HARMONIZED_BUFFER_RESTORED"]
            )
        ]
    else:
        filtered_df = triage_df

    if len(filtered_df) == 0:
        filtered_df = triage_df

    # 2. Fast-Resolution Workbench (Top of Tab 1)
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 10px; margin-bottom: 8px;">
            1-CLICK RESOLUTION WORKBENCH
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = filtered_df["asn_line_id"].tolist()
    selected_id = st.selectbox(
        "Select Shortage Record to Resolve:",
        options=options,
        format_func=lambda x: (
            f"⚡ {x} | PO: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'po_number_ref'].values[0]} | "
            f"Part: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'resolved_part_num'].values[0]} | "
            f"Line: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'affected_lines'].values[0]} | "
            f"Net Risk: {format_inr_crore_lakh(filtered_df.loc[filtered_df['asn_line_id'] == x, 'revenue_at_risk_net_inr'].values[0])}"
        ),
        label_visibility="collapsed",
    )

    sel_row = filtered_df[filtered_df["asn_line_id"] == selected_id].iloc[0]

    # 3 Executive Data Tiles
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            f"""
            <div class="mangrove-tile">
                <div class="mangrove-tile-title">1. Inbound Raw Dispatch (Anomaly)</div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Supplier:</span><span class="mangrove-tile-val">{sel_row['supplier_name']} ({sel_row['tier_level']})</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Transport:</span><span class="mangrove-tile-val">{sel_row['source_format']} • {sel_row['vehicle_lorry_no']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Raw SKU String:</span><span class="mangrove-tile-val" style="color: {COLOR_DANGER}; font-weight: 700;">{sel_row['raw_supplier_sku']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Raw Shipped:</span><span class="mangrove-tile-val">{sel_row['raw_shipped_qty']} {sel_row['raw_shipped_uom']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Reported ETA:</span><span class="mangrove-tile-val">{sel_row['raw_eta_date']} ({sel_row['anomaly_type']})</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            f"""
            <div class="mangrove-tile-highlight">
                <div class="mangrove-tile-title-green">2. Exasol In-DB Resolution (RAM)</div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Resolved SKU:</span><span class="mangrove-tile-val" style="color: {COLOR_BRAND_PRIMARY}; font-weight: 700;">{sel_row['resolved_part_num']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Match Method:</span><span class="mangrove-tile-val">{sel_row['sku_match_method']} ({sel_row['sku_confidence']:.2f})</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Normalized Qty:</span><span class="mangrove-tile-val" style="color: {COLOR_BRAND_PRIMARY}; font-weight: 700;">{sel_row['harmonized_shipped_qty']:,.1f} {sel_row['canonical_uom']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">PO Target Qty:</span><span class="mangrove-tile-val">{sel_row['po_ordered_qty']:,.0f} {sel_row['canonical_uom']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Parsed Date:</span><span class="mangrove-tile-val">{sel_row['harmonized_eta_date']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        halt_color = COLOR_DANGER if sel_row["min_hours_to_stop_harmonized"] < 24.0 else COLOR_BRAND_PRIMARY
        roi_disp = f"{sel_row['mitigation_roi_x']:,.0f}x" if sel_row["mitigation_roi_x"] > 0 else "N/A"
        freight_disp = f"Rs {sel_row['expedited_freight_cost_inr']:,.0f}" if sel_row["expedited_freight_cost_inr"] > 0 else "Rs 45,000"
        st.markdown(
            f"""
            <div class="mangrove-tile">
                <div class="mangrove-tile-title">3. Line Halt Risk &amp; Freight Trade-Off</div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Assembly Line:</span><span class="mangrove-tile-val">{sel_row['affected_lines']}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Hours to Halt:</span><span class="mangrove-tile-val" style="color: {halt_color}; font-weight: 700;">{sel_row['min_hours_to_stop_harmonized']}h (Legacy: {sel_row['min_hours_to_stop_legacy']}h)</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Plant Downtime Loss:</span><span class="mangrove-tile-val" style="color: {COLOR_DANGER}; font-weight: 700;">{format_inr_crore_lakh(sel_row['total_stoppage_exposure_inr'])}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Hot-Shot Freight:</span><span class="mangrove-tile-val">{freight_disp}</span></div>
                <div class="mangrove-tile-row"><span class="mangrove-tile-label">Mitigation ROI:</span><span class="mangrove-tile-val" style="color: {COLOR_BRAND_PRIMARY}; font-size: 0.88rem; font-weight: 700;">{roi_disp}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Action Buttons with proper spacing
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            f"Approve In-DB Harmonization ({sel_row['harmonized_shipped_qty']:,.0f} {sel_row['canonical_uom']})",
            use_container_width=True,
        ):
            write_ms = client.approve_harmonization_override(
                asn_line_id=str(sel_row["asn_line_id"]),
                resolved_part_num=str(sel_row["resolved_part_num"]),
                normalized_qty=float(sel_row["harmonized_shipped_qty"]),
                normalized_uom=str(sel_row["canonical_uom"]),
                normalized_eta_date=str(sel_row["harmonized_eta_date"]),
                action="PLANNER_APPROVED_UDF",
            )
            st.success(f"Committed UDF harmonization to Exasol in {write_ms:.2f} ms.")
            st.rerun()

    with b2:
        full_po_qty = float(sel_row["po_ordered_qty"])
        btn_roi_label = f" | ROI: {sel_row['mitigation_roi_x']:,.0f}x" if sel_row["mitigation_roi_x"] > 0 else ""
        if st.button(
            f"Approve & Cover Shortfall via Hot-Shot (Full PO: {full_po_qty:,.0f} {sel_row['canonical_uom']}{btn_roi_label})",
            type="primary",
            use_container_width=True,
        ):
            write_ms = client.approve_harmonization_override(
                asn_line_id=str(sel_row["asn_line_id"]),
                resolved_part_num=str(sel_row["resolved_part_num"]),
                normalized_qty=full_po_qty,
                normalized_uom=str(sel_row["canonical_uom"]),
                normalized_eta_date=str(sel_row["harmonized_eta_date"]),
                action="EXPEDITED_SHORTFALL_COVERED",
            )
            st.success(f"Authorized emergency shortfall cover and updated Exasol in {write_ms:.2f} ms.")
            st.rerun()

    # 3. Prioritized Quarantined Stream Table
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 22px; margin-bottom: 8px;">
            PRIORITIZED INBOUND DISPATCH QUEUE
        </div>
        """,
        unsafe_allow_html=True,
    )

    def format_verdict_badge(row: pd.Series) -> str:
        verdict = row["operational_verdict"]
        net_risk = row["revenue_at_risk_net_inr"]
        if net_risk > 0:
            return "🔴 Line Halt Threat"
        if verdict in ["FALSE_STARVATION_CLEARED_BY_UDF", "HARMONIZED_BUFFER_RESTORED"]:
            return "🟢 Cleared by UDF"
        return "🟡 Monitored"

    display_df = pd.DataFrame(
        {
            "Urgency": filtered_df.apply(format_verdict_badge, axis=1),
            "ASN ID": filtered_df["asn_line_id"],
            "PO Ref": filtered_df["po_number_ref"],
            "Supplier": filtered_df["supplier_name"] + " (" + filtered_df["tier_level"] + ")",
            "Resolved Part": filtered_df["resolved_part_num"],
            "Inbound vs PO": filtered_df["harmonized_shipped_qty"].apply(lambda v: f"{safe_float(v):,.0f}")
            + " / "
            + filtered_df["po_ordered_qty"].apply(lambda v: f"{safe_float(v):,.0f}")
            + " "
            + filtered_df["canonical_uom"],
            "Target Line": filtered_df["affected_lines"],
            "Hours to Halt": filtered_df["min_hours_to_stop_harmonized"].apply(lambda v: f"{safe_float(v):.1f}h"),
            "True Net Risk": filtered_df["revenue_at_risk_net_inr"].apply(format_inr_crore_lakh),
            "Mitigation ROI": filtered_df["mitigation_roi_x"].apply(
                lambda v: f"{safe_float(v):,.0f}x" if safe_float(v) > 0 else "-"
            ),
            "Status": filtered_df["harmonization_state"],
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 4. Active Overrides with 1-Click Rollback Control
    ov_active = client.tables.get("ASN_PLANNER_OVERRIDES", pd.DataFrame())
    if len(ov_active) > 0:
        st.markdown(
            f"""
            <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 18px; margin-bottom: 8px;">
                ACTIVE PLANNER OVERRIDES &amp; 1-CLICK ROLLBACK
            </div>
            """,
            unsafe_allow_html=True,
        )
        for _, ov_row in ov_active.iterrows():
            ov_id = str(ov_row["asn_line_id"])
            col_ov1, col_ov2 = st.columns([4, 1])
            with col_ov1:
                st.info(
                    f"**Active Override: `{ov_id}`** | Part: `{ov_row['resolved_part_num']}` | "
                    f"Qty: `{ov_row['normalized_qty']:,.0f} {ov_row['normalized_uom']}` | "
                    f"Action: `{ov_row['resolution_action']}` | By: `{ov_row['resolved_by']}` at `{ov_row['resolved_at']}`"
                )
            with col_ov2:
                if st.button(f"↩️ Revert ({ov_id})", key=f"revert_{ov_id}", use_container_width=True):
                    rev_ms = client.revert_planner_override(ov_id)
                    st.success(f"Reverted override {ov_id} in {rev_ms:.2f} ms!")
                    st.rerun()

    # 5. Cryptographic Merkle Audit Trail in Expander
    with st.expander("🛡️ Cryptographic Merkle Audit Trail (SHA-256 Chained Ledger)", expanded=False):
        audit_df, chain_valid = client.get_verified_audit_ledger()
        if len(audit_df) > 0:
            status_color = COLOR_BRAND_PRIMARY if chain_valid else COLOR_DANGER
            status_text = (
                "CRYPTOGRAPHIC INTEGRITY: 100% VERIFIED (CHAIN VALID)"
                if chain_valid
                else "INTEGRITY WARNING: CORRUPTED HASH DETECTED"
            )
            st.markdown(
                f"""
                <div style="background-color: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER}; border-left: 4px solid {status_color}; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 0.78rem;">
                    <span style="color: {status_color}; font-weight: 700;">{status_text}</span>
                    <span style="color: {COLOR_TEXT_SECONDARY}; margin-left: 10px;">Every override and reversal is sealed with SHA-256 Merkle cryptography.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            display_audit = audit_df[
                [
                    "event_id",
                    "event_type",
                    "asn_line_id",
                    "resolved_part_num",
                    "normalized_qty",
                    "action",
                    "operator_id",
                    "timestamp",
                    "sha256_hash",
                    "chain_verified",
                ]
            ].copy()
            st.dataframe(display_audit, use_container_width=True, hide_index=True)
        else:
            st.caption(
                "No override events recorded yet. Approving or reverting overrides will log immutable cryptographic blocks here."
            )
