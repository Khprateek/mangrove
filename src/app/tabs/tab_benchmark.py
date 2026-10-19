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


def render_scale_benchmark_tab(client: ChakanExasolClient, marts: dict) -> None:
    """Tab 4: High-Scale Stress Benchmark (500 to 10,000 Rows)."""
    st.subheader("High-Scale Stress Benchmark: Set-Based Columnar Pipeline vs. Row-by-Row ETL")
    st.caption(
        "In high-volume automotive powertrain plants in the Pune-Chakan industrial corridor, inbound supplier ASN dispatches "
        "spike from 500 records on normal shifts to 10,000+ dispatches during weekend supplier reconciliations. "
        "By default, this benchmark reports pure measured CPU wall-clock times (0.0 ms synthetic overhead) comparing "
        "set-based columnar execution against uncached row-by-row Python ETL (`iterrows()`)."
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
    else:
        bench_results = get_verified_scale_benchmark(network_hop_penalty_ms=penalty_val)

    rows_data = bench_results["results_table"]
    df_bench = pd.DataFrame(rows_data)

    peak_speedup = float(bench_results["peak_speedup_factor"])
    peak_tp = float(bench_results["peak_exasol_throughput"])
    row_10k = [r for r in rows_data if r["batch_rows"] == 10000][0]

    # 2. Executive KPI Summary Cards
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Peak Throughput Speedup",
        f"{peak_speedup:.1f}x Faster",
        "At 10,000 Inbound Rows",
    )
    k2.metric(
        "Peak Exasol Throughput",
        f"{peak_tp:,.0f} Rows/Sec",
        f"vs {row_10k['legacy_throughput_rows_sec']:,.0f} Rows/Sec (Legacy)",
    )
    k3.metric(
        "10k-Row Analytical Latency",
        f"{row_10k['exasol_latency_ms']:.1f} ms",
        f"-{row_10k['latency_reduction_pct']:.1f}% vs {row_10k['legacy_latency_ms']:,.0f} ms Legacy",
        delta_color="inverse",
    )
    k4.metric(
        "Inter-Node Network Shuffling",
        "0 Net Hops",
        f"vs {row_10k['legacy_network_hops']:,} Shuffles (DISTRIBUTE BY)",
    )

    # 3. Side-by-Side Visualizations with generous spacing
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Latency Scaling Curve
        fig_lat = go.Figure()
        fig_lat.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"],
                y=df_bench["exasol_latency_ms"],
                mode="lines+markers",
                name="Exasol Columnar (In-Memory MPP)",
                line=dict(color=COLOR_BRAND_PRIMARY, width=3),
                marker=dict(size=8),
            )
        )
        fig_lat.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"],
                y=df_bench["legacy_latency_ms"],
                mode="lines+markers",
                name="Legacy Row-by-Row ETL (Total)",
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
                    name="Legacy ETL (Pure CPU Compute)",
                    line=dict(color="#A66B20", width=2, dash="dot"),
                    marker=dict(size=6),
                )
            )
        fig_lat.add_hline(
            y=150.0,
            line_dash="dash",
            line_color=COLOR_BRAND_ACCENT,
            annotation_text="150ms Real-Time In-DB SLA Target",
            annotation_position="top left",
        )
        fig_lat = apply_mangrove_theme(fig_lat, height=380)
        fig_lat.update_layout(
            title="Execution Latency Scaling Curve (Lower is Better)",
            xaxis_title="Inbound ASN Stream Scale (Rows)",
            yaxis_title="Execution Latency (Milliseconds)",
        )
        st.plotly_chart(fig_lat, use_container_width=True)

    with col_chart2:
        # Throughput & Speedup Multiplier
        fig_tp = go.Figure()
        fig_tp.add_trace(
            go.Bar(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["exasol_throughput_rows_sec"],
                name="Exasol Throughput (Rows/s)",
                marker_color=COLOR_BRAND_PRIMARY,
                yaxis="y",
            )
        )
        fig_tp.add_trace(
            go.Bar(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["legacy_throughput_rows_sec"],
                name="Legacy ETL (Rows/s)",
                marker_color="#8E9E93",
                yaxis="y",
            )
        )
        fig_tp.add_trace(
            go.Scatter(
                x=df_bench["batch_rows"].astype(str) + " Rows",
                y=df_bench["speedup_factor"],
                name="Speedup Factor (X)",
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
            title="Throughput (Rows/Sec) & Relative Speedup Acceleration",
            xaxis_title="Inbound Batch Size Tier",
            yaxis=dict(title="Throughput (Rows / Sec)"),
            yaxis2=dict(title="Speedup Factor (X)", overlaying="y", side="right", showgrid=False),
            barmode="group",
        )
        st.plotly_chart(fig_tp, use_container_width=True)

    # 4. Detailed Comparative Audit Table
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("Multi-Tier High-Scale Stress Benchmark Audit Ledger")
    st.caption("Quantitative audit comparing Exasol Personal columnar execution against row-by-row ETL across scale tiers.")

    display_table = pd.DataFrame(
        {
            "Batch Scale": [f"{r['batch_rows']:,} Rows" for r in rows_data],
            "Exasol Latency": [f"{r['exasol_latency_ms']:.1f} ms" for r in rows_data],
            "Legacy ETL Latency": [f"{r['legacy_latency_ms']:,.1f} ms" for r in rows_data],
            "Latency Saved": [f"{r['latency_reduction_pct']:.1f}%" for r in rows_data],
            "Measured Speedup": [f"{r['speedup_factor']:.1f}x" for r in rows_data],
            "Exasol Throughput": [f"{r['exasol_throughput_rows_sec']:,.0f} rows/s" for r in rows_data],
            "Legacy Throughput": [f"{r['legacy_throughput_rows_sec']:,.0f} rows/s" for r in rows_data],
            "Network Shuffles": ["0 Hops (Co-located)" for _ in rows_data],
        }
    )
    st.dataframe(display_table, use_container_width=True, hide_index=True)

    # 5. Technical Architecture Deep-Dive Expander
    with st.expander("🔬 Architectural Analysis: Why Exasol Scales Sub-Second at 10,000 Rows", expanded=False):
        col_ad1, col_ad2 = st.columns(2)
        with col_ad1:
            st.markdown(
                """
                #### 1. In-Memory Columnar Vectorization
                - **Legacy ETL:** Processes records one by one in Python, loading entire dictionary payloads into interpreter memory with high GIL contention.
                - **Exasol:** Scans only needed columns from RAM. CPU cache utilization is maximized via SIMD vector instructions, evaluating millions of cells in parallel.

                #### 2. In-Database Python 3 Scalar UDF Parallelization
                - **Legacy ETL:** Ingests raw rows to external worker threads, parses strings row-by-row via slow regex loops, and dispatches separate DB queries for master data resolution.
                - **Exasol:** UDFs execute compiled inside native worker containers in RAM. Data is transferred via zero-copy C memory buffers (`EMITS`), eliminating serialization and IPC bottlenecks.
                """
            )
        with col_ad2:
            st.markdown(
                """
                #### 3. MPP Co-Location Partitioning (`DISTRIBUTE BY internal_part_num`)
                - **Legacy ETL:** Joins `ASN_LINES` to `PURCHASE_ORDER_LINES`, `ITEM_MASTER`, and `BILL_OF_MATERIALS` across unpartitioned tables. In distributed clusters (Spark/Trino), this forces expensive **Shuffle Operations**—serializing millions of rows across network cards.
                - **Exasol:** Physical slices of all 5 tables are co-located in memory on `internal_part_num`. Joins are executed as **local hash lookups with 0 network hops**, scaling with flat sub-second latency even as volume grows to 10,000+ rows.
                """
            )
