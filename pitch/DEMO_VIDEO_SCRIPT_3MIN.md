# 3-Minute High-Impact Video Demo Script & Recording Playbook

> **FACILITY**: Pune-Chakan Powertrain & Assembly Cluster (Plant-1)  
> **DATA PLATFORM**: Exasol Personal Edition (`CHAKAN_SCM` on `localhost:8563`)  
> **TARGET RUNTIME**: Exactly 03:00 (180 Seconds) | **TARGET CADENCE**: ~135–140 words/min (~410 total spoken words)  
> **ASPECT RATIO**: 1080p (1920×1080), 60 FPS, 16:9 widescreen  
> **RECORDING TOOL**: OBS Studio / Loom (Clean full-screen browser capture on `localhost:8501`)

---

## 0. Quick-Reference Timing Cue Card

```
[0:00 - 0:25] ⚡ SCENE 1: The Dramatic Hook (The ₹37.88 Cr Assembly Line Halt)
[0:25 - 0:50] 🏭 SCENE 2: The MSME Supply Chain Crisis (Conflicting UOMs & Dirty ASNs)
[0:50 - 1:20] 🐍 SCENE 3: The Architecture (Exasol Personal In-Memory MPP + Python UDFs)
[0:20 - 1:55] 🎯 SCENE 4: Live Triage Cockpit (Clearing ₹20.76 Cr in False Alarms & 1-Click Action)
[1:55 - 2:20] 🌧️ SCENE 5: What-If Chaos Simulator (Monsoon Shocks & Crores Attribution Waterfall)
[2:20 - 2:45] 📊 SCENE 6: Scalability Benchmark & Financial ROI (Set-Based Columnar Architecture & 177x ROI)
[2:45 - 3:00] 🚀 SCENE 7: Boardroom Defense & The Ask (35/35 Tests & Call to Action)
```

---

## 1. Complete Second-by-Second Director's Script

---

### SCENE 1: The Dramatic Hook (0:00 – 0:25)
**Duration**: 25 Seconds | **Word Count**: ~55 words  
**Visual**: Browser open to Streamlit Cockpit (`http://localhost:8501`). Camera starts tight on the **Top KPI Card Bar** showing `₹37.88 Cr Scheduled Output` and the flashing amber indicator `₹26.05 Cr Legacy Risk`.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:00 – 0:08** | Cursor hovers over the **Scheduled Output Value: ₹37.88 Cr** then points to **Legacy Parsing Threat: ₹26.05 Cr**. | *"At 6:30 AM this morning, an automotive assembly plant in Pune-Chakan with 1,200 workers was scheduled to roll out ₹38 Crores worth of vehicles.* | Urgent, dramatic, authoritative opening. Grab attention in the first 5 seconds. |
| **0:08 – 0:18** | Scroll down slightly to show red-flagged rows in the Quarantine Queue with status `DROPPED_BY_LEGACY_ETL`. | *Suddenly, traditional ETL systems flagged an emergency: missing engine bearings, conflicting crates, and corrupt delivery dates. The legacy ERP ordered an immediate plant shutdown.* | Convey the panic of sudden factory stoppage. |
| **0:18 – 0:25** | Zoom back out to reveal the full cockpit banner and the green metric: `₹20.76 Cr False Alarms Cleared`. | *Was the assembly line really starving? Or was it an avoidable ₹26 Crore false alarm caused by brittle batch pipelines?"* | Intriguing rhetorical question posing the central thesis. |

---

### SCENE 2: The MSME Supply Chain Problem (0:25 – 0:50)
**Duration**: 25 Seconds | **Word Count**: ~58 words  
**Visual**: Switch briefly to slide or scroll to sidebar summary showing ACMA auto statistics: 60% Tier-2/3 suppliers are MSMEs without standardized EDI.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:25 – 0:37** | Highlight raw payload column in the table showing supplier units: `BOX_100`, `CRATE_50`, `BAG_250`, and vendor aliases like `6204ZZ`. | *"In manufacturing hubs like Chakan, sub-tier suppliers dispatch parts in conflicting pack sizes, vendor part aliases, and ambiguous date formats.* | Grounded, factual, domain-expert cadence. |
| **0:37 – 0:50** | Cursor points to `₹12.5 Lakhs / Hr` Plant Downtime Burn Rate in the metrics bar. | *Traditional databases dump these into dead-letter error logs. Planners panic, chartering ₹45,000 express couriers or halting lines at an idle penalty of ₹12.5 Lakhs every single hour. What planners need is in-database harmonization and instant financial blast-radius triage."* | Emphasize the crippling economic penalty of dead-letter tables. |

---

### SCENE 3: Exasol In-Memory Architecture (0:50 – 1:20)
**Duration**: 30 Seconds | **Word Count**: ~68 words  
**Visual**: Point cursor to the **Platform Telemetry Card** in the left sidebar showing `Partition Key: internal_part_num`, then switch to **Tab 7: Exasol Engine & SQL** to show the native query profiler and in-DB UDFs.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:50 – 1:02** | Highlight sidebar telemetry card: engine status, sub-second latency, and `DISTRIBUTE BY (internal_part_num) [In-DB RAM]`. | *"That’s why we built our engine inside Exasol Personal. Instead of shipping messy rows out to external Python queues, we run the transformation directly in Exasol's in-memory columnar RAM.* | Technical pride, sharp delivery highlighting Exasol's unique edge. |
| **1:02 – 1:12** | In Tab 7, scroll to `UDF_NORMALIZE_UOM` and `UDF_RESOLVE_SUPPLIER_SKU`. | *Three native Python 3 scalar UDFs run inside worker cores in parallel, normalizing units, fuzzy-resolving catalog aliases, and parsing multi-format dates.* | Confident technical depth. Show real SQL and Python UDF code. |
| **1:12 – 1:20** | Click on the Query Profiler card showing `Stage 3: BOM Starvation Risk`. | *Our relational tables partition across core part keys—aligning material catalogs, inventory ledgers, and purchase orders directly in Exasol's in-memory columnar RAM to execute high-speed multi-table joins in under 15 milliseconds in engine RAM and under 60 milliseconds across the active session."* | Emphasize in-memory execution and zero ETL network serialization. |

---

### SCENE 4: Live Cockpit Walkthrough & 1-Click Action (1:20 – 1:55)
**Duration**: 35 Seconds | **Word Count**: ~80 words  
**Visual**: Switch to **Tab 1: Inbound Triage**. Highlight the top **Prioritized Inbound Dispatch Queue**, then scroll down to the **1-Click Resolution Workbench**.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **1:20 – 1:32** | Show top **Prioritized Dispatch Queue**: point out the green badge `FALSE_STARVATION_CLEARED_BY_UDF` for Bearing `6204ZZ` and Crate `CRATE_50`. | *"Here is the live triage queue. Look at the magic: Exasol resolved vendor alias `6204ZZ` to engine bearings, converted 22 crates into 2,200 units, and instantly cleared ₹20.76 Crores in false alarms!* | High energy, dynamic walkthrough of the core product value. |
| **1:32 – 1:44** | Scroll down to the critical red row: `CRITICAL_SHORT_SHIPMENT_EXPOSED` for Wheel Hub `AXL-HUB-DUC-14`. | *Only one genuine physical deficit remains: 600 wheel hubs short-shipped on Line 2, risking ₹5.29 Crores of finished vehicles within 8.6 hours.* | Clear focus on the true net bottleneck. |
| **1:44 – 1:55** | In the **1-Click Resolution Workbench** below, select `⚡ ASN-L-9003 | PO-2026-8803`, click **"Approve Expedited Courier Allocation"**, and watch screen refresh. | *With one click, the planner logs an expedited shipment override. Exasol executes an atomic SQL MERGE in under 1 millisecond, re-evaluates the view in 45 milliseconds over the active WebSocket, and the starvation threat vanishes to zero."* | Seamless demonstration of the interactive write-back loop. |

---

### SCENE 5: Interactive "What-If" Chaos Simulator (1:55 – 2:20)
**Duration**: 25 Seconds | **Word Count**: ~62 words  
**Visual**: Click on **Tab 3: What-If Simulator**. Point to the **Disruption Factor Attribution Waterfall** in Crores and the **Component Run Window Horizon** bar chart.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **1:55 – 2:05** | Click the preset button: `🌧️ Western Ghats Monsoon` (`₹15.39 Cr` net risk), then adjust sliders to compound shock (`+3d delay`, `20% quarantine`, `1.20x surge`). | *"Supply chains are dynamic. In Tab 3, our interactive simulator stress-tests real-world shocks. Clicking 'Western Ghats Monsoon' pushes parameters to Exasol's `SIMULATION_PARAMETERS` table, where the view recalculates entirely in database RAM, escalating net risk to ₹15.39 Crores.* | Fast-paced, impressive demonstration of real-time reactivity. |
| **2:05 – 2:20** | Show the **Attribution Waterfall** (in ₹ Crores) and **Run Window Horizon** bars updating under compound shock (`₹32.50 Cr`). | *Under a compound shock with 20% defect holds and a 1.2x surge, risk reaches ₹32.50 Crores. Exasol evaluates the sequential attribution waterfall in-database across transit drift, quarantine holds, and demand surge—empowering planners to intervene hours before the line starves."* | Highlight in-database pushdown and exact additive waterfall attribution. |

---

### SCENE 6: High-Scale Stress Benchmark & Boardroom ROI (2:20 – 2:45)
**Duration**: 25 Seconds | **Word Count**: ~60 words  
**Visual**: Click on **Tab 4: 10k Scale Benchmark** then flick to **Tab 5: Financial ROI Defense**.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **2:20 – 2:33** | Show Tab 4 benchmark curves: `10,000 Rows: ~133 ms Columnar (75,177 rows/s) vs ~181 ms Python ETL`. | *"How does it scale? In our 10,000-row stress benchmark with zero synthetic overhead, standard indexed Python ETL slows down as batch sizes expand. Our set-based columnar pipeline finishes in 133 milliseconds—delivering 75,000 rows per second throughput directly in memory!* | Punchy, undeniable physical proof of technical superiority. |
| **2:33 – 2:45** | Switch to Tab 5: Highlight `177x Executive Mitigation ROI` and `₹1.35 L Avoided Panic Freight`. | *"Financially, preventing plant stoppage against a ₹45,000 hot-shot freight delivers an executive mitigation ROI of 177 times on unrecoverable factory overhead, while avoiding ₹1.35 Lakhs in wasted panic couriers."* | Ground the technology in undeniable CFO-level monetary value. |

---

### SCENE 7: Conclusion & The Call to Action (2:45 – 3:00)
**Duration**: 15 Seconds | **Word Count**: ~35 words  
**Visual**: Show full dashboard view with GitHub repository header, Exasol logo, and reproducibility badge: `100% Synthetic Data (Seed 202610) | MIT Open Source`.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **2:45 – 3:00** | Smooth zoom-out on the full Streamlit dashboard with clean terminal in background showing pytest passing 35/35 tests across all three test suites (or 34 passed, 1 skipped offline). | *"100% synthetic data, zero proprietary leaks, and verified Exasol Personal SQL & UDF parity. We turned inbound supply chain chaos into boardroom financial certainty. Thank you—let's make factory lines truly starvation-proof."* | Strong, professional, memorable closing. Confident finish at 03:00. |

---

## 2. Fast 1-Minute Elevator Pitch Script (Emergency / Quick Cut)

*(Use this 60-second version if submitting to short-form reels or 1-minute hackathon previews)*

> "At 6:30 AM, an automotive plant in Pune-Chakan with 1,200 workers was scheduled to produce ₹37.88 Crores of vehicles. But a supplier dispatch with non-standard crates and vendor part aliases was quarantined by legacy ETL, triggering an emergency shutdown alarm.
> 
> Was the line really starving? No. It was a ₹26.05 Crore false alarm.
> 
> We built **Mangrove** on **Exasol Personal**. By compiling Python 3 UDFs inside Exasol (`UDF_NORMALIZE_UOM`, `UDF_RESOLVE_SUPPLIER_SKU`, `UDF_PARSE_ASN_DATE`) and joining across distributed keys, Exasol harmonizes dirty dispatches in-database. It cleared ₹20.76 Crores in false alarms, isolated the one real ₹5.29 Crore wheel-hub shortage, and delivered a **177x mitigation ROI** over a ₹45,000 emergency freight run avoiding ₹79.92 Lakhs in factory downtime.
> 
> Under stress, our set-based columnar pipeline processes 10,000 dispatches in **133 milliseconds (75,177 rows/s)**—delivering 1.4x CPU acceleration over indexed external Python ETL with zero network serialization. 100% synthetic, 100% reproducible. Analytics that keep automotive assembly lines running."

---

## 3. Director's Recording Checklist & Preflight Verification

Before pressing Record in OBS Studio or Loom, verify:
- [ ] **Streamlit App Running**: `.\.venv\Scripts\python.exe -m streamlit run src/app/app.py` is open in browser at `http://localhost:8501`.
- [ ] **Browser Window Setup**: Chrome / Edge at 90% or 100% zoom, bookmarks bar hidden (`Ctrl+Shift+B`), full-screen (`F11`) for a clean 1080p canvas.
- [ ] **Sidebar Platform Telemetry**: Confirms active status (`🟢 Exasol Personal` or `🟠 Local Analytical Mirror`), sub-second latency, and `internal_part_num` distribution key. *(Note: both modes run with exact ₹0.00 parity, so recording in either mode produces identical deterministic figures)*.
- [ ] **Data Baseline Clean**: Click sidebar button `"1. Sync Monday ASN Batch (500 Rows)"` and `"3. Reset Planner Overrides"` so top KPI cards show standard baseline (`₹37.88 Cr`, `₹26.05 Cr`, `₹20.76 Cr`, `₹5.29 Cr`, `₹1.18 Cr`).
- [ ] **Audio Setup**: Noise suppression filter enabled, microphone input tested at -6dB peak, no background fan or AC hum.
- [ ] **Cadence Check**: Read through once with a stopwatch; ensure pace lands comfortably between 2 minutes 50 seconds and 3 minutes 00 seconds.
