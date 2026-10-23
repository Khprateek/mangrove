"""Tab 8: Industrial Ingestion & Custom Bring-Your-Own-Data (BYOD) Studio.

Allows automotive planners to stress-test Mangrove with dirty CSV/Excel dispatches,
client-side anonymization, and authentic Chakan industrial presets.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_CANOPY_GREEN,
    COLOR_CARD_BG,
    COLOR_DANGER,
    COLOR_INK_GREEN,
    COLOR_PALE_SAGE,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    format_inr_crore_lakh,
)
from src.exasol_engine.custom_ingestor import (
    anonymize_dataset,
    detect_and_map_columns,
    generate_expedite_manifest,
    generate_sap_migo_export,
    get_industrial_scenario_preset,
    harmonize_and_evaluate_inbound,
    parse_custom_inbound_stream,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_byod_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Render the Industrial Ingestion and BYOD Studio."""
    # 1. Enterprise Privacy & Security Trust Banner
    st.markdown(
        f"""
        <div style="background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 12px; padding: 18px 24px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="margin: 0; color: {COLOR_BRAND_PRIMARY}; font-size: 1.25rem;">
                        🏭 Industrial Ingestion & Bring-Your-Own-Data (BYOD) Studio
                    </h3>
                    <p style="margin: 4px 0 0 0; color: {COLOR_TEXT_SECONDARY}; font-size: 0.85rem;">
                        Test dirty delivery dispatches against bill-of-materials explosion with in-memory privacy.
                    </p>
                </div>
                <div>
                    <span style="background-color: {COLOR_PALE_SAGE}; color: {COLOR_INK_GREEN}; font-weight: 700; font-size: 0.75rem; padding: 4px 10px; border-radius: 6px; border: 1px solid {COLOR_BORDER};">
                        🔒 ZERO-PERSISTENCE IN-MEMORY ISOLATION
                    </span>
                </div>
            </div>
            <p style="margin: 10px 0 0 0; color: {COLOR_TEXT_SECONDARY}; font-size: 0.8rem; line-height: 1.4;">
                <b>Data Sovereignty Guarantee</b>: Any uploaded CSV/Excel file is processed purely in volatile RAM within this browser session. 
                Zero records are persisted to disk or external servers. For corporate deployments, Mangrove deploys 100% on-premise inside your private subnet via <code>docker-compose.yml</code>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Ingestion Source Selection
    source_mode = st.radio(
        "Select Ingestion Source",
        options=[
            "Preset: Tata Motors Chakan Inbound (Mixed Packaging UOMs & OCR Suffixes)",
            "Preset: Bharat Forge Foundry (Casting Revisions & Scrap Short-Shipments)",
            "Preset: Bosch Powertrain Electronics (Epoch Timestamps & Sensor Harnesses)",
            "Upload Custom Delivery Dispatch (.CSV, .TSV, .XLSX)",
        ],
        index=0,
        horizontal=False,
    )

    raw_df: pd.DataFrame | None = None
    source_name = "TATA_CHAKAN_CORRIDOR"

    if "Tata Motors" in source_mode:
        source_name = "TATA_CHAKAN_CORRIDOR"
        raw_df = get_industrial_scenario_preset("TATA_CHAKAN_CORRIDOR")
    elif "Bharat Forge" in source_mode:
        source_name = "BHARAT_FORGE_FOUNDRY"
        raw_df = get_industrial_scenario_preset("BHARAT_FORGE_FOUNDRY")
    elif "Bosch" in source_mode:
        source_name = "BOSCH_POWERTRAIN_ELECTRONICS"
        raw_df = get_industrial_scenario_preset("BOSCH_POWERTRAIN_ELECTRONICS")
    else:
        source_name = "CUSTOM_UPLOAD"
        uploaded_file = st.file_uploader(
            "Upload Delivery Dispatch / Challan / ASN File",
            type=["csv", "tsv", "xlsx", "xls"],
            help="Upload your supplier delivery schedule or challan export. Data stays purely in-memory.",
        )
        if uploaded_file is not None:
            raw_bytes = uploaded_file.read()
            raw_df = parse_custom_inbound_stream(raw_bytes, uploaded_file.name)
        else:
            st.info("👆 Upload a CSV or Excel file to begin custom blast-radius analysis, or choose one of the industrial presets above.")

    if raw_df is not None and len(raw_df) > 0:
        st.markdown("---")

        # 3. Smart Column Mapping & Anonymization Options
        col_opts1, col_opts2 = st.columns([2, 1], gap="medium")

        with col_opts1:
            st.markdown(f"#### 📋 Raw Inbound Preview (`{len(raw_df)}` rows)")
            st.dataframe(raw_df.head(6), use_container_width=True, height=180)

        with col_opts2:
            st.markdown("#### 🛡️ Privacy & Column Controls")
            anonymize_toggle = st.checkbox(
                "🔒 Client-Side Anonymizer",
                value=False,
                help="Mask supplier names and internal codes into anonymous tokens (e.g. SUP-ANON-01, SKU-ANON-01) while preserving exact MRP graph mathematics.",
            )

            with st.expander("⚙️ Advanced Column Mapping"):
                st.caption("Auto-detected standard headers. Adjust only if necessary:")
                mapped_cols, used_mapping = detect_and_map_columns(raw_df)
                for canon, src in used_mapping.items():
                    st.text(f"• {canon} ➔ {src}")

        # Apply anonymization if selected
        dataset_to_process = raw_df
        if anonymize_toggle:
            dataset_to_process, anon_meta = anonymize_dataset(raw_df)
            st.info(f"🛡️ Data Anonymized: {anon_meta['anonymized_suppliers_count']} suppliers and {anon_meta['anonymized_skus_count']} SKUs mapped to privacy tokens.")

        # 4. In-Database Harmonization Trigger
        if st.button("⚡ Execute In-Database Harmonization & Blast Radius Engine", type="primary", use_container_width=True):
            with st.spinner("Executing Python UDFs & BOM explosion..."):
                results = harmonize_and_evaluate_inbound(dataset_to_process, client)
                st.session_state["byod_results"] = results
                st.session_state["byod_source"] = source_name

        # 5. Display Harmonization Results if Available
        if "byod_results" in st.session_state:
            res = st.session_state["byod_results"]
            summary = res["summary"]
            harmo_df = res["harmonized_df"]
            shortage_df = res["shortage_df"]

            st.markdown("---")
            st.markdown("### 📊 Operational Triage & Blast Radius Summary")

            # KPI Metric Banner
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Total Inbound Value", format_inr_crore_lakh(summary["total_shipped_value_inr"]))
            with m_col2:
                st.metric("False Alarms Cleared", format_inr_crore_lakh(summary["false_alarms_cleared_inr"]), delta="Cleared by UDFs")
            with m_col3:
                net_short = summary["net_shortage_deficit_inr"]
                st.metric("Net Shortage Deficit", format_inr_crore_lakh(net_short), delta=f"-{format_inr_crore_lakh(net_short)}" if net_short > 0 else "Fully Stocked", delta_color="inverse")
            with m_col4:
                st.metric("Avg Resolution Confidence", f"{summary['avg_confidence'] * 100:.1f}%", help="Calculated via Jaro-Winkler metric across all lines.")

            # Threatened Lines Alert
            threatened = summary.get("threatened_lines", [])
            if threatened:
                st.error(
                    f"🚨 **Catastrophic Starvation Warning**: Assembly lines **{', '.join(threatened)}** face critical component deficits! "
                    f"Total Stoppage Exposure: **{format_inr_crore_lakh(summary['total_stoppage_exposure_inr'])}**."
                )
            else:
                st.success("✅ **Zero Line Starvations**: Inbound shipments and True ATP physical stock satisfy all active assembly schedules!")

            # Detailed Harmonization Grid
            st.markdown("#### 🔍 Line-by-Line In-Database Harmonization Ledger")
            display_cols = [
                "asn_number",
                "supplier_id",
                "supplier_part_num",
                "resolved_part_num",
                "sku_match_method",
                "sku_confidence",
                "raw_qty",
                "raw_uom",
                "normalized_qty",
                "normalized_uom",
                "status",
            ]
            st.dataframe(harmo_df[display_cols], use_container_width=True, height=240)

            # 6. Actionable 1-Click Exports
            st.markdown("#### 📤 Actionable Operational Exports")
            exp_col1, exp_col2 = st.columns(2)

            with exp_col1:
                sap_csv = generate_sap_migo_export(harmo_df)
                st.download_button(
                    "📥 Download SAP MIGO / ME21N Clean Inbound Feed (CSV)",
                    data=sap_csv,
                    file_name="mangrove_sap_migo_cleared.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with exp_col2:
                expedite_txt = generate_expedite_manifest(summary, shortage_df)
                st.download_button(
                    "📄 Download Emergency Supplier Expedite Directive (MD)",
                    data=expedite_txt,
                    file_name="mangrove_emergency_expedite_directive.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
