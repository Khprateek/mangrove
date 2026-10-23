# 🌿 Mangrove — Boardroom Presentation Deck

> **PRODUCT**: **Mangrove** (In-Memory Supply Chain Triage & Assembly Starvation Engine)  
> **ENGINE**: Exasol Personal Edition (`CHAKAN_SCM` MPP In-Memory Cluster)  
> **TARGET AUDIENCE**: Hackathon Judges, Chief Supply Chain Officers (CSCO), Plant Directors  
> **FORMAT**: 10 High-Impact Slides (Convertible to PPTX / Google Slides / Marp / PDF)

---

## Slide 1: Title & Executive Overview

<p align="center">
  <img src="../assets/logo.png" alt="Mangrove Logo" width="120" />
</p>

### **🌿 Mangrove**
#### *Sub-Second In-Database Supply Chain Harmonization & Assembly Line Starvation Defense on Exasol Personal*

```mermaid
flowchart LR
    A["Raw Inbound ASNs<br/>(Dirty MSME Dispatches)"] --> B["⚡ Exasol In-Memory MPP<br/>(Python 3 UDFs in RAM)"]
    B --> C["0 Net Hops<br/>(DISTRIBUTE BY)"]
    C --> D["🎯 Plant Triage Cockpit<br/>(&lt;15ms Response Time)"]
```

- **Presenter**: Lead Inbound Materials & Data Architecture Team
- **Target Plant**: Pune-Chakan Powertrain & Vehicle Assembly Hub (1,200 Line Workers)
- **Core Technology**: Native Exasol Personal Edition (`localhost:8563`, Schema `CHAKAN_SCM`)
- **Key Metric**: **₹20.76 Crores in False Alarms Cleared in 11.8 ms | 1,175× Mitigation ROI**

---

## Slide 2: The Real-World Automotive Problem

### **Why Multi-Crore Assembly Lines Halt Over Simple Dispatches**

- **The Chakan Context**: Automotive plants rely on thousands of Tier-1 and sub-tier MSME suppliers for critical assembly parts (bearings, gaskets, wheel hubs, sensors).
- **The MSME Reality (ACMA Research)**: Over **60% of Tier-2/3 Indian auto component suppliers** lack standardized electronic data interchange (EDI). They dispatch goods using fragmented local units (`BAG_250`, `CRATE_50`, `MT`), vendor catalog aliases (`6204ZZ`), and conflicting regional date conventions.
- **The High-Stakes Dilemma**:
  - If a supplier dispatch is delayed or corrupted, the entire assembly line starves within **8 to 24 hours**.
  - **Plant Stoppage Penalty**: **₹12,50,000 every single hour** in unrecoverable idle labor, line depreciation, and OEM delivery delay fines.
- **The Core Flaw**: Standard ERP and ETL pipelines drop malformed payloads into dead-letter tables, forcing planners to either **panic-charter ₹45,000 couriers** or **halt the plant on false alarms**.

---

## Slide 3: The Failure of Traditional Batch ETL Pipelines

### **Why Row-by-Row ETL Pipelines Collapse Under Supply Chain Volatility**

```mermaid
flowchart TD
    subgraph Legacy ["❌ Traditional Batch ETL Pipeline (Fragile & Slow)"]
        L1["Raw EDI / CSV Stream"] --> L2["External Python / Airflow Worker"]
        L2 --> L3["Row-by-Row Regex Parsing<br/>(Fails on Novel UOMs)"]
        L3 --> L4["Dead-Letter Quarantine Log<br/>(Dropped from ERP Ledger)"]
        L4 --> L5["Phantom Starvation False Alarm<br/>(₹26.05 Cr Threat Escalation)"]
        L5 --> L6["Wasted Air-Charter Courier<br/>(₹45,000 Panic Freight)"]
    end
```

- **Data Sinks Without Intelligence**: Dead-letter queues record syntax errors but lack supply-chain context—they cannot calculate whether a bad row threatens a ₹5 Lakh sensor or a ₹38 Crore assembly line.
- **Network Shuffling Bottlenecks**: In distributed clusters (Spark/Trino without co-location), multi-table joins across purchase orders, item masters, and BOM trees force massive inter-node network data shuffles ($10,000+$ RPC transfers).
- **Batch Latency Delay**: Hourly batch ETL jobs deliver triage information hours after the critical window for emergency freight rerouting has already closed.

---

## Slide 4: Architectural Primacy — Exasol In-Memory Columnar MPP

### **Moving the Computation Directly to the Memory Slice**

```mermaid
flowchart TD
    subgraph ExasolCluster ["🟢 Exasol Personal Engine (CHAKAN_SCM @ localhost:8563)"]
        direction TB
        subgraph MemoryScan ["1. Hot Columnar RAM Scan"]
            T1["ASN_LINES_RAW<br/>(500 to 10k Records)"]
            T2["Deduplication Window Filter<br/>(transmission_seq = 1)"]
        end

        subgraph UDFWorkers ["2. In-Database Python 3 Scalar UDFs"]
            U1["UDF_NORMALIZE_UOM(qty, uom, pack, wt)"]
            U2["UDF_RESOLVE_SUPPLIER_SKU(raw_sku, po_part)"]
            U3["UDF_PARSE_ASN_DATE(raw_date, format)"]
        end

        subgraph CoLocatedJoins ["3. Distributed Hash Joins (DISTRIBUTE BY)"]
            J1["ITEM_MASTER<br/>DISTRIBUTE BY (internal_part_num)"]
            J2["BILL_OF_MATERIALS<br/>DISTRIBUTE BY (component_part_num)"]
            J3["PURCHASE_ORDER_LINES<br/>DISTRIBUTE BY (internal_part_num)"]
            J4["WAREHOUSE_INVENTORY_LEDGER<br/>DISTRIBUTE BY (internal_part_num)"]
        end

        subgraph Marts ["4. Analytical Starvation Materialization"]
            M1["VW_INVENTORY_TRUE_ATP (Pickable Stock)"]
            M2["VW_BOM_LINE_STARVATION_RISK (Horizon & Deficit)"]
            M3["VW_FINANCIAL_ROI_SUMMARY (Boardroom Defense)"]
        end

        MemoryScan ==> UDFWorkers
        UDFWorkers ==> CoLocatedJoins
        CoLocatedJoins ==> Marts
    end
```

- **In-DB Python 3 Scalar UDFs**: `UDF_NORMALIZE_UOM`, `UDF_RESOLVE_SUPPLIER_SKU` (with Jaro-Winkler $\ge 0.85$ similarity), and `UDF_PARSE_ASN_DATE` execute inside Exasol using `EMITS (...)` and `RETURNS`.
- **Schema Distribution Alignment**: `ITEM_MASTER`, `PURCHASE_ORDER_LINES`, and `WAREHOUSE_INVENTORY_LEDGER` distribute on `internal_part_num`, while `BILL_OF_MATERIALS` distributes on `component_part_num` so part-level joins align across slices.
- **Interactive Write-Back Loop**: Planner override decisions persist to `ASN_PLANNER_OVERRIDES` via parameterized SQL and trigger immediate analytical view recalculation.

---

## Slide 5: Mathematical Formulations & True Pickable ATP

### **Quantifying Real Risk vs. ERP Illusions**

#### Formulation 1: True Pickable Available-to-Promise (ATP)
Traditional ERP queries report ledger balances on hand ($Q_{oh}$), masking quality holds and physical shrinkage:
$$ATP_{true} = Q_{on\_hand} - Q_{quarantine} - Q_{phantom} - Q_{allocated\_to\_prod}$$
*Empirical Plant Audit*: Reconciles **₹1.18 Crores in phantom stock** hidden across 16 storage bins at Chakan Plant-1.

#### Formulation 2: Component Starvation & Financial Blast Radius
For each production schedule $s$ requiring component $i$ with bill-of-materials multiplier $Q_{per\_assy}$:
$$Required_{s, i} = PlannedOutput_s \times Q_{per\_assy} \times (1 + ScrapPct)$$
$$NetDeficit_{s, i} = \max\left(0, Required_{s, i} - \left(ATP_{true, i} + \sum InTransitHarmonized_{i, \le ETA}\right)\right)$$
If $NetDeficit_{s, i} > 0$, the production schedule halts. The Financial Blast Radius is:
$$BlastRadius_s = \min\left(PlannedUnits_s, \lceil NetDeficit_{s, i} / Q_{per\_assy} \rceil\right) \times UnitSalesPrice_s$$

- **Pre-UDF (Legacy Parsing Failure)**: Apparent Starvation Threat = **₹26.05 Crores** (Lines 1, 2, 3 flagged).
- **Post-UDF (Exasol In-DB Harmonization)**: False Alarms Cleared = **₹20.76 Crores**; Real Physical Shortage = strictly **₹5.29 Crores** on Line 2 (`AXL-HUB-DUC-14`).

---

## Slide 6: The Triage Cockpit & Interactive Override Loop

### **From Raw Chaos to Clear Action in One Screen**

| KPI Metric Card | Value (INR) | Operational Significance |
| :--- | :---: | :--- |
| **Total Scheduled Factory Output** | **₹37.88 Cr** | Total planned output across all 4 assembly lines for the 48-hour cycle. |
| **Legacy ETL Threat (False Alarms)** | **₹26.05 Cr** | Phantom shutdown risk created by unparsed UOMs and supplier SKU aliases. |
| **UDF Harmonization Savings** | **₹20.76 Cr** | False alarms cleared automatically without human intervention. |
| **True Real Starvation Risk** | **₹5.29 Cr** | Real physical deficit strictly isolated to Line 2 wheel hubs (`AXL-HUB-DUC-14`). |
| **Warehouse Phantom Stock** | **₹1.18 Cr** | Discrepancies between ERP ledger balances and physical WMS bin audits. |

- **Prioritized Action Queue**: Inbound anomalies ranked by **Revenue Blast Radius**, not arbitrary error codes.
- **1-Click Planner Action**: Materials planners review normalized quantities and click `"Approve & Trigger Emergency Replenishment"`.
- **Parameterized Writeback**: Overrides write back directly to `CHAKAN_SCM.ASN_PLANNER_OVERRIDES`, driving net line starvation on `AXL-HUB-DUC-14` to **₹0.00**.

---

## Slide 7: Interactive "What-If" Chaos Simulation

### **Stress-Testing Supply Chain Shocks with Additive Attribution**

- **The Reality of Indian Auto Logistics**: Monsoons cause landslides along the NH-48 Western Ghats corridor; foundry batches suffer casting porosity; festive OEM demand surges unexpectedly.
- **One-Click Disruption Presets**:
  - `🌧️ Western Ghats Monsoon` (`+3d delay, 5% defect, 1.0x surge`): escalates net vehicle risk to **₹15.39 Cr** (**₹37.75 Cr** total stoppage exposure).
  - `⚙️ Tier-2 Foundry Porosity` (`+1d delay, 35% defect, 1.0x surge`): escalates net vehicle risk to **₹15.80 Cr** (**₹39.96 Cr** total stoppage exposure).
  - `📈 Festive OEM Surge` (`+2d delay, 15% defect, 1.35x surge`): escalates net vehicle risk to **₹35.93 Cr** (**₹65.24 Cr** total stoppage exposure).
- **Sequential Additive Waterfall (`+3d delay, 20% defect, 1.20x surge` compound scenario)**:
  - 1. Baseline True Shortage: **₹5.29 Cr**
  - 2. Logistics Transit Drift (`+3d`): **+₹8.25 Cr** (cumulative `₹13.54 Cr`)
  - 3. Quarantine Defect Spike (`+20%`): **+₹4.79 Cr** (cumulative `₹18.33 Cr`)
  - 4. Surge Output Demand (`1.20x`): **+₹14.17 Cr**
  - **Total Simulated Exposure**: **₹32.50 Cr** ($\sum \text{stages} \equiv \text{Total}$).

---

## Slide 8: High-Scale Stress Benchmark (500 to 10,000 Rows)

### **Empirical Proof: 35.4x Pure Measured CPU Speedup (Zero Synthetic Overhead)**

```mermaid
xychart-beta
    title "Measured CPU Latency at Scale (Lower is Better - Milliseconds)"
    x-axis ["500 Rows", "2500 Rows", "5000 Rows", "10000 Rows"]
    y-axis "Latency (ms)" 0 --> 3200
    line [95, 84, 86, 84]
    line [145, 730, 1573, 2961]
```
*(Line 1 = Set-Based / Columnar Pipeline | Line 2 = Uncached Row-by-Row Python ETL `iterrows()`, `0.0 ms` synthetic penalty)*

| Scale Point | Columnar Latency | Columnar Throughput | Row-by-Row CPU Latency | Row-by-Row Throughput | Measured CPU Speedup | Latency Reduction |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **500 Rows** | **95.0 ms** | 5,261 rows/s | 145.3 ms | 3,440 rows/s | **1.5x** | 34.6% |
| **2,500 Rows** | **84.3 ms** | 29,649 rows/s | 730.3 ms | 3,423 rows/s | **8.7x** | 88.5% |
| **5,000 Rows** | **86.4 ms** | 57,904 rows/s | 1,572.7 ms | 3,179 rows/s | **18.2x** | 94.5% |
| **10,000 Rows** | **83.6 ms** | **119,646 rows/s** | **2,961.2 ms** | 3,377 rows/s | **35.4x** | **97.2%** |

- **Key Takeaway**: With **zero synthetic network penalty (`0.0 ms/row`)**, uncached row-by-row Python ETL (`iterrows()`) degrades linearly to **2,961.2 ms** at 10,000 rows, while our set-based columnar pipeline finishes in **83.6 ms**—a **35.4× measured CPU speedup** and **97.2% latency reduction**.

---

## Slide 9: Boardroom Financial Defense & Economic ROI

### **The Quantitative Business Case for Plant Leadership**

$$\text{Mitigation ROI} = \frac{\text{Averted Vehicle Revenue Loss (₹5,29,05,000)} - \text{Expedited Freight Cost (₹45,000)}}{\text{Expedited Freight Cost (₹45,000)}} = \mathbf{1,174.7\times}$$

- **Idle Cost Defense**: Line stoppage idle penalties of **₹7,20,000 to ₹14,50,000 per hour** (`₹2.63 Cr` across the 48h window, bringing total stoppage exposure to **₹7.92 Cr**) dwarf emergency logistics expenses.
- **Avoided Panic Freight Ledger**:
  - Legacy ETL quarantined valid dispatches as `0 stock`, which would have triggered unnecessary emergency courier dispatches (**₹1,35,000** in avoided panic freight across cleared lines).
- **Boardroom Narrative**: Transforms supply chain data engineering from a passive error logger into a quantifiable financial risk hedge.

---

## Slide 10: Open-Source Reproducibility & Technical Defense

### **Zero Proprietary Leaks, 100% Deterministic Reproducibility**

- **Rule #4 Compliance**: 100% synthetic auto ERP dataset generated deterministically (`SEED = 202610`). Zero employer or real supplier NDA data.
- **Full Reproducibility (`docs/run-guide.md`)**:
  - Clone repo $\to$ Run automated test suite: `.\.venv\Scripts\python.exe -m pytest -v` (**12/12 Unit & Live Parity Tests Pass**).
  - Launch UI: `.\.venv\Scripts\python.exe -m streamlit run src/app/app.py`.
- **Verified Dual-Engine Parity**:
  - Connects to native Exasol Personal Docker container on `localhost:8563` (`CHAKAN_SCM`) and computes baseline marts directly via `VW_INVENTORY_TRUE_ATP`, `VW_ASN_HARMONIZED_LINEAGE`, and `VW_BOM_LINE_STARVATION_RISK` (`compute_source = EXASOL_VIEWS`).
  - Automated parity test (`test_exasol_views_match_pandas_mirror`) verifies `0.00 INR` discrepancy between Exasol SQL views and the offline Pandas mirror.

---

## Appendix: Anticipated Hackathon Judge Q&A Defense

#### Q1: "Why use Exasol instead of external Python ETL scripts for this workload?"
> **Answer**: "Moving raw ASN rows out to external row-by-row scripts incurs both serialization overhead and row-level iteration bottlenecks (`2,961 ms` at 10,000 rows in pure CPU time). By compiling `UDF_NORMALIZE_UOM`, `UDF_RESOLVE_SUPPLIER_SKU`, and `UDF_PARSE_ASN_DATE` directly inside Exasol (`CHAKAN_SCM`), the database harmonizes messy supplier rows inside `VW_ASN_HARMONIZED_LINEAGE` and joins them immediately against `ITEM_MASTER`, `BILL_OF_MATERIALS`, and `WAREHOUSE_INVENTORY_LEDGER` in a single SQL query plane."

#### Q2: "How does your solution handle new, unknown supplier SKU formats?"
> **Answer**: "Both `UDF_RESOLVE_SUPPLIER_SKU` and `harmonizer_core.py` implement a 5-tier resolution hierarchy: (1) Exact match (`1.00`), (2) Alphanumeric hyphen-normalized match (`0.98`), (3) Known vendor catalog alias (`0.95`), (4) PO token match (`0.89`), and (5) Jaro-Winkler string similarity (`>= 0.85` threshold) against both the PO part number and known vendor aliases. Any row requiring human review surfaces in the triage queue for 1-click planner override."

#### Q3: "What makes your financial ROI calculation realistic?"
> **Answer**: "Our assembly line downtime rates (`₹7.2L` to `₹14.5L/hr`) and expediting tariffs (`₹45,000` dedicated hot-shot charter) are modeled on industry benchmark ranges for Indian automotive OEMs. Spending `₹45,000` to prevent `₹5.29 Cr` in unproduced vehicles (`₹7.92 Cr` including idle plant overhead) yields the deterministic `1,174.7x` headline ROI verified in our test suite."

#### Q4: "Why does the codebase contain a Pandas mirror if Exasol is the primary engine? Doesn't that suggest Exasol is optional?"
> **Answer**: "The Pandas mirror is an **air-gapped architectural test double and offline verification harness**, not a production alternative. In enterprise software delivery, having a mathematical twin serves two critical functions:
> 1. **Zero-Flake Automated Parity Verification**: Our test suite runs `test_exasol_views_match_pandas_mirror` on every commit, asserting a `0.00 INR` delta between the compiled Exasol SQL views (`VW_BOM_LINE_STARVATION_RISK`) and the mirror.
> 2. **Graceful Demonstration Fallback**: Evaluators without an active Docker daemon or on lightweight cloud runners can preview the application without encountering hard connection crashes.
> 
> However, **Exasol is irreplaceable at operational scale**: at 10,000 rows, Pandas iteration takes **2,961 ms** and hits Python GIL/memory limits, whereas Exasol executes the same analytical query in **83.6 ms (35.4x faster)**. In high-frequency plant environments running 50,000 dispatches daily, only Exasol's in-memory columnar engine delivers sub-second real-time triage."

#### Q5: "Does the Bring-Your-Own-Data (BYOD) Inbound Studio actually execute on Exasol?"
> **Answer**: "Yes. In `src/exasol_engine/custom_ingestor.py`, when a live Exasol connection is active, `_harmonize_exasol()` creates a temporary scratch staging table in `CHAKAN_SCM`, streams the uploaded batch into columnar storage, and executes the exact same three in-database Python UDFs (`UDF_RESOLVE_SUPPLIER_SKU`, `UDF_NORMALIZE_UOM`, `UDF_PARSE_ASN_DATE`) joined against `ITEM_MASTER` and `SUPPLIER_MASTER`. The UI prominently displays an `⚡ NATIVE EXASOL IN-DATABASE EXECUTION` audit badge confirming the compute location. If Exasol is offline, it transparently falls back to local parity logic and explicitly alerts the user."

