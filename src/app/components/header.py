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
    """Renders the compact executive Mangrove brand header with logo, title, and plant role badge."""
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]
    logo_path = project_root / "assets" / "logo.png"

    col_logo, col_title, col_meta = st.columns([0.42, 7.33, 4.25])
    with col_logo:
        if logo_path.exists():
            st.image(str(logo_path), width=38)
    with col_title:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-top: -4px;">
                <span style="font-size: 1.35rem; font-weight: 700; color: {COLOR_TEXT_PRIMARY}; letter-spacing: -0.3px;">
                    Mangrove
                </span>
                <span style="background-color: {COLOR_BRAND_SOFT}; color: {COLOR_BRAND_PRIMARY}; font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 5px; border: 1px solid #C6DBC3; letter-spacing: 0.5px;">
                    IN-MEMORY SCM DEFENSE
                </span>
            </div>
            <div style="margin-top: 1px; font-size: 0.78rem; color: {COLOR_TEXT_SECONDARY}; line-height: 1.25;">
                Real-Time In-Database Supply Chain Triage &amp; Line Starvation Engine on Exasol Personal
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_meta:
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 0px;">
                <span style="background-color: {COLOR_SURFACE}; color: {COLOR_TEXT_PRIMARY}; font-size: 0.72rem; font-weight: 600; padding: 4px 10px; border-radius: 6px; border: 1px solid {COLOR_BORDER}; white-space: nowrap; letter-spacing: 0.3px; box-shadow: 0 1px 2px rgba(24, 61, 50, 0.03);">
                    CHAKAN INDUSTRIAL CORRIDOR &bull; PLANT-1
                </span>
                <div style="font-size: 0.70rem; color: {COLOR_TEXT_SECONDARY}; margin-top: 3px;">
                    Role: Lead Inbound Materials &amp; Line-Feed Planner
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

