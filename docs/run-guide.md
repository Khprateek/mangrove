# Reproducibility & Verification Runbook (`docs/run-guide.md`)

This guide walks through reproducing **Mangrove (In-Memory Supply Chain Triage & Assembly Starvation Engine)** from a clean checkout, both via the **Turnkey 1-Command Enterprise Appliance (`docker compose`)** and via manual local environments (**Exasol Personal Live SQL Views & Python 3 UDFs** or **Offline Analytical Mirror**).

---

## 0. Turnkey 1-Command Enterprise Appliance Launch (Recommended)

For zero-configuration deployment on evaluation servers, industrial edge appliances, or CI/CD testbeds, the entire system is packaged as an automated multi-container stack:

```bash
# 1-Command Appliance Launch (spins up Exasol DB + Auto-DDL/UDF + Cockpit UI)
docker compose up -d
```

### Automated Self-Bootstrapping Sequence:
1. **Container 1 (`exasol-personal-db`)**: Launches Exasol Personal (`exasol/docker-db:latest`) on port `8563` with privileged memory mapping and a native Docker TCP healthcheck (`cat < /dev/null > /dev/tcp/127.0.0.1/8563`).
2. **Container 2 (`mangrove-cockpit`)**: Waits for `exasol-engine` to reach `service_healthy` via Docker Compose orchestration, spawns [`scripts/entrypoint.py`](../scripts/entrypoint.py), automatically executes `bootstrap_exasol_schema_and_data()` (creating schema `CHAKAN_SCM`, compiling the 3 Python 3 UDFs, creating the 4 analytical views, and bulk-loading all 8 ERP tables and cross-references), and launches Streamlit.
3. Access the Cockpit UI: Open `http://localhost:8501` in your browser.

To stop the appliance:
```bash
docker compose down
```

---

## 1. Local Environment Setup (Windows PowerShell / Linux / macOS)

Create and activate an isolated Python 3.12+ virtual environment (`include-system-site-packages = false`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` (optional; defaults target `localhost:8563`):

```powershell
Copy-Item .env.example .env
```

---

## 2. Deterministic Synthetic ERP & ASN Chaos Generation

Regenerate all 8 synthetic ERP master tables (including supplier catalog cross-references) and the 498-row inbound ASN chaos stream (`seed = 202610`):

```powershell
.\.venv\Scripts\python.exe -m src.data_generator.generate_all --extra-asns 480
```

### Verified Baseline Invariants (`seed = 202610`, 498 ASN rows)
- **48-Hour Scheduled Output**: `₹37.88 Cr` (`378,750,000.00 INR` across 4 assembly lines)
- **Pre-UDF Legacy Blind-Spot Risk**: `₹26.05 Cr` (`260,500,000.00 INR`)
- **False Alarms Cleared by In-DB Python 3 UDFs**: `₹20.76 Cr` (`207,595,000.00 INR`)
- **True Net Shortage Exposed**: `₹5.29 Cr` (`52,905,000.00 INR` on `AXL-HUB-DUC-14`)
- **Plant Idle Labor & Overhead Exposure**: `₹2.63 Cr` (`26,283,000.00 INR`)
- **Total Unmitigated Stoppage Exposure**: `₹7.92 Cr` (`79,188,000.00 INR`)
- **Warehouse Phantom Inventory Detected**: `₹1.18 Cr` (`11,813,950.00 INR` across `7,138` unpickable units)
- **Headline Emergency Freight ROI**: `176.6x` (`₹45,000` charter vs `₹79.92 Lakhs` unrecoverable idle burn on `LINE-03-AXLE`; `176.6x` fleet-wide)

---

## 3. Starting Exasol Personal (Port 8563) & Bootstrapping Schema

### Option A: Docker / Podman Single-Node Container
```powershell
docker run -d --name exasol-personal -p 8563:8563 --privileged --stop-timeout 120 exasol/docker-db:latest
Test-NetConnection -ComputerName localhost -Port 8563
```

### Option B: Bootstrap `CHAKAN_SCM` Schema, Python 3 UDFs, Views, and Tables
```powershell
.\.venv\Scripts\python.exe -c "from src.exasol_engine.db_client import ChakanExasolClient; c = ChakanExasolClient(); mode, ms = c.bootstrap_exasol_schema_and_data(); print(f'Engine: {mode} in {ms}ms')"
```

What `bootstrap_exasol_schema_and_data()` executes and verifies:
1. Creates schema `CHAKAN_SCM` and all 8 tables in [`src/exasol_engine/ddl_schema.sql`](../src/exasol_engine/ddl_schema.sql) with their `DISTRIBUTE BY` keys (`internal_part_num`, `component_part_num`, `parent_part_num`, `po_number_ref`, `asn_line_id`).
2. Compiles 3 Python 3 scalar UDF scripts in [`src/exasol_engine/udfs_harmonization.sql`](../src/exasol_engine/udfs_harmonization.sql):
   - `CHAKAN_SCM.UDF_NORMALIZE_UOM` (`RETURNS DOUBLE`)
   - `CHAKAN_SCM.UDF_RESOLVE_SUPPLIER_SKU` (`EMITS (resolved_part_num, sku_match_method, sku_confidence)` including Jaro-Winkler $\ge 0.85$ similarity)
   - `CHAKAN_SCM.UDF_PARSE_ASN_DATE` (`RETURNS DATE`)
3. Compiles 4 analytical views in [`src/exasol_engine/blast_radius_marts.sql`](../src/exasol_engine/blast_radius_marts.sql):
   - `VW_INVENTORY_TRUE_ATP`
   - `VW_ASN_HARMONIZED_LINEAGE`
   - `VW_BOM_LINE_STARVATION_RISK`
   - `VW_FINANCIAL_ROI_SUMMARY`
4. Bulk-imports all 8 CSV tables via `import_from_pandas` and verifies `SELECT COUNT(*)` on every table against the source DataFrame length (raising `ExasolBootstrapError` on any mismatch or SQL error).

---

## 4. Running the Automated Verification Suite (`pytest`)

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The test suite in [`tests/`](../tests/) verifies full-stack coverage across database engine, cockpit UI, and BYOD telemetry (**35 total tests collected across 3 test suites**: 35 passed with live Exasol / 34 passed, 1 skipped offline):

### Engine & UDF Test Suite (`tests/test_harmonization.py` — 14 Tests)
1. `test_uom_normalization_pack_and_weight_inversions`: Pack multipliers (`BOX_100`, `BAG_250`, `CRATE_50`) and weight-to-piece conversions (`MT` $\to$ `KG`, `MT` $\to$ `EA`).
2. `test_supplier_sku_drift_and_jaro_winkler_resolution`: Exact, hyphen-normalized, vendor catalog alias, and Jaro-Winkler ($\ge 0.85$) fuzzy SKU resolution.
3. `test_adaptive_ngram_prefiltering_and_safety_fallback`: Boundary-padded bigrams/trigrams for sub-millisecond filtering plus 0.00% false-negative safety fallback.
4. `test_multiformat_date_parsing`: `DD/MM/YYYY`, `MM/DD/YYYY`, ISO `YYYY-MM-DD`, and Unix epoch disambiguation.
5. `test_blast_radius_analytical_marts`: End-to-end mart calculation, planner override writeback (`ASN-L-9011`), and state idempotency on reset.
6. `test_cryptographic_audit_trail_and_rollback`: SHA-256 Merkle-chained audit ledger, selective override rollback, and mathematical chain validation.
7. `test_financial_roi_and_downtime_cost_engine`: Downtime burn rates, freight costs, and realistic line stoppage ROI calculations (~177x on unrecoverable idle burn).
8. `test_multiline_po_cartesian_join_isolation`: Verifies multi-line POs join on composite key `(po_number, internal_part_num, line_number)`, preventing phantom supply inflation.
9. `test_dynamic_supplier_catalog_cross_ref_table`: Confirms relational `SUPPLIER_CATALOG_CROSS_REF` table resolves newly onboarded supplier SKUs dynamically without UDF code changes.
10. `test_telemetry_and_query_profiler`: Stage timing instrumentation and distribution key metadata.
11. `test_what_if_scenario_simulation_additive_waterfall`: Verifies null shock (`0` delta) and confirms sequential waterfall stages sum identically to total simulated exposure.
12. `test_scale_benchmark_suite`: Verifies pure CPU benchmark (`network_hop_penalty_ms = 0.0`) across 500 to 10,000 rows.
13. `test_broken_connection_raises_explicit_errors`: Confirms broken DB connections raise `ExasolBootstrapError` / `ExasolWriteError` instead of silently passing.
14. `test_exasol_views_match_pandas_mirror`: Confirms `compute_analytical_marts(source="exasol")` and `compute_analytical_marts(source="pandas")` match to `0.00 INR` across all financial KPIs.

### UI & Cockpit Smoke Test Suite (`tests/test_cockpit_smoke.py` — 5 Tests)
15. `test_theme_tokens_and_formatting_utilities`: Validates color tokens, safe float coercion, and Indian Rupee formatting helpers (`Rs XX.XX Cr`, `Rs XX.XX L`).
16. `test_component_exports_and_callables`: Ensures all reusable UI components export valid render callables.
17. `test_tab_module_exports_and_callables`: Ensures all 8 domain tab modules export valid render callables.
18. `test_streamlit_cockpit_headless_execution`: End-to-end integration test executing the complete Streamlit Cockpit app via official `AppTest` with zero unhandled exceptions.
19. `test_perspective_switcher_toggle_lifecycle`: Verifies segmented pill execution mode toggle with zero widget instantiation conflicts.

### BYOD Inbound & Feedback Log Test Suite (`tests/test_byod_and_telemetry.py` — 16 Tests)
- Feedback log starts empty (no placeholder reviews), hash-chain verification and tamper detection.
- Presets contain no real company names; each preset harmonizes and can only reduce exposure.
- An empty batch reproduces the baseline KPIs exactly (`legacy_risk_inr`, `net_risk_inr`).
- Duplicate and low-confidence rows are not counted; UOM normalization sanity (`BOX_100`, `MT` to `KG`).
- Engine reporting: no connection and a failing Exasol connection both fall back to local UDF-parity logic and say why.
- Column auto-mapping, display-only identifier masking, exports, and webhook failure handling.

---

## 5. Running the Scale Benchmark CLI (500 to 10,000 Rows)

```powershell
.\.venv\Scripts\python.exe -m src.benchmarks.scale_benchmark
```

By default (`--penalty 0.0`), the benchmark reports pure measured CPU wall-clock timings comparing set-based columnar execution against a standard indexed row-by-row Python ETL pipeline and real `memory_usage(deep=True)` footprints.

---

## 6. Launching the Materials Planner Cockpit UI

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/app/app.py
```

Open `http://localhost:8501` in your browser. When Exasol Personal is active on `localhost:8563`, the telemetry banner displays `🟢 EXASOL PERSONAL (LIVE SQL VIEWS & UDFs)` and `Compute Source: EXASOL_VIEWS`.
