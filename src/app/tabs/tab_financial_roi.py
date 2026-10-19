"""Financial ROI & Line-Stop Defense Tab Module for Mangrove Cockpit."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    apply_mangrove_theme,
    format_inr_crore_lakh,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_financial_roi_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Render Tab 5: Formulation 3 Boardroom Financial Defense & Line-Stop ROI Engine."""
    roi = marts.get("financial_roi_mart", {})
    bom_df: pd.DataFrame = marts["bom_risk_mart"].copy()
    triage_df: pd.DataFrame = marts["triage_queue"].copy()

    st.subheader("Formulation 3: Boardroom Financial Defense & Line-Stop ROI Engine")
    st.caption(
        "Quantifies the business case for Exasol: weighing the severe penalty of unmitigated plant downtime "
        "and unproduced vehicle output against low-cost emergency logistics."
    )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric(
        "Total Inaction Stoppage Loss",
        format_inr_crore_lakh(roi.get("total_stoppage_exposure_inr", 0)),
        f"{format_inr_crore_lakh(roi.get('net_risk_inr', 0))} Goods + {format_inr_crore_lakh(roi.get('total_idle_loss_inr', 0))} Idle",
        delta_color="inverse",
    )
    r2.metric(
        "Emergency Mitigation Freight",
        format_inr_crore_lakh(roi.get("benchmark_freight_inr", 45000)),
        "Dedicated Hot-Shot Transport Run",
    )
    r3.metric(
        "Executive Mitigation ROI",
        f"{roi.get('headline_roi_x', 1175):,.0f}x Return",
        "Averted Factory Stoppage / Freight",
    )
    r4.metric(
        "Avoided Panic Freight Waste",
        format_inr_crore_lakh(roi.get("avoided_panic_freight_inr", 135000)),
        f"{roi.get('false_alarms_cleared_count', 1)} False Alarms Cleared by UDFs",
    )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Interactive What-If Line-Stop & Logistics Breakeven Simulator")
    st.caption(
        "Adjust hourly downtime penalty and emergency freight tariffs to model plant break-even economics in real-time."
    )

    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        sim_burn_rate = st.slider(
            "Average Assembly Line Idle Burn Rate (Rs / Hour):",
            min_value=500_000,
            max_value=2_500_000,
            value=1_050_000,
            step=50_000,
            format="Rs %d",
        )
    with col_sim2:
        sim_freight_cost = st.slider(
            "Dedicated Express Hot-Shot Logistics Tariff (Rs / Incident):",
            min_value=15_000,
            max_value=150_000,
            value=45_000,
            step=5_000,
            format="Rs %d",
        )

    # Reactive Calculations
    total_short_downtime_hrs = float(bom_df["downtime_hours_net"].sum())
    sim_idle_loss = total_short_downtime_hrs * sim_burn_rate
    sim_total_loss = float(roi.get("net_risk_inr", 0)) + sim_idle_loss
    sim_roi = (sim_total_loss - sim_freight_cost) / sim_freight_cost if sim_freight_cost > 0 else 0.0
    breakeven_minutes = (sim_freight_cost / sim_burn_rate) * 60.0

    st.markdown(
        f"""
        <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 4px solid {COLOR_BRAND_PRIMARY}; border-radius: 8px; padding: 12px 18px; margin-top: 10px; margin-bottom: 20px; font-size: 0.82rem; line-height: 1.5; color: {COLOR_TEXT_PRIMARY};">
            <strong>Live Breakeven Economic Proof:</strong> At <strong>Rs {sim_burn_rate/100000:.2f} Lakh/hr</strong> line downtime burn, 
            the entire <strong>Rs {sim_freight_cost:,.0f}</strong> emergency freight dispatch pays for itself in just 
            <strong>{breakeven_minutes:.1f} minutes</strong> of prevented stoppage. Over the 48h horizon, avoiding line halts saves 
            <strong>{format_inr_crore_lakh(sim_total_loss)}</strong>, generating a <strong>{sim_roi:,.0f}x</strong> financial return on freight investment.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Assembly Line Stoppage Loss Breakdown: Finished Goods vs. Idle Labor Burn")

    line_rollup = (
        bom_df.groupby("assembly_line_id", as_index=False)
        .agg(
            revenue_at_risk_net_inr=("revenue_at_risk_net_inr", "max"),
            plant_idle_cost_inr=("plant_idle_cost_inr", "max"),
            total_stoppage_exposure_inr=("total_stoppage_exposure_inr", "max"),
            expedited_freight_cost_inr=("expedited_freight_cost_inr", "sum"),
        )
    )

    fig_fin = go.Figure()
    fig_fin.add_trace(
        go.Bar(
            x=line_rollup["assembly_line_id"],
            y=line_rollup["revenue_at_risk_net_inr"],
            name="Unproduced Vehicle Revenue (Rs)",
            marker_color=COLOR_DANGER,
        )
    )
    fig_fin.add_trace(
        go.Bar(
            x=line_rollup["assembly_line_id"],
            y=line_rollup["plant_idle_cost_inr"],
            name="Plant Idle Labor & Depreciation Penalty (Rs)",
            marker_color=COLOR_WARNING,
        )
    )
    fig_fin.add_trace(
        go.Bar(
            x=line_rollup["assembly_line_id"],
            y=line_rollup["expedited_freight_cost_inr"],
            name="Emergency Hot-Shot Freight Cost (Rs)",
            marker_color=COLOR_BRAND_PRIMARY,
        )
    )
    fig_fin = apply_mangrove_theme(fig_fin, height=380)
    fig_fin.update_layout(
        barmode="stack",
        title="Financial Blast Radius by Assembly Line (Inaction Stoppage vs. Freight Intervention)",
        xaxis_title="Assembly Line",
        yaxis_title="Total Financial Exposure (INR)",
    )
    st.plotly_chart(fig_fin, use_container_width=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Component Deficit & Emergency Mitigation Allocation Ledger")
    st.caption("Detailed view of components causing active production deficits and their quantitative mitigation ROI.")

    short_comp_df = bom_df[bom_df["true_net_deficit_qty"] > 0].copy()
    display_short = pd.DataFrame(
        {
            "Assembly Line": short_comp_df["assembly_line_id"],
            "Component SKU": short_comp_df["component_part_num"],
            "Description": short_comp_df["part_description"],
            "Net Deficit Qty": short_comp_df["true_net_deficit_qty"],
            "Hours to Stop": short_comp_df["hours_to_starvation_harmonized"],
            "Downtime Penalty": short_comp_df["plant_idle_cost_inr"].apply(format_inr_crore_lakh),
            "Unproduced Vehicles": short_comp_df["revenue_at_risk_net_inr"].apply(format_inr_crore_lakh),
            "Total Inaction Loss": short_comp_df["total_stoppage_exposure_inr"].apply(format_inr_crore_lakh),
            "Expedited Freight": short_comp_df["expedited_freight_cost_inr"].apply(lambda v: f"Rs {v:,.0f}"),
            "Action ROI": short_comp_df["mitigation_roi_ratio"].apply(lambda v: f"{v:,.0f}x"),
        }
    )
    st.dataframe(display_short, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Avoided Panic Freight Ledger (Direct Savings from In-DB UDF Harmonization)")
    st.caption(
        "Shows supplier dispatches that legacy ETL systems quarantined as '0 stock', which would have triggered "
        "costly panic courier dispatches without Exasol's in-database harmonization."
    )

    cleared_asns = triage_df[
        triage_df["operational_verdict"].isin(["FALSE_STARVATION_CLEARED_BY_UDF", "HARMONIZED_BUFFER_RESTORED"])
    ].copy()
    display_cleared = pd.DataFrame(
        {
            "ASN Line ID": cleared_asns["asn_line_id"],
            "PO Number": cleared_asns["po_number_ref"],
            "Supplier": cleared_asns["supplier_name"],
            "Raw Payload Anomaly": cleared_asns["anomaly_type"],
            "UDF Harmonization": cleared_asns["raw_supplier_sku"] + " -> " + cleared_asns["resolved_part_num"],
            "Apparent Legacy Threat": cleared_asns["revenue_at_risk_legacy_inr"].apply(format_inr_crore_lakh),
            "Outcome": cleared_asns["operational_verdict"],
            "Avoided Panic Freight": cleared_asns["avoided_panic_freight_inr"].apply(
                lambda v: f"Rs {v:,.0f} Saved" if v > 0 else "Buffer Protected"
            ),
        }
    )
    st.dataframe(display_cleared, use_container_width=True, hide_index=True)
