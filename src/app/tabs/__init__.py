"""Operational Tab Modules for Mangrove Cockpit."""

from src.app.tabs.tab_triage import render_triage_tab
from src.app.tabs.tab_starvation import render_bom_horizon_tab
from src.app.tabs.tab_simulator import render_scenario_simulator_tab
from src.app.tabs.tab_benchmark import render_scale_benchmark_tab
from src.app.tabs.tab_financial_roi import render_financial_roi_tab
from src.app.tabs.tab_inventory import render_phantom_inventory_tab
from src.app.tabs.tab_engine_profiler import render_exasol_engine_tab

__all__ = [
    "render_triage_tab",
    "render_bom_horizon_tab",
    "render_scenario_simulator_tab",
    "render_scale_benchmark_tab",
    "render_financial_roi_tab",
    "render_phantom_inventory_tab",
    "render_exasol_engine_tab",
]
