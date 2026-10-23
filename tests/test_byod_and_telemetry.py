"""Automated Test Suite for BYOD Industrial Ingestion and Live Feedback Telemetry."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from src.exasol_engine.custom_ingestor import (
    anonymize_dataset,
    detect_and_map_columns,
    generate_expedite_manifest,
    generate_sap_migo_export,
    get_industrial_scenario_preset,
    harmonize_and_evaluate_inbound,
    parse_custom_inbound_stream,
)
from src.exasol_engine.db_client import ChakanExasolClient
from src.utils.telemetry import (
    dispatch_webhook_alert,
    get_all_feedback,
    get_feedback_summary,
    record_feedback,
    verify_feedback_chain,
)


@pytest.fixture(scope="module")
def client() -> ChakanExasolClient:
    """Fixture providing initialized client."""
    c = ChakanExasolClient()
    c.ensure_data_loaded()
    return c


def test_feedback_ledger_cryptographic_chain():
    """Verify SHA-256 Merkle hash chaining, tamper detection, and summary statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_feedback_ledger.json"

        # 1. Initial seed generation
        chain = get_all_feedback(ledger_path)
        assert len(chain) == 3
        is_valid, msg = verify_feedback_chain(ledger_path)
        assert is_valid is True

        # 2. Add new review
        new_entry = record_feedback(
            rating=5,
            persona="Automotive Materials Planner",
            organization="Tata Motors Ancillary Facility",
            feedback_text="Testing False Starvation UDF clearance in production.",
            scenario_tested="BYOD Studio",
            ledger_path=ledger_path,
        )
        assert new_entry["index"] == 4
        assert new_entry["prev_hash"] == chain[-1]["hash"]

        # Verify chain with 4 blocks
        is_valid2, _ = verify_feedback_chain(ledger_path)
        assert is_valid2 is True

        # Summary check
        summary = get_feedback_summary(ledger_path)
        assert summary["total_reviews"] == 4
        assert summary["avg_rating"] == 5.0
        assert summary["stars_5_pct"] == 100.0

        # 3. Tamper detection
        with open(ledger_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data[1]["feedback_text"] = "TAMPERED_FEEDBACK_TEXT"
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        is_valid_tampered, tamper_msg = verify_feedback_chain(ledger_path)
        assert is_valid_tampered is False
        assert "Tampered hash" in tamper_msg


def test_industrial_scenario_presets_and_harmonization(client: ChakanExasolClient):
    """Verify that all 3 industrial presets evaluate with high confidence and valid Blast Radius."""
    presets = ["TATA_CHAKAN_CORRIDOR", "BHARAT_FORGE_FOUNDRY", "BOSCH_POWERTRAIN_ELECTRONICS"]

    for p in presets:
        df = get_industrial_scenario_preset(p)
        assert len(df) > 0
        assert "asn_number" in df.columns
        assert "supplier_part_num" in df.columns

        res = harmonize_and_evaluate_inbound(df, client)
        summary = res["summary"]
        harmo_df = res["harmonized_df"]

        assert len(harmo_df) == len(df)
        assert summary["total_shipped_value_inr"] > 0
        assert summary["avg_confidence"] >= 0.85
        assert "threatened_lines" in summary


def test_column_auto_mapping_and_synonyms():
    """Verify that messy, non-standard column headers are automatically resolved to canonical schema."""
    messy_data = pd.DataFrame({
        "LR_NO": ["CH-101", "CH-102"],
        "PO_REF": ["PO-9001", "PO-9002"],
        "VENDOR_NAME": ["Kalyani Steels", "Bharat Bearings"],
        "ITEM_CODE": ["ENG-BLT-M12-109", "ENG-BRG-6204-01"],
        "DISPATCH_QUANTITY": [2500, 120],
        "PACK_TYPE": ["EA", "BOX_100"],
        "ETA": ["2026-10-25", "2026-10-26"],
    })

    mapped_df, mapping = detect_and_map_columns(messy_data)

    assert "asn_number" in mapped_df.columns
    assert "po_number_ref" in mapped_df.columns
    assert "supplier_id" in mapped_df.columns
    assert "supplier_part_num" in mapped_df.columns
    assert "shipped_qty" in mapped_df.columns
    assert "shipped_uom" in mapped_df.columns
    assert "expected_delivery_date" in mapped_df.columns

    assert mapping["asn_number"] == "LR_NO"
    assert mapping["supplier_part_num"] == "ITEM_CODE"
    assert mapped_df["shipped_qty"].iloc[0] == 2500.0


def test_dataset_anonymization_privacy_guarantee():
    """Verify that client-side anonymizer masks proprietary identifiers while preserving token relationships."""
    raw_df = pd.DataFrame({
        "asn_number": ["ASN-SECRET-1", "ASN-SECRET-2"],
        "po_number_ref": ["PO-CONFIDENTIAL-1", "PO-CONFIDENTIAL-2"],
        "supplier_id": ["TATA_AUTOPARTS_CHAKAN", "TATA_AUTOPARTS_CHAKAN"],
        "supplier_part_num": ["PROPRIETARY_SKU_ALPHA", "PROPRIETARY_SKU_BETA"],
        "shipped_qty": [100.0, 50.0],
        "shipped_uom": ["EA", "BOX_100"],
        "expected_delivery_date": ["2026-10-25", "2026-10-25"],
    })

    anon_df, meta = anonymize_dataset(raw_df)

    # Identifiers must be masked
    assert not anon_df["supplier_id"].str.contains("TATA").any()
    assert not anon_df["supplier_part_num"].str.contains("PROPRIETARY").any()
    assert anon_df["supplier_id"].iloc[0].startswith("SUP-ANON-")
    assert anon_df["supplier_part_num"].iloc[0].startswith("SKU-ANON-")

    # Identical supplier must map to identical anonymous token
    assert anon_df["supplier_id"].iloc[0] == anon_df["supplier_id"].iloc[1]

    # Quantities and UOMs must remain intact
    assert anon_df["shipped_qty"].iloc[0] == 100.0
    assert anon_df["shipped_uom"].iloc[1] == "BOX_100"


def test_export_manifest_and_sap_migo_generation(client: ChakanExasolClient):
    """Verify generation of SAP MIGO CSV export and supplier expedite directive."""
    df = get_industrial_scenario_preset("BHARAT_FORGE_FOUNDRY")
    res = harmonize_and_evaluate_inbound(df, client)

    # SAP MIGO
    migo_csv = generate_sap_migo_export(res["harmonized_df"])
    assert "MANDT,EBELN,BOLNR,MATNR,MENGE,MEINS,BUDAT,LIFNR,BKTXT" in migo_csv
    assert "MANGROVE_EXASOL_CLEARED" in migo_csv

    # Expedite directive
    expedite_md = generate_expedite_manifest(res["summary"], res["shortage_df"])
    assert "CRITICAL EXPEDITE DISPATCH MANIFEST" in expedite_md
    assert "Threatened Production Lines" in expedite_md


def test_webhook_dispatcher_graceful_handling():
    """Verify that webhook dispatch fails safely without exceptions when URL is absent or invalid."""
    # Absent URL
    sent1 = dispatch_webhook_alert("TEST", {"rating": 5}, webhook_url="")
    assert sent1 is False

    # Invalid URL
    sent2 = dispatch_webhook_alert("TEST", {"rating": 5}, webhook_url="https://invalid.domain.example/webhook")
    assert sent2 is False
