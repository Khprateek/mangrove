"""Sidebar Component with Deep Mangrove Navigation & Platform Telemetry."""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.data_generator.generate_all import generate_dataset
from src.exasol_engine.db_client import ChakanExasolClient


def render_sidebar(client: ChakanExasolClient, marts: dict, project_root: Path | None = None) -> None:
    """Renders the executive sidebar with branding, engine telemetry, and dataset actions."""
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    logo_path = project_root / "assets" / "logo.png"
    if not logo_path.exists():
        logo_path = project_root / "assets" / "logo.svg"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=52)
    st.sidebar.markdown(
        """
        <div style="margin-top: -4px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.12);">
            <div style="font-weight: 700; font-size: 1.25rem; color: #FFFFFF; letter-spacing: -0.3px;">Mangrove</div>
            <div style="font-size: 0.74rem; color: #A3B899; margin-top: 2px;">In-Memory SCM Defense &amp; Triage</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    telemetry = marts.get("telemetry", {})
    compute_source = marts.get("compute_source", telemetry.get("compute_source", "PANDAS_MIRROR"))
    is_live = marts.get("engine_mode") == "EXASOL_PERSONAL" and compute_source == "EXASOL_VIEWS"
    latency_ms = marts.get("query_latency_ms", telemetry.get("latency_ms", 0.0))
    total_eval = telemetry.get("total_rows_evaluated", len(marts.get("asn_lineage_mart", [])))

    status_dot = "🟢" if is_live else "🟠"
    status_label = "Exasol Personal (Live)" if is_live else "Local Analytical Mirror"
    status_color = "#6F9F78" if is_live else "#F3B05C"

    st.sidebar.markdown(
        f"""
        <div style="font-size: 0.68rem; font-weight: 700; color: #A3B899; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px;">
            PLATFORM TELEMETRY
        </div>
        <div style="background-color: #1F4D3F; border: 1px solid #2B5E4E; border-radius: 8px; padding: 12px 14px; margin-bottom: 18px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 9px; padding-bottom: 7px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                <span style="font-size: 0.74rem; color: #D1E0D7; font-weight: 600;">Engine:</span>
                <span style="font-size: 0.76rem; font-weight: 700; color: {status_color};">{status_dot} {status_label}</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px;">
                <span style="font-size: 0.74rem; color: #A3B899;">Source:</span>
                <code style="font-size: 0.70rem; color: #FFFFFF; background: rgba(0, 0, 0, 0.25); padding: 2px 6px; border-radius: 4px;">{compute_source}</code>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px;">
                <span style="font-size: 0.74rem; color: #A3B899;">Latency:</span>
                <span style="font-size: 0.76rem; font-weight: 600; color: #E8F2E5;">{latency_ms:.1f} ms</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px;">
                <span style="font-size: 0.74rem; color: #A3B899;">Evaluated:</span>
                <span style="font-size: 0.76rem; font-weight: 600; color: #FFFFFF;">{total_eval:,} rows</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 7px;">
                <span style="font-size: 0.74rem; color: #A3B899;">Schema / DSN:</span>
                <span style="font-size: 0.72rem; color: #D1E0D7; font-family: monospace;">CHAKAN_SCM:8563</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 0.74rem; color: #A3B899;">Partition Key:</span>
                <code style="font-size: 0.70rem; color: #E8F2E5; background: rgba(47, 107, 79, 0.4); border: 1px solid #336B56; padding: 2px 6px; border-radius: 4px;">internal_part_num</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
        <div style="font-size: 0.68rem; font-weight: 700; color: #A3B899; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px;">
            DATASET ACTIONS
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("⚡ Sync Monday Batch (500 Rows)", use_container_width=True):
        generate_dataset(output_dir=str(client.data_dir), extra_asns=480)
        client.bootstrap_exasol_schema_and_data()
        st.rerun()

    if st.sidebar.button("🚀 Stress Test Batch (5,000 Rows)", use_container_width=True):
        generate_dataset(output_dir=str(client.data_dir), extra_asns=4982)
        client.bootstrap_exasol_schema_and_data()
        st.rerun()

    if st.sidebar.button("↩️ Reset All Overrides", use_container_width=True):
        client.reset_planner_overrides()
        st.rerun()

    st.sidebar.markdown(
        """
        <div style="font-size: 0.68rem; font-weight: 700; color: #A3B899; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 18px; margin-bottom: 8px;">
            ARCHITECTURE SUMMARY
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar.expander("ℹ️ Problem Context & Invariants", expanded=False):
        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #E8F2E5; line-height: 1.5;">
                <b>Sub-tier MSME suppliers</b> submit dispatches with conflicting UOMs (<code>BAG_250</code>, <code>CRATE_50</code>, <code>MT</code>), SKU aliases (<code>6204ZZ</code>), and mixed dates.<br><br>
                Instead of dropping rows into dead-letter sinks, <b>Exasol Personal</b> harmonizes them in-database and ranks every anomaly by <b>Rs Production Output at Risk</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
