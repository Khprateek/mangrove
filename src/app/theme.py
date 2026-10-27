"""Mangrove Forest Design System, Theme Tokens & Styling Utilities.

Implements the official Mangrove Forest palette:
- Deep Mangrove (#183D32): Navigation, sidebar, dark structure
- Forest Green (#2F6B4F): Primary buttons, active tabs, links, primary highlights
- Canopy Green (#6F9F78): Secondary highlights, chart accents
- Pale Sage (#E8F2E5): Positive KPI cards, subtle status backgrounds
- Mangrove Mist (#F7F8F4): Main canvas background
- Clean White (#FFFFFF): Elevated cards, panels, dataframes
- Soft Stone (#E2E7E0 / #E7EBE5): Dividers, subtle borders, neutral cards
- Ink Green (#26332C): Primary text, headings, numbers
- Moss Grey (#68756B): Secondary labels, captions, metadata
"""

from __future__ import annotations

from typing import Any
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Color Constants
COLOR_BRAND_PRIMARY = "#2F6B4F"
COLOR_BRAND_DARK = "#183D32"
COLOR_BRAND_ACCENT = "#6F9F78"
COLOR_BRAND_SOFT = "#E8F2E5"

COLOR_BACKGROUND = "#F7F8F4"
COLOR_SURFACE = "#FFFFFF"
COLOR_SURFACE_MUTED = "#F0F2ED"
COLOR_BORDER = "#E2E7E0"
COLOR_BORDER_LIGHT = "#E7EBE5"

COLOR_TEXT_PRIMARY = "#26332C"
COLOR_TEXT_SECONDARY = "#68756B"
COLOR_TEXT_INVERSE = "#FFFFFF"

COLOR_SUCCESS = "#2F6B4F"
COLOR_WARNING = "#A66B20"
COLOR_DANGER = "#B54747"

# Semantic Aliases for Mangrove Forest Palette
COLOR_CANOPY_GREEN = COLOR_BRAND_ACCENT
COLOR_PALE_SAGE = COLOR_BRAND_SOFT
COLOR_INK_GREEN = COLOR_TEXT_PRIMARY
COLOR_MOSS_GREY = COLOR_TEXT_SECONDARY
COLOR_CARD_BG = COLOR_SURFACE_MUTED

# Universal High-Contrast Chart Palette (Benchmark Harmonized)
COLOR_CHART_PRIMARY = "#2F6B4F"    # Deep Pine Green (Active, True ATP, Exasol, Mitigated)
COLOR_CHART_SECONDARY = "#8E9E93"  # Neutral Slate Stone Grey (Baseline, Legacy ETL, Python ETL, Book Stock)
COLOR_CHART_ACCENT = "#B54747"     # Distinct Brick Red (Critical Alert, Shortage, Deficit, Speedup Line)
COLOR_CHART_MUTED = "#B8C7BD"      # Soft Pale Slate (Auxiliary / Secondary Allocations)



def inject_minimalist_theme() -> None:
    """Injects the complete Mangrove Forest design system into Streamlit."""
    st.markdown(
        f"""
        <style>
        /* CSS Root Tokens */
        :root {{
            --color-brand-primary: {COLOR_BRAND_PRIMARY};
            --color-brand-dark: {COLOR_BRAND_DARK};
            --color-brand-accent: {COLOR_BRAND_ACCENT};
            --color-brand-soft: {COLOR_BRAND_SOFT};

            --color-background: {COLOR_BACKGROUND};
            --color-surface: {COLOR_SURFACE};
            --color-surface-muted: {COLOR_SURFACE_MUTED};
            --color-border: {COLOR_BORDER};

            --color-text-primary: {COLOR_TEXT_PRIMARY};
            --color-text-secondary: {COLOR_TEXT_SECONDARY};
            --color-text-inverse: {COLOR_TEXT_INVERSE};

            --color-success: {COLOR_SUCCESS};
            --color-warning: {COLOR_WARNING};
            --color-danger: {COLOR_DANGER};
        }}

        /* Global Typography Standard */
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            background-color: {COLOR_BACKGROUND} !important;
        }}

        /* Main Container Spacing & Generous Breathing Room */
        .main .block-container {{
            max-width: 1440px !important;
            padding: 1.5rem 2.5rem 4rem 2.5rem !important;
        }}

        /* Column Horizontal Spacing */
        [data-testid="stHorizontalBlock"] {{
            gap: 1.25rem !important;
        }}

        /* Vertical Block Rhythm */
        [data-testid="stVerticalBlock"] {{
            gap: 1.15rem !important;
        }}

        /* Standardize Headings & Spacing */
        h1 {{
            font-size: 1.70rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0.5rem !important;
        }}
        h2 {{
            font-size: 1.25rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.015em !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            margin-top: 1.75rem !important;
            margin-bottom: 0.75rem !important;
        }}
        h3, [data-testid="stSubheader"] {{
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.01em !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.6rem !important;
        }}
        [data-testid="stCaptionContainer"] {{
            color: {COLOR_TEXT_SECONDARY} !important;
            font-size: 0.84rem !important;
            line-height: 1.45 !important;
            margin-top: -0.25rem !important;
            margin-bottom: 1.25rem !important;
        }}

        /* Dividers */
        hr {{
            border: none !important;
            border-top: 1px solid {COLOR_BORDER} !important;
            margin: 1.25rem 0 !important;
        }}

        /* Elevated Clean White Metric Cards with Compact Footprint */
        [data-testid="stMetric"] {{
            background-color: {COLOR_SURFACE} !important;
            border: 1px solid {COLOR_BORDER} !important;
            border-radius: 12px !important;
            padding: 12px 18px !important;
            box-shadow: 0 1px 3px rgba(24, 61, 50, 0.03) !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            min-height: 94px !important;
            cursor: pointer !important;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {COLOR_BRAND_PRIMARY} !important;
            background: linear-gradient(180deg, #FFFFFF 0%, #E8F2E5 100%) !important;
            box-shadow: 0 6px 18px rgba(47, 107, 79, 0.12) !important;
            transform: translateY(-2px) !important;
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            color: {COLOR_TEXT_SECONDARY} !important;
            margin-bottom: 4px !important;
            white-space: normal !important;
            word-wrap: break-word !important;
        }}
        [data-testid="stMetricLabel"] > div {{
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow: visible !important;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            line-height: 1.15 !important;
        }}
        [data-testid="stMetricDelta"] {{
            font-size: 0.76rem !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            margin-top: 4px !important;
        }}

        /* Sidebar: Deep Mangrove Forest Styling */
        [data-testid="stSidebar"] {{
            background-color: {COLOR_BRAND_DARK} !important;
            border-right: 1px solid #14352B !important;
        }}
        [data-testid="stSidebar"] * {{
            color: #FFFFFF;
        }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
            gap: 0.85rem !important;
            padding: 1.5rem 1rem !important;
        }}
        [data-testid="stSidebar"] .stButton > button {{
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            padding: 9px 14px !important;
            border-radius: 8px !important;
            border: 1px solid #2A5A4A !important;
            background-color: #204B3E !important;
            color: #FFFFFF !important;
            transition: all 0.15s ease-in-out !important;
            width: 100% !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            border-color: {COLOR_BRAND_PRIMARY} !important;
            background-color: {COLOR_BRAND_PRIMARY} !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        }}
        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            background-color: #14352B !important;
            border: 1px solid #2A5A4A !important;
            border-radius: 8px !important;
        }}

        /* Buttons in Main Area */
        button[kind="primary"] {{
            background-color: {COLOR_BRAND_PRIMARY} !important;
            border-color: {COLOR_BRAND_PRIMARY} !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: 9px 20px !important;
            box-shadow: 0 1px 3px rgba(47, 107, 79, 0.2) !important;
            transition: all 0.15s ease-in-out !important;
        }}
        button[kind="primary"]:hover {{
            background-color: #245840 !important;
            border-color: #245840 !important;
            box-shadow: 0 3px 8px rgba(47, 107, 79, 0.3) !important;
        }}
        button[kind="secondary"] {{
            background-color: {COLOR_SURFACE} !important;
            border: 1px solid {COLOR_BORDER} !important;
            color: {COLOR_TEXT_PRIMARY} !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: 9px 20px !important;
        }}
        button[kind="secondary"]:hover {{
            border-color: {COLOR_BRAND_PRIMARY} !important;
            color: {COLOR_BRAND_PRIMARY} !important;
            background-color: {COLOR_BRAND_SOFT} !important;
        }}

        /* -------------------------------------------------------------------------
           STREAMLIT TAB NAVIGATION: ENCLOSED PILL CAPSULE TRACK (ALL VERSIONS)
           ------------------------------------------------------------------------- */

        /* 1. Eliminate Default Underlines, Borders and Overflow Scroll Buttons */
        [data-testid="stTabs"] [role="tablist"]::after,
        .stTabs [role="tablist"]::after,
        [data-testid="stTab"] .react-aria-SelectionIndicator,
        button[role="tab"] .react-aria-SelectionIndicator,
        [data-testid="stTabsScrollLeft"],
        [data-testid="stTabsScrollRight"],
        .stTabs [data-baseweb="tab-highlight"],
        .stTabs [data-baseweb="tab-border"] {{
            display: none !important;
            height: 0 !important;
            width: 0 !important;
            visibility: hidden !important;
            opacity: 0 !important;
            background: transparent !important;
            pointer-events: none !important;
        }}

        /* 2. Outer Enclosed Capsule Track - Responsive Full Width */
        [data-testid="stTabs"] [role="tablist"],
        .stTabs [role="tablist"],
        [data-testid="stTabs"] > div > div:first-child,
        .stTabs [data-baseweb="tab-list"] {{
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: space-between !important;
            background-color: #FFFFFF !important;
            border: 1px solid #D5DCD4 !important;
            border-radius: 12px !important;
            padding: 3px 4px !important;
            gap: 2px !important;
            box-shadow: 0 1px 4px rgba(24, 61, 50, 0.04) !important;
            margin-top: 1.0rem !important;
            margin-bottom: 1.25rem !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }}

        /* 3. Base Tab Buttons - Compact & Proportional */
        [data-testid="stTab"],
        button[role="tab"],
        .stTabs [data-baseweb="tab"] {{
            display: inline-flex !important;
            flex: 1 1 auto !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 0.77rem !important;
            font-weight: 500 !important;
            padding: 6px 10px !important;
            color: #68756B !important;
            border-radius: 8px !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
            cursor: pointer !important;
            white-space: nowrap !important;
            height: auto !important;
            min-height: 32px !important;
            position: relative !important;
            outline: none !important;
            box-sizing: border-box !important;
        }}

        /* 4. Tab Inactive Hover */
        [data-testid="stTab"]:not([aria-selected="true"]):not([data-selected="true"]):hover,
        button[role="tab"]:not([aria-selected="true"]):not([data-selected="true"]):hover,
        .stTabs [data-baseweb="tab"]:not([aria-selected="true"]):hover {{
            color: {COLOR_BRAND_PRIMARY} !important;
            background-color: #F4F7F3 !important;
            border-color: #E2E8E0 !important;
        }}

        /* 5. Active Tab (Elevated Pale Sage Chip matching Image Reference) */
        [data-testid="stTab"][aria-selected="true"],
        [data-testid="stTab"][data-selected="true"],
        button[role="tab"][aria-selected="true"],
        button[role="tab"][data-selected="true"],
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            color: #1E4D38 !important;
            font-weight: 700 !important;
            background-color: #E2EFE5 !important;
            border: 1px solid #BED8C5 !important;
            border-bottom: 2px solid #2F6B4F !important;
            box-shadow: 0 1px 3px rgba(47, 107, 79, 0.10) !important;
        }}
        [data-testid="stTab"][aria-selected="true"] p,
        [data-testid="stTab"][data-selected="true"] p,
        [data-testid="stTab"][aria-selected="true"] span,
        [data-testid="stTab"][data-selected="true"] span,
        button[role="tab"][aria-selected="true"] p,
        button[role="tab"][data-selected="true"] p,
        .stTabs [data-baseweb="tab"][aria-selected="true"] p {{
            color: #1E4D38 !important;
            font-weight: 700 !important;
        }}

        /* 6. Subtle Vertical Divider Between Inactive Adjacent Tabs */
        [data-testid="stTab"]:not([aria-selected="true"]):not([data-selected="true"]) + [data-testid="stTab"]:not([aria-selected="true"]):not([data-selected="true"])::before,
        button[role="tab"]:not([aria-selected="true"]):not([data-selected="true"]) + button[role="tab"]:not([aria-selected="true"]):not([data-selected="true"])::before,
        .stTabs [data-baseweb="tab"]:not([aria-selected="true"]) + .stTabs [data-baseweb="tab"]:not([aria-selected="true"])::before {{
            content: "" !important;
            position: absolute !important;
            left: -2px !important;
            top: 25% !important;
            height: 50% !important;
            width: 1px !important;
            background-color: #DDE3DC !important;
            pointer-events: none !important;
        }}

        /* 7. Tab Panel Buffer */
        [data-testid="stTabPanel"],
        .stTabs [data-baseweb="tab-panel"] {{
            padding-top: 0.85rem !important;
            padding-bottom: 1.5rem !important;
        }}

        /* Tab Vector Outline Icons - Compact Footprint */
        [data-testid="stTab"] p,
        button[role="tab"] p,
        .stTabs [data-baseweb="tab"] p {{
            display: inline-flex !important;
            align-items: center !important;
            margin: 0 !important;
            line-height: 1.2 !important;
            font-size: 0.77rem !important;
        }}
        [data-testid="stTab"] p::before,
        button[role="tab"] p::before,
        .stTabs [data-baseweb="tab"] p::before {{
            content: "" !important;
            display: inline-block !important;
            width: 14px !important;
            height: 14px !important;
            margin-right: 5px !important;
            background-size: contain !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            flex-shrink: 0 !important;
        }}
        /* Tab 1: Inbound Triage (Inbox/Tray) */
        [data-testid="stTab"]:nth-child(1) p::before,
        button[role="tab"]:nth-child(1) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(1) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-6l-2 3h-4l-2-3H2'/%3E%3Cpath d='M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(1)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(1)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(1)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(1)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(1)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 12h-6l-2 3h-4l-2-3H2'/%3E%3Cpath d='M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z'/%3E%3C/svg%3E") !important;
        }}
        /* Tab 2: Inventory & Starvation Horizon (Hierarchy Tree) */
        [data-testid="stTab"]:nth-child(2) p::before,
        button[role="tab"]:nth-child(2) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(2) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='5' r='3'/%3E%3Ccircle cx='6' cy='19' r='3'/%3E%3Ccircle cx='18' cy='19' r='3'/%3E%3Cpath d='M12 8v4'/%3E%3Cpath d='M6 16v-1a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v1'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(2)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(2)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(2)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(2)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(2)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='5' r='3'/%3E%3Ccircle cx='6' cy='19' r='3'/%3E%3Ccircle cx='18' cy='19' r='3'/%3E%3Cpath d='M12 8v4'/%3E%3Cpath d='M6 16v-1a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v1'/%3E%3C/svg%3E") !important;
        }}
        /* Tab 3: What-If Simulator (Sliders/Sliders-H) */
        [data-testid="stTab"]:nth-child(3) p::before,
        button[role="tab"]:nth-child(3) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(3) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='4' y1='21' x2='4' y2='14'/%3E%3Cline x1='4' y1='10' x2='4' y2='3'/%3E%3Cline x1='12' y1='21' x2='12' y2='12'/%3E%3Cline x1='12' y1='8' x2='12' y2='3'/%3E%3Cline x1='20' y1='21' x2='20' y2='16'/%3E%3Cline x1='20' y1='12' x2='20' y2='3'/%3E%3Cline x1='1' y1='14' x2='7' y2='14'/%3E%3Cline x1='9' y1='8' x2='15' y2='8'/%3E%3Cline x1='17' y1='16' x2='23' y2='16'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(3)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(3)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(3)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(3)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(3)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='4' y1='21' x2='4' y2='14'/%3E%3Cline x1='4' y1='10' x2='4' y2='3'/%3E%3Cline x1='12' y1='21' x2='12' y2='12'/%3E%3Cline x1='12' y1='8' x2='12' y2='3'/%3E%3Cline x1='20' y1='21' x2='20' y2='16'/%3E%3Cline x1='20' y1='12' x2='20' y2='3'/%3E%3Cline x1='1' y1='14' x2='7' y2='14'/%3E%3Cline x1='9' y1='8' x2='15' y2='8'/%3E%3Cline x1='17' y1='16' x2='23' y2='16'/%3E%3C/svg%3E") !important;
        }}
        /* Tab 4: 10k Scale Benchmark (Stopwatch Timer) */
        [data-testid="stTab"]:nth-child(4) p::before,
        button[role="tab"]:nth-child(4) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(4) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='13' r='8'/%3E%3Cpath d='M12 9v4l2 2'/%3E%3Cpath d='M10 2h4'/%3E%3Cpath d='M18 6l1.5-1.5'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(4)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(4)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(4)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(4)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(4)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='13' r='8'/%3E%3Cpath d='M12 9v4l2 2'/%3E%3Cpath d='M10 2h4'/%3E%3Cpath d='M18 6l1.5-1.5'/%3E%3C/svg%3E") !important;
        }}
        /* Tab 5: Financial ROI Defense (Bar Chart) */
        [data-testid="stTab"]:nth-child(5) p::before,
        button[role="tab"]:nth-child(5) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(5) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(5)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(5)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(5)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(5)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(5)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='20' x2='18' y2='10'/%3E%3Cline x1='12' y1='20' x2='12' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='14'/%3E%3C/svg%3E") !important;
        }}
        /* Tab 6: Exasol Engine & SQL (Settings Gear / Database Engine) */
        [data-testid="stTab"]:nth-child(6) p::before,
        button[role="tab"]:nth-child(6) p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(6) p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2368756B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
        }}
        [data-testid="stTab"]:nth-child(6)[aria-selected="true"] p::before,
        [data-testid="stTab"]:nth-child(6)[data-selected="true"] p::before,
        button[role="tab"]:nth-child(6)[aria-selected="true"] p::before,
        button[role="tab"]:nth-child(6)[data-selected="true"] p::before,
        .stTabs [data-baseweb="tab"]:nth-of-type(6)[aria-selected="true"] p::before {{
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E4D38' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3Cpath d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z'/%3E%3C/svg%3E") !important;
        }}

        /* Dataframe & Tables with Proper Padding */
        [data-testid="stDataFrame"] {{
            border: 1px solid {COLOR_BORDER} !important;
            border-radius: 10px !important;
            background-color: {COLOR_SURFACE} !important;
            box-shadow: 0 1px 4px rgba(24, 61, 50, 0.03) !important;
            margin-top: 0.85rem !important;
            margin-bottom: 1.5rem !important;
        }}

        /* Expanders in Main Area */
        [data-testid="stExpander"] {{
            border: 1px solid {COLOR_BORDER} !important;
            border-radius: 10px !important;
            background-color: {COLOR_SURFACE} !important;
            box-shadow: 0 1px 4px rgba(24, 61, 50, 0.03) !important;
            margin-bottom: 1.25rem !important;
        }}

        /* Segmented Radio Filter Pills (Clean, Modern, Uncongested) */
        [data-testid="stRadio"] [role="radiogroup"] {{
            gap: 6px !important;
            background-color: #F4F6F2 !important;
            border: 1px solid #DCE3DB !important;
            padding: 4px 6px !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }}
        [data-testid="stRadio"] [role="radiogroup"] label {{
            border-radius: 6px !important;
            padding: 4px 10px !important;
            transition: all 0.15s ease !important;
        }}

        /* Selectboxes & Inputs */
        [data-testid="stSelectbox"] {{
            margin-top: 4px !important;
            margin-bottom: 12px !important;
        }}
        [data-baseweb="select"] {{
            border-radius: 8px !important;
        }}
        [data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid #C6DBC3 !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 3px rgba(24, 61, 50, 0.05) !important;
        }}
        [data-baseweb="select"] div,
        [data-baseweb="select"] span,
        [data-baseweb="select"] p {{
            color: #26332C !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
        }}
        [data-baseweb="select"] svg {{
            fill: #2F6B4F !important;
        }}
        /* Dropdown Popover Menu */
        [data-baseweb="popover"],
        [data-baseweb="menu"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #C6DBC3 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 16px rgba(24, 61, 50, 0.12) !important;
        }}
        [data-baseweb="menu"] li {{
            color: #26332C !important;
            font-size: 0.85rem !important;
            padding: 8px 12px !important;
        }}
        [data-baseweb="menu"] li:hover,
        [data-baseweb="menu"] li[aria-selected="true"] {{
            background-color: #E8F2E5 !important;
            color: #2F6B4F !important;
        }}

        /* Sliders */
        [data-testid="stSlider"] {{
            padding-top: 0.6rem !important;
            padding-bottom: 0.6rem !important;
        }}

        /* Custom Mangrove Presentation Tiles */
        .mangrove-tile {{
            background-color: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-radius: 12px;
            padding: 18px 20px;
            height: 100%;
            box-shadow: 0 1px 4px rgba(24, 61, 50, 0.03);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .mangrove-tile-highlight {{
            background-color: {COLOR_BRAND_SOFT};
            border: 1px solid #C6DBC3;
            border-radius: 12px;
            padding: 18px 20px;
            height: 100%;
            box-shadow: 0 1px 4px rgba(24, 61, 50, 0.03);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .mangrove-tile-title {{
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: {COLOR_TEXT_SECONDARY};
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid {COLOR_BORDER};
        }}
        .mangrove-tile-title-green {{
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: {COLOR_BRAND_PRIMARY};
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #C6DBC3;
        }}
        .mangrove-tile-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.82rem;
            margin-bottom: 7px;
        }}
        .mangrove-tile-label {{
            color: {COLOR_TEXT_SECONDARY};
        }}
        .mangrove-tile-val {{
            color: {COLOR_TEXT_PRIMARY};
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_float(val: Any) -> float:
    """Defensively coerce any value into a float, returning 0.0 on NaN or error."""
    if val is None or pd.isna(val):
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def format_inr_crore_lakh(amount_inr: Any) -> str:
    """Format numeric Indian Rupee amounts into Cr / L / Rs notation."""
    val = safe_float(amount_inr)
    if val >= 10_000_000:
        return f"Rs {val / 10_000_000:.2f} Cr"
    if val >= 100_000:
        return f"Rs {val / 100_000:.2f} L"
    return f"Rs {val:,.0f}"


def apply_mangrove_theme(fig: go.Figure, height: int = 400) -> go.Figure:
    """Applies a clean, high-precision Mangrove Forest aesthetic across all Plotly visualizations."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        colorway=[COLOR_CHART_PRIMARY, COLOR_CHART_SECONDARY, COLOR_CHART_ACCENT, COLOR_CHART_MUTED],
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            color=COLOR_TEXT_PRIMARY,
            size=11,
        ),
        xaxis=dict(
            gridcolor=COLOR_BORDER_LIGHT,
            zerolinecolor=COLOR_BORDER,
            showline=True,
            linecolor=COLOR_BORDER,
            tickfont=dict(color=COLOR_TEXT_SECONDARY, size=10),
            title_font=dict(color=COLOR_TEXT_PRIMARY, size=11),
        ),
        yaxis=dict(
            gridcolor=COLOR_BORDER_LIGHT,
            zerolinecolor=COLOR_BORDER,
            showline=True,
            linecolor=COLOR_BORDER,
            tickfont=dict(color=COLOR_TEXT_SECONDARY, size=10),
            title_font=dict(color=COLOR_TEXT_PRIMARY, size=11),
        ),
        height=height,
        margin=dict(l=36, r=20, t=28, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=COLOR_TEXT_SECONDARY),
        ),
    )
    return fig


# Backward compatibility alias
apply_dark_theme = apply_mangrove_theme
