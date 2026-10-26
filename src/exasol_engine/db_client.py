from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, Tuple
from dotenv import load_dotenv
import numpy as np
import pandas as pd

from src.data_generator.generate_all import generate_dataset
from src.exasol_engine import domain_config
from src.exasol_engine.harmonizer_core import (
    normalize_uom_quantity,
    parse_asn_date,
    resolve_supplier_sku,
)

load_dotenv()
GENESIS_HASH: str = "GENESIS_HASH_BLOCK_" + ("0" * 45)


class ExasolBootstrapError(RuntimeError):
    """Raised when DDL, UDF, view deployment or table loading fails or is incomplete."""


class ExasolWriteError(RuntimeError):
    """Raised when a planner write-back to Exasol fails while a live connection exists."""


class ChakanExasolClient:
    """
    Manages connection to Exasol Personal via pyexasol and executes DDL, UDF registration,
    bulk table loading, and sub-second blast-radius analytical queries.
    Includes a deterministic in-memory execution mode when Exasol Personal is offline.
    """

    def __init__(self, data_dir: str = "data/raw") -> None:
        self.dsn = os.getenv("EXASOL_DSN", "localhost:8563")
        self.user = os.getenv("EXASOL_USER", "sys")
        self.password = os.getenv("EXASOL_PASSWORD", "exasol")
        self.schema = os.getenv("EXASOL_SCHEMA", "CHAKAN_SCM")
        self.data_dir = Path(data_dir)
        self.conn = None
        self.mode = "LOCAL_MIRROR"
        self.tables: Dict[str, pd.DataFrame] = {}
        self.last_fallback_reason: str | None = None

    def connect(self) -> bool:
        try:
            import pyexasol  # type: ignore

            encryption = os.getenv("EXASOL_ENCRYPTION", "True").lower() == "true"
            try:
                self.conn = pyexasol.connect(
                    dsn=self.dsn,
                    user=self.user,
                    password=self.password,
                    schema=self.schema,
                    encryption=encryption,
                    websocket_sslopt={"cert_reqs": 0},
                    compression=True,
                )
            except Exception:
                # If target schema does not exist yet, connect to system and initialize schema
                self.conn = pyexasol.connect(
                    dsn=self.dsn,
                    user=self.user,
                    password=self.password,
                    encryption=encryption,
                    websocket_sslopt={"cert_reqs": 0},
                    compression=True,
                )
                self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema}")
                self.conn.execute(f"OPEN SCHEMA {self.schema}")

            self.mode = "EXASOL_PERSONAL"
            return True
        except Exception:
            self.conn = None
            self.mode = "LOCAL_MIRROR"
            return False

    def ensure_data_loaded(self) -> Dict[str, pd.DataFrame]:
        if self.tables and all(
            k in self.tables
            for k in (
                "SUPPLIER_MASTER",
                "ITEM_MASTER",
                "BILL_OF_MATERIALS",
                "PRODUCTION_SCHEDULES",
                "WAREHOUSE_INVENTORY_LEDGER",
                "PURCHASE_ORDER_LINES",
                "ASN_LINES_RAW",
                "ASN_PLANNER_OVERRIDES",
                "SUPPLIER_CATALOG_CROSS_REF",
            )
        ):
            return self.tables

        required_files = [
            "supplier_master.csv",
            "item_master.csv",
            "bill_of_materials.csv",
            "production_schedules.csv",
            "warehouse_inventory_ledger.csv",
            "purchase_order_lines.csv",
            "asn_lines_raw.csv",
            "asn_planner_overrides.csv",
            "supplier_catalog_cross_ref.csv",
        ]
        if not all((self.data_dir / f).exists() for f in required_files):
            self.tables = generate_dataset(output_dir=str(self.data_dir))
        else:
            for f in required_files:
                t_name = f.replace(".csv", "").upper()
                self.tables[t_name] = pd.read_csv(self.data_dir / f)

        audit_file = self.data_dir / "audit_log_ledger.csv"
        if audit_file.exists():
            self.tables["AUDIT_LOG_LEDGER"] = pd.read_csv(
                audit_file,
                dtype={"prev_hash": str, "sha256_hash": str, "asn_line_id": str, "event_id": str},
            )
        elif "AUDIT_LOG_LEDGER" not in self.tables:
            self.tables["AUDIT_LOG_LEDGER"] = pd.DataFrame(
                columns=[
                    "event_id",
                    "event_type",
                    "asn_line_id",
                    "resolved_part_num",
                    "normalized_qty",
                    "normalized_uom",
                    "action",
                    "operator_id",
                    "timestamp",
                    "sha256_hash",
                    "prev_hash",
                ]
            )

        return self.tables

    def bootstrap_exasol_schema_and_data(self) -> Tuple[str, float]:
        """
        Deploys DDL, Python3 UDFs and analytical views to Exasol and loads all tables.

        Every statement failure is collected and raised together as ExasolBootstrapError.
        After loading, row counts in Exasol are verified against the source frames so a
        partial load can never be reported as success.
        """
        t0 = time.perf_counter()
        self.ensure_data_loaded()

        if self.conn is None:
            self.connect()

        if self.conn is not None:
            import re
            sql_dir = Path(__file__).parent
            errors: list[str] = []

            def run_stmt(label: str, stmt: str) -> None:
                try:
                    self.conn.execute(stmt)
                except Exception as exc:  # collected and raised below
                    first_line = stmt.strip().splitlines()[0][:90]
                    errors.append(f"[{label}] {first_line} -> {type(exc).__name__}: {str(exc)[:240]}")

            # 1. DDL Schema
            ddl_sql = (sql_dir / "ddl_schema.sql").read_text(encoding="utf-8")
            for block in ddl_sql.split(";"):
                clean = "\n".join([l for l in block.splitlines() if not l.strip().startswith("--")]).strip()
                if clean:
                    run_stmt("DDL", clean)

            # 2. Python 3 UDFs (delimited by /)
            udf_sql = (sql_dir / "udfs_harmonization.sql").read_text(encoding="utf-8")
            udf_blocks = [b.strip() for b in re.split(r"\n/\s*\n", udf_sql) if b.strip()]
            for b in udf_blocks:
                clean_lines = []
                for l in b.splitlines():
                    if l.strip().startswith("--") or l.strip().upper().startswith("OPEN SCHEMA"):
                        continue
                    clean_lines.append(l)
                clean = "\n".join(clean_lines).strip().rstrip("/").rstrip(";").strip()
                if clean:
                    run_stmt("UDF", clean)

            # 3. Analytical Views
            views_sql = (sql_dir / "blast_radius_marts.sql").read_text(encoding="utf-8")
            for block in views_sql.split(";"):
                clean = "\n".join([l for l in block.splitlines() if not l.strip().startswith("--")]).strip()
                if clean:
                    run_stmt("VIEW", clean)

            # 4. Import Tables from Pandas, then verify row counts
            for table_name, df in self.tables.items():
                if len(df) > 0:
                    try:
                        self.conn.execute(f"TRUNCATE TABLE {self.schema}.{table_name}")
                        self.conn.import_from_pandas(df, (self.schema, table_name))
                        loaded = int(self.conn.execute(f"SELECT COUNT(*) FROM {self.schema}.{table_name}").fetchone()[0])
                        if loaded != len(df):
                            errors.append(f"[LOAD] {table_name}: expected {len(df)} rows, Exasol holds {loaded}")
                    except Exception as exc:
                        errors.append(f"[LOAD] {table_name} -> {type(exc).__name__}: {str(exc)[:240]}")

            # 5. Seed POLICY_PARAMETERS from domain_config (SSOT)
            policies = [
                ("PLANNING_HORIZON_HOURS", domain_config.PLANNING_HORIZON_HOURS, "TIME_HORIZON", "Standard production cycle buffer horizon in hours"),
                ("EBITDA_MARGIN_RATIO", domain_config.EBITDA_MARGIN_RATIO, "FINANCIAL", "Protected operating contribution margin ratio on finished vehicles"),
                ("HOT_SHOT_BENCHMARK_FREIGHT_INR", domain_config.HOT_SHOT_BENCHMARK_FREIGHT_INR, "LOGISTICS", "Dedicated single hot-shot air/road courier charter cost"),
                ("FREIGHT_BASE_INR", domain_config.FREIGHT_BASE_INR, "LOGISTICS", "Minimum base dispatch fee for dedicated emergency courier"),
                ("FREIGHT_MAX_INR", domain_config.FREIGHT_MAX_INR, "LOGISTICS", "Maximum ceiling cap on emergency charter per component"),
                ("FREIGHT_WEIGHT_TARIFF_INR_PER_KG", domain_config.FREIGHT_WEIGHT_TARIFF_INR_PER_KG, "LOGISTICS", "Incremental weight tariff per kilogram"),
                ("AVOIDED_PANIC_FREIGHT_INR", domain_config.AVOIDED_PANIC_FREIGHT_INR, "FINANCIAL", "Avoided panic freight cost across 3 uncoordinated courier dispatches"),
                ("TRANSIT_DELAY_DAILY_DECAY", 0.18, "CHAOS_MODEL", "Daily logistics transit drift reduction factor"),
            ]
            for pkey, pval, pcat, pdesc in policies:
                try:
                    self.conn.execute(
                        f"""MERGE INTO {self.schema}.POLICY_PARAMETERS tgt
                        USING (SELECT {{pkey}}, {{pval}}, {{pcat}}, {{pdesc}}, CURRENT_TIMESTAMP FROM DUAL) AS src
                          (policy_key, policy_value, policy_category, description, updated_at)
                        ON tgt.policy_key = src.policy_key
                        WHEN MATCHED THEN UPDATE SET tgt.policy_value = src.policy_value, tgt.updated_at = src.updated_at
                        WHEN NOT MATCHED THEN INSERT VALUES (src.policy_key, src.policy_value, src.policy_category, src.description, src.updated_at)""",
                        {"pkey": pkey, "pval": float(pval), "pcat": pcat, "pdesc": pdesc}
                    )
                except Exception as exc:
                    errors.append(f"[POLICY] {pkey} -> {type(exc).__name__}: {str(exc)[:240]}")

            if errors:
                raise ExasolBootstrapError(
                    f"Exasol bootstrap failed with {len(errors)} error(s):\n  - " + "\n  - ".join(errors)
                )

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return self.mode, elapsed_ms

    def _build_triage_and_roi(
        self, risk_df: pd.DataFrame, active_asns: pd.DataFrame, sched_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Shared post-processing: ranks quarantined ASNs by blast radius and builds the ROI summary.
        Inputs come either from the pandas mirror pipeline or from Exasol view results.
        """
        if "ordered_qty" not in risk_df.columns and "po_ordered_qty" in risk_df.columns:
            risk_df = risk_df.assign(ordered_qty=risk_df["po_ordered_qty"])
        # 4. Build Actionable Quarantine Triage Queue ranked by Blast Radius (Rs)
        comp_blast = (
            risk_df.groupby("component_part_num", as_index=False)
            .agg(
                affected_lines=("assembly_line_id", lambda s: ", ".join(sorted(set(s)))),
                gross_required_qty=("gross_required_qty", "sum"),
                true_pickable_atp_qty=("true_pickable_atp_qty", "first"),
                phantom_inventory_qty=("phantom_inventory_qty", "first"),
                po_ordered_qty=("ordered_qty", "first"),
                min_hours_to_stop_legacy=("hours_to_starvation_legacy", "min"),
                min_hours_to_stop_harmonized=("hours_to_starvation_harmonized", "min"),
                revenue_at_risk_legacy_inr=("revenue_at_risk_legacy_inr", "sum"),
                revenue_at_risk_net_inr=("revenue_at_risk_net_inr", "sum"),
                true_net_deficit_qty=("true_net_deficit_qty", "sum"),
                downtime_burn_rate_inr_hr=("downtime_burn_rate_inr_hr", "max"),
                plant_idle_cost_inr=("plant_idle_cost_inr", "sum"),
                total_stoppage_exposure_inr=("total_stoppage_exposure_inr", "sum"),
                expedited_freight_cost_inr=("expedited_freight_cost_inr", "sum"),
            )
            .rename(columns={"component_part_num": "resolved_part_num"})
        )

        triage_queue = (
            active_asns[active_asns["legacy_etl_status"] == "QUARANTINED"]
            .merge(comp_blast, on="resolved_part_num", how="left")
            .fillna(
                {
                    "affected_lines": "BUFFER_REPLENISHMENT",
                    "revenue_at_risk_legacy_inr": 0.0,
                    "revenue_at_risk_net_inr": 0.0,
                    "true_net_deficit_qty": 0.0,
                    "min_hours_to_stop_legacy": 48.0,
                    "min_hours_to_stop_harmonized": 48.0,
                    "downtime_burn_rate_inr_hr": 0.0,
                    "plant_idle_cost_inr": 0.0,
                    "total_stoppage_exposure_inr": 0.0,
                    "expedited_freight_cost_inr": 0.0,
                }
            )
        )

        numeric_triage_cols = [
            "revenue_at_risk_legacy_inr",
            "revenue_at_risk_net_inr",
            "true_net_deficit_qty",
            "min_hours_to_stop_legacy",
            "min_hours_to_stop_harmonized",
            "downtime_burn_rate_inr_hr",
            "plant_idle_cost_inr",
            "total_stoppage_exposure_inr",
            "expedited_freight_cost_inr",
        ]
        for c in numeric_triage_cols:
            if c in triage_queue.columns:
                triage_queue[c] = pd.to_numeric(triage_queue[c], errors="coerce").fillna(0.0)

        def classify_operational_outcome(r: pd.Series) -> str:
            if int(r["transmission_seq"]) > 1:
                return "DUPLICATE_PAYLOAD_SUPPRESSED"
            if float(r["true_net_deficit_qty"]) > 0:
                return "CRITICAL_SHORT_SHIPMENT_EXPOSED"
            if float(r["revenue_at_risk_legacy_inr"]) > 0 and float(r["true_net_deficit_qty"]) == 0:
                return "FALSE_STARVATION_CLEARED_BY_UDF"
            return "HARMONIZED_BUFFER_RESTORED"

        if len(triage_queue) == 0:
            triage_queue["operational_verdict"] = pd.Series(dtype=object)
            triage_queue["mitigation_roi_x"] = pd.Series(dtype=float)
            triage_queue["avoided_panic_freight_inr"] = pd.Series(dtype=float)
        else:
            triage_queue["operational_verdict"] = triage_queue.apply(classify_operational_outcome, axis=1)
            triage_queue["mitigation_roi_x"] = np.maximum(
                0.0,
                np.where(
                    (triage_queue["expedited_freight_cost_inr"] > 0) & (triage_queue["plant_idle_cost_inr"] > 0),
                    ((triage_queue["plant_idle_cost_inr"] - triage_queue["expedited_freight_cost_inr"]) / triage_queue["expedited_freight_cost_inr"]).round(1),
                    0.0,
                ),
            )
            triage_queue["avoided_panic_freight_inr"] = np.where(
                triage_queue["operational_verdict"] == "FALSE_STARVATION_CLEARED_BY_UDF",
                45000.0,
                0.0,
            )
        triage_queue = triage_queue.sort_values(
            by=["revenue_at_risk_legacy_inr", "true_net_deficit_qty"], ascending=[False, False]
        )

        # 5. Financial ROI Executive Summary Mart (Formulation 3 Boardroom Defense)
        total_sched_val = float((sched_df["planned_output_units"] * sched_df["finished_unit_value_inr"]).sum())
        legacy_risk = float(risk_df["revenue_at_risk_legacy_inr"].sum())
        net_risk = float(risk_df["revenue_at_risk_net_inr"].sum())
        cleared_val = max(0.0, legacy_risk - net_risk)
        total_idle_loss = float(risk_df["plant_idle_cost_inr"].sum())
        total_stoppage_loss = float(risk_df["total_stoppage_exposure_inr"].sum())
        total_freight_cost = float(risk_df["expedited_freight_cost_inr"].sum())
        benchmark_freight_inr = domain_config.HOT_SHOT_BENCHMARK_FREIGHT_INR
        # Manufacturing Economics: Unrecoverable factory idle burn + 15% operating contribution margin
        contribution_margin_inr = round(net_risk * domain_config.EBITDA_MARGIN_RATIO, 2)
        unrecoverable_stoppage_inr = round(total_idle_loss + contribution_margin_inr, 2)

        # Realistic Industrial ROI: Avoided unrecoverable plant idle loss vs total expedited freight
        headline_roi_x = round((total_idle_loss - benchmark_freight_inr) / benchmark_freight_inr, 1) if benchmark_freight_inr > 0 else 0.0
        all_lines_roi_x = round((total_idle_loss - total_freight_cost) / total_freight_cost, 1) if total_freight_cost > 0 else 0.0
        contribution_margin_roi_x = round((contribution_margin_inr - total_freight_cost) / total_freight_cost, 1) if total_freight_cost > 0 else 0.0
        total_financial_roi_x = round((unrecoverable_stoppage_inr - total_freight_cost) / total_freight_cost, 1) if total_freight_cost > 0 else 0.0
        false_alarms_cleared_count = int((triage_queue["operational_verdict"] == "FALSE_STARVATION_CLEARED_BY_UDF").sum())
        avoided_panic_freight_total = max(domain_config.AVOIDED_PANIC_FREIGHT_INR, false_alarms_cleared_count * benchmark_freight_inr)

        financial_roi_mart = {
            "total_scheduled_value_inr": total_sched_val,
            "legacy_risk_inr": legacy_risk,
            "net_risk_inr": net_risk,
            "cleared_by_udf_inr": cleared_val,
            "total_idle_loss_inr": total_idle_loss,
            "contribution_margin_at_risk_inr": contribution_margin_inr,
            "unrecoverable_stoppage_exposure_inr": unrecoverable_stoppage_inr,
            "total_stoppage_exposure_inr": total_stoppage_loss,
            "benchmark_freight_inr": benchmark_freight_inr,
            "total_freight_cost_inr": total_freight_cost,
            "headline_roi_x": headline_roi_x,
            "all_lines_roi_x": all_lines_roi_x,
            "contribution_margin_roi_x": contribution_margin_roi_x,
            "total_financial_roi_x": total_financial_roi_x,
            "false_alarms_cleared_count": false_alarms_cleared_count,
            "avoided_panic_freight_inr": avoided_panic_freight_total,
        }

        return triage_queue, financial_roi_mart

    def _fetch_df(self, sql: str) -> pd.DataFrame:
        """Runs a query on Exasol over the active WebSocket session and returns a normalized DataFrame."""
        stmt = self.conn.execute(sql)
        cols = [str(c).lower() for c in stmt.column_names()]
        rows = stmt.fetchall()
        df = pd.DataFrame.from_records(rows, columns=cols)
        skip_suffixes = ("_id", "_code", "_sku", "_num", "_format", "_name", "_action", "_by", "_method", "_state", "_verdict", "_status", "_type", "_category", "_ts", "_date")
        for col in df.columns:
            if df[col].dtype == object:
                # First convert any Decimal instances to float
                df[col] = df[col].apply(lambda v: float(v) if isinstance(v, Decimal) else v)
                # Attempt conversion to numeric if it's not a text identifier
                if not any(col.endswith(sfx) for sfx in skip_suffixes):
                    try:
                        converted = pd.to_numeric(df[col], errors="coerce")
                        if converted.notna().sum() > 0 and converted.notna().sum() == df[col].notna().sum():
                            df[col] = converted
                    except (ValueError, TypeError):
                        pass
        return df

    def _make_telemetry(
        self,
        compute_source: str,
        elapsed_ms: float,
        stages: Dict[str, float],
        table_row_counts: Dict[str, int],
        total_asns: int,
        sim_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        in_exasol = compute_source == "EXASOL_VIEWS"
        return {
            "engine_mode": "EXASOL_PERSONAL" if in_exasol else "LOCAL_MIRROR",
            "compute_source": compute_source,
            "connected_to_exasol": self.conn is not None,
            "fallback_reason": self.last_fallback_reason,
            "latency_ms": elapsed_ms,
            "latency_sla_target_ms": 15.0,
            "total_rows_evaluated": int(sum(table_row_counts.values())),
            "total_asns": int(total_asns),
            "table_row_counts": table_row_counts,
            "colocation_key": "internal_part_num",
            "colocation_keys": [
                "internal_part_num",
                "component_part_num",
                "po_number_ref",
                "parent_part_num",
            ],
            "colocation_status": "CO_LOCATED_ACTIVE" if in_exasol else "MIRROR_IN_PROCESS",
            "cluster_nodes": 1,  # Single-node Exasol Personal Docker container
            "inter_node_hops": 0,  # Zero inter-node hops on single-node shared RAM
            "ram_cache_status": "HOT_COLUMNAR_RAM" if in_exasol else "APP_PROCESS_MEMORY",
            "udf_engine": "PYTHON3_IN_DB_RAM" if in_exasol else "PYTHON_APP_PROCESS",
            "schema": self.schema,
            "dsn": self.dsn,
            "simulation_parameters": sim_params,
            "is_simulated": bool(
                int(sim_params["transit_delay_days"]) > 0
                or float(sim_params["quarantine_defect_pct"]) > 0.0
                or float(sim_params["demand_surge_multiplier"]) != 1.0
            ),
            "latency_stages_ms": stages,
        }

    def _sync_simulation_parameters_to_exasol(
        self,
        transit_delay_days: int = 0,
        quarantine_defect_pct: float = 0.0,
        demand_surge_multiplier: float = 1.0,
    ) -> None:
        """Syncs simulation scenario parameters into Exasol SIMULATION_PARAMETERS table via atomic MERGE."""
        if self.conn is None:
            return
        try:
            merge_sql = f"""
            MERGE INTO {self.schema}.SIMULATION_PARAMETERS tgt
            USING (
                SELECT CAST(CURRENT_SESSION AS VARCHAR(40)), {{transit_delay_days}}, {{quarantine_defect_pct}}, {{demand_surge_multiplier}}, CURRENT_TIMESTAMP
                FROM DUAL
            ) AS src (
                session_id, transit_delay_days, quarantine_defect_pct, demand_surge_multiplier, updated_at
            )
            ON tgt.session_id = src.session_id
            WHEN MATCHED THEN UPDATE SET
                tgt.transit_delay_days = src.transit_delay_days,
                tgt.quarantine_defect_pct = src.quarantine_defect_pct,
                tgt.demand_surge_multiplier = src.demand_surge_multiplier,
                tgt.updated_at = src.updated_at
            WHEN NOT MATCHED THEN INSERT VALUES (
                src.session_id, src.transit_delay_days, src.quarantine_defect_pct, src.demand_surge_multiplier, src.updated_at
            )
            """
            self.conn.execute(
                merge_sql,
                {
                    "transit_delay_days": int(transit_delay_days),
                    "quarantine_defect_pct": float(quarantine_defect_pct),
                    "demand_surge_multiplier": float(demand_surge_multiplier),
                },
            )
            self.conn.execute(
                f"DELETE FROM {self.schema}.SIMULATION_PARAMETERS WHERE updated_at < ADD_DAYS(CURRENT_TIMESTAMP, -1)"
            )
        except Exception as exc:
            raise ExasolWriteError(f"Simulation parameters could not be synced to Exasol: {exc}") from exc

    def _scenario_totals(
        self,
        transit_delay_days: int,
        quarantine_defect_pct: float,
        demand_surge_multiplier: float,
        source: str = "auto",
    ) -> Tuple[float, float]:
        """
        Lightweight scenario read: (net revenue at risk, total stoppage exposure) for one parameter set.
        On live Exasol this is a single aggregate over VW_BOM_LINE_STARVATION_RISK (no triage/ROI
        round-trips); offline it falls back to the full mirror.
        """
        if source in ("auto", "exasol") and self.conn is not None:
            try:
                self._sync_simulation_parameters_to_exasol(
                    transit_delay_days, quarantine_defect_pct, demand_surge_multiplier
                )
                row = self._fetch_df(
                    f"SELECT SUM(revenue_at_risk_net_inr) AS net_risk, "
                    f"SUM(total_stoppage_exposure_inr) AS exposure FROM {self.schema}.VW_BOM_LINE_STARVATION_RISK"
                ).iloc[0]
                return float(row["net_risk"]), float(row["exposure"])
            except Exception:
                if source == "exasol":
                    raise
        m = self.compute_analytical_marts(
            transit_delay_days, quarantine_defect_pct, demand_surge_multiplier, source=source
        )
        roi = m["financial_roi_mart"]
        return float(roi["net_risk_inr"]), float(roi["total_stoppage_exposure_inr"])

    def _compute_marts_from_exasol(
        self,
        transit_delay_days: int = 0,
        quarantine_defect_pct: float = 0.0,
        demand_surge_multiplier: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Baseline marts computed BY Exasol: inventory ATP, UDF-harmonized ASN lineage and BOM
        starvation risk are read from the deployed views (which invoke the Python3 UDFs and
        join planner overrides inside the database). Only the quarantine ranking and ROI
        roll-up are post-processed in Python on those results.
        """
        if self.conn is None:
            raise ExasolBootstrapError("No live Exasol connection available for view-based computation.")

        self.ensure_data_loaded()
        t0 = time.perf_counter()
        s = self.schema
        stages: Dict[str, float] = {}

        # 1. Sync simulation parameters into Exasol memory so SQL views evaluate them in-database
        self._sync_simulation_parameters_to_exasol(
            transit_delay_days=transit_delay_days,
            quarantine_defect_pct=quarantine_defect_pct,
            demand_surge_multiplier=demand_surge_multiplier,
        )

        def timed(name: str, sql: str) -> pd.DataFrame:
            ts = time.perf_counter()
            df = self._fetch_df(sql)
            stages[name] = round((time.perf_counter() - ts) * 1000.0, 2)
            return df

        inv_mart = timed("view_inventory_true_atp", f"SELECT * FROM {s}.VW_INVENTORY_TRUE_ATP")
        asn_joined = timed("view_asn_harmonized_lineage", f"SELECT * FROM {s}.VW_ASN_HARMONIZED_LINEAGE")
        risk_df = timed("view_bom_line_starvation_risk", f"SELECT * FROM {s}.VW_BOM_LINE_STARVATION_RISK")
        roi_view_df = timed("view_financial_roi_summary", f"SELECT * FROM {s}.VW_FINANCIAL_ROI_SUMMARY")
        triage_queue = timed("view_triage_dispatch_queue", f"SELECT * FROM {s}.VW_TRIAGE_DISPATCH_QUEUE")

        ts = time.perf_counter()
        sched_df = self.tables["PRODUCTION_SCHEDULES"]
        table_row_counts = {
            t: len(self.tables[t])
            for t in (
                "ASN_LINES_RAW",
                "PURCHASE_ORDER_LINES",
                "ITEM_MASTER",
                "BILL_OF_MATERIALS",
                "PRODUCTION_SCHEDULES",
                "WAREHOUSE_INVENTORY_LEDGER",
                "SUPPLIER_MASTER",
                "ASN_PLANNER_OVERRIDES",
            )
        }
        total_sched_val = float((sched_df["planned_output_units"] * sched_df["finished_unit_value_inr"]).sum())
        roi_row = roi_view_df.iloc[0] if len(roi_view_df) > 0 else {}
        false_alarms_cleared_count = int((triage_queue["operational_verdict"] == "FALSE_STARVATION_CLEARED_BY_UDF").sum())
        avoided_panic_freight_total = max(
            domain_config.AVOIDED_PANIC_FREIGHT_INR,
            false_alarms_cleared_count * domain_config.HOT_SHOT_BENCHMARK_FREIGHT_INR,
        )

        financial_roi_mart = {
            "total_scheduled_value_inr": total_sched_val,
            "legacy_risk_inr": float(roi_row.get("legacy_pipeline_risk_inr", 0.0)),
            "net_risk_inr": float(roi_row.get("net_starvation_risk_inr", 0.0)),
            "cleared_by_udf_inr": float(roi_row.get("false_alarm_value_cleared_inr", 0.0)),
            "total_idle_loss_inr": float(roi_row.get("plant_idle_overhead_at_risk_inr", 0.0)),
            "contribution_margin_at_risk_inr": float(roi_row.get("contribution_margin_at_risk_inr", 0.0)),
            "unrecoverable_stoppage_exposure_inr": float(roi_row.get("unrecoverable_stoppage_exposure_inr", 0.0)),
            "total_stoppage_exposure_inr": float(roi_row.get("total_plant_loss_exposure_inr", 0.0)),
            "benchmark_freight_inr": domain_config.HOT_SHOT_BENCHMARK_FREIGHT_INR,
            "total_freight_cost_inr": float(roi_row.get("total_mitigation_cost_inr", 0.0)),
            "headline_roi_x": float(roi_row.get("headline_mitigation_roi_x", 0.0)),
            "all_lines_roi_x": float(roi_row.get("all_lines_mitigation_roi_x", 0.0)),
            "contribution_margin_roi_x": round((float(roi_row.get("contribution_margin_at_risk_inr", 0.0)) - float(roi_row.get("total_mitigation_cost_inr", 0.0))) / float(roi_row.get("total_mitigation_cost_inr", 1.0)), 1) if float(roi_row.get("total_mitigation_cost_inr", 0.0)) > 0 else 0.0,
            "total_financial_roi_x": round((float(roi_row.get("unrecoverable_stoppage_exposure_inr", 0.0)) - float(roi_row.get("total_mitigation_cost_inr", 0.0))) / float(roi_row.get("total_mitigation_cost_inr", 1.0)), 1) if float(roi_row.get("total_mitigation_cost_inr", 0.0)) > 0 else 0.0,
            "false_alarms_cleared_count": false_alarms_cleared_count,
            "avoided_panic_freight_inr": avoided_panic_freight_total,
        }
        stages["python_triage_postprocess"] = round((time.perf_counter() - ts) * 1000.0, 2)

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        sim_params = {
            "transit_delay_days": int(transit_delay_days),
            "quarantine_defect_pct": float(quarantine_defect_pct),
            "demand_surge_multiplier": float(demand_surge_multiplier),
        }
        telemetry = self._make_telemetry(
            "EXASOL_VIEWS", elapsed_ms, stages, table_row_counts, table_row_counts["ASN_LINES_RAW"], sim_params
        )
        return {
            "engine_mode": "EXASOL_PERSONAL",
            "compute_source": "EXASOL_VIEWS",
            "query_latency_ms": elapsed_ms,
            "inventory_mart": inv_mart,
            "asn_lineage_mart": asn_joined,
            "bom_risk_mart": risk_df,
            "triage_queue": triage_queue,
            "financial_roi_mart": financial_roi_mart,
            "telemetry": telemetry,
        }

    def _baseline_cache_key(self, source: str) -> Tuple[Any, ...]:
        t = self.tables
        return (
            source,
            self.conn is not None,
            len(t.get("ASN_PLANNER_OVERRIDES", [])),
            len(t.get("AUDIT_LOG_LEDGER", [])),
            len(t.get("ASN_LINES_RAW", [])),
            id(t.get("ASN_LINES_RAW")),
        )

    def compute_analytical_marts(
        self,
        transit_delay_days: int = 0,
        quarantine_defect_pct: float = 0.0,
        demand_surge_multiplier: float = 1.0,
        source: str = "auto",
    ) -> Dict[str, Any]:
        """Baseline results are memoized per data version (overrides/audit/ASN batch); scenarios never are."""
        sim_active = (
            int(transit_delay_days) > 0
            or float(quarantine_defect_pct) > 0.0
            or float(demand_surge_multiplier) != 1.0
        )
        if sim_active or source not in ("auto", "exasol", "pandas"):
            return self._compute_analytical_marts_uncached(
                transit_delay_days, quarantine_defect_pct, demand_surge_multiplier, source
            )
        self.ensure_data_loaded()
        key = self._baseline_cache_key(source)
        cache = getattr(self, "_baseline_cache", None)
        if cache is not None and cache[0] == key:
            return dict(cache[1])
        result = self._compute_analytical_marts_uncached(0, 0.0, 1.0, source)
        self._baseline_cache = (key, result)
        return dict(result)

    def _compute_analytical_marts_uncached(
        self,
        transit_delay_days: int = 0,
        quarantine_defect_pct: float = 0.0,
        demand_surge_multiplier: float = 1.0,
        source: str = "auto",
    ) -> Dict[str, Any]:
        """
        Computes the analytical marts (True ATP -> ASN UDF harmonization -> BOM blast radius).

        source:
          - "auto":   baseline requests use Exasol views when a live connection exists; otherwise
                      (or when simulation parameters are set) the pandas pipeline is used.
          - "exasol": always use Exasol views; raises if unavailable.
          - "pandas": always use the in-process pandas pipeline (offline fallback, simulation model).

        The result always states where the numbers were computed in `compute_source`.
        """
        sim_active = (
            int(transit_delay_days) > 0
            or float(quarantine_defect_pct) > 0.0
            or float(demand_surge_multiplier) != 1.0
        )
        if source not in ("auto", "exasol", "pandas"):
            raise ValueError(f"Unknown source '{source}'")
        if source == "exasol" or (source == "auto" and self.conn is not None):
            try:
                result = self._compute_marts_from_exasol(transit_delay_days, quarantine_defect_pct, demand_surge_multiplier)
                self.last_fallback_reason = None
                return result
            except Exception as exc:
                if source == "exasol":
                    raise
                self.last_fallback_reason = f"{type(exc).__name__}: {str(exc)[:200]}"

        t0 = time.perf_counter()
        t_mark = t0
        stage_ms: Dict[str, float] = {}
        self.ensure_data_loaded()

        sup_df = self.tables["SUPPLIER_MASTER"].copy()
        item_df = self.tables["ITEM_MASTER"].copy()
        bom_df = self.tables["BILL_OF_MATERIALS"].copy()
        sched_df = self.tables["PRODUCTION_SCHEDULES"].copy()
        inv_df = self.tables["WAREHOUSE_INVENTORY_LEDGER"].copy()
        po_df = self.tables["PURCHASE_ORDER_LINES"].copy()
        asn_df = self.tables["ASN_LINES_RAW"].copy()
        ov_df = self.tables["ASN_PLANNER_OVERRIDES"].copy()

        if float(demand_surge_multiplier) != 1.0:
            sched_df["planned_output_units"] = (sched_df["planned_output_units"] * float(demand_surge_multiplier)).round(0)

        # 1. True ATP & Phantom Inventory Mart
        inv_mart = inv_df.merge(
            item_df[["internal_part_num", "part_description", "part_category", "base_uom", "standard_cost_inr", "safety_stock_qty"]],
            on="internal_part_num",
            how="left",
        )
        inv_mart["phantom_inventory_qty"] = np.maximum(0.0, inv_mart["erp_system_on_hand_qty"] - inv_mart["wms_physical_counted_qty"])
        inv_mart["phantom_inventory_value_inr"] = (inv_mart["phantom_inventory_qty"] * inv_mart["standard_cost_inr"]).round(2)
        inv_mart["erp_apparent_atp_qty"] = np.maximum(0.0, inv_mart["erp_system_on_hand_qty"] - inv_mart["allocated_to_prod_qty"])

        sim_quality_hold = inv_mart["quality_hold_qty"] * (1.0 + float(quarantine_defect_pct) * 2.0)
        inv_mart["true_pickable_atp_qty"] = np.maximum(
            0.0,
            inv_mart["wms_physical_counted_qty"] - inv_mart["allocated_to_prod_qty"] - sim_quality_hold,
        )

        stage_ms["inventory_mart"] = round((time.perf_counter() - t_mark) * 1000.0, 2)
        t_mark = time.perf_counter()

        # 2. ASN UDF Harmonization & Deduplication Mart
        asn_sorted = asn_df.sort_values("ingested_at").copy()
        clean_asn = asn_sorted["asn_number"].astype(str).str.strip().str.upper()
        clean_po = asn_sorted["po_number_ref"].astype(str).str.strip().str.upper()
        clean_sku = asn_sorted["raw_supplier_sku"].astype(str).str.strip().str.upper()
        clean_qty = pd.to_numeric(
            asn_sorted["raw_shipped_qty"].astype(str).str.replace(",", "").str.strip(), errors="coerce"
        ).fillna(0.0)
        asn_sorted["transmission_seq"] = (
            asn_sorted.groupby([clean_asn, clean_po, clean_sku, clean_qty]).cumcount() + 1
        )

        asn_joined = asn_sorted.merge(
            po_df[["po_number", "line_number", "internal_part_num", "ordered_qty", "ordered_uom", "promised_delivery_date"]],
            left_on=["po_number_ref", "po_line_number_ref"],
            right_on=["po_number", "line_number"],
            how="left",
        ).merge(
            sup_df[["supplier_id", "supplier_name", "tier_level", "default_date_format"]],
            on="supplier_id",
            how="left",
        )

        item_lookup = item_df.set_index("internal_part_num").to_dict(orient="index")
        ov_lookup = ov_df.set_index("asn_line_id").to_dict(orient="index") if len(ov_df) > 0 else {}

        resolved_skus = []
        match_methods = []
        confidences = []
        canonical_uoms = []
        harmonized_qtys = []
        legacy_qtys = []
        harmonized_etas = []
        harm_states = []

        asn_line_ids = asn_joined["asn_line_id"].astype(str).tolist()
        internal_parts = asn_joined["internal_part_num"].tolist()
        raw_skus = asn_joined["raw_supplier_sku"].astype(str).tolist()
        ordered_uoms = asn_joined["ordered_uom"].tolist()
        raw_qtys = asn_joined["raw_shipped_qty"].astype(float).tolist()
        raw_uoms = asn_joined["raw_shipped_uom"].astype(str).tolist()
        transmission_seqs = asn_joined["transmission_seq"].astype(int).tolist()
        legacy_statuses = asn_joined["legacy_etl_status"].astype(str).tolist()
        raw_dates = asn_joined["raw_eta_date"].astype(str).tolist()
        date_formats = (
            asn_joined["default_date_format"].fillna("DD/MM/YYYY").astype(str).tolist()
            if "default_date_format" in asn_joined.columns
            else ["DD/MM/YYYY"] * len(asn_joined)
        )

        xref_df = self.tables.get("SUPPLIER_CATALOG_CROSS_REF", pd.DataFrame())
        catalog_map: Dict[str, str] = {}
        if len(xref_df) > 0:
            active_xref = xref_df[xref_df.get("is_active", True) == True] if "is_active" in xref_df.columns else xref_df
            for _, r in active_xref.iterrows():
                clean_k = re.sub(r"[^A-Z0-9]", "", str(r.get("clean_supplier_part_num", r.get("supplier_part_num", ""))).strip().upper())
                clean_v = str(r.get("internal_part_num", "")).strip().upper()
                if clean_k and clean_v:
                    catalog_map[clean_k] = clean_v

        sku_cache = {}
        date_cache = {}
        uom_cache = {}

        for line_id, po_part, raw_sku, ord_uom, raw_qty, raw_uom, seq, leg_status, raw_date, date_fmt in zip(
            asn_line_ids,
            internal_parts,
            raw_skus,
            ordered_uoms,
            raw_qtys,
            raw_uoms,
            transmission_seqs,
            legacy_statuses,
            raw_dates,
            date_formats,
        ):
            ref_part = str(po_part) if pd.notna(po_part) else None
            sku_k = (raw_sku, ref_part)
            if sku_k not in sku_cache:
                sku_cache[sku_k] = resolve_supplier_sku(raw_sku, ref_part, catalog_map=catalog_map)
            res_sku, method, conf = sku_cache[sku_k]

            if line_id in ov_lookup and pd.notna(ov_lookup[line_id].get("resolved_part_num")):
                res_sku = str(ov_lookup[line_id]["resolved_part_num"])
                method = "PLANNER_VERIFIED"
                conf = 1.00

            item_meta = item_lookup.get(res_sku, {})
            c_uom = str(item_meta.get("base_uom", ord_uom if pd.notna(ord_uom) else "EA"))
            pack_sz = float(item_meta.get("standard_pack_size_ea", 1.0))
            u_wt = float(item_meta.get("unit_weight_kg", 1.0))

            if seq > 1:
                h_qty = 0.0
                state = "DUPLICATE_SUPPRESSED"
            elif line_id in ov_lookup and pd.notna(ov_lookup[line_id].get("normalized_qty")):
                h_qty = float(ov_lookup[line_id]["normalized_qty"])
                state = str(ov_lookup[line_id].get("resolution_action", "PLANNER_APPROVED"))
            else:
                uom_k = (raw_qty, raw_uom, c_uom, pack_sz, u_wt)
                if uom_k not in uom_cache:
                    uom_cache[uom_k] = normalize_uom_quantity(
                        raw_qty,
                        raw_uom,
                        c_uom,
                        pack_size_ea=pack_sz,
                        unit_weight_kg=u_wt,
                    )
                h_qty = uom_cache[uom_k]
                state = (
                    "CLEAN_INGESTED"
                    if leg_status == "ACCEPTED"
                    else "UDF_HARMONIZED_PENDING_APPROVAL"
                )

            leg_qty = raw_qty if (leg_status == "ACCEPTED" and seq == 1) else 0.0

            dt_k = (raw_date, date_fmt)
            if dt_k not in date_cache:
                date_cache[dt_k] = parse_asn_date(raw_date, date_fmt)
            eta_dt = date_cache[dt_k]

            resolved_skus.append(res_sku)
            match_methods.append(method)
            confidences.append(conf)
            canonical_uoms.append(c_uom)
            harmonized_qtys.append(h_qty)
            legacy_qtys.append(leg_qty)
            harmonized_etas.append(eta_dt)
            harm_states.append(state)

        asn_joined["resolved_part_num"] = resolved_skus
        asn_joined["sku_match_method"] = match_methods
        asn_joined["sku_confidence"] = confidences
        asn_joined["canonical_uom"] = canonical_uoms
        asn_joined["harmonized_shipped_qty"] = harmonized_qtys
        asn_joined["legacy_visible_qty"] = legacy_qtys
        asn_joined["harmonized_eta_date"] = harmonized_etas
        asn_joined["harmonization_state"] = harm_states

        stage_ms["asn_harmonization"] = round((time.perf_counter() - t_mark) * 1000.0, 2)
        t_mark = time.perf_counter()

        # 3. BOM Explosion & Line Starvation Risk Mart
        active_asns = asn_joined[asn_joined["po_number_ref"].isin(po_df["po_number"])].copy()

        if int(transit_delay_days) > 0 or float(quarantine_defect_pct) > 0.0:
            inbound_factor = max(0.0, 1.0 - (float(transit_delay_days) * 0.18)) * max(0.0, 1.0 - float(quarantine_defect_pct))
            active_asns["harmonized_shipped_qty"] = (active_asns["harmonized_shipped_qty"] * inbound_factor).round(2)
            active_asns["legacy_visible_qty"] = (active_asns["legacy_visible_qty"] * inbound_factor).round(2)

        # Multi-line PO cartesian fix: group active ASNs by composite key
        active_asns["po_line_join_key"] = active_asns["po_line_number_ref"].fillna(1).astype(int)
        po_asn_agg = (
            active_asns.groupby(["po_number_ref", "resolved_part_num", "po_line_join_key"], as_index=False)
            .agg(
                legacy_inbound_qty=("legacy_visible_qty", "sum"),
                harmonized_inbound_qty=("harmonized_shipped_qty", "sum"),
                asn_shipment_count=("asn_line_id", "count"),
            )
        )
        po_merged = po_df.merge(
            po_asn_agg,
            left_on=["po_number", "internal_part_num", "line_number"],
            right_on=["po_number_ref", "resolved_part_num", "po_line_join_key"],
            how="left",
        )
        po_rollup = (
            po_merged[po_merged["po_line_status"] == "OPEN"]
            .groupby("internal_part_num", as_index=False)
            .agg(
                po_number=("po_number", "first"),
                supplier_id=("supplier_id", "first"),
                ordered_qty=("ordered_qty", "sum"),
                legacy_inbound_qty=("legacy_inbound_qty", "sum"),
                harmonized_inbound_qty=("harmonized_inbound_qty", "sum"),
            )
        )
        po_rollup["legacy_inbound_qty"] = po_rollup["legacy_inbound_qty"].fillna(0.0)
        po_rollup["harmonized_inbound_qty"] = po_rollup["harmonized_inbound_qty"].fillna(0.0)
        po_merged = po_rollup

        bom_lvl1 = bom_df[bom_df["bom_level"] == 1].copy()
        risk_df = (
            sched_df.merge(bom_lvl1, on="parent_part_num", how="inner")
            .merge(
                item_df[["internal_part_num", "part_description", "base_uom", "unit_weight_kg", "standard_cost_inr"]],
                left_on="component_part_num",
                right_on="internal_part_num",
                how="left",
            )
            .merge(
                inv_mart[
                    [
                        "internal_part_num",
                        "erp_apparent_atp_qty",
                        "true_pickable_atp_qty",
                        "phantom_inventory_qty",
                        "phantom_inventory_value_inr",
                    ]
                ],
                on="internal_part_num",
                how="left",
            )
            .merge(
                po_merged[
                    [
                        "po_number",
                        "internal_part_num",
                        "supplier_id",
                        "ordered_qty",
                        "legacy_inbound_qty",
                        "harmonized_inbound_qty",
                    ]
                ],
                on="internal_part_num",
                how="left",
            )
        )

        risk_df["gross_required_qty"] = (
            risk_df["planned_output_units"] * risk_df["qty_per_assembly"] * (1.0 + risk_df["scrap_allowance_pct"])
        ).round(2)
        risk_df["hourly_burn_qty"] = (risk_df["gross_required_qty"] / domain_config.PLANNING_HORIZON_HOURS).round(2)

        # Notice how ERP Apparent Stock tricks the planner if they ignore Phantom Inventory
        risk_df["erp_blind_available_qty"] = risk_df["erp_apparent_atp_qty"] + risk_df["legacy_inbound_qty"]
        risk_df["legacy_total_available_qty"] = risk_df["true_pickable_atp_qty"] + risk_df["legacy_inbound_qty"]
        risk_df["harmonized_total_available_qty"] = risk_df["true_pickable_atp_qty"] + risk_df["harmonized_inbound_qty"]

        risk_df["supplier_short_shipped_qty"] = np.maximum(0.0, risk_df["ordered_qty"] - risk_df["harmonized_inbound_qty"])
        risk_df["legacy_deficit_qty"] = np.maximum(0.0, risk_df["gross_required_qty"] - risk_df["legacy_total_available_qty"]).round(2)
        risk_df["true_net_deficit_qty"] = np.maximum(
            0.0, risk_df["gross_required_qty"] - risk_df["harmonized_total_available_qty"]
        ).round(2)

        risk_df["hours_to_starvation_legacy"] = np.minimum(
            48.0,
            (risk_df["legacy_total_available_qty"] / risk_df["hourly_burn_qty"].replace(0, np.nan)).fillna(48.0),
        ).round(1)
        risk_df["hours_to_starvation_harmonized"] = np.minimum(
            48.0,
            (risk_df["harmonized_total_available_qty"] / risk_df["hourly_burn_qty"].replace(0, np.nan)).fillna(48.0),
        ).round(1)

        risk_df["starved_parent_units_legacy"] = np.ceil(
            risk_df["legacy_deficit_qty"] / risk_df["qty_per_assembly"]
        ).clip(upper=risk_df["planned_output_units"])
        risk_df["starved_parent_units_net"] = np.ceil(
            risk_df["true_net_deficit_qty"] / risk_df["qty_per_assembly"]
        ).clip(upper=risk_df["planned_output_units"])

        risk_df["revenue_at_risk_legacy_inr"] = (
            risk_df["starved_parent_units_legacy"] * risk_df["finished_unit_value_inr"]
        ).round(2)
        risk_df["revenue_at_risk_net_inr"] = (
            risk_df["starved_parent_units_net"] * risk_df["finished_unit_value_inr"]
        ).round(2)

        # Plant Downtime & Financial Exposure Math
        risk_df["downtime_hours_net"] = np.maximum(0.0, domain_config.PLANNING_HORIZON_HOURS - risk_df["hours_to_starvation_harmonized"]).round(1)
        risk_df["plant_idle_cost_inr"] = (risk_df["downtime_hours_net"] * risk_df["downtime_burn_rate_inr_hr"]).round(2)
        risk_df["total_stoppage_exposure_inr"] = (risk_df["revenue_at_risk_net_inr"] + risk_df["plant_idle_cost_inr"]).round(2)
        risk_df["expedited_freight_cost_inr"] = np.where(
            risk_df["true_net_deficit_qty"] > 0,
            np.clip(domain_config.FREIGHT_BASE_INR + risk_df["true_net_deficit_qty"] * risk_df["unit_weight_kg"] * domain_config.FREIGHT_WEIGHT_TARIFF_INR_PER_KG, domain_config.FREIGHT_BASE_INR, domain_config.FREIGHT_MAX_INR).round(2),
            0.0,
        )
        risk_df["mitigation_roi_ratio"] = np.where(
            risk_df["expedited_freight_cost_inr"] > 0,
            ((risk_df["plant_idle_cost_inr"] - risk_df["expedited_freight_cost_inr"]) / risk_df["expedited_freight_cost_inr"]).round(1),
            0.0,
        )

        stage_ms["bom_risk_mart"] = round((time.perf_counter() - t_mark) * 1000.0, 2)
        t_mark = time.perf_counter()
        triage_queue, financial_roi_mart = self._build_triage_and_roi(risk_df, active_asns, sched_df)
        stage_ms["triage_and_roi"] = round((time.perf_counter() - t_mark) * 1000.0, 2)

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        table_row_counts = {
            "ASN_LINES_RAW": len(asn_df),
            "PURCHASE_ORDER_LINES": len(po_df),
            "ITEM_MASTER": len(item_df),
            "BILL_OF_MATERIALS": len(bom_df),
            "PRODUCTION_SCHEDULES": len(sched_df),
            "WAREHOUSE_INVENTORY_LEDGER": len(inv_df),
            "SUPPLIER_MASTER": len(sup_df),
            "ASN_PLANNER_OVERRIDES": len(ov_df),
        }
        sim_params = {
            "transit_delay_days": int(transit_delay_days),
            "quarantine_defect_pct": float(quarantine_defect_pct),
            "demand_surge_multiplier": float(demand_surge_multiplier),
        }
        compute_source = "PANDAS_SIMULATION" if sim_active else "PANDAS_MIRROR"
        telemetry = self._make_telemetry(compute_source, elapsed_ms, stage_ms, table_row_counts, len(asn_df), sim_params)

        return {
            "engine_mode": "LOCAL_MIRROR",
            "compute_source": compute_source,
            "query_latency_ms": elapsed_ms,
            "inventory_mart": inv_mart,
            "asn_lineage_mart": asn_joined,
            "bom_risk_mart": risk_df,
            "triage_queue": triage_queue,
            "financial_roi_mart": financial_roi_mart,
            "telemetry": telemetry,
        }


    def compute_simulation_marts(
        self,
        transit_delay_days: int = 0,
        quarantine_defect_pct: float = 0.0,
        demand_surge_multiplier: float = 1.0,
        source: str = "auto",
    ) -> Dict[str, Any]:
        """
        Computes side-by-side comparative analytics: Baseline state vs Simulated Chaos state.
        Demonstrates Exasol in-memory sub-second recalculation under dynamic supply chain disruptions.
        """
        baseline = self.compute_analytical_marts(0, 0.0, 1.0, source=source)
        simulated = self.compute_analytical_marts(transit_delay_days, quarantine_defect_pct, demand_surge_multiplier, source=source)

        base_net = float(baseline["financial_roi_mart"]["net_risk_inr"])
        sim_net = float(simulated["financial_roi_mart"]["net_risk_inr"])
        delta_net = sim_net - base_net

        base_exposure = float(baseline["financial_roi_mart"]["total_stoppage_exposure_inr"])
        sim_exposure = float(simulated["financial_roi_mart"]["total_stoppage_exposure_inr"])
        delta_exposure = sim_exposure - base_exposure

        base_min_hrs = float(baseline["bom_risk_mart"]["hours_to_starvation_harmonized"].min())
        sim_min_hrs = float(simulated["bom_risk_mart"]["hours_to_starvation_harmonized"].min())
        delta_hrs = round(sim_min_hrs - base_min_hrs, 1)

        step1_net, _ = self._scenario_totals(transit_delay_days, 0.0, 1.0, source)
        step2_net, _ = self._scenario_totals(transit_delay_days, quarantine_defect_pct, 1.0, source)

        s0 = round(base_net, 2)
        s1 = round(step1_net, 2)
        s2 = round(step2_net, 2)
        s3 = round(sim_net, 2)

        waterfall_data = [
            {"Stage": "1. Baseline True Shortage", "Amount": s0, "Type": "relative"},
            {"Stage": "2. Logistics Transit Drift", "Amount": round(s1 - s0, 2), "Type": "relative"},
            {"Stage": "3. Quarantine Defect Spike", "Amount": round(s2 - s1, 2), "Type": "relative"},
            {"Stage": "4. Surge Output Demand", "Amount": round(s3 - s2, 2), "Type": "relative"},
            {"Stage": "Total Simulated Exposure", "Amount": s3, "Type": "total"},
        ]

        return {
            "baseline": baseline,
            "simulated": simulated,
            "delta_net_risk_inr": delta_net,
            "delta_total_exposure_inr": delta_exposure,
            "delta_min_hours_to_halt": delta_hrs,
            "waterfall_data": waterfall_data,
            "simulation_parameters": {
                "transit_delay_days": int(transit_delay_days),
                "quarantine_defect_pct": float(quarantine_defect_pct),
                "demand_surge_multiplier": float(demand_surge_multiplier),
            },
        }

    def _log_audit_event(
        self,
        event_type: str,
        asn_line_id: str,
        resolved_part_num: str,
        normalized_qty: float,
        normalized_uom: str,
        action: str,
        operator_id: str,
    ) -> str:
        """
        Appends an immutable, cryptographically chained SHA-256 audit block to AUDIT_LOG_LEDGER.
        Returns the 64-character hexadecimal SHA-256 fingerprint.
        """
        audit_df = self.tables.get("AUDIT_LOG_LEDGER")
        if audit_df is None or len(audit_df) == 0:
            prev_hash = GENESIS_HASH
            next_seq = 1
        else:
            prev_hash = str(audit_df.iloc[-1].get("sha256_hash", GENESIS_HASH))
            next_seq = len(audit_df) + 1

        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        event_id = f"AUD-{datetime.now().strftime('%Y%m%d')}-{next_seq:04d}"

        payload = f"{event_id}|{event_type}|{asn_line_id}|{resolved_part_num}|{float(normalized_qty):.2f}|{normalized_uom}|{action}|{operator_id}|{ts_str}|{prev_hash}"
        sha256_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        new_audit_row = pd.DataFrame(
            [
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "asn_line_id": asn_line_id,
                    "resolved_part_num": resolved_part_num,
                    "normalized_qty": float(normalized_qty),
                    "normalized_uom": normalized_uom,
                    "action": action,
                    "operator_id": operator_id,
                    "timestamp": ts_str,
                    "sha256_hash": sha256_hash,
                    "prev_hash": prev_hash,
                }
            ]
        )
        updated_audit = (
            new_audit_row if audit_df is None or len(audit_df) == 0 else pd.concat([audit_df, new_audit_row], ignore_index=True)
        )
        self.tables["AUDIT_LOG_LEDGER"] = updated_audit
        updated_audit.to_csv(self.data_dir / "audit_log_ledger.csv", index=False)
        return sha256_hash

    def get_verified_audit_ledger(self) -> Tuple[pd.DataFrame, bool]:
        """
        Retrieves the audit log and mathematically verifies the integrity of the SHA-256 hash chain.
        Returns (audit_dataframe, is_chain_valid).
        """
        self.ensure_data_loaded()
        audit_df = self.tables.get("AUDIT_LOG_LEDGER")
        if audit_df is None or len(audit_df) == 0:
            return pd.DataFrame(), True

        df = audit_df.copy()
        is_valid = True
        verification_statuses = []

        for pos, (_, row) in enumerate(df.iterrows()):
            expected_prev = GENESIS_HASH if pos == 0 else str(df.iloc[pos - 1]["sha256_hash"])
            curr_prev = str(row["prev_hash"])
            if curr_prev != str(expected_prev):
                is_valid = False
                verification_statuses.append(False)
                continue

            payload = f"{row['event_id']}|{row['event_type']}|{row['asn_line_id']}|{row['resolved_part_num']}|{float(row['normalized_qty']):.2f}|{row['normalized_uom']}|{row['action']}|{row['operator_id']}|{row['timestamp']}|{curr_prev}"
            computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            match = (computed == str(row["sha256_hash"]))
            if not match:
                is_valid = False
            verification_statuses.append(match)

        df["chain_verified"] = verification_statuses
        return df, is_valid

    def approve_harmonization_override(
        self,
        asn_line_id: str,
        resolved_part_num: str,
        normalized_qty: float,
        normalized_uom: str,
        normalized_eta_date: str,
        action: str = "PLANNER_APPROVED_EXPEDITE",
        user: str = "lead_planner_chakan",
    ) -> float:
        t0 = time.perf_counter()
        self.ensure_data_loaded()
        ov_df = self.tables["ASN_PLANNER_OVERRIDES"]
        ov_df = ov_df[ov_df["asn_line_id"] != asn_line_id].copy()

        # 1. Generate Cryptographic Audit Block
        sha256_hash = self._log_audit_event(
            event_type="OVERRIDE_APPROVED",
            asn_line_id=asn_line_id,
            resolved_part_num=resolved_part_num,
            normalized_qty=normalized_qty,
            normalized_uom=normalized_uom,
            action=action,
            operator_id=user,
        )

        new_row = pd.DataFrame(
            [
                {
                    "asn_line_id": asn_line_id,
                    "resolved_part_num": resolved_part_num,
                    "normalized_qty": float(normalized_qty),
                    "normalized_uom": normalized_uom,
                    "normalized_eta_date": normalized_eta_date,
                    "resolution_action": action,
                    "resolved_by": user,
                    "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ]
        )
        updated = new_row if len(ov_df) == 0 else pd.concat([ov_df, new_row], ignore_index=True)
        self.tables["ASN_PLANNER_OVERRIDES"] = updated
        updated.to_csv(self.data_dir / "asn_planner_overrides.csv", index=False)

        if self.conn is not None:
            try:
                merge_sql = f"""
                MERGE INTO {self.schema}.ASN_PLANNER_OVERRIDES tgt
                USING (
                    VALUES (
                        {{asn_line_id}},
                        {{resolved_part_num}},
                        {{normalized_qty}},
                        {{normalized_uom}},
                        CAST({{normalized_eta_date}} AS DATE),
                        {{resolution_action}},
                        {{resolved_by}},
                        CURRENT_TIMESTAMP
                    )
                ) AS src (
                    asn_line_id, resolved_part_num, normalized_qty, normalized_uom,
                    normalized_eta_date, resolution_action, resolved_by, resolved_at
                )
                ON tgt.asn_line_id = src.asn_line_id
                WHEN MATCHED THEN UPDATE SET
                    tgt.resolved_part_num = src.resolved_part_num,
                    tgt.normalized_qty = src.normalized_qty,
                    tgt.normalized_uom = src.normalized_uom,
                    tgt.normalized_eta_date = src.normalized_eta_date,
                    tgt.resolution_action = src.resolution_action,
                    tgt.resolved_by = src.resolved_by,
                    tgt.resolved_at = src.resolved_at
                WHEN NOT MATCHED THEN INSERT VALUES (
                    src.asn_line_id, src.resolved_part_num, src.normalized_qty, src.normalized_uom,
                    src.normalized_eta_date, src.resolution_action, src.resolved_by, src.resolved_at
                )
                """
                self.conn.execute(
                    merge_sql,
                    {
                        "asn_line_id": str(asn_line_id),
                        "resolved_part_num": str(resolved_part_num),
                        "normalized_qty": float(normalized_qty),
                        "normalized_uom": str(normalized_uom),
                        "normalized_eta_date": str(normalized_eta_date),
                        "resolution_action": str(action),
                        "resolved_by": str(user),
                    },
                )
            except Exception as exc:
                raise ExasolWriteError(f"Planner override for {asn_line_id} could not be written to Exasol: {exc}") from exc

        return round((time.perf_counter() - t0) * 1000.0, 2)

    def revert_planner_override(
        self,
        asn_line_id: str,
        user: str = "lead_planner_chakan",
    ) -> float:
        """
        Safely rolls back a specific planner override, restores baseline state for that ASN,
        and logs an immutable cryptographic reversal block to AUDIT_LOG_LEDGER.
        """
        t0 = time.perf_counter()
        self.ensure_data_loaded()
        ov_df = self.tables["ASN_PLANNER_OVERRIDES"]

        target_rows = ov_df[ov_df["asn_line_id"] == asn_line_id]
        if len(target_rows) == 0:
            return round((time.perf_counter() - t0) * 1000.0, 2)

        reverted_row = target_rows.iloc[0]
        resolved_part = str(reverted_row.get("resolved_part_num", "UNKNOWN"))
        norm_qty = float(reverted_row.get("normalized_qty", 0.0))
        norm_uom = str(reverted_row.get("normalized_uom", "EA"))

        # 1. Remove from active overrides table
        remaining_ov = ov_df[ov_df["asn_line_id"] != asn_line_id].copy()
        self.tables["ASN_PLANNER_OVERRIDES"] = remaining_ov
        remaining_ov.to_csv(self.data_dir / "asn_planner_overrides.csv", index=False)

        # 2. Append cryptographic reversal to audit ledger
        self._log_audit_event(
            event_type="OVERRIDE_REVERTED",
            asn_line_id=asn_line_id,
            resolved_part_num=resolved_part,
            normalized_qty=norm_qty,
            normalized_uom=norm_uom,
            action="ROLLBACK_REVERT_TO_BASELINE",
            operator_id=user,
        )

        # 3. Propagate deletion to Exasol DB if connected
        if self.conn is not None:
            try:
                self.conn.execute(
                    f"DELETE FROM {self.schema}.ASN_PLANNER_OVERRIDES WHERE asn_line_id = {{asn_line_id}}",
                    {"asn_line_id": asn_line_id},
                )
            except Exception as exc:
                raise ExasolWriteError(f"Revert of override {asn_line_id} failed in Exasol: {exc}") from exc

        return round((time.perf_counter() - t0) * 1000.0, 2)

    def reset_planner_overrides(self) -> float:
        t0 = time.perf_counter()
        self.ensure_data_loaded()
        empty_ov = pd.DataFrame(
            columns=[
                "asn_line_id",
                "resolved_part_num",
                "normalized_qty",
                "normalized_uom",
                "normalized_eta_date",
                "resolution_action",
                "resolved_by",
                "resolved_at",
            ]
        )
        self.tables["ASN_PLANNER_OVERRIDES"] = empty_ov
        empty_ov.to_csv(self.data_dir / "asn_planner_overrides.csv", index=False)

        self._log_audit_event(
            event_type="ALL_OVERRIDES_RESET",
            asn_line_id="ALL",
            resolved_part_num="ALL",
            normalized_qty=0.0,
            normalized_uom="ALL",
            action="SYSTEM_RESET_ALL_OVERRIDES",
            operator_id="lead_planner_chakan",
        )

        if self.conn is not None:
            try:
                self.conn.execute(f"TRUNCATE TABLE {self.schema}.ASN_PLANNER_OVERRIDES")
            except Exception as exc:
                raise ExasolWriteError(f"Planner overrides could not be reset in Exasol: {exc}") from exc

        return round((time.perf_counter() - t0) * 1000.0, 2)


