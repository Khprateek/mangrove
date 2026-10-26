"""End-to-End Application Smoke & UI Integration Test Suite."""

from __future__ import annotations

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from src.app.theme import (
    COLOR_BRAND_PRIMARY,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    format_inr_crore_lakh,
    safe_float,
)
from src.app.components import (
    render_feedback_hub_section,
    render_header,
    render_kpi_header,
    render_perspective_switcher,
    render_sidebar,
    render_telemetry_banner,
    render_visual_audit_ledger,
)
from src.app.tabs import (
    render_bom_horizon_tab,
    render_byod_tab,
    render_exasol_engine_tab,
    render_financial_roi_tab,
    render_phantom_inventory_tab,
    render_scale_benchmark_tab,
    render_scenario_simulator_tab,
    render_triage_tab,
)


def test_theme_tokens_and_formatting_utilities() -> None:
    """Verifies color tokens and financial formatting helpers."""
    assert COLOR_BRAND_PRIMARY == "#2F6B4F"
    assert COLOR_DANGER == "#B54747"
    assert COLOR_TEXT_PRIMARY == "#26332C"

    # Numeric coercion & formatting
    assert safe_float("123.45") == 123.45
    assert safe_float(None) == 0.0
    assert safe_float("invalid") == 0.0

    assert format_inr_crore_lakh(378_800_000) == "Rs 37.88 Cr"
    assert format_inr_crore_lakh(52_900_000) == "Rs 5.29 Cr"
    assert format_inr_crore_lakh(135_000) == "Rs 1.35 L"
    assert format_inr_crore_lakh(45_000) == "Rs 45,000"


def test_component_exports_and_callables() -> None:
    """Ensures all reusable UI components export valid render callables."""
    components = [
        render_header,
        render_telemetry_banner,
        render_perspective_switcher,
        render_kpi_header,
        render_sidebar,
        render_visual_audit_ledger,
        render_feedback_hub_section,
    ]
    for comp_fn in components:
        assert callable(comp_fn), f"{comp_fn.__name__} must be a callable function"


def test_tab_module_exports_and_callables() -> None:
    """Ensures all 8 domain tab modules export valid render callables."""
    tab_callables = [
        render_triage_tab,
        render_bom_horizon_tab,
        render_scenario_simulator_tab,
        render_scale_benchmark_tab,
        render_financial_roi_tab,
        render_phantom_inventory_tab,
        render_exasol_engine_tab,
        render_byod_tab,
    ]
    for tab_fn in tab_callables:
        assert callable(tab_fn), f"{tab_fn.__name__} must be a callable function"


def test_streamlit_cockpit_headless_execution() -> None:
    """E2E Smoke Test: Executes the complete Streamlit Cockpit app entrypoint.
    
    Verifies that all components, KPI headers, tabs, charts, and data tables
    render in headless mode with zero unhandled exceptions.
    """
    app_path = Path(__file__).resolve().parents[1] / "src" / "app" / "app.py"
    assert app_path.exists(), f"App entrypoint not found at {app_path}"

    from src.app.app import get_client, main

    # 1. Verify client singleton initializes and analytical marts are populated
    client = get_client()
    assert client is not None
    marts = client.compute_analytical_marts()
    required_marts = [
        "inventory_mart",
        "asn_lineage_mart",
        "bom_risk_mart",
        "financial_roi_mart",
        "triage_queue",
    ]
    for m in required_marts:
        assert m in marts, f"Required mart '{m}' missing from engine output"

    # 2. Execute main() lifecycle end-to-end (all 8 tabs and components)
    try:
        main()
    except Exception as exc:
        pytest.fail(f"Cockpit main() headless execution raised unhandled exception: {exc}")


def test_perspective_switcher_toggle_lifecycle() -> None:
    """Verifies that selecting perspective options toggles perspective mode cleanly
    without unhandled exceptions.
    """
    from unittest.mock import patch
    import streamlit as st
    from src.app.components.perspective_switcher import (
        MODE_LEGACY,
        MODE_MANGROVE,
        activate_legacy_mode,
        activate_mangrove_mode,
        render_perspective_switcher,
    )

    state_mock = {}
    with patch.object(st, "session_state", state_mock):
        # 1. Test state callback lifecycle
        activate_legacy_mode()
        assert state_mock.get("engine_perspective_mode") == MODE_LEGACY

        activate_mangrove_mode()
        assert state_mock.get("engine_perspective_mode") == MODE_MANGROVE

    # 2. Test switcher render callable in both states
    try:
        with patch.object(st, "radio", return_value=MODE_LEGACY):
            res_legacy = render_perspective_switcher()
            assert res_legacy == "TRADITIONAL_ERP"

        with patch.object(st, "radio", return_value=MODE_MANGROVE):
            res_mangrove = render_perspective_switcher()
            assert res_mangrove == "MANGROVE_ACTIVE"
    except Exception as exc:
        pytest.fail(f"Perspective switcher lifecycle raised an unhandled exception: {exc}")



