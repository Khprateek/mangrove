"""UI Components for Mangrove Cockpit."""

from src.app.components.audit_ledger import render_visual_audit_ledger
from src.app.components.header import render_header, render_telemetry_banner
from src.app.components.kpi_header import render_kpi_header
from src.app.components.perspective_switcher import (
    activate_legacy_mode,
    activate_mangrove_mode,
    render_perspective_switcher,
)
from src.app.components.sidebar import render_sidebar

__all__ = [
    "activate_legacy_mode",
    "activate_mangrove_mode",
    "render_header",
    "render_telemetry_banner",
    "render_kpi_header",
    "render_perspective_switcher",
    "render_sidebar",
    "render_visual_audit_ledger",
]
