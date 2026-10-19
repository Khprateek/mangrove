"""Header & Engine Telemetry Status Banner Component."""

from __future__ import annotations

from pathlib import Path
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


def render_header(project_root: Path | None = None) -> None:
    """Renders the executive Mangrove brand header with logo, title, and plant role badge."""
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    logo_path = project_root / "assets" / "logo.png"
    if not logo_path.exists():
        logo_path = project_root / "assets" / "logo.svg"

    col_logo, col_title, col_meta = st.columns([0.65, 6.35, 4.0])
    with col_logo:
        if logo_path.exists():
            st.image(str(logo_path), width=52)
    with col_title:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-top: -2px;">
                <span style="font-size: 1.75rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; letter-spacing: -0.5px;">
                    Mangrove
                </span>
                <span style="background-color: {COLOR_BRAND_SOFT}; color: {COLOR_BRAND_PRIMARY}; font-size: 0.70rem; font-weight: 700; padding: 4px 10px; border-radius: 6px; border: 1px solid #C6DBC3; letter-spacing: 0.6px;">
                    IN-MEMORY SCM DEFENSE
                </span>
            </div>
            <div style="margin-top: 3px; font-size: 0.86rem; color: {COLOR_TEXT_SECONDARY}; line-height: 1.4;">
                Real-Time In-Database Supply Chain Triage &amp; Line Starvation Engine on Exasol Personal
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_meta:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 4px;">
                <span style="background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; font-size: 0.76rem; font-weight: 600; padding: 6px 12px; border-radius: 8px; border: 1px solid {COLOR_BORDER}; white-space: nowrap; letter-spacing: 0.3px; box-shadow: 0 1px 3px rgba(24, 61, 50, 0.04);">
                    CHAKAN INDUSTRIAL CORRIDOR &bull; PLANT-1
                </span>
                <div style="font-size: 0.74rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 6px;">
                    Role: Lead Inbound Materials &amp; Line-Feed Planner
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_telemetry_banner(marts: dict) -> None:
    """Renders the single-line unboxed live engine telemetry status bar."""
    telemetry = marts.get("telemetry", {})
    engine_mode = marts.get("engine_mode", "LOCAL_MIRROR")
    compute_source = marts.get("compute_source", telemetry.get("compute_source", "PANDAS_MIRROR"))
    latency_ms = float(marts.get("query_latency_ms", telemetry.get("latency_ms", 0.0)))
    total_rows = int(telemetry.get("total_rows_evaluated", len(marts.get("asn_lineage_mart", []))))
    colocation_key = telemetry.get("colocation_key", "internal_part_num")

    is_live = (engine_mode == "EXASOL_PERSONAL" and compute_source == "EXASOL_VIEWS")
    status_label = "Exasol Personal (Live In-Memory)" if is_live else "Local Analytical Mirror (Fallback)"
    status_color = COLOR_BRAND_PRIMARY if is_live else "#A66B20"
    dot_color = "#2F6B4F" if is_live else "#A66B20"

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding: 10px 0; margin-top: 8px; margin-bottom: 20px; border-top: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY};">
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 14px;">
                <span style="display: inline-flex; align-items: center; gap: 6px; font-weight: 600; color: {status_color};">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {dot_color}; box-shadow: 0 0 6px {dot_color};"></span>
                    {status_label}
                </span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span>Latency: <strong style="color: {COLOR_TEXT_PRIMARY}; font-weight: 700;">{latency_ms:.1f} ms</strong> <span style="color: {COLOR_BRAND_PRIMARY}; font-size: 0.72rem;">({compute_source})</span></span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span>Evaluated: <strong style="color: {COLOR_TEXT_PRIMARY}; font-weight: 700;">{total_rows:,} rows</strong></span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span>Partition: <code style="color: {COLOR_BRAND_PRIMARY}; background: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem;">DISTRIBUTE BY ({colocation_key})</code></span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span style="color: {COLOR_TEXT_SECONDARY};">Python 3 In-DB RAM UDFs</span>
            </div>
            <div style="font-size: 0.70rem; color: {COLOR_BRAND_PRIMARY}; font-weight: 700; letter-spacing: 0.6px;">
                SUB-SECOND MPP IN-MEMORY CO-LOCATION
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
