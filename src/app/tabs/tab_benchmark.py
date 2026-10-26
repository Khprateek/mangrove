"""Tab 4: High-Scale Stress Benchmark (500 to 10,000 Rows)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.app.theme import (
    COLOR_BRAND_ACCENT,
    COLOR_BRAND_PRIMARY,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    apply_mangrove_theme,
)
from src.benchmarks.scale_benchmark import (
    get_verified_scale_benchmark,
    run_scale_benchmark,
)
from src.exasol_engine.db_client import ChakanExasolClient
from src.exasol_engine import domain_config


def render_scale_benchmark_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Tab 4: High-Scale Stress Benchmark (500 to 10,000 Rows)."""
    st.subheader("High-Scale Stress Benchmark: Set-Based Columnar Pipeline vs. Row-by-Row ETL")
    st.caption(
        "In high-volume automotive powertrain plants in the Pune-Chakan industrial corridor, inbound supplier ASN dispatches "
        "spike from 500 records on normal shifts to 10,000+ dispatches during weekend supplier reconciliations. "
        "By default, this benchmark reports pure measured CPU wall-clock times (0.0 ms synthetic overhead) comparing "
        "set-based columnar execution against a standard indexed row-by-row Python ETL pipeline."
    )

    # 1. Benchmark Execution Configuration Controls
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        sim_penalty = st.checkbox(
            "Optional: Add Modeled Multi-Node RPC Hop Overhead (+0.45 ms/row) on top of measured CPU time",
            value=st.session_state.get("bench_include_penalty", False),
            help="When unchecked (default), 100% of numbers are real measured CPU wall-clock timings. Checking this adds a modeled 0.45 ms/row network RPC penalty to illustrate unpartitioned remote lookups.",
            key="cb_bench_penalty",
        )
        st.session_state["bench_include_penalty"] = sim_penalty

    with col_c2:
        penalty_val = 0.45 if sim_penalty else 0.0
        run_live = st.button("⚡ Run Live Scale Benchmark (500 to 10k Rows)", use_container_width=True)

    if run_live:
        with st.spinner("Executing live multi-tier benchmark across 500, 2,500, 5,000, and 10,000 rows..."):
            bench_results = run_scale_benchmark(
                scales=[500, 2500, 5000, 10000],
                network_hop_penalty_ms=penalty_val,
                client=client,
            )
            st.session_state["live_bench_results"] = bench_results
    elif "live_bench_results" in st.session_state and not sim_penalty:
        bench_results = st.session_state["live_bench_results"]
    else:
        # Instant reference baseline (<1 ms) — decoupled from page render to prevent startup freezes
        bench_results = get_verified_scale_benchmark(network_hop_penalty_ms=penalty_val, client=client, force_rerun=False)

    rows_data = bench_results["results_table"]
    df_bench = pd.DataFrame(rows_data)

    is_live_db = bool(bench_results.get("is_live_database", False))
    engine_name = str(bench_results.get("engine_tested", "Vectorized Set-Based Engine"))
    peak_speedup = float(bench_results["peak_speedup_factor"])
    peak_tp = float(bench_results["peak_exasol_throughput"])
    row_10k = [r for r in rows_data if r["batch_rows"] == 10000][0]

    # Engine Status Alert Banner
    if is_live_db:
        st.markdown(
            """
            <div style="background-color: #E8F2E5; border: 1px solid #C6DBC3; border-left: 4px solid #2F6B4F; border-radius: 6px; padding: 8px 14px; margin-top: 10px; font-size: 0.80rem; color: #26332C;">
                ⚡ <b>Live Database Engine Connected</b>: Exasol Personal (Port 8563, Schema: <code>CHAKAN_SCM</code>) — Batch rows dynamically staged into Exasol memory; SQL views and Python 3 UDFs evaluated directly in database RAM.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background-color: #FEF9E7; border: 1px solid #FAD7A0; border-left: 4px solid #D4AC0D; border-radius: 6px; padding: 8px 14px; margin-top: 10px; font-size: 0.80rem; color: #7D6608;">
                ℹ️ <b>Vectorized In-Memory Mirror Mode</b>: Database offline. Benchmarks are measured using the local Pandas/NumPy columnar memory pipeline. Connect the Exasol appliance (<code>docker compose up -d</code>) to benchmark the native in-database MPP engine.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Executive KPI Summary Cards
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Peak Throughput Speedup",
        f"{peak_speedup:.1f}x Faster",
        "At 10,000 Inbound Rows",
    )
    col_tp_label = "Peak Exasol Throughput" if is_live_db else "Peak Columnar Throughput"
    k2.metric(
        col_tp_label,
        f"{peak_tp:,.0f} Rows/Sec",
        f"vs {row_10k['legacy_throughput_rows_sec']:,.0f} Rows/Sec (Python ETL)",
    )
    col_lat_label = "10k Exasol Latency" if is_live_db else "10k Columnar Latency"
    k3.metric(
        col_lat_label,
        f"{row_10k['columnar_latency_ms']:.1f} ms",
        f"-{row_10k['latency_reduction_pct']:.1f}% vs {row_10k['legacy_latency_ms']:,.0f} ms Python ETL",
        delta_color="inverse",
    )
    k4.metric(
        "ETL Network Serialization",
        "0 Network Hops",
        "In-database RAM vs external ETL extraction",
    )

    # 3. Side-by-Side Visualizations with generous spacing
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)

    columnar_trace_name = "Exasol In-DB SQL" if is_live_db else "Vectorized Mirror"

    with col_chart1:
        st.markdown(
            f"""
            <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-bottom: 2px;">
                Execution Latency Scaling Curve (Lower is Better)
            </div>
            <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 8px;">
                Columnar set-based pipeline vs indexed Python ETL pipeline latency
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_lat = go.Figure()
        fig_lat.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"],
                y=df_bench["columnar_latency_ms"],
                mode="lines+markers",
                name=columnar_trace_name,
                line=dict(color=COLOR_BRAND_PRIMARY, width=3),
                marker=dict(size=8),
            )
        )
        fig_lat.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"],
                y=df_bench["legacy_latency_ms"],
                mode="lines+markers",
                name="Indexed Python ETL Total",
                line=dict(color=COLOR_DANGER, width=3, dash="solid"),
                marker=dict(size=8),
            )
        )
        if sim_penalty:
            fig_lat.add_trace(
                go.Scatter(
                    x=df_bench["batch_rows"],
                    y=df_bench["legacy_cpu_ms"],
                    mode="lines+markers",
                    name="Indexed Python ETL Pure CPU",
                    line=dict(color="#A66B20", width=2, dash="dot"),
                    marker=dict(size=6),
                )
            )
        fig_lat.add_hline(
            y=150.0,
            line_dash="dash",
            line_color=COLOR_BRAND_ACCENT,
            annotation_text=" 150ms In-DB SLA",
            annotation_position="bottom right",
            annotation_font=dict(size=9.5, color=COLOR_BRAND_ACCENT),
        )
        fig_lat = apply_mangrove_theme(fig_lat, height=380)
        fig_lat.update_layout(
            margin=dict(l=36, r=16, t=28, b=45),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(size=10, color=COLOR_TEXT_SECONDARY),
            ),
            xaxis_title="Inbound Stream Scale (Rows)",
            yaxis_title="Execution Latency (ms)",
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    with col_chart2:
        st.markdown(
            f"""
            <div style="font-weight: 700; font-size: 0.92rem; color: {COLOR_TEXT_PRIMARY}; margin-bottom: 2px;">
                Throughput & Speedup Multiplier (Higher is Better)
            </div>
            <div style="font-size: 0.76rem; color: {COLOR_TEXT_SECONDARY}; margin-bottom: 8px;">
                Measured rows/second throughput and relative columnar acceleration factor
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig_tp = go.Figure()
        fig_tp.add_trace(
            go.Bar(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["columnar_throughput_rows_sec"],
                name=f"{columnar_trace_name} Throughput",
                marker_color=COLOR_BRAND_PRIMARY,
                yaxis="y",
            )
        )
        fig_tp.add_trace(
            go.Bar(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["legacy_throughput_rows_sec"],
                name="Python ETL Throughput",
                marker_color="#8E9E93",
                yaxis="y",
            )
        )
        fig_tp.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["speedup_factor"],
                name="Speedup Factor",
                mode="lines+markers+text",
                text=[f"{s:.1f}x" for s in df_bench["speedup_factor"]],
                textposition="top center",
                line=dict(color=COLOR_DANGER, width=2),
                marker=dict(size=7, color=COLOR_DANGER),
                yaxis="y2",
            )
        )
        fig_tp = apply_mangrove_theme(fig_tp, height=380)
        fig_tp.update_layout(
            margin=dict(l=36, r=36, t=28, b=45),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(size=10, color=COLOR_TEXT_SECONDARY),
            ),
            xaxis_title="Inbound Batch Size Tier",
            yaxis=dict(title="Throughput (Rows/s)"),
            yaxis2=dict(title="Speedup (X)", overlaying="y", side="right", showgrid=False),
            barmode="group",
        )
        st.plotly_chart(fig_tp, use_container_width=True)

    # 4. Detailed Comparative Audit Table
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Multi-Tier High-Scale Stress Benchmark Audit Ledger")
    st.caption("Quantitative audit comparing columnar execution against standard indexed Python ETL across scale tiers.")

    display_table = pd.DataFrame(
        {
            "Batch Scale": [f"{r['batch_rows']:,} Rows" for r in rows_data],
            "Columnar Latency": [f"{r['columnar_latency_ms']:.1f} ms" for r in rows_data],
            "Python ETL Latency": [f"{r['legacy_latency_ms']:,.1f} ms" for r in rows_data],
            "Latency Saved": [f"{r['latency_reduction_pct']:.1f}%" for r in rows_data],
            "Measured Speedup": [f"{r['speedup_factor']:.1f}x" for r in rows_data],
            "Columnar Throughput": [f"{r['columnar_throughput_rows_sec']:,.0f} rows/s" for r in rows_data],
            "Python ETL Throughput": [f"{r['legacy_throughput_rows_sec']:,.0f} rows/s" for r in rows_data],
            "Execution Engine": [r["engine_name"] for r in rows_data],
        }
    )
    st.dataframe(display_table, use_container_width=True, hide_index=True)

    # 5. Technical Architecture Deep-Dive Expander
    with st.expander("🔬 Architectural Analysis: Set-Based Columnar Execution vs. Traditional ETL", expanded=False):
        col_ad1, col_ad2 = st.columns(2)
        with col_ad1:
            st.markdown(
                """
                #### 1. In-Memory Columnar Vectorization
                - **Row-by-Row ETL:** Processes records one by one in Python, loading entire dictionary payloads into interpreter heap memory with high GIL contention and serialization overhead.
                - **Exasol:** Scans only needed columns from RAM. CPU cache utilization is maximized via SIMD vector instructions, evaluating millions of cells in parallel.

                #### 2. In-Database Python 3 Scalar UDF Parallelization
                - **Traditional ETL:** Ingests raw rows to external worker threads, parses strings row-by-row, and dispatches separate DB queries for master data resolution across the network.
                - **Exasol:** UDFs execute compiled inside native worker containers in RAM. Data is transferred via zero-copy C memory buffers (`EMITS`), eliminating serialization and IPC bottlenecks.
                """
            )
        with col_ad2:
            st.markdown(
                """
                #### 3. In-Database Processing vs External ETL Network Serialization
                - **External Python ETL:** Extracts raw tables across network connections to external worker processes, incurring heavy serialization, network socket latency, and high heap memory footprints.
                - **Exasol In-Database Engine:** Evaluates views and Python 3 UDFs directly in database RAM. Core tables (`ITEM_MASTER`, `PURCHASE_ORDER_LINES`, `WAREHOUSE_INVENTORY_LEDGER`) are partitioned on `internal_part_num` for co-located part lookups, executing without external data movement.
                """
            )

    # 6. Enterprise Data Locality Law Deep Dive
    with st.expander("🏛️ Why 10k Rows? The Enterprise Data Locality Law (Zero Egress vs. The ETL Serialization Tax)", expanded=False):
        st.markdown(
            """
            <div style="background-color: #F8F9FA; border: 1px solid #E5E7EB; border-left: 4px solid #2F6B4F; border-radius: 6px; padding: 12px 16px; margin-bottom: 14px; font-size: 0.84rem; color: #1F2937;">
                <strong>The Architectural Reality of 10,000 Rows:</strong> In local RAM, a single-threaded Python script with an indexed C dictionary is fast (~180 ms) because a 10,000-row batch (~1.5 MB) fits entirely inside CPU L3 cache.
                However, benchmark isolation hides the true enterprise bottleneck: <strong>The Data Locality Law</strong>.
                In automotive manufacturing, inbound dispatches cannot be reconciled in a vacuum—they must be cross-referenced against multi-million-row ERP master tables (<code>ITEM_MASTER</code>, <code>PURCHASE_ORDER_LINES</code>, <code>WAREHOUSE_INVENTORY_LEDGER</code>).
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_loc1, col_loc2 = st.columns(2)
        with col_loc1:
            st.markdown(
                """
                ##### The 3 Fatal Bottlenecks of External Python ETL
                1. **Network Egress Serialization Tax**: Moving 500,000 to 10,000,000 ERP rows across a 1 Gbps corporate network incurs 5 to 20+ seconds of socket transfer latency before processing even begins.
                2. **Heap Memory Explosion & GC Pauses**: Deserializing millions of JSON/CSV/pickle records into Python dictionaries consumes 2–5 GB of application heap, triggering aggressive garbage collection freezes.
                3. **GIL Contention & CPU Cache Thrashing**: Python's Global Interpreter Lock (GIL) serializes thread execution, preventing true multi-core parallel SIMD vectorization.
                """
            )
        with col_loc2:
            st.markdown(
                """
                ##### Exasol's In-Database Zero-Egress Moat
                1. **Zero Network Egress**: ERP master ledgers remain permanently pinned in Exasol's compressed columnar RAM slices. Data never crosses network boundaries.
                2. **In-Situ Python 3 UDF Evaluation**: Inbound dirty dispatches are streamed into scratch tables, where compiled UDFs and joins execute adjacent to columnar storage via zero-copy C memory buffers.
                3. **MPP Hardware Scale-Out**: Co-locating related partition slices on <code>DISTRIBUTE BY</code> keys enables parallel C++ vector execution across all CPU cores without inter-process bottlenecks.
                """
            )

        st.markdown("##### Enterprise Scale Extrapolation: External ETL Network Egress vs. Exasol In-DB")
        scale_df = pd.DataFrame([
            {
                "Operational Scale": tier_name,
                "Inbound ASN Batch": f"{tier_data['asn_rows']:,} Rows",
                "ERP Ledger Baseline": f"{tier_data['erp_ledger_rows']:,} Rows",
                "External ETL Network Egress": f"{tier_data['network_egress_mb']:.1f} MB (~{tier_data['external_etl_network_sec_1gbps']:.1f}s on 1 Gbps)",
                "Exasol In-DB Egress": "0.0 MB (Zero Egress)",
                "In-Database Advantage": "Instant In-Situ RAM Join",
            }
            for tier_name, tier_data in domain_config.ENTERPRISE_SCALE_TIERS.items()
        ])
        st.dataframe(scale_df, use_container_width=True, hide_index=True)

