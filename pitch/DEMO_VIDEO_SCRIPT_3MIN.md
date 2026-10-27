# 3-Minute High-Impact Video Demo Script & Recording Playbook

> **FACILITY**: Pune-Chakan Powertrain & Assembly Cluster (Plant-1)  
> **DATA PLATFORM**: Exasol Personal Edition (`CHAKAN_SCM` on `localhost:8563`)  
> **TARGET RUNTIME**: Exactly 03:00 (180 Seconds) | **TARGET CADENCE**: ~135–140 words/min (~410 total spoken words)  
> **ASPECT RATIO**: 1080p (1920×1080), 60 FPS, 16:9 widescreen  
> **RECORDING TOOL**: OBS Studio / Loom (Clean full-screen browser capture on `localhost:8501`)

---

## 0. Quick-Reference Timing Cue Card

```
[0:00 - 0:25] ⚡ SCENE 1: The Dramatic Hook (ERP Baseline Crisis: 4 of 4 Lines Halting)
[0:25 - 0:50] 🏭 SCENE 2: The MSME Supply Chain Problem (Gate Rejections & Dead-Letter Logs)
[0:50 - 1:20] 🌿 SCENE 3: The Reveal & Exasol In-DB Architecture (Toggle Mangrove Guard & In-DB UDFs)
[1:20 - 1:55] 🎯 SCENE 4: Live Triage Cockpit & 1-Click Action (Clearing ₹20.76 Cr & 1-Click Writeback)
[1:55 - 2:20] 🌧️ SCENE 5: What-If Chaos Simulator (Monsoon Shocks & Additive Waterfall)
[2:20 - 2:45] 📊 SCENE 6: Scalability Benchmark & Financial ROI (1M-Row In-DB Query & 177x ROI)
[2:45 - 3:00] 🚀 SCENE 7: Boardroom Defense & The Ask (41/41 Tests & Call to Action)
```

---

## 1. Complete Second-by-Second Director's Script

---

### SCENE 1: The Dramatic Hook — The Legacy ERP Crisis (0:00 – 0:25)
**Duration**: 25 Seconds | **Word Count**: ~55 words  
**Visual**: Browser open to Streamlit Cockpit (`http://localhost:8501`).  
**Initial State**: Ensure the **Execution Mode** segmented pill toggle is on **`ERP Baseline`** (default).  
Camera starts tight on the **Top KPI Card Bar** showing the red-flagged emergency metrics:  
- `Scheduled Output: ₹37.88 Cr`
- `Quarantined ASNs: 13 Dispatches (REJECTED AT FACTORY GATE)`
- `Production Blocked: ₹26.05 Cr (13 Dispatches Dropped)`
- `Assembly Lines Halting: 4 of 4 Lines`
- `Panic Freight Required: ₹5.85 L (13 Emergency Couriers)`

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:00 – 0:10** | Cursor hovers over **Scheduled Output: ₹37.88 Cr**, then points to the red cards: **Production Blocked: ₹26.05 Cr** and **Assembly Lines Halting: 4 of 4 Lines**. | *"At 6:30 AM this morning, an automotive assembly plant in Pune-Chakan with 1,200 workers was scheduled to roll out ₹38 Crores worth of vehicles.* | Urgent, dramatic, authoritative opening. Grab attention in the first 5 seconds. |
| **0:10 – 0:18** | Scroll down slightly to Tab 1 showing the **Gate Quarantine Log (Traditional ERP Batch Rejections)** with crimson rows marked `🔴 REJECTED AT GATE` and `ZERO STOCK CREDITED (HALT)`. | *Suddenly, traditional ERP validation flagged a catastrophic emergency: 13 supplier shipments rejected at the factory gate, ordering an immediate shutdown across all 4 assembly lines.* | Convey the panic of sudden factory stoppage. |
| **0:18 – 0:25** | Point cursor to the red banner: `TRADITIONAL ERP PERSPECTIVE: UNMITIGATED LINE-STOP EXPOSURE`. | *Was the assembly plant really starving? Or was it an avoidable ₹26 Crore false alarm caused by brittle batch data pipelines?"* | Intriguing rhetorical question posing the central problem. |

---

### SCENE 2: The MSME Supply Chain Problem (0:25 – 0:50)
**Duration**: 25 Seconds | **Word Count**: ~58 words  
**Visual**: Remain on Tab 1 in `ERP Baseline` mode. Zoom in on the raw supplier payload column in the Gate Quarantine Log.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:25 – 0:37** | Highlight raw defect strings in the table: `BOX_100` packaging mismatch, vendor catalog aliases like `6204ZZ`, and ambiguous dates. | *"In manufacturing hubs like Chakan, 60% of sub-tier suppliers are MSMEs without standardized EDI. They dispatch genuine parts in non-standard crates, vendor part codes, and conflicting packaging units.* | Grounded, factual, domain-expert cadence. |
| **0:37 – 0:50** | Cursor points to `ETL Rejection Cause` and the `Panic Freight Required: ₹5.85 L` card. | *Traditional databases dump these into dead-letter error logs. To enterprise IT, the database looks pristine. But to the plant floor, a quarantined truck is invisible stock—triggering panic courier charters or line halts costing ₹12.5 Lakhs every single hour."* | Emphasize the crippling economic penalty of dead-letter tables. |

---

### SCENE 3: The Reveal & Exasol In-Memory Architecture (0:50 – 1:20)
**Duration**: 30 Seconds | **Word Count**: ~68 words  
**Visual**:  
1. **The Click**: At 0:50, click **`Mangrove Guard`** on the Execution Mode segmented pill toggle!  
   - Watch the pill switch to deep forest green (`#23533F`) with an electric mint dot.  
   - Watch the Top KPI header dynamically transform:  
     - Card 3 lights up in mint green: `Cleared in RAM: ₹20.76 Cr (↗ Harmonized by Exasol UDFs)`!  
     - Card 4 drops to `True Net Shortage: ₹5.29 Cr (1 Actionable Deficit on Line 3)`!  
     - Card 5 isolates `Phantom Stock: ₹1.18 Cr (7,138 Unpickable Units)`!  
     - The business defense strip displays: `Executive ROI: 177x | Avoided Panic Freight: ₹1.35 L`.  
2. Switch to **Tab 7: Exasol Engine & SQL** to show the native query profiler and in-DB UDFs.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **0:50 – 1:02** | **Click `Mangrove Guard` toggle**. Highlight the green metric `Cleared in RAM: ₹20.76 Cr` and `True Net Shortage: ₹5.29 Cr`. | *"Watch what happens when we engage Mangrove Guard on Exasol Personal. Instantly, ₹20.76 Crores of false alarms dissolve in memory! The true physical shortage drops to just ₹5.29 Crores on Line 3.* | High energy, dynamic reveal of the core technological transformation. |
| **1:02 – 1:12** | Switch to **Tab 7: Exasol Engine & SQL**. Scroll through `UDF_NORMALIZE_UOM` and `UDF_RESOLVE_SUPPLIER_SKU`. | *Instead of shipping messy rows out to external Python queues, Exasol executes three compiled Python 3 UDFs directly adjacent to columnar tables in RAM—normalizing pack sizes, fuzzy-resolving catalog aliases, and parsing dates in parallel.* | Confident technical depth. Show real SQL and Python UDF code. |
| **1:12 – 1:20** | Click on Tab 7's **Live Query Profiler** showing `Stage 1: True ATP`, `Stage 2: ASN UDF`, `Stage 3: BOM Risk`, and `DISTRIBUTE BY (internal_part_num)`. | *Our relational tables partition on core part keys, aligning material catalogs and inventory ledgers directly in Exasol memory to execute high-speed multi-table joins with zero inter-process network roundtrips."* | Emphasize in-memory execution and zero ETL network serialization. |

---

### SCENE 4: Live Cockpit Walkthrough & 1-Click Action (1:20 – 1:55)
**Duration**: 35 Seconds | **Word Count**: ~80 words  
**Visual**: Switch to **Tab 1: Inbound Triage** (now running in Mangrove Guard mode). Highlight the **Actionable Shortage-Risk Queue**, then scroll down to the **1-Click Resolution Workbench**.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **1:20 – 1:32** | Show top table: point out the green badge `FALSE_STARVATION_CLEARED_BY_UDF` for Bearing `6204ZZ` and Crate `CRATE_50`. | *"Back in Tab 1, the triage queue is crystal clear: Exasol resolved vendor alias `6204ZZ` to engine bearings, converted crates to units, and verified that 4 components are fully secured.* | High energy, clear operational demonstration. |
| **1:32 – 1:44** | Scroll down to the single red row: `CRITICAL_SHORT_SHIPMENT_EXPOSED` for Wheel Hub `AXL-HUB-DUC-14` on Line 3. | *Only one genuine physical deficit remains: 600 wheel hubs short-shipped on Line 3, risking ₹5.29 Crores of heavy commercial axles within 8.6 hours.* | Sharp focus on the true net bottleneck. |
| **1:44 – 1:55** | In the **1-Click Resolution Workbench** below, highlight the 3 data tiles (Anomaly, In-DB Resolution, Line Halt Risk), click **"Approve Expedited Courier Allocation"**, and show the screen update. | *In the 1-Click Workbench below, the planner authorizes an expedited courier. Exasol executes an atomic SQL MERGE in under a millisecond, recalculates the view over WebSocket, and seals the override into a cryptographic SHA-256 Merkle audit ledger."* | Seamless demonstration of the interactive write-back loop. |

---

### SCENE 5: Interactive "What-If" Chaos Simulator (1:55 – 2:20)
**Duration**: 25 Seconds | **Word Count**: ~62 words  
**Visual**: Click on **Tab 3: What-If Simulator**. Point to the **Disruption Factor Attribution Waterfall** in Crores and the **Component Run Window Horizon** bar chart.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **1:55 – 2:05** | Click preset button: `🌧️ Western Ghats Monsoon` (`₹15.39 Cr` net risk), then adjust sliders to compound shock (`+3d delay`, `20% quarantine`, `1.20x surge`). | *"Supply chains face dynamic volatility. In Tab 3, our interactive simulator stress-tests real-world disruptions. Clicking 'Western Ghats Monsoon' pushes parameters to Exasol's session-isolated table, recalculating risk to ₹15.39 Crores entirely in database RAM.* | Fast-paced, impressive demonstration of real-time reactivity. |
| **2:05 – 2:20** | Show the **Attribution Waterfall** (in ₹ Crores) and **Run Window Horizon** bars updating under compound shock (`₹32.50 Cr`). | *Under compound shocks with 20% defect holds and a 1.2x demand surge, Exasol evaluates a strictly additive attribution waterfall across transit delays, defect scrap, and schedule surges—empowering planners to intervene hours before the line starves."* | Highlight in-database pushdown and exact additive waterfall attribution. |

---

### SCENE 6: Scalability Benchmark & Financial ROI (2:20 – 2:45)
**Duration**: 25 Seconds | **Word Count**: ~60 words  
**Visual**: Click on **Tab 4: 10k Scale Benchmark**, highlight the 10k curve and the **1,000,000-Row In-Database MPP Columnar Benchmark** card. Then flick to **Tab 5: Financial ROI Defense**.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **2:20 – 2:33** | Show Tab 4 benchmark curves (`10,000 Rows: 133 ms Columnar vs 181 ms Python ETL`) and point to the 1M-Row In-DB metric: `56.9 ms (17,568,517 rows/s)`. | *"How does it scale? In our 10,000-row benchmark, set-based columnar processing completes in 133 milliseconds. Pushing Exasol's native C++ engine to true million-row scale, in-database columnar queries evaluate 1,000,000 rows in just 57 milliseconds—over 17 million rows per second with zero network egress!* | Punchy, undeniable physical proof of technical superiority. |
| **2:33 – 2:45** | Switch to Tab 5: Highlight `177x Executive Mitigation ROI` and `₹1.35 L Avoided Panic Freight`. | *Financially, in Tab 5, dispatching a ₹45,000 emergency freight saves ₹79.92 Lakhs in factory downtime, delivering an executive mitigation ROI of 177 times while avoiding ₹1.35 Lakhs in wasted panic couriers."* | Ground the technology in undeniable CFO-level monetary value. |

---

### SCENE 7: Conclusion & The Call to Action (2:45 – 3:00)
**Duration**: 15 Seconds | **Word Count**: ~35 words  
**Visual**: Smooth cut to clean terminal in background showing pytest passing **41/41 tests**, then full dashboard view with GitHub repository header, Exasol logo, and reproducibility badge: `100% Synthetic Data (Seed 202610) | MIT Open Source`.

| Timestamp | Visual Action (Screen / Mouse) | Narration Audio (Spoken Word-for-Word) | Tone & Direction |
| :---: | :--- | :--- | :--- |
| **2:45 – 3:00** | Point cursor to terminal with `41 passed in 60s`, then zoom back out on the full Streamlit dashboard. | *"100% synthetic data, zero proprietary leaks, and verified Exasol Personal SQL & UDF parity with 41 passing automated tests. We turned inbound supply chain chaos into boardroom financial certainty. Thank you—let's make factory assembly lines truly starvation-proof."* | Strong, professional, memorable closing. Confident finish at 02:58. |

---

## 2. Fast 1-Minute Elevator Pitch Script (Emergency / Quick Cut)

*(Use this 60-second version if submitting to short-form reels or 1-minute hackathon previews)*

> "At 6:30 AM, an automotive plant in Pune-Chakan with 1,200 workers was scheduled to produce ₹37.88 Crores of vehicles. But a supplier dispatch with non-standard crates and vendor part aliases was quarantined by legacy ERP, triggering an emergency shutdown alarm across all 4 assembly lines.
> 
> Was the line really starving? No. It was a ₹26.05 Crore false alarm.
> 
> We built **Mangrove** on **Exasol Personal**. When we engage Mangrove Guard, Exasol's in-database Python 3 UDFs (`UDF_NORMALIZE_UOM`, `UDF_RESOLVE_SUPPLIER_SKU`, `UDF_PARSE_ASN_DATE`) harmonize dirty dispatches directly in RAM. It instantly dissolved ₹20.76 Crores in false alarms, isolated the one real ₹5.29 Crore wheel-hub shortage, and delivered a **177x mitigation ROI** over a ₹45,000 emergency freight run avoiding ₹79.92 Lakhs in factory downtime.
> 
> In benchmarks, our set-based columnar pipeline processes 10,000 dispatches in **133 milliseconds**, and evaluates 1,000,000 rows in **57 milliseconds (17.5M rows/s)** with zero network egress. 41 automated tests, 100% synthetic, 100% reproducible. Analytics that keep automotive assembly lines running."

---

## 3. Director's Recording Checklist & Preflight Verification

Before pressing Record in OBS Studio or Loom, verify:
- [ ] **Exasol Container Running**: `docker ps` confirms `exasol-personal` running on port 8563.
- [ ] **Streamlit App Running**: `.\.venv\Scripts\python.exe -m streamlit run src/app/app.py` is open in browser at `http://localhost:8501`.
- [ ] **Browser Window Setup**: Chrome / Edge at 100% zoom, bookmarks bar hidden (`Ctrl+Shift+B`), full-screen (`F11`) for a clean 1080p canvas.
- [ ] **Default Perspective**: Make sure the segmented pill toggle starts on **`ERP Baseline`** (white pill with crimson dot).
- [ ] **Data Baseline Clean**: Click sidebar button `"1. Sync Monday ASN Batch (500 Rows)"` and `"3. Reset Planner Overrides"` so top KPI cards show standard baseline (`₹37.88 Cr`, `₹26.05 Cr`, `₹20.76 Cr`, `₹5.29 Cr`, `₹1.18 Cr`).
- [ ] **Audio Setup**: Noise suppression filter enabled, microphone input tested at -6dB peak, no background fan or AC hum.
- [ ] **Cadence Check**: Read through once with a stopwatch; ensure pace lands comfortably between 2 minutes 50 seconds and 2 minutes 58 seconds.
