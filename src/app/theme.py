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

        /* Main Container Spacing & Generous Breathing Room with Compact Header */
        .main .block-container {{
            max-width: 1440px !important;
            padding: 1.25rem 2.5rem 3.5rem 2.5rem !important;
        }}

        /* Column Horizontal Spacing */
        [data-testid="stHorizontalBlock"] {{
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
            transition: all 0.2s ease-in-out !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            min-height: 94px !important;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {COLOR_BRAND_ACCENT} !important;
            box-shadow: 0 4px 12px rgba(24, 61, 50, 0.08) !important;
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

        /* Tab Navigation Bar with Balanced Margins */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px !important;
            border-bottom: 1px solid {COLOR_BORDER} !important;
            padding-bottom: 3px !important;
            margin-top: 0.5rem !important;
            margin-bottom: 1.0rem !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 0.86rem !important;
            font-weight: 500 !important;
            padding: 9px 18px !important;
            color: {COLOR_TEXT_SECONDARY} !important;
            border-radius: 8px 8px 0 0 !important;
            border: none !important;
            background: transparent !important;
            transition: all 0.15s ease !important;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLOR_BRAND_PRIMARY} !important;
            background: rgba(47, 107, 79, 0.05) !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLOR_BRAND_PRIMARY} !important;
            font-weight: 700 !important;
            background: {COLOR_BRAND_SOFT} !important;
            border-bottom: 3px solid {COLOR_BRAND_PRIMARY} !important;
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

        /* Radio Buttons (Urgency Filter Pills) */
        [data-testid="stRadio"] [role="radiogroup"] {{
            gap: 8px !important;
            background-color: {COLOR_SURFACE} !important;
            border: 1px solid {COLOR_BORDER} !important;
            padding: 5px 8px !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(24, 61, 50, 0.03) !important;
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
