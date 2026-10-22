"""Mangrove: Inbound Triage & Starvation Engine on Exasol Personal.

Main Streamlit Application Entrypoint. Orchestrates components and tabs.
"""

from __future__ import annotations

from pathlib import Path
import streamlit as st
from PIL import Image

from src.app.components import (
    render_header,
    render_kpi_header,
    render_sidebar,
)
from src.app.tabs import (
    render_bom_horizon_tab,
    render_exasol_engine_tab,
    render_financial_roi_tab,
    render_phantom_inventory_tab,
    render_scale_benchmark_tab,
    render_scenario_simulator_tab,
    render_triage_tab,
)
from src.app.theme import (
    apply_dark_theme,
    format_inr_crore_lakh,
    inject_minimalist_theme,
    safe_float,
)
from src.exasol_engine.db_client import ChakanExasolClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Re-export key utilities for backward compatibility
__all__ = [
    "PROJECT_ROOT",
    "get_client",
    "main",
    "inject_minimalist_theme",
    "format_inr_crore_lakh",
    "safe_float",
    "apply_dark_theme",
]


@st.cache_resource(show_spinner=False)
def get_client() -> ChakanExasolClient:
    """Instantiate and cache the Chakan Exasol client singleton."""
    return ChakanExasolClient()


def main() -> None:
    """Main application lifecycle orchestrating layout, components, and tabs."""
    logo_path = PROJECT_ROOT / "assets" / "logo.png"
    logo = Image.open(logo_path)
    st.set_page_config(
        page_title="Mangrove",
        page_icon=logo,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_minimalist_theme()

    client = get_client()
    marts = client.compute_analytical_marts()

    render_sidebar(client, marts, project_root=PROJECT_ROOT)
    render_header(project_root=PROJECT_ROOT)
    render_kpi_header(marts, client)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "1. Inbound Triage",
            "2. Starvation Horizon",
            "3. What-If Simulator",
            "4. 10k Scale Benchmark",
            "5. Financial ROI Defense",
            "6. Phantom Inventory",
            "7. Exasol Engine & SQL",
        ]
    )

    with tab1:
        render_triage_tab(client, marts)
    with tab2:
        render_bom_horizon_tab(marts)
    with tab3:
        render_scenario_simulator_tab(client, marts)
    with tab4:
        render_scale_benchmark_tab(client, marts)
    with tab5:
        render_financial_roi_tab(client, marts)
    with tab6:
        render_phantom_inventory_tab(marts)
    with tab7:
        render_exasol_engine_tab(client, marts, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
