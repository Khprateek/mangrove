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
    COLOR_CARD_BG,
    COLOR_INK_GREEN,
    COLOR_PALE_SAGE,
    COLOR_TEXT_SECONDARY,
    format_inr_crore_lakh,
)
from src.exasol_engine.custom_ingestor import (
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
            <h3 style="margin:0; color:{COLOR_BRAND_PRIMARY}; font-size:1.2rem;">Bring-Your-Own-Data Inbound Studio</h3>
            <p style="margin:4px 0 0 0; color:{COLOR_TEXT_SECONDARY}; font-size:0.85rem;">
                Your batch is layered on top of the baseline ASN feed, so the numbers below are directly comparable with Tabs 1-7.
                An empty batch reproduces the baseline exactly.
            </p>
            <p style="margin:8px 0 0 0; color:{COLOR_TEXT_SECONDARY}; font-size:0.78rem;">
                <b>Privacy:</b> files are processed in memory for this session only and are never written to disk by the app.
                With a live Exasol connection the rows are staged in a scratch table that is dropped immediately afterwards.
                Presets below use only synthetic suppliers and parts.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    source = st.radio("Inbound source", options=[*PRESET_LABELS.values(), UPLOAD_OPTION], index=0)

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
        with st.expander("Detected column mapping"):
            _, used = detect_and_map_columns(raw_df)
            if used:
                for canon, src in used.items():
                    st.text(f"{canon}  <-  {src}")
            else:
                st.text("No headers matched; defaults applied.")

    if st.button("Harmonize batch and evaluate impact", type="primary", use_container_width=True):
        with st.spinner("Running SKU resolution, UOM normalization and date parsing..."):
            st.session_state["byod_result"] = harmonize_and_evaluate_inbound(raw_df, client, marts)
            st.session_state["byod_source"] = source

    result = st.session_state.get("byod_result")
    if not result or st.session_state.get("byod_source") != source:
        return

    summary, harmo, shortage, engine = result["summary"], result["harmonized_df"], result["shortage_df"], result["engine"]

    if engine["engine"] == "EXASOL_UDF":
        st.success("Executed inside Exasol: the three Python UDFs ran against a scratch staging table.")
    else:
        st.warning(f"Engine: local UDF-parity logic. {engine.get('fallback_reason') or ''}")

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
