from datetime import date
import pandas as pd
import pytest



from src.exasol_engine import domain_config
from src.exasol_engine.db_client import (

    ChakanExasolClient,

    ExasolBootstrapError,

    ExasolWriteError,

)

from src.exasol_engine.harmonizer_core import (

    build_ngram_inverted_index,

    extract_adaptive_ngrams,

    jaro_winkler_similarity,

    normalize_uom_quantity,

    parse_asn_date,

    resolve_supplier_sku,

)





def test_uom_normalization_pack_and_weight_inversions() -> None:

    assert normalize_uom_quantity(22.0, "BOX_100", "EA") == 2200.0

    assert normalize_uom_quantity(26.0, "BAG_250", "EA") == 6500.0

    assert normalize_uom_quantity(12.0, "CRATE_50", "EA") == 600.0

    assert normalize_uom_quantity(3.15, "MT", "KG") == 3150.0

    assert normalize_uom_quantity(3.312, "MT", "EA", unit_weight_kg=18.4) == 180.0

    # Extended conversions: Grams to KG, Pieces/Numbers to EA, fallback 100 EA for unverified BOX

    assert normalize_uom_quantity(500.0, "G", "KG") == 0.5

    assert normalize_uom_quantity(25.0, "NOS", "EA") == 25.0

    assert normalize_uom_quantity(10.0, "BOX", "EA", pack_size_ea=1.0) == 1000.0  # 10 * 100 EA fallback

    # Robustness additions: UOM synonyms (KGS, GMS, SETS) and flexible packaging delimiters (-, space, /, PK)

    assert normalize_uom_quantity(1000.0, "KGS", "MT") == 1.0

    assert normalize_uom_quantity(500.0, "GMS", "KG") == 0.5

    assert normalize_uom_quantity(5.0, "SETS", "EA") == 5.0

    assert normalize_uom_quantity(10.0, "BOX-100", "EA") == 1000.0

    assert normalize_uom_quantity(4.0, "PK_50", "EA") == 200.0

    assert normalize_uom_quantity(2.0, "CRATE/40", "EA") == 80.0

    # Industrial hardware packaging and string quantity cleaning

    assert normalize_uom_quantity("1,200.50", "EA", "EA") == 1200.5

    assert normalize_uom_quantity(-50.0, "EA", "EA") == 0.0

    assert normalize_uom_quantity(10.0, "DZN", "EA") == 120.0

    assert normalize_uom_quantity(2.0, "GROSS", "EA") == 288.0

    assert normalize_uom_quantity(50.0, "PAIR", "EA") == 100.0





def test_supplier_sku_drift_and_jaro_winkler_resolution() -> None:

    sku, method, conf = resolve_supplier_sku("6204ZZ", "ENG-BRG-6204-01")

    assert sku == "ENG-BRG-6204-01"

    assert method == "VENDOR_CATALOG_ALIAS"

    assert conf >= 0.90



    sku_h, method_h, _ = resolve_supplier_sku("ENGGSKMLS06", "ENG-GSK-MLS-06")

    assert sku_h == "ENG-GSK-MLS-06"

    assert method_h == "HYPHEN_NORMALIZED"



    # Genuine Jaro-Winkler similarity (>= 0.85 threshold) on OCR/typo SKUs

    assert jaro_winkler_similarity("FBD6204Z", "FBD6204ZZ") >= 0.90

    sku_jw, method_jw, conf_jw = resolve_supplier_sku("FBD6204Z", None)

    assert sku_jw == "ENG-BRG-6204-01"

    assert method_jw == "JARO_WINKLER_FUZZY"

    assert conf_jw >= 0.85



    # Revision Collision Guard: Flag engineering revision conflicts for safety

    sku_rev, method_rev, conf_rev = resolve_supplier_sku("ENG-CRK-42CR-02", "ENG-CRK-42CR-01")

    assert sku_rev == "ENG-CRK-42CR-02"

    assert method_rev == "REVISION_MISMATCH_SUSPECTED"

    assert conf_rev < 0.85  # Below auto-resolve threshold -> routes to planner triage



    # Zero-padded revisions (REV-1 vs REV-01) must NOT trigger revision mismatch

    sku_zpad, _, conf_zpad = resolve_supplier_sku("ENG-CRK-42CR-1", "ENG-CRK-42CR-01")

    assert conf_zpad >= 0.80



    # Numeric Transposition Guard: Prevent auto-resolving swapped digits (e.g. 6204 vs 6240)

    sku_trans, method_trans, conf_trans = resolve_supplier_sku("ENG-BRG-6240-01", "ENG-BRG-6204-01")

    assert sku_trans == "ENG-BRG-6240-01"

    assert method_trans == "NUMERIC_TRANSPOSITION_SUSPECTED"

    assert conf_trans < 0.70



    # Dimension Conflict Guard: Sizing/numerical tokens (M12 bolt vs M6 bolt) MUST NOT match

    sku_m12, method_m12, conf_m12 = resolve_supplier_sku("FAST-12-M", "FAST-06-M")

    assert sku_m12 == "FAST-12-M"

    assert method_m12 == "UNRESOLVED"

    assert conf_m12 == 0.0



    # Dimension Guard Refinement: Suffix omission (e.g., variant '01') is NOT a dimension conflict

    sku_crk, method_crk, conf_crk = resolve_supplier_sku("ENGCRK42CRMO", "ENG-CRK-42CR-01")

    assert sku_crk == "ENG-CRK-42CR-01"

    assert conf_crk >= 0.80



    # Vendor Prefix Stripping (e.g., 'VNDR-ENG-BRG-6204-01' -> 'ENG-BRG-6204-01')

    sku_vndr, method_vndr, conf_vndr = resolve_supplier_sku("VNDR-ENG-BRG-6204-01", "ENG-BRG-6204-01")

    assert sku_vndr == "ENG-BRG-6204-01"

    assert method_vndr == "VENDOR_PREFIX_STRIPPED"

    assert conf_vndr >= 0.95





def test_adaptive_ngram_prefiltering_and_safety_fallback() -> None:

    # 1. Short code boundary padding guarantees non-empty bigrams

    m6_ngrams = extract_adaptive_ngrams("M6")

    assert "^M" in m6_ngrams

    assert "M6" in m6_ngrams

    assert "6$" in m6_ngrams



    # 2. Long code trigrams and boundary anchors

    brg_ngrams = extract_adaptive_ngrams("6204ZZ")

    assert "620" in brg_ngrams

    assert "204" in brg_ngrams

    assert "04Z" in brg_ngrams

    assert "4ZZ" in brg_ngrams

    assert "^6" in brg_ngrams

    assert "Z$" in brg_ngrams



    # 3. Inverted index lookup

    test_catalog = {"6204ZZ": "ENG-BRG-6204-01", "M6": "FAST-06-M"}

    idx = build_ngram_inverted_index(test_catalog)

    assert "620" in idx

    assert "6204ZZ" in idx["620"]

    assert "M6" in idx["^M"]



    # 4. Phase 1 Fast Path resolution

    sku_fast, method_fast, conf_fast = resolve_supplier_sku("FBD6204Z", None)

    assert sku_fast == "ENG-BRG-6204-01"

    assert method_fast == "JARO_WINKLER_FUZZY"

    assert conf_fast >= 0.85



    # 5. Fallback safety verification: Severe transposition or unseen query

    # guarantees 0.00% False Negatives by exhausting remaining keys if Phase 1 falls below 0.85

    sku_unseen, method_unseen, conf_unseen = resolve_supplier_sku("TOTALLY-UNSEEN-PART-XYZ", None)

    assert sku_unseen == "TOTALLY-UNSEEN-PART-XYZ"

    assert method_unseen == "UNRESOLVED"

    assert conf_unseen == 0.00





def test_multiformat_date_parsing() -> None:

    assert parse_asn_date("12/10/2026", "DD/MM/YYYY") == date(2026, 10, 12)

    assert parse_asn_date("10/12/2026", "MM/DD/YYYY") == date(2026, 10, 12)

    assert parse_asn_date("2026-10-12", "YYYY-MM-DD") == date(2026, 10, 12)

    # European dot dates, compact 8-digit EDI dates, and timestamps

    assert parse_asn_date("2026.10.24") == date(2026, 10, 24)

    assert parse_asn_date("24.10.2026", "DD/MM/YYYY") == date(2026, 10, 24)

    assert parse_asn_date("20261024") == date(2026, 10, 24)

    assert parse_asn_date("2026-10-24 14:30:00") == date(2026, 10, 24)

    assert parse_asn_date("2026-10-24T08:00:00Z") == date(2026, 10, 24)

    # Excel 5-digit serial dates, 2-digit years, and text dates with spaces

    assert parse_asn_date("46307") == date(2026, 10, 12)

    assert parse_asn_date("12/10/26", "DD/MM/YYYY") == date(2026, 10, 12)

    assert parse_asn_date("12 Oct 2026") == date(2026, 10, 12)

    # Unix epoch timestamps: valid multi-year dates (2025, 2026, 2027) vs out-of-bounds phone/part numbers
    assert parse_asn_date("1765756800") == date(2025, 12, 15)  # Dec 2025
    assert parse_asn_date("1792800000") == date(2026, 10, 24)  # Oct 2026
    assert parse_asn_date("1800000000") == date(2027, 1, 15)   # Jan 2027
    assert parse_asn_date("9876543210") is None                 # 10-digit number out of bounds (year 2282)
    assert parse_asn_date("123456789") is None                  # 9-digit number out of bounds (year 1973)

    # Silent date fallback prevention: corrupt or empty values return None

    assert parse_asn_date("garbage") is None

    assert parse_asn_date("") is None

    assert parse_asn_date("invalid-date-string") is None





def test_blast_radius_analytical_marts(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))

    marts = client.compute_analytical_marts(source="pandas")



    inv_df = marts["inventory_mart"]

    assert (inv_df["phantom_inventory_qty"] >= 0).all()

    assert inv_df["phantom_inventory_value_inr"].sum() > 0



    triage_df = marts["triage_queue"]

    assert len(triage_df) >= 10

    verdicts = set(triage_df["operational_verdict"].unique())

    assert "CRITICAL_SHORT_SHIPMENT_EXPOSED" in verdicts

    assert "FALSE_STARVATION_CLEARED_BY_UDF" in verdicts

    assert "DUPLICATE_PAYLOAD_SUPPRESSED" in verdicts



    initial_net_risk = float(marts["bom_risk_mart"]["revenue_at_risk_net_inr"].sum())

    assert initial_net_risk > 0



    client.approve_harmonization_override(

        asn_line_id="ASN-L-9011",

        resolved_part_num="AXL-HUB-DUC-14",

        normalized_qty=600.0,

        normalized_uom="EA",

        normalized_eta_date="2026-10-12",

        action="EXPEDITED_SHORTFALL_COVERED",

    )

    updated_marts = client.compute_analytical_marts(source="pandas")

    updated_net_risk = float(updated_marts["bom_risk_mart"]["revenue_at_risk_net_inr"].sum())

    assert updated_net_risk < initial_net_risk



    client.reset_planner_overrides()

    reset_marts = client.compute_analytical_marts(source="pandas")

    assert float(reset_marts["bom_risk_mart"]["revenue_at_risk_net_inr"].sum()) == initial_net_risk





def test_cryptographic_audit_trail_and_rollback(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))

    marts = client.compute_analytical_marts(source="pandas")

    initial_net_risk = float(marts["bom_risk_mart"]["revenue_at_risk_net_inr"].sum())



    # 1. Approve Override -> creates chained SHA-256 block

    client.approve_harmonization_override(

        asn_line_id="ASN-L-9011",

        resolved_part_num="AXL-HUB-DUC-14",

        normalized_qty=600.0,

        normalized_uom="EA",

        normalized_eta_date="2026-10-12",

        action="EXPEDITED_SHORTFALL_COVERED",

        user="test_operator_1",

    )



    audit_df, chain_valid = client.get_verified_audit_ledger()

    assert chain_valid is True

    assert len(audit_df) >= 1

    latest_evt = audit_df.iloc[-1]

    assert latest_evt["event_type"] == "OVERRIDE_APPROVED"

    assert latest_evt["asn_line_id"] == "ASN-L-9011"

    assert bool(latest_evt["chain_verified"]) is True



    # 2. Revert Override -> rolls back to baseline and creates cryptographically chained reversal block

    client.revert_planner_override("ASN-L-9011", user="test_operator_1")

    reverted_marts = client.compute_analytical_marts(source="pandas")

    assert float(reverted_marts["bom_risk_mart"]["revenue_at_risk_net_inr"].sum()) == initial_net_risk



    audit_df_after, chain_valid_after = client.get_verified_audit_ledger()

    assert chain_valid_after is True

    assert len(audit_df_after) >= 2

    revert_evt = audit_df_after.iloc[-1]

    assert revert_evt["event_type"] == "OVERRIDE_REVERTED"

    assert revert_evt["prev_hash"] == latest_evt["sha256_hash"]

    assert bool(revert_evt["chain_verified"]) is True





def test_financial_roi_and_downtime_cost_engine(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))

    marts = client.compute_analytical_marts(source="pandas")



    roi_mart = marts["financial_roi_mart"]

    assert roi_mart is not None

    assert roi_mart["headline_roi_x"] >= 150.0  # Approx 176.6x (177x) ROI on unrecoverable plant idle penalty

    assert roi_mart["all_lines_roi_x"] >= 150.0

    assert roi_mart["contribution_margin_roi_x"] >= 40.0  # Approx 52.6x on 15% contribution margin

    assert roi_mart["total_financial_roi_x"] >= 200.0  # Approx 230.2x comprehensive stoppage ROI

    assert roi_mart["net_risk_inr"] > 50_000_000.0  # Rs 5.29 Cr

    assert roi_mart["total_idle_loss_inr"] > 20_000_000.0  # Rs 2.63 Cr

    assert roi_mart["total_stoppage_exposure_inr"] > 75_000_000.0  # Rs 7.92 Cr

    assert roi_mart["avoided_panic_freight_inr"] >= domain_config.AVOIDED_PANIC_FREIGHT_INR

    # Policy Contract Verification (Single Source of Truth enforcement)
    assert roi_mart["contribution_margin_at_risk_inr"] == pytest.approx(
        roi_mart["net_risk_inr"] * domain_config.EBITDA_MARGIN_RATIO, abs=0.01
    )
    assert roi_mart["unrecoverable_stoppage_exposure_inr"] == pytest.approx(
        roi_mart["total_idle_loss_inr"] + roi_mart["contribution_margin_at_risk_inr"], abs=0.01
    )



    bom_risk = marts["bom_risk_mart"]

    assert "downtime_hours_net" in bom_risk.columns

    assert "plant_idle_cost_inr" in bom_risk.columns

    assert "total_stoppage_exposure_inr" in bom_risk.columns

    assert "expedited_freight_cost_inr" in bom_risk.columns



    short_rows = bom_risk[bom_risk["true_net_deficit_qty"] > 0]

    assert len(short_rows) > 0

    assert (short_rows["expedited_freight_cost_inr"] > 0).all()

    assert (short_rows["plant_idle_cost_inr"] > 0).all()



    secured_rows = bom_risk[bom_risk["true_net_deficit_qty"] == 0]

    assert (secured_rows["expedited_freight_cost_inr"] == 0).all()

    assert (secured_rows["plant_idle_cost_inr"] == 0).all()



    triage = marts["triage_queue"]

    assert "mitigation_roi_x" in triage.columns

    assert "avoided_panic_freight_inr" in triage.columns





def test_multiline_po_cartesian_join_isolation(tmp_path) -> None:

    """Verifies that an enterprise Purchase Order with multiple lines for different parts

    does NOT suffer a Cartesian explosion when an inbound ASN ships only one of the parts.

    """

    client = ChakanExasolClient(data_dir=str(tmp_path))

    client.ensure_data_loaded()



    # Create a synthetic 2-line PO on PO-2026-MULTI-99:

    # Line 1: ENG-CRD-42CR-04 (Conrod), ordered 100

    # Line 2: ENG-BLT-M12-109 (Bolt), ordered 500

    test_po_lines = pd.DataFrame([

        {

            "po_line_id": "PO-LINE-M99-1",

            "po_number": "PO-2026-MULTI-99",

            "line_number": 1,

            "supplier_id": "SUP-T2-202",

            "internal_part_num": "ENG-CRD-42CR-04",

            "ordered_qty": 100.0,

            "ordered_uom": "EA",

            "unit_price_inr": 420.0,

            "order_date": "2026-10-01",

            "promised_delivery_date": "2026-10-12",

            "po_line_status": "OPEN",

        },

        {

            "po_line_id": "PO-LINE-M99-2",

            "po_number": "PO-2026-MULTI-99",

            "line_number": 2,

            "supplier_id": "SUP-T2-202",

            "internal_part_num": "ENG-BLT-M12-109",

            "ordered_qty": 500.0,

            "ordered_uom": "EA",

            "unit_price_inr": 45.0,

            "order_date": "2026-10-01",

            "promised_delivery_date": "2026-10-12",

            "po_line_status": "OPEN",

        },

    ])

    client.tables["PURCHASE_ORDER_LINES"] = test_po_lines



    # Create an ASN for PO-2026-MULTI-99 shipping ONLY Line 1 (100 conrods)

    test_asns = pd.DataFrame([

        {

            "asn_line_id": "ASN-TEST-M99-01",

            "asn_number": "ASN-M99-01",

            "supplier_id": "SUP-T2-202",

            "po_number_ref": "PO-2026-MULTI-99",

            "po_line_number_ref": 1,

            "raw_supplier_sku": "ENG-CRD-42CR-04",

            "raw_shipped_qty": 100.0,

            "raw_shipped_uom": "EA",

            "raw_shipment_date": "2026-10-11",

            "raw_eta_date": "2026-10-12",

            "carrier_name": "Chakan Express Logistics",

            "vehicle_lorry_no": "MH-12-AB-1234",

            "source_format": "AS2_EDI",

            "legacy_etl_status": "ACCEPTED",

            "anomaly_type": "CLEAN",

            "ingested_at": pd.Timestamp.now(),

        }

    ])

    client.tables["ASN_LINES_RAW"] = test_asns



    marts = client.compute_analytical_marts(source="pandas")

    risk_df = marts["bom_risk_mart"]



    # Conrods (ENG-CRD-42CR-04) should receive the 100 units inbound

    conrod_risk = risk_df[risk_df["component_part_num"] == "ENG-CRD-42CR-04"]

    assert len(conrod_risk) > 0

    # Inbound qty on conrods should be 100

    assert conrod_risk["harmonized_total_available_qty"].iloc[0] == conrod_risk["true_pickable_atp_qty"].iloc[0] + 100.0



    # Bolts (ENG-BLT-M12-109) must receive exactly 0 inbound units from this PO (no cross-line phantom bleed!)

    bolt_risk = risk_df[risk_df["component_part_num"] == "ENG-BLT-M12-109"]

    assert len(bolt_risk) > 0

    assert bolt_risk["harmonized_total_available_qty"].iloc[0] == bolt_risk["true_pickable_atp_qty"].iloc[0]


def test_dynamic_supplier_catalog_cross_ref_table(tmp_path) -> None:
    """Verifies that catalog aliases are NOT hardcoded inside UDFs, but dynamically resolved
    via the relational SUPPLIER_CATALOG_CROSS_REF table.
    Onboarding a new supplier cross-reference in the table immediately resolves the SKU
    without any UDF or Python code modifications.
    """
    client = ChakanExasolClient(data_dir=str(tmp_path))
    client.ensure_data_loaded()

    # 1. Verify baseline catalog table exists and has 10 active cross-references
    assert "SUPPLIER_CATALOG_CROSS_REF" in client.tables
    xref_df = client.tables["SUPPLIER_CATALOG_CROSS_REF"]
    assert len(xref_df) >= 10
    assert "clean_supplier_part_num" in xref_df.columns
    assert "internal_part_num" in xref_df.columns

    # 2. Onboard a BRAND NEW supplier cross-reference into the relational table:
    # Supplier SUP-T2-206 sends 'PNU-INJ-2200-MAX' for canonical 'ENG-INJ-PZO-22'
    new_cross_ref = pd.DataFrame([
        {
            "cross_ref_id": "XREF-TEST-999",
            "supplier_id": "SUP-T2-206",
            "supplier_part_num": "PNU-INJ-2200-MAX",
            "clean_supplier_part_num": "PNUINJ2200MAX",
            "internal_part_num": "ENG-INJ-PZO-22",
            "mapping_confidence": 0.98,
            "is_active": True,
            "effective_date": "2026-10-01",
        }
    ])
    client.tables["SUPPLIER_CATALOG_CROSS_REF"] = pd.concat([xref_df, new_cross_ref], ignore_index=True)

    # 3. Create an inbound ASN dispatch referencing the new vendor SKU
    test_asns = pd.DataFrame([
        {
            "asn_line_id": "ASN-XREF-TEST-01",
            "asn_number": "ASN-XREF-01",
            "supplier_id": "SUP-T2-206",
            "po_number_ref": "PO-2026-8806",
            "po_line_number_ref": 1,
            "raw_supplier_sku": "PNU-INJ-2200-MAX",
            "raw_shipped_qty": 400.0,
            "raw_shipped_uom": "EA",
            "raw_shipment_date": "2026-10-10",
            "raw_eta_date": "2026-10-12",
            "carrier_name": "Chakan Express Logistics",
            "vehicle_lorry_no": "MH-14-GH-1234",
            "source_format": "EDI_856",
            "legacy_etl_status": "QUARANTINED",
            "anomaly_type": "UNMAPPED_SUPPLIER_SKU",
            "ingested_at": pd.Timestamp.now(),
        }
    ])
    client.tables["ASN_LINES_RAW"] = test_asns

    # Compute analytical marts
    marts = client.compute_analytical_marts(source="pandas")
    lineage = marts["asn_lineage_mart"]

    matched_line = lineage[lineage["asn_line_id"] == "ASN-XREF-TEST-01"]
    assert len(matched_line) == 1
    # Must dynamically resolve to ENG-INJ-PZO-22 from the relational table
    assert matched_line["resolved_part_num"].iloc[0] == "ENG-INJ-PZO-22"
    assert matched_line["sku_match_method"].iloc[0] == "VENDOR_CATALOG_ALIAS"
    assert matched_line["sku_confidence"].iloc[0] >= 0.90





def test_telemetry_and_query_profiler(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))

    marts = client.compute_analytical_marts(source="pandas")



    assert "telemetry" in marts

    telemetry = marts["telemetry"]



    assert telemetry["engine_mode"] in ("EXASOL_PERSONAL", "LOCAL_MIRROR")

    assert telemetry["compute_source"] in ("EXASOL_VIEWS", "PANDAS_MIRROR")

    assert telemetry["latency_ms"] > 0

    assert telemetry["total_rows_evaluated"] >= 500

    assert telemetry["colocation_key"] == "internal_part_num"

    assert "component_part_num" in telemetry["colocation_keys"]

    assert telemetry["colocation_status"] in ("CO_LOCATED_ACTIVE", "MIRROR_IN_PROCESS")

    assert telemetry["udf_engine"] in ("PYTHON3_IN_DB_RAM", "PYTHON_APP_PROCESS")



    stages = telemetry["latency_stages_ms"]

    assert len(stages) == 4

    for _, stage_latency in stages.items():

        assert stage_latency >= 0.0



    counts = telemetry["table_row_counts"]

    assert counts["ASN_LINES_RAW"] >= 400

    assert counts["ITEM_MASTER"] >= 15

    assert counts["BILL_OF_MATERIALS"] >= 15





def test_what_if_scenario_simulation_additive_waterfall(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))



    # 1. Null Shock (Zero chaos parameters must equal baseline exactly)

    null_sim = client.compute_simulation_marts(

        transit_delay_days=0,

        quarantine_defect_pct=0.0,

        demand_surge_multiplier=1.0,

    )

    assert null_sim["delta_net_risk_inr"] == 0.0

    assert null_sim["delta_total_exposure_inr"] == 0.0

    assert null_sim["delta_min_hours_to_halt"] == 0.0



    # 2. Compound Disruption Shock (+3 days delay, 20% quarantine defect, 1.25x demand surge)

    shock_sim = client.compute_simulation_marts(

        transit_delay_days=3,

        quarantine_defect_pct=0.20,

        demand_surge_multiplier=1.25,

    )



    base_net = shock_sim["baseline"]["financial_roi_mart"]["net_risk_inr"]

    sim_net = shock_sim["simulated"]["financial_roi_mart"]["net_risk_inr"]

    assert sim_net > base_net

    assert shock_sim["delta_net_risk_inr"] > 0

    assert shock_sim["delta_total_exposure_inr"] > 0



    # Check Waterfall Stages AND strict additivity (sum of relative stages == total)

    wf = shock_sim["waterfall_data"]

    assert len(wf) == 5

    assert wf[0]["Stage"] == "1. Baseline True Shortage"

    assert wf[0]["Amount"] == base_net

    assert wf[4]["Stage"] == "Total Simulated Exposure"

    assert wf[4]["Amount"] == sim_net

    assert sum(step["Amount"] for step in wf[:4]) == pytest.approx(wf[4]["Amount"], abs=0.01)



    # Starvation run hours must be reduced or equal under shock

    base_hrs = shock_sim["baseline"]["bom_risk_mart"]["hours_to_starvation_harmonized"]

    sim_hrs = shock_sim["simulated"]["bom_risk_mart"]["hours_to_starvation_harmonized"]

    assert (sim_hrs <= base_hrs).all()





def test_scale_benchmark_suite() -> None:

    from src.benchmarks.scale_benchmark import (

        get_verified_scale_benchmark,

        run_scale_benchmark,

    )



    # 1. Pure Measured CPU Benchmark Integrity (0.0 ms synthetic network penalty)

    bench = get_verified_scale_benchmark(network_hop_penalty_ms=0.0)

    assert bench["max_scale_rows"] == 10000

    assert bench["network_hop_penalty_ms"] == 0.0

    if bench["is_live_database"]:
        assert bench["peak_speedup_factor"] >= 1.0
    else:
        assert bench["peak_speedup_factor"] > 0.0

    assert len(bench["results_table"]) == 4

    assert bench["engine_tested"] in [

        "Vectorized In-Memory Mirror (Pandas/NumPy)",

        "Native Exasol Personal Engine (In-DB SQL & Python 3 UDFs)",

    ]



    for row in bench["results_table"]:

        assert row["legacy_network_ms"] == 0.0

        assert row["columnar_latency_ms"] > 0.0

        assert row["legacy_cpu_ms"] > 0.0

        assert row["speedup_factor"] > 0.0

        assert row["engine_name"] in [

            "Vectorized In-Memory Mirror (Pandas/NumPy)",

            "Native Exasol Personal Engine (In-DB SQL & Python 3 UDFs)",

        ]



    # 2. Live Dynamic Scaling Test (Fast subset 500 rows, zero synthetic penalty)

    live_res = run_scale_benchmark(scales=[500], network_hop_penalty_ms=0.0)

    assert len(live_res["results_table"]) == 1

    assert live_res["results_table"][0]["legacy_network_ms"] == 0.0

    assert live_res["results_table"][0]["columnar_latency_ms"] > 0.0





def test_broken_connection_raises_explicit_errors(tmp_path) -> None:

    class BrokenConn:

        def execute(self, *args, **kwargs):

            raise RuntimeError("Simulated database failure")



        def import_from_pandas(self, *args, **kwargs):

            raise RuntimeError("Simulated bulk import failure")



    client = ChakanExasolClient(data_dir=str(tmp_path))

    client.conn = BrokenConn()



    with pytest.raises(ExasolBootstrapError):

        client.bootstrap_exasol_schema_and_data()



    client.conn = BrokenConn()

    with pytest.raises(ExasolWriteError):

        client.approve_harmonization_override(

            asn_line_id="ASN-L-9011",

            resolved_part_num="AXL-HUB-DUC-14",

            normalized_qty=600.0,

            normalized_uom="EA",

            normalized_eta_date="2026-10-12",

        )





def test_exasol_views_match_pandas_mirror(tmp_path) -> None:

    client = ChakanExasolClient(data_dir=str(tmp_path))

    if not client.connect():

        pytest.skip("Exasol Personal container not reachable on localhost:8563")



    mode, _ = client.bootstrap_exasol_schema_and_data()

    assert mode == "EXASOL_PERSONAL"



    exa_marts = client.compute_analytical_marts(source="exasol")

    pan_marts = client.compute_analytical_marts(source="pandas")



    assert exa_marts["compute_source"] == "EXASOL_VIEWS"

    assert pan_marts["compute_source"] == "PANDAS_MIRROR"



    for kpi_key in (

        "total_scheduled_value_inr",

        "legacy_risk_inr",

        "net_risk_inr",

        "cleared_by_udf_inr",

        "total_idle_loss_inr",

        "total_stoppage_exposure_inr",

        "total_freight_cost_inr",

        "headline_roi_x",

        "false_alarms_cleared_count",

        "avoided_panic_freight_inr",

    ):

        assert exa_marts["financial_roi_mart"][kpi_key] == pytest.approx(

            pan_marts["financial_roi_mart"][kpi_key], abs=0.01

        ), f"Mismatch on {kpi_key}"













# ---------------------------------------------------------------------------
# Phase 2: live simulation parity + session isolation (skipped when Exasol is offline)
# ---------------------------------------------------------------------------
_SIM_PRESETS = [
    (3, 0.05, 1.0),   # Western Ghats Monsoon
    (1, 0.35, 1.0),   # Tier-2 Foundry Porosity
    (2, 0.15, 1.35),  # Festive OEM Surge
    (3, 0.20, 1.20),  # Compound shock
]


def _live_client(tmp_path) -> ChakanExasolClient:
    client = ChakanExasolClient(data_dir=str(tmp_path))
    if not client.connect():
        pytest.skip("Exasol Personal container not reachable on localhost:8563")
    client.bootstrap_exasol_schema_and_data()
    return client


@pytest.mark.parametrize("delay,defect,surge", _SIM_PRESETS)
def test_live_simulation_matches_pandas_mirror(tmp_path, delay, defect, surge) -> None:
    client = _live_client(tmp_path)
    exa = client.compute_analytical_marts(delay, defect, surge, source="exasol")
    pan = client.compute_analytical_marts(delay, defect, surge, source="pandas")
    assert exa["compute_source"] == "EXASOL_VIEWS"
    for key in ("net_risk_inr", "legacy_risk_inr", "total_stoppage_exposure_inr", "total_idle_loss_inr"):
        assert exa["financial_roi_mart"][key] == pytest.approx(pan["financial_roi_mart"][key], abs=0.01), key
    assert float(exa["bom_risk_mart"]["hours_to_starvation_harmonized"].min()) == pytest.approx(
        float(pan["bom_risk_mart"]["hours_to_starvation_harmonized"].min()), abs=0.05
    )


def test_live_waterfall_is_additive_and_matches_mirror(tmp_path) -> None:
    client = _live_client(tmp_path)
    exa = client.compute_simulation_marts(3, 0.2, 1.2, source="exasol")
    pan = client.compute_simulation_marts(3, 0.2, 1.2, source="pandas")
    for e, p in zip(exa["waterfall_data"], pan["waterfall_data"]):
        assert e["Amount"] == pytest.approx(p["Amount"], abs=0.01), e["Stage"]
    steps = exa["waterfall_data"]
    assert sum(s["Amount"] for s in steps[:4]) == pytest.approx(steps[4]["Amount"], abs=0.01)


def test_live_simulation_parameters_are_session_isolated(tmp_path) -> None:
    a = _live_client(tmp_path)
    b = ChakanExasolClient(data_dir=str(tmp_path))
    assert b.connect()
    base_b = b.compute_analytical_marts(source="exasol")["financial_roi_mart"]["net_risk_inr"]
    shock_a = a.compute_analytical_marts(3, 0.2, 1.2, source="exasol")["financial_roi_mart"]["net_risk_inr"]
    assert shock_a != pytest.approx(base_b)
    # Session A's scenario row must not change what session B reads from the shared view.
    rows = b._fetch_df(f"SELECT SUM(revenue_at_risk_net_inr) AS n FROM {b.schema}.VW_BOM_LINE_STARVATION_RISK")
    assert float(rows.iloc[0]["n"]) == pytest.approx(base_b, abs=0.01)
