"""Tab 3: Interactive 'What-If' Chaos Simulator: Real-Time In-DB Stress Testing."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BORDER,
    COLOR_BRAND_PRIMARY,
    COLOR_BRAND_SOFT,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    apply_mangrove_theme,
    format_inr_crore_lakh,
)
from src.exasol_engine.db_client import ChakanExasolClient


def render_scenario_simulator_tab(
    client: ChakanExasolClient,
    marts: dict,
    perspective_mode: str = "MANGROVE_ACTIVE",
) -> None:
    """Tab 3: Interactive 'What-If' Chaos Simulator: Real-Time In-DB Stress Testing."""
    is_mangrove = (perspective_mode == "MANGROVE_ACTIVE")

    if not is_mangrove:
        st.markdown(
            f"""
            <div style="background-color: #FDF4F4; border: 1px solid #F5C6C6; border-left: 5px solid {COLOR_DANGER}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_DANGER}; font-size: 0.82rem;">⚠️ TRADITIONAL ERP SIMULATION RESTRICTION</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Traditional ERP operates on static batch ETL schedules and cannot simulate multi-parameter supply disruptions in memory. Turn ON Mangrove to unlock real-time monsoon delay, foundry defect spike, and demand surge simulations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background-color: {COLOR_BRAND_SOFT}; border: 1px solid #C6DBC3; border-left: 5px solid {COLOR_BRAND_PRIMARY}; border-radius: 9px; padding: 10px 16px; margin-bottom: 14px;">
                <span style="font-weight: 700; color: {COLOR_BRAND_PRIMARY}; font-size: 0.82rem;">🟢 MANGROVE IN-DB SIMULATOR: LIVE RECURSIVE BOM STRESS-TESTING</span>
                <div style="font-size: 0.76rem; color: #68756B; margin-top: 2px;">
                    Exasol evaluates multi-table joins, Python UDFs, and starvation horizons in sub-second columnar RAM as disruption sliders move.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.subheader("Interactive 'What-If' Chaos Simulator: Real-Time In-DB Stress Testing")
    st.caption(
        "Automotive supply chains face simultaneous compound disruptions: transit roadblocks, "
        "metallurgy casting porosity at Tier-2 foundries, and sudden OEM assembly line throughput surges. "
        "Exasol evaluates multi-table joins, UDFs, and starvation horizons sub-second in columnar RAM."
    )

    # 1. 1-Click Crisis Presets
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 6px; margin-bottom: 8px;">
            1. ONE-CLICK OPERATIONAL CRISIS PRESETS
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    if col_b1.button("🟢 Baseline Operations", help="Reset all disruption parameters to normal Monday operations (0 delay, 0% defects, 1.0x surge)", use_container_width=True):
        st.session_state["sim_transit_delay"] = 0
        st.session_state["sim_quarantine_rate"] = 0
        st.session_state["sim_demand_surge"] = 1.00
        st.rerun()

    if col_b2.button("🌧️ Western Ghats Monsoon", help="NH-48 Ghat highway landslides causing +3 days transit delay & 5% transit damage", use_container_width=True):
        st.session_state["sim_transit_delay"] = 3
        st.session_state["sim_quarantine_rate"] = 5
        st.session_state["sim_demand_surge"] = 1.00
        st.rerun()

    if col_b3.button("⚙️ Foundry Porosity Crisis", help="Tier-2 engine casting porosity defect spike (35% quarantine reject, +1 day delay)", use_container_width=True):
        st.session_state["sim_transit_delay"] = 1
        st.session_state["sim_quarantine_rate"] = 35
        st.session_state["sim_demand_surge"] = 1.00
        st.rerun()

    if col_b4.button("📈 Festive OEM Demand Surge", help="Festival season production surge (+35% assembly throughput, +2 days delay, 15% quarantine)", use_container_width=True):
        st.session_state["sim_transit_delay"] = 2
        st.session_state["sim_quarantine_rate"] = 15
        st.session_state["sim_demand_surge"] = 1.35
        st.rerun()

    # 2. Interactive Parameter Sliders
    st.markdown(
        f"""
        <div style="font-size: 0.70rem; font-weight: 700; color: {COLOR_TEXT_SECONDARY}; letter-spacing: 0.8px; text-transform: uppercase; margin-top: 16px; margin-bottom: 8px;">
            2. FINE-TUNED CHAOS CONTROL KNOBS
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_s1, col_s2, col_s3 = st.columns(3)

    cur_delay = st.session_state.get("sim_transit_delay", 0)
    cur_quar = st.session_state.get("sim_quarantine_rate", 0)
    cur_surge = st.session_state.get("sim_demand_surge", 1.00)

    with col_s1:
        sim_delay = st.slider(
            "Logistics Transit Delay (Days):",
            min_value=0,
            max_value=5,
            value=cur_delay,
            step=1,
            help="Simulates highway closures, customs holds, or carrier delays on incoming shipments.",
            key="slider_transit_delay",
        )
        st.session_state["sim_transit_delay"] = sim_delay

    with col_s2:
        sim_quar = st.slider(
            "Supplier Quality Defect Rate (% Hold):",
            min_value=0,
            max_value=50,
            value=cur_quar,
            step=5,
            help="Simulates in-plant QA gate rejection rate sequestering incoming stock into quality hold.",
            key="slider_quarantine_rate",
        )
        st.session_state["sim_quarantine_rate"] = sim_quar

    with col_s3:
        sim_surge = st.slider(
            "Assembly Throughput Surge Multiplier:",
            min_value=1.00,
            max_value=1.50,
            value=cur_surge,
            step=0.05,
            format="%.2fx",
            help="Simulates OEM assembly overtime / weekend surge shifts accelerating component burn rate.",
            key="slider_demand_surge",
        )
        st.session_state["sim_demand_surge"] = sim_surge

    # 3. Compute Simulated Marts
    sim_results = client.compute_simulation_marts(
        transit_delay_days=sim_delay,
        quarantine_defect_pct=float(sim_quar) / 100.0,
        demand_surge_multiplier=float(sim_surge),
    )

    sim_marts = sim_results["simulated"]
    base_marts = sim_results["baseline"]
    sim_roi = sim_marts["financial_roi_mart"]
    base_roi = base_marts["financial_roi_mart"]
    sim_bom = sim_marts["bom_risk_mart"]
    base_bom = base_marts["bom_risk_mart"]

    sim_net = float(sim_roi["net_risk_inr"])
    delta_net = float(sim_results["delta_net_risk_inr"])
    sim_exp = float(sim_roi["total_stoppage_exposure_inr"])
    delta_exp = float(sim_results["delta_total_exposure_inr"])

    base_min_hrs = float(base_bom["hours_to_starvation_harmonized"].min())
    sim_min_hrs = float(sim_bom["hours_to_starvation_harmonized"].min())
    delta_hrs = round(sim_min_hrs - base_min_hrs, 1)

    base_short_count = int((base_bom["true_net_deficit_qty"] > 0).sum())
    sim_short_count = int((sim_bom["true_net_deficit_qty"] > 0).sum())
    delta_short = sim_short_count - base_short_count

    is_chaos_active = (sim_delay > 0 or sim_quar > 0 or sim_surge > 1.00)
    recalc_latency = float(sim_marts["query_latency_ms"])
    sim_total_rows = int(sim_marts.get("telemetry", {}).get("total_rows_evaluated", len(sim_marts["asn_lineage_mart"])))
    base_net_val = float(base_roi["net_risk_inr"])
    base_exp_val = float(base_roi["total_stoppage_exposure_inr"])

    status_label = (
        f"🔴 CHAOS ACTIVE (+{sim_delay}d delay, {sim_quar}% defect, {sim_surge:.2f}x surge)"
        if is_chaos_active
        else "🟢 BASELINE RUN (Standard Operations)"
    )
    status_color = COLOR_DANGER if is_chaos_active else COLOR_BRAND_PRIMARY

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 8px 0; margin-top: 8px; margin-bottom: 16px; border-top: 1px solid {COLOR_BORDER}; border-bottom: 1px solid {COLOR_BORDER}; font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY};">
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 14px;">
                <span style="font-weight: 700; color: {status_color};">{status_label}</span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span>Recalculation: <strong style="color: {COLOR_TEXT_PRIMARY};">{recalc_latency:.1f} ms</strong> <code style="font-size: 0.70rem; color: #FFFFFF; background: rgba(0, 0, 0, 0.25); padding: 2px 6px; border-radius: 4px;">{sim_marts.get('compute_source', 'PANDAS_MIRROR')}</code></span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span>Evaluated: <strong style="color: {COLOR_TEXT_PRIMARY};">{sim_total_rows:,} rows</strong></span>
                <span style="color: {COLOR_BORDER};">•</span>
                <span style="color: {COLOR_BRAND_PRIMARY}; font-weight: 600;">Sequential Additive Attribution</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Comparative Delta KPI Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Simulated Revenue at Risk",
        format_inr_crore_lakh(sim_net),
        f"+{format_inr_crore_lakh(delta_net)} Escalation" if delta_net > 0 else f"Baseline ({format_inr_crore_lakh(base_net_val)})",
        delta_color="inverse",
    )
    m2.metric(
        "Total Inaction Exposure",
        format_inr_crore_lakh(sim_exp),
        f"+{format_inr_crore_lakh(delta_exp)} Downtime Loss" if delta_exp > 0 else f"Baseline ({format_inr_crore_lakh(base_exp_val)})",
        delta_color="inverse",
    )
    m3.metric(
        "Earliest Assembly Line Halt",
        f"{sim_min_hrs:.1f} Hours",
        f"{delta_hrs:+.1f} Hours Shift" if delta_hrs != 0 else f"Baseline ({base_min_hrs:.1f} hrs)",
        delta_color="inverse",
    )
    m4.metric(
        "Starving Component SKUs",
        f"{sim_short_count} of {len(sim_bom)} SKUs",
        f"+{delta_short} Newly Starving SKUs" if delta_short > 0 else f"Baseline ({base_short_count} SKU{'s' if base_short_count != 1 else ''})",
        delta_color="inverse",
    )

    # 5. Visualizations with generous spacing & clean separation
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    col_v1, col_v2 = st.columns([1, 1])

    with col_v1:
        st.markdown(
            f"""
            <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-bottom: 2px;">
                Component Run Window Horizon (Baseline vs Chaos)
            </div>
            <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 8px;">
                Available production hours per component before assembly line starvation
            </div>
            """,
            unsafe_allow_html=True,
        )

        merged_bom = base_bom[["assembly_line_id", "component_part_num", "part_description", "hours_to_starvation_harmonized"]].rename(
            columns={"hours_to_starvation_harmonized": "baseline_run_hours"}
        ).merge(
            sim_bom[["assembly_line_id", "component_part_num", "hours_to_starvation_harmonized"]].rename(
                columns={"hours_to_starvation_harmonized": "simulated_run_hours"}
            ),
            on=["assembly_line_id", "component_part_num"],
        )

        fig_horizon = go.Figure()
        fig_horizon.add_trace(
            go.Bar(
                x=merged_bom["component_part_num"],
                y=merged_bom["baseline_run_hours"],
                name="Baseline Hours",
                marker_color=COLOR_BRAND_PRIMARY,
            )
        )
        fig_horizon.add_trace(
            go.Bar(
                x=merged_bom["component_part_num"],
                y=merged_bom["simulated_run_hours"],
                name="Post-Shock Hours",
                marker_color=COLOR_DANGER,
            )
        )
        fig_horizon.add_hline(
            y=48.0,
            line_dash="dash",
            line_color=COLOR_BRAND_PRIMARY,
            annotation_text=" 48h Safety Target",
            annotation_position="top right",
            annotation_font=dict(size=9.5, color=COLOR_BRAND_PRIMARY),
        )
        fig_horizon = apply_mangrove_theme(fig_horizon, height=390)
        fig_horizon.update_layout(
            barmode="group",
            margin=dict(l=36, r=16, t=28, b=85),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(size=10, color=COLOR_TEXT_SECONDARY),
            ),
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=9, color=COLOR_TEXT_SECONDARY),
                title=None,
            ),
            yaxis=dict(
                title=dict(text="Available Hours", font=dict(size=10, color=COLOR_TEXT_SECONDARY)),
                tickfont=dict(size=10, color=COLOR_TEXT_SECONDARY),
            ),
        )
        st.plotly_chart(fig_horizon, use_container_width=True)

    with col_v2:
        st.markdown(
            f"""
            <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-bottom: 2px;">
                Disruption Factor Exposure Attribution Waterfall
            </div>
            <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 8px;">
                Step-by-step risk escalation from baseline deficit to compound shock
            </div>
            """,
            unsafe_allow_html=True,
        )

        wf_data = sim_results["waterfall_data"]
        label_map = {
            "1. Baseline True Shortage": "1. Baseline<br>Shortage",
            "2. Logistics Transit Drift": "2. Transit<br>Drift",
            "3. Quarantine Defect Spike": "3. Quarantine<br>Defects",
            "4. Surge Output Demand": "4. Demand<br>Surge",
            "Total Simulated Exposure": "Total Net<br>Exposure",
        }
        stages = [label_map.get(d["Stage"], d["Stage"]) for d in wf_data]
        amounts = [d["Amount"] for d in wf_data]
        amounts_cr = [round(a / 10_000_000.0, 2) for a in amounts]
        measures = [d["Type"] for d in wf_data]

        text_amounts = []
        for i, a in enumerate(amounts):
            if abs(a) > 1000 or measures[i] == "total":
                text_amounts.append(format_inr_crore_lakh(a))
            else:
                text_amounts.append("")

        fig_wf = go.Figure(
            go.Waterfall(
                name="Attribution",
                orientation="v",
                measure=measures,
                x=stages,
                textposition="outside",
                text=text_amounts,
                y=amounts_cr,
                cliponaxis=False,
                textfont=dict(size=10, color=COLOR_TEXT_PRIMARY),
                connector={"line": {"color": COLOR_BORDER, "width": 1.5, "dash": "dot"}},
                decreasing={"marker": {"color": COLOR_BRAND_PRIMARY}},
                increasing={"marker": {"color": COLOR_DANGER}},
                totals={"marker": {"color": "#8B2626"}},
            )
        )
        fig_wf = apply_mangrove_theme(fig_wf, height=390)
        max_cr = max(amounts_cr) if amounts_cr else 6.0
        fig_wf.update_layout(
            margin=dict(l=44, r=16, t=28, b=65),
            xaxis=dict(
                tickangle=0,
                tickfont=dict(size=9.5, color=COLOR_TEXT_SECONDARY),
                title=None,
            ),
            yaxis=dict(
                title=dict(text="Escalated Exposure (₹ Cr)", font=dict(size=10, color=COLOR_TEXT_SECONDARY)),
                tickfont=dict(size=10, color=COLOR_TEXT_SECONDARY),
                ticksuffix=" Cr",
                tickprefix="₹",
                range=[0, max(max_cr * 1.25, 6.0)],
            ),
        )
        st.plotly_chart(fig_wf, use_container_width=True)

    # 6. Detailed Component Deficit & Emergency Action Matrix
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Simulated Component Deficit & Emergency Action Matrix")
    st.caption("Displays components under risk of halting production lines and the recommended emergency mitigation.")

    def get_action_recommendation(row: pd.Series) -> str:
        deficit = row["true_net_deficit_qty"]
        hrs = row["hours_to_starvation_harmonized"]
        if deficit <= 0:
            return "SECURED: Within Buffer"
        if hrs < 12.0:
            return "CRITICAL: Air-Charter Express Hotshot"
        if hrs < 24.0:
            return "URGENT: Dedicated Hot-Shot Direct Truck"
        return "PRIORITY: Reallocate Line Safety Buffer"

    sim_display_df = sim_bom.copy()
    sim_display_df = sim_display_df.merge(
        base_bom[["assembly_line_id", "component_part_num", "hours_to_starvation_harmonized"]].rename(
            columns={"hours_to_starvation_harmonized": "base_hrs_to_stop"}
        ),
        on=["assembly_line_id", "component_part_num"],
    )
    sim_display_df["recommended_action"] = sim_display_df.apply(get_action_recommendation, axis=1)

    table_data = pd.DataFrame(
        {
            "Assembly Line": sim_display_df["assembly_line_id"],
            "Component SKU": sim_display_df["component_part_num"],
            "Part Description": sim_display_df["part_description"],
            "Baseline Run Hrs": sim_display_df["base_hrs_to_stop"].apply(lambda v: f"{v:.1f} hrs"),
            "Simulated Run Hrs": sim_display_df["hours_to_starvation_harmonized"].apply(lambda v: f"{v:.1f} hrs"),
            "Simulated Deficit Qty": sim_display_df["true_net_deficit_qty"].apply(lambda v: f"{v:,.0f}" if v > 0 else "0 (Balanced)"),
            "Revenue at Risk": sim_display_df["revenue_at_risk_net_inr"].apply(format_inr_crore_lakh),
            "Plant Idle Loss": sim_display_df["plant_idle_cost_inr"].apply(format_inr_crore_lakh),
            "Total Inaction Loss": sim_display_df["total_stoppage_exposure_inr"].apply(format_inr_crore_lakh),
            "Recommended Action": sim_display_df["recommended_action"],
        }
    )
    st.dataframe(table_data, use_container_width=True, hide_index=True)
