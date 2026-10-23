"""Tab 1: Actionable Shortage-Risk Queue & 1-Click Fast-Resolution Workbench."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.components.audit_ledger import render_visual_audit_ledger
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

DEFECT_LABELS = {
    "SKU_DRIFT_AND_UOM_BOX": "Alias SKU + Box-100",
    "SKU_DRIFT_AND_UOM_BAG": "Fuzzy SKU + Bag-250",
    "EPOCH_DATE_AND_UOM_BOX": "Corrupt Unix Date + Box",
    "SKU_HYPHEN_STRIPPED": "Stripped Hyphen (OCR)",
    "OCR_SKU_ALIAS_AND_BOX": "OCR Vendor Code + Box",
    "UOM_MT_VS_KG_CLEAN_QTY": "MT to KG Multiplier",
    "SPLIT_PO_AND_UOM_CRATE": "Crate-50 + Split Shortage",
    "SPLIT_PO_SHORT_SHIPMENT": "Split PO Short-Shipment",
    "UOM_MT_VS_KG_SHORTAGE": "MT to KG + Shortage",
    "SKU_ALIAS_AND_SHORT_QTY": "Catalog Alias + Shortage",
    "DUPLICATE_ASN_RETRANSMIT": "Duplicate Retransmit",
    "WEIGHT_MT_TO_EA_INVERSION": "Weight MT to Piece (EA)",
}

DEFECT_DESCRIPTIONS_LEGACY = {
    "SKU_DRIFT_AND_UOM_BOX": "Unrecognized SKU Drift & Non-Standard Packaging (BOX_100)",
    "SKU_DRIFT_AND_UOM_BAG": "Unrecognized SKU Drift & Bulk Bag Packaging (BAG_250)",
    "EPOCH_DATE_AND_UOM_BOX": "Corrupt Unix Epoch Timestamp & Crate Inversion",
    "SKU_HYPHEN_STRIPPED": "OCR Parsing Failure (Missing Hyphen in Part Number)",
    "OCR_SKU_ALIAS_AND_BOX": "Unmapped Vendor Catalog Alias & Packaging Mismatch",
    "UOM_MT_VS_KG_CLEAN_QTY": "Metric Ton to Kilogram Unit Conversion Mismatch",
    "SPLIT_PO_AND_UOM_CRATE": "Unrecognized Crate Packaging & PO Short-Shipment",
    "SPLIT_PO_SHORT_SHIPMENT": "Partial Delivery Shortfall against Active Purchase Order",
    "UOM_MT_VS_KG_SHORTAGE": "Metric Ton Unit Inversion & Physical Weight Deficit",
    "SKU_ALIAS_AND_SHORT_QTY": "Unrecognized Catalog Code & Confirmed Material Shortage",
    "DUPLICATE_ASN_RETRANSMIT": "Duplicate Transmission ID Quarantined by Gate System",
    "WEIGHT_MT_TO_EA_INVERSION": "Weight Metric Ton to Piece Conversion Mismatch",
}


def render_triage_tab(
    client: ChakanExasolClient,
    marts: dict,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Tab 1: Actionable Shortage-Risk Queue & 1-Click Fast-Resolution Workbench

    dynamically renders authentic views depending on perspective:
    - TRADITIONAL_ERP: Authentic legacy quarantine log (NO 'Harmonized In-DB' column).
    - MANGROVE_ACTIVE: In-DB Harmonized triage workbench with UDF-resolved SKUs and True Net Risk.
    """
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")
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
        by=["revenue_at_risk_net_inr" if is_mangrove else "revenue_at_risk_legacy_inr", "min_hours_to_stop_harmonized"],
        ascending=[False, True],
    )

    # 1. Actionable Queue Header & Urgency Filter
    col_t_title, col_t_filter = st.columns([1.2, 0.9])
    with col_t_title:
        title_text = (
            "Actionable Shortage-Risk Queue &amp; Fast Triage"
            if is_mangrove
            else "Gate Quarantine Log (Traditional ERP Batch Rejections)"
        )
        sub_text = (
            "Ranked by plant halt urgency and net revenue threatened over the next 48 hours."
            if is_mangrove
            else "All 13 supplier shipments rejected at factory gate by legacy ETL. Zero stock credited to assembly lines."
        )
        st.markdown(
            f"""
            <div style="margin-bottom: 6px;">
                <span style="font-size: 1.15rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; letter-spacing: -0.2px;">{title_text}</span>
                <div style="font-size: 0.80rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 2px;">
                    {sub_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_t_filter:
        if is_mangrove:
            urgency_filter = st.radio(
                "Filter Stream:",
                ["All Quarantined (13 ASNs)", "🔴 Active Threats (7)", "🟢 Cleared by UDF (6)"],
                horizontal=True,
                label_visibility="collapsed",
            )
            if urgency_filter == "🔴 Active Threats (7)":
                filtered_df = triage_df[triage_df["revenue_at_risk_net_inr"] > 0]
            elif urgency_filter == "🟢 Cleared by UDF (6)":
                filtered_df = triage_df[
                    triage_df["operational_verdict"].isin(
                        ["FALSE_STARVATION_CLEARED_BY_UDF", "HARMONIZED_BUFFER_RESTORED"]
                    )
                ]
            else:
                filtered_df = triage_df
        else:
            urgency_filter = st.radio(
                "Filter Stream:",
                ["🔴 All 13 Shipments Rejected (Zero Stock)", "🔴 Emergency Line Shutdowns (13)"],
                horizontal=True,
                label_visibility="collapsed",
            )
            filtered_df = triage_df

    if len(filtered_df) == 0:
        filtered_df = triage_df

    # 1. Prioritized Quarantined Stream Table (Top of Tab 1)
    queue_label = "PRIORITIZED INBOUND DISPATCH QUEUE" if is_mangrove else "LEGACY ERP GATE REJECTION LOG (RAW UNHARMONIZED PAYLOADS)"
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 10px; margin-bottom: 8px;">
            {queue_label}
        </div>
        """,
        unsafe_allow_html=True,
    )

    def format_raw_payload(row: pd.Series) -> str:
        uom = str(row["raw_shipped_uom"])
        qty = safe_float(row["raw_shipped_qty"])
        qty_str = f"{qty:.3f}" if uom == "MT" else f"{qty:,.0f}"
        return f"{row['raw_supplier_sku']} ({qty_str} {uom})"

    def format_legacy_alarm(row: pd.Series) -> str:
        alarm = safe_float(row["revenue_at_risk_legacy_inr"])
        return f"REJECTED ({format_inr_crore_lakh(alarm)})" if alarm > 0 else "REJECTED AT GATE (Dirty Data)"

    if is_mangrove:
        # Mangrove In-DB Harmonized Table (with Harmonized In-DB and True Net Risk)
        def format_verdict_badge(row: pd.Series) -> str:
            net_risk = safe_float(row["revenue_at_risk_net_inr"])
            verdict = row["operational_verdict"]
            if net_risk > 0:
                return "🔴 Line Threat"
            if verdict == "FALSE_STARVATION_CLEARED_BY_UDF":
                return "🟢 False Alarm Cleared"
            if verdict == "HARMONIZED_BUFFER_RESTORED":
                return "🟢 Buffer Restored"
            return "🟡 Duplicate Suppressed"

        def format_harmonized_part(row: pd.Series) -> str:
            qty = safe_float(row["harmonized_shipped_qty"])
            return f"{row['resolved_part_num']} ({qty:,.0f} {row['canonical_uom']})"

        def format_true_net_risk(row: pd.Series) -> str:
            net = safe_float(row["revenue_at_risk_net_inr"])
            alarm = safe_float(row["revenue_at_risk_legacy_inr"])
            if net > 0:
                return format_inr_crore_lakh(net)
            if alarm > 0:
                return "Rs 0.00 (Cleared)"
            return "Rs 0.00 (Unblocked)"

        display_df = pd.DataFrame(
            {
                "Verdict": filtered_df.apply(format_verdict_badge, axis=1),
                "ASN ID": filtered_df["asn_line_id"],
                "Supplier": filtered_df["supplier_name"],
                "Raw Payload (Defect)": filtered_df.apply(format_raw_payload, axis=1),
                "Defect Mode": filtered_df["anomaly_type"].map(DEFECT_LABELS).fillna(filtered_df["anomaly_type"]),
                "Harmonized In-DB": filtered_df.apply(format_harmonized_part, axis=1),
                "Target Line": filtered_df["affected_lines"],
                "Legacy ERP Status": filtered_df.apply(format_legacy_alarm, axis=1),
                "True Net Risk": filtered_df.apply(format_true_net_risk, axis=1),
            }
        )
    else:
        # Traditional ERP Table: Authentic Legacy Structure (NO "Harmonized In-DB" column!)
        display_df = pd.DataFrame(
            {
                "Gate Status": ["🔴 REJECTED AT GATE"] * len(filtered_df),
                "ASN Line ID": filtered_df["asn_line_id"],
                "Supplier Name": filtered_df["supplier_name"],
                "Supplier SKU & Qty (Raw)": filtered_df.apply(format_raw_payload, axis=1),
                "ETL Rejection Cause": filtered_df["anomaly_type"].map(DEFECT_DESCRIPTIONS_LEGACY).fillna(filtered_df["anomaly_type"]),
                "Affected Assembly Line": filtered_df["affected_lines"],
                "ERP Line Verdict": ["ZERO STOCK CREDITED (HALT)"] * len(filtered_df),
                "Revenue Threatened": filtered_df["revenue_at_risk_legacy_inr"].map(format_inr_crore_lakh),
            }
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # 2. Fast-Resolution Workbench & Cryptographic Audit Ledger (Only available in Mangrove Guard)
    if is_mangrove:
        st.markdown(
            f"""
            <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 20px; margin-bottom: 8px;">
                1-CLICK RESOLUTION WORKBENCH
            </div>
            """,
            unsafe_allow_html=True,
        )

        shortage_ids = [
            x for x in filtered_df["asn_line_id"].tolist()
            if safe_float(filtered_df.loc[filtered_df['asn_line_id'] == x, 'revenue_at_risk_net_inr'].values[0]) > 0
        ]
        options = shortage_ids if shortage_ids else filtered_df["asn_line_id"].tolist()

        selected_id = st.selectbox(
            "Select Shortage Record to Resolve:",
            options=options,
            format_func=lambda x: (
                f"⚡ {x} | PO: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'po_number_ref'].values[0]} | "
                f"Supplier: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'supplier_name'].values[0]} | "
                f"Line: {filtered_df.loc[filtered_df['asn_line_id'] == x, 'affected_lines'].values[0]} | "
                f"Exposure: {format_inr_crore_lakh(filtered_df.loc[filtered_df['asn_line_id'] == x, 'revenue_at_risk_net_inr'].values[0])}"
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

        # Action Buttons
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

        # 3. Cryptographic Merkle Audit Trail & 1-Click Rollback Explorer
        render_visual_audit_ledger(client)
