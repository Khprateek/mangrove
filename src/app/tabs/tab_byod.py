"""Tab 8: Bring-Your-Own-Data (BYOD) Inbound Studio.

Upload (or pick a preset) inbound delivery batch, harmonize it through the same three
UDFs the Exasol views use, and see how it changes the baseline starvation exposure.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_CARD_BG,
    COLOR_INK_GREEN,
    COLOR_PALE_SAGE,
    COLOR_TEXT_SECONDARY,
    format_inr_crore_lakh,
)
from src.exasol_engine.custom_ingestor import (
    DOMAIN_PROFILES,
    PRESET_LABELS,
    anonymize_frame,
    detect_and_map_columns,
    generate_expedite_manifest,
    generate_sap_migo_export,
    get_industrial_scenario_preset,
    harmonize_and_evaluate_inbound,
    parse_custom_inbound_stream,
)
from src.exasol_engine.db_client import ChakanExasolClient

UPLOAD_OPTION = "Upload your own delivery file (.csv, .tsv, .xlsx)"


def render_byod_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Render the BYOD inbound studio."""
    st.markdown(
        f"""
        <div style="background-color:{COLOR_CARD_BG}; border:1px solid {COLOR_BORDER}; border-left:5px solid {COLOR_BRAND_PRIMARY}; border-radius:12px; padding:16px 22px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <h3 style="margin:0; color:{COLOR_BRAND_PRIMARY}; font-size:1.2rem;">Enterprise Pilot & Onboarding Sandbox (BYOD Studio)</h3>
                <span style="font-size:0.75rem; background-color:{COLOR_PALE_SAGE}; color:{COLOR_INK_GREEN}; font-weight:700; padding:3px 10px; border-radius:12px; border:1px solid #C6DBC3;">PILOT SANDBOX & PROTO-LAB</span>
            </div>
            <p style="margin:4px 0 0 0; color:{COLOR_TEXT_SECONDARY}; font-size:0.85rem;">
                In production, Mangrove connects directly via native SAP S/4HANA (IDocs/BAPIs), Oracle SCM, or Kafka pipelines.
                This Sandbox Studio allows prospective enterprise clients and evaluators to test raw supplier dispatches, assess cross-industry adaptability, and auto-onboard new product catalogs.
            </p>
            <p style="margin:8px 0 0 0; color:{COLOR_TEXT_SECONDARY}; font-size:0.78rem;">
                <b>Privacy:</b> Files are processed strictly in memory for this session. With a live Exasol connection, records are staged in an ephemeral scratch table and dropped immediately.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d_col1, d_col2 = st.columns([1, 1], gap="medium")
    with d_col1:
        domain_key = st.selectbox(
            "1. Operating Domain Profile",
            options=list(DOMAIN_PROFILES.keys()),
            format_func=lambda k: DOMAIN_PROFILES[k],
            index=0,
            help="Defines the reference enterprise master taxonomy and demand schedule for this evaluation session.",
        )
    with d_col2:
        sample_csv_path = "data/sample_kaggle_delivery_challan.csv"
        try:
            with open(sample_csv_path, "r", encoding="utf-8") as f:
                sample_csv_data = f.read()
            st.caption("Ready-to-test sample batch matching automotive OEM format:")
            st.download_button(
                "📥 Download Sample Automotive Delivery Batch (.csv)",
                data=sample_csv_data,
                file_name="sample_automotive_delivery_batch.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except Exception:
            pass

    if domain_key != "AUTOMOTIVE":
        st.info(
            f"🌐 **Auto-Onboarding & Canonical Taxonomy Mode Active**: When external data (e.g. DataCo or custom logistics feeds) is uploaded, Mangrove auto-discovers unique items and applies standardized enterprise taxonomy (`[RET-CARD-XXXX]` or `[CORP-SKU-XXXX]`) before evaluating UOMs and starvation risk."
        )

    source = st.radio("2. Inbound source", options=[*PRESET_LABELS.values(), UPLOAD_OPTION], index=0)

    raw_df: pd.DataFrame | None = None
    if source == UPLOAD_OPTION:
        st.caption("Rows are matched to open purchase orders by PO number, so include a PO column for best resolution.")
        uploaded = st.file_uploader("Delivery / challan / ASN file", type=["csv", "tsv", "xlsx", "xls"])
        if uploaded is not None:
            raw_df = parse_custom_inbound_stream(uploaded.read(), uploaded.name)
        else:
            st.info("Upload a file, or choose a preset above.")
    else:
        key = next(k for k, v in PRESET_LABELS.items() if v == source)
        raw_df = get_industrial_scenario_preset(key)

    if raw_df is None or len(raw_df) == 0:
        return

    st.markdown("---")
    left, right = st.columns([2, 1], gap="medium")
    with left:
        st.markdown(f"#### Raw inbound preview ({len(raw_df)} rows)")
        st.dataframe(raw_df.head(8), use_container_width=True, height=220)
    with right:
        st.markdown("#### Options")
        mask = st.checkbox(
            "Mask identifiers in results and exports",
            value=False,
            help="Replaces supplier, SKU, PO and ASN identifiers with tokens in the displayed table and downloads. "
            "Resolution itself always runs on the real identifiers.",
        )
        eval_df = raw_df
        if len(raw_df) > 1000:
            scope = st.selectbox(
                f"Batch evaluation scope ({len(raw_df):,} rows)",
                options=["First 1,000 rows (Instant - recommended)", "First 5,000 rows (High speed)", "Full dataset"],
                index=0,
                help="High-volume datasets can be sampled for instant sub-second interactive triage or evaluated in full.",
            )
            if "1,000" in scope:
                eval_df = raw_df.head(1000)
            elif "5,000" in scope:
                eval_df = raw_df.head(5000)

        with st.expander("Detected column mapping"):
            _, used = detect_and_map_columns(raw_df)
            if used:
                for canon, src in used.items():
                    st.text(f"{canon}  <-  {src}")
            else:
                st.text("No headers matched; defaults applied.")

    if st.button("Harmonize batch and evaluate impact", type="primary", use_container_width=True):
        with st.spinner("Running SKU resolution, UOM normalization and date parsing..."):
            st.session_state["byod_result"] = harmonize_and_evaluate_inbound(
                eval_df, client, marts, domain=domain_key
            )
            st.session_state["byod_source"] = source
            st.session_state["byod_domain"] = domain_key

    result = st.session_state.get("byod_result")
    if not result or st.session_state.get("byod_source") != source:
        return

    summary, harmo, shortage, engine = result["summary"], result["harmonized_df"], result["shortage_df"], result["engine"]
    onboard = result.get("onboarding_meta")

    if onboard:
        st.markdown(
            f"""
            <div style="background-color: #EBF3ED; border: 1px solid #C4DCCB; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 12px 18px; margin-bottom: 16px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.88rem;">🚀 ENTERPRISE CATALOG AUTO-ONBOARDED & STANDARDIZED</span>
                <div style="font-size: 0.78rem; color: #26332C; margin-top: 4px;">
                    <b>Domain</b>: {onboard['domain_label']}<br/>
                    <b>Discovered Products</b>: {onboard['products_onboarded']} distinct SKUs mapped to canonical taxonomy <code>[{onboard['canonical_taxonomy']}]</code><br/>
                    <b>Open Orders Linked</b>: {onboard['pos_synthesized']} purchase orders synchronized to regional fulfillment lines ({onboard['lines_monitored']} lines monitored).
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if engine["engine"] == "EXASOL_UDF":
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 12px 18px; margin-bottom: 16px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.88rem;">⚡ NATIVE EXASOL IN-DATABASE EXECUTION</span>
                <div style="font-size: 0.78rem; color: #26332C; margin-top: 4px;">
                    <b>Compute Location</b>: Exasol In-Memory Columnar Engine (Port 8563, Schema: <code>CHAKAN_SCM</code>)<br/>
                    <b>Executed UDFs</b>: <code>UDF_RESOLVE_SUPPLIER_SKU</code> (Jaro-Winkler &ge;0.85), <code>UDF_NORMALIZE_UOM</code> (Pack/Weight Inversion), <code>UDF_PARSE_ASN_DATE</code><br/>
                    <b>Relational Push-down</b>: Ingested batch joined directly against in-memory <code>ITEM_MASTER</code>, <code>SUPPLIER_MASTER</code>, and <code>PURCHASE_ORDER_LINES</code> without data egress.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: #FDF9E8; border: 1px solid #F5E6A3; border-left: 5px solid #D9A700; border-radius: 9px; padding: 12px 18px; margin-bottom: 16px;">
                <span style="font-weight: 700; color: #8A6A00; font-size: 0.88rem;">🟡 OFFLINE SIMULATION MIRROR ACTIVE</span>
                <div style="font-size: 0.78rem; color: #5C4700; margin-top: 4px;">
                    {engine.get('fallback_reason') or 'No live Exasol connection detected on port 8563.'} Running local Python parity logic.<br/>
                    <i>For full 35.4x in-memory speedup, boot the Exasol appliance via <code>docker compose up -d</code>.</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Impact on 48-hour starvation exposure")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Legacy ERP view (with batch)", format_inr_crore_lakh(summary["legacy_risk_with_batch_inr"]))
    c2.metric(
        "After harmonization",
        format_inr_crore_lakh(summary["net_risk_with_batch_inr"]),
        delta=f"{format_inr_crore_lakh(abs(summary['net_risk_change_vs_baseline_inr']))} "
        f"{'lower' if summary['net_risk_change_vs_baseline_inr'] < 0 else 'higher'} than baseline",
        delta_color="inverse",
    )
    c3.metric("False alarms cleared", format_inr_crore_lakh(summary["false_alarm_cleared_inr"]))
    c4.metric(
        "Batch value recovered",
        format_inr_crore_lakh(summary["batch_value_recovered_inr"]),
        help="Inbound value the legacy ETL would have rejected but the UDFs resolved.",
    )
    st.caption(
        f"Baseline without this batch: legacy {format_inr_crore_lakh(summary['baseline_legacy_risk_inr'])}, "
        f"harmonized {format_inr_crore_lakh(summary['baseline_net_risk_inr'])}. "
        "Legacy model: a row is visible only if its SKU is an exact catalog key and its UOM already equals the base UOM."
    )

    counts = summary["status_counts"]
    st.markdown(
        f"<div style='background:{COLOR_PALE_SAGE}; color:{COLOR_INK_GREEN}; border-radius:8px; padding:8px 14px; font-size:0.85rem;'>"
        + " &nbsp;|&nbsp; ".join(f"<b>{k.replace('_', ' ').title()}</b>: {v}" for k, v in counts.items())
        + f" &nbsp;|&nbsp; <b>Avg SKU confidence</b>: {summary['avg_confidence'] * 100:.1f}%</div>",
        unsafe_allow_html=True,
    )
    if counts.get("NEEDS_PLANNER_REVIEW"):
        st.info("Rows marked NEEDS PLANNER REVIEW (confidence below 0.85 or unknown part) are not counted as inbound stock.")

    if summary["threatened_lines"]:
        st.error(f"Lines still short after harmonization: {', '.join(summary['threatened_lines'])}")
    else:
        st.success("No assembly line is short after harmonization.")

    display = harmo.copy()
    if mask:
        display, _ = anonymize_frame(display)

    st.markdown("#### Line-by-line harmonization ledger")
    cols = [
        "asn_number", "supplier_id", "supplier_part_num", "resolved_part_num", "sku_match_method",
        "sku_confidence", "raw_qty", "raw_uom", "normalized_qty", "canonical_uom", "harmonized_eta_date", "status",
    ]
    st.dataframe(display[cols], use_container_width=True, height=280)

    if len(shortage):
        st.markdown("#### Components still short")
        st.dataframe(shortage, use_container_width=True, height=200)

    st.markdown("#### Exports")
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Download goods-receipt style CSV (SAP-like field names, illustrative)",
            data=generate_sap_migo_export(display),
            file_name="mangrove_goods_receipt.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with e2:
        st.download_button(
            "Download expedite review note (Markdown)",
            data=generate_expedite_manifest(summary, shortage),
            file_name="mangrove_expedite_note.md",
            mime="text/markdown",
            use_container_width=True,
        )
