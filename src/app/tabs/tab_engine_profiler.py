"""Exasol Engine & SQL Profiler Tab Module for Mangrove Cockpit."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from src.exasol_engine.db_client import ChakanExasolClient


def render_exasol_engine_tab(client: ChakanExasolClient, marts: dict, project_root: Path | None = None) -> None:
    """Render Tab 7: Exasol Personal Architecture, In-Database UDFs, & SQL Execution Profiler."""
    if project_root is None:
        project_root = Path(__file__).resolve().parents[3]

    st.subheader("Exasol Personal Architecture & In-Database UDF Definitions")
    st.markdown(
        """
        This solution uses **Exasol Personal** (`CHAKAN_SCM` schema) as the core analytical and data-harmonization platform:
        - **Schema Distribution (`DISTRIBUTE BY`):** `ITEM_MASTER`, `PURCHASE_ORDER_LINES`, `WAREHOUSE_INVENTORY_LEDGER`, and `SUPPLIER_CATALOG_CROSS_REF` distribute on `internal_part_num`; `BILL_OF_MATERIALS` distributes on `component_part_num` so part-level joins align.
        - **In-Database Python 3 Scalar UDFs:** `UDF_NORMALIZE_UOM`, `UDF_RESOLVE_SUPPLIER_SKU`, and `UDF_PARSE_ASN_DATE` run inside Exasol next to the columnar tables.
        - **Interactive Writeback Loop:** Planner overrides persist directly to `CHAKAN_SCM.ASN_PLANNER_OVERRIDES` and trigger immediate view recalculation.
        """
    )

    sql_dir = project_root / "src" / "exasol_engine"
    t_ddl, t_udf, t_views, t_prof = st.tabs(
        [
            "1. MPP Schema DDL (ddl_schema.sql)",
            "2. Python 3 UDFs (udfs_harmonization.sql)",
            "3. Analytical Views (blast_radius_marts.sql)",
            "4. Live Query Profiler & Execution Pipeline",
        ]
    )
    with t_ddl:
        st.code((sql_dir / "ddl_schema.sql").read_text(encoding="utf-8"), language="sql")
    with t_udf:
        st.code((sql_dir / "udfs_harmonization.sql").read_text(encoding="utf-8"), language="sql")
    with t_views:
        st.code((sql_dir / "blast_radius_marts.sql").read_text(encoding="utf-8"), language="sql")
    with t_prof:
        telemetry = marts.get("telemetry", {})
        stages = telemetry.get("latency_stages_ms", {})
        s1_ms = stages.get("view_inventory_true_atp", stages.get("inventory_mart", 0.0))
        s2_ms = stages.get("view_asn_harmonized_lineage", stages.get("asn_harmonization", 0.0))
        s3_ms = stages.get("view_bom_line_starvation_risk", stages.get("bom_risk_mart", 0.0))
        s4_ms = stages.get("python_triage_postprocess", stages.get("triage_and_roi", 0.0))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stage 1: True ATP Mart", f"{s1_ms:.2f} ms", "VW_INVENTORY_TRUE_ATP")
        c2.metric("Stage 2: ASN UDF Lineage", f"{s2_ms:.2f} ms", "VW_ASN_HARMONIZED_LINEAGE")
        c3.metric("Stage 3: BOM Starvation Risk", f"{s3_ms:.2f} ms", "VW_BOM_LINE_STARVATION_RISK")
        c4.metric("Stage 4: Triage & ROI Rollup", f"{s4_ms:.2f} ms", "Triage Ranking & ROI")

        st.markdown("---")
        col_prof1, col_prof2 = st.columns([1, 1])
        with col_prof1:
            st.markdown("**Schema Distribution Strategy (`ddl_schema.sql`):**")
            st.markdown(
                """
                Tables in `CHAKAN_SCM` are partitioned on their primary join keys so part-level joins align across slices:
                - `ITEM_MASTER`, `PURCHASE_ORDER_LINES`, `WAREHOUSE_INVENTORY_LEDGER`, `SUPPLIER_CATALOG_CROSS_REF`: `DISTRIBUTE BY (internal_part_num)`
                - `BILL_OF_MATERIALS`: `DISTRIBUTE BY (component_part_num)`
                - `PRODUCTION_SCHEDULES`: `DISTRIBUTE BY (parent_part_num)`
                - `ASN_LINES_RAW`, `ASN_PLANNER_OVERRIDES`: `DISTRIBUTE BY (po_number_ref)` / `(asn_line_id)`
                """
            )
        with col_prof2:
            st.markdown("**Live Table Row Counts:**")
            counts = telemetry.get("table_row_counts", {})
            prof_table = pd.DataFrame(
                [
                    {"Table Name": "ASN_LINES_RAW", "Distribution Key": "po_number_ref", "Storage": "Columnar RAM", "Rows": f"{counts.get('ASN_LINES_RAW', 0):,}"},
                    {"Table Name": "PURCHASE_ORDER_LINES", "Distribution Key": "internal_part_num", "Storage": "Columnar RAM", "Rows": f"{counts.get('PURCHASE_ORDER_LINES', 0):,}"},
                    {"Table Name": "ITEM_MASTER", "Distribution Key": "internal_part_num", "Storage": "Columnar RAM", "Rows": f"{counts.get('ITEM_MASTER', 0):,}"},
                    {"Table Name": "BILL_OF_MATERIALS", "Distribution Key": "component_part_num", "Storage": "Columnar RAM", "Rows": f"{counts.get('BILL_OF_MATERIALS', 0):,}"},
                    {"Table Name": "WAREHOUSE_INVENTORY_LEDGER", "Distribution Key": "internal_part_num", "Storage": "Columnar RAM", "Rows": f"{counts.get('WAREHOUSE_INVENTORY_LEDGER', 0):,}"},
                    {"Table Name": "PRODUCTION_SCHEDULES", "Distribution Key": "parent_part_num", "Storage": "Columnar RAM", "Rows": f"{counts.get('PRODUCTION_SCHEDULES', 0):,}"},
                    {"Table Name": "SUPPLIER_MASTER", "Distribution Key": "supplier_id (PK)", "Storage": "Columnar RAM", "Rows": f"{counts.get('SUPPLIER_MASTER', 0):,}"},
                    {"Table Name": "ASN_PLANNER_OVERRIDES", "Distribution Key": "asn_line_id", "Storage": "Columnar RAM", "Rows": f"{counts.get('ASN_PLANNER_OVERRIDES', 0):,}"},
                ]
            )
            st.dataframe(prof_table, use_container_width=True, hide_index=True)

        st.markdown("---")
        measured_ms = float(marts.get("query_latency_ms", 0.0))
        compute_src = marts.get("compute_source", telemetry.get("compute_source", "PANDAS_MIRROR"))
        asn_rows = int(telemetry.get("total_asns", 498))
        st.markdown("### Native Exasol Query Execution Pipeline")
        st.caption(f"Live compute source: `{compute_src}` | Measured round-trip latency: `{measured_ms:.2f} ms`")

        st.code(
            f"""-- LOGICAL EXECUTION PIPELINE (VW_BOM_LINE_STARVATION_RISK)
----------------------------------------------------------------------------------------------------------------
STAGE 1: IN-MEMORY COLUMNAR SCAN & DEDUPLICATION
  -> SCAN CHAKAN_SCM.ASN_LINES_RAW ({asn_rows} records)
  -> ROW_NUMBER() OVER (PARTITION BY asn_number, po_number_ref, raw_supplier_sku, raw_shipped_qty)
  -> DEDUPLICATION FILTER (transmission_seq = 1)

STAGE 2: IN-DATABASE PYTHON 3 SCALAR SCRIPT EXECUTION
  -> EXECUTE SCALAR PYTHON UDF: CHAKAN_SCM.UDF_RESOLVE_SUPPLIER_SKU(raw_supplier_sku, po_part_num)
     [Exact / Hyphen-Normalized / Vendor Alias Catalog / Token / Jaro-Winkler >= 0.85]
  -> EXECUTE SCALAR PYTHON UDF: CHAKAN_SCM.UDF_NORMALIZE_UOM(raw_shipped_qty, raw_shipped_uom, base_uom, pack_size, unit_wt)
     [Standard Pack Multiplication + Weight-to-Count Conversions]
  -> EXECUTE SCALAR PYTHON UDF: CHAKAN_SCM.UDF_PARSE_ASN_DATE(raw_eta_date, default_date_format)

STAGE 3: MULTI-TABLE HASH JOIN ACROSS DISTRIBUTED KEYS
  -> JOIN CHAKAN_SCM.ITEM_MASTER ON (internal_part_num)
  -> JOIN CHAKAN_SCM.BILL_OF_MATERIALS ON (component_part_num)
  -> JOIN CHAKAN_SCM.PRODUCTION_SCHEDULES ON (parent_part_num)
  -> LEFT JOIN CHAKAN_SCM.WAREHOUSE_INVENTORY_LEDGER ON (internal_part_num)

STAGE 4: ANALYTICAL AGGREGATION & STARVATION DEFICIT MATERIALIZATION
  -> COMPUTE TRUE PICKABLE ATP = wms_counted - allocated - quality_hold
  -> COMPUTE HOURLY ASSEMBLY BURN RATE = ROUND(gross_required_qty / 48.0, 2)
  -> COMPUTE STARVATION HORIZON = ROUND(LEAST(48.0, available_qty / hourly_burn_qty), 1)
  -> COMPUTE DOWNTIME LOSS = ROUND(downtime_hours * downtime_burn_rate_inr_hr, 2)
  -> COMPUTE HEADLINE MITIGATION ROI = ROUND((net_stoppage_loss - 45000.0) / 45000.0, 1)
----------------------------------------------------------------------------------------------------------------
MEASURED ROUND-TRIP LATENCY ({compute_src}): {measured_ms:.2f} ms
----------------------------------------------------------------------------------------------------------------""",
            language="sql",
        )
