"""Tests for BYOD inbound harmonization and the community feedback log."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from src.exasol_engine.custom_ingestor import (
    PRESET_LABELS,
    anonymize_dataset,
    detect_and_map_columns,
    evaluate_batch_impact,
    generate_expedite_manifest,
    generate_sap_migo_export,
    get_industrial_scenario_preset,
    harmonize_and_evaluate_inbound,
    harmonize_batch,
)
from src.exasol_engine.db_client import ChakanExasolClient
from src.utils.telemetry import (
    dispatch_webhook_alert,
    get_all_feedback,
    get_feedback_summary,
    record_feedback,
    verify_feedback_chain,
)

REAL_COMPANY_MARKERS = ("tata", "bharat forge", "bosch", "mahindra", "bajaj")


@pytest.fixture(scope="module")
def client() -> ChakanExasolClient:
    c = ChakanExasolClient()
    c.ensure_data_loaded()
    return c


@pytest.fixture(scope="module")
def marts(client: ChakanExasolClient) -> dict:
    return client.compute_analytical_marts()


def test_feedback_log_starts_empty_with_no_placeholder_reviews():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.json"
        assert get_all_feedback(path) == []
        summary = get_feedback_summary(path)
        assert summary["total_reviews"] == 0
        assert summary["avg_rating"] is None
        assert not path.exists(), "reading an empty log must not create placeholder data"


def test_feedback_log_hash_chain_and_tamper_detection():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ledger.json"
        first = record_feedback(5, "Supply Chain Analyst", "Org A", "Clear triage view.", "Tab 1", ledger_path=path)
        second = record_feedback(3, "Data Engineer / Judge", "Org B", "Needs time-phasing.", "Tab 2", ledger_path=path)
        assert first["index"] == 1 and second["index"] == 2
        assert second["prev_hash"] == first["hash"]
        assert verify_feedback_chain(path)[0] is True

        summary = get_feedback_summary(path)
        assert summary["total_reviews"] == 2
        assert summary["avg_rating"] == 4.0

        data = json.loads(path.read_text(encoding="utf-8"))
        data[0]["feedback_text"] = "TAMPERED"
        path.write_text(json.dumps(data), encoding="utf-8")
        ok, msg = verify_feedback_chain(path)
        assert ok is False and "Tampered" in msg


def test_presets_use_no_real_company_names():
    labels = " ".join(PRESET_LABELS.values()).lower()
    assert not any(m in labels for m in REAL_COMPANY_MARKERS)
    for key in PRESET_LABELS:
        text = get_industrial_scenario_preset(key).to_csv().lower()
        assert not any(m in text for m in REAL_COMPANY_MARKERS)


def test_empty_batch_reproduces_baseline_exactly(marts: dict):
    empty = pd.DataFrame({
        "resolved_part_num": pd.Series(dtype=str), "legacy_visible_qty": pd.Series(dtype=float),
        "harmonized_qty": pd.Series(dtype=float), "unit_cost_inr": pd.Series(dtype=float),
        "line_value_inr": pd.Series(dtype=float), "sku_confidence": pd.Series(dtype=float),
        "status": pd.Series(dtype=str),
    })
    s = evaluate_batch_impact(empty, marts)["summary"]
    roi = marts["financial_roi_mart"]
    assert s["baseline_legacy_risk_inr"] == pytest.approx(roi["legacy_risk_inr"])
    assert s["baseline_net_risk_inr"] == pytest.approx(roi["net_risk_inr"])
    assert s["net_risk_with_batch_inr"] == pytest.approx(s["baseline_net_risk_inr"])
    assert s["legacy_risk_with_batch_inr"] == pytest.approx(s["baseline_legacy_risk_inr"])


@pytest.mark.parametrize("preset", list(PRESET_LABELS))
def test_presets_harmonize_and_only_reduce_exposure(client, marts, preset):
    res = harmonize_and_evaluate_inbound(get_industrial_scenario_preset(preset), client, marts)
    s, df = res["summary"], res["harmonized_df"]
    assert len(df) == len(get_industrial_scenario_preset(preset))
    assert s["net_risk_with_batch_inr"] <= s["baseline_net_risk_inr"] + 1e-6
    assert s["net_risk_with_batch_inr"] <= s["legacy_risk_with_batch_inr"] + 1e-6
    assert s["batch_value_recovered_inr"] >= 0.0
    assert res["engine"]["engine"] in {"EXASOL_UDF", "PYTHON_UDF_PARITY"}


def test_duplicates_and_low_confidence_rows_are_not_counted(client, marts):
    df = harmonize_and_evaluate_inbound(get_industrial_scenario_preset("PACKAGING_CHAOS"), client, marts)["harmonized_df"]
    dup = df[df["status"] == "DUPLICATE_SUPPRESSED"]
    review = df[df["status"] == "NEEDS_PLANNER_REVIEW"]
    assert len(dup) == 1 and (dup["harmonized_qty"] == 0).all()
    assert len(review) == 1 and (review["harmonized_qty"] == 0).all()
    # UOM normalization sanity: 40 x BOX_100 -> 4,000 EA; 4.5 MT -> 4,500 KG
    assert df.loc[0, "normalized_qty"] == 4000.0
    assert df[df["supplier_part_num"] == "42CRMO4BILLET"]["normalized_qty"].iloc[0] == 4500.0


def test_engine_label_without_exasol_reports_fallback(client):
    offline = SimpleNamespace(conn=None, tables=client.tables, schema="CHAKAN_SCM", ensure_data_loaded=lambda: None)
    _, info = harmonize_batch(get_industrial_scenario_preset("SKU_REVISIONS"), offline)
    assert info["engine"] == "PYTHON_UDF_PARITY"
    assert info["fallback_reason"]


def test_exasol_failure_falls_back_and_says_so(client):
    class BrokenConn:
        def execute(self, *_a, **_k):
            raise RuntimeError("boom")

    broken = SimpleNamespace(conn=BrokenConn(), tables=client.tables, schema="CHAKAN_SCM", ensure_data_loaded=lambda: None)
    out, info = harmonize_batch(get_industrial_scenario_preset("SKU_REVISIONS"), broken)
    assert info["engine"] == "PYTHON_UDF_PARITY"
    assert "boom" in info["fallback_reason"]
    assert len(out) == 6


def test_column_auto_mapping_and_synonyms():
    messy = pd.DataFrame({
        "LR_NO": ["CH-101", "CH-102"], "PO_REF": ["PO-9001", "PO-9002"],
        "VENDOR_NAME": ["A", "B"], "ITEM_CODE": ["X1", "X2"],
        "DISPATCH_QUANTITY": [2500, 120], "PACK_TYPE": ["EA", "BOX_100"], "ETA": ["2026-10-25", "2026-10-26"],
    })
    mapped, mapping = detect_and_map_columns(messy)
    assert mapping["asn_number"] == "LR_NO" and mapping["supplier_part_num"] == "ITEM_CODE"
    assert mapped["shipped_qty"].iloc[0] == 2500.0


def test_anonymization_masks_identifiers_consistently():
    raw = pd.DataFrame({
        "asn_number": ["ASN-SECRET-1", "ASN-SECRET-2"], "po_number_ref": ["PO-CONF-1", "PO-CONF-2"],
        "supplier_id": ["ACME", "ACME"], "supplier_part_num": ["ALPHA", "BETA"],
        "shipped_qty": [100.0, 50.0], "shipped_uom": ["EA", "BOX_100"], "expected_delivery_date": ["2026-10-25"] * 2,
    })
    anon, meta = anonymize_dataset(raw)
    assert not anon["supplier_id"].str.contains("ACME").any()
    assert anon["supplier_id"].iloc[0] == anon["supplier_id"].iloc[1]
    assert anon["shipped_qty"].tolist() == [100.0, 50.0]
    assert meta["anonymized_suppliers_count"] == 1


def test_masked_exports_still_resolve_because_masking_is_display_only(client, marts):
    from src.exasol_engine.custom_ingestor import anonymize_frame

    res = harmonize_and_evaluate_inbound(get_industrial_scenario_preset("SKU_REVISIONS"), client, marts)
    masked, _ = anonymize_frame(res["harmonized_df"])
    assert (res["harmonized_df"]["harmonized_qty"] > 0).any()
    assert masked["supplier_part_num"].str.startswith("SKU-ANON-").all()
    assert (masked["resolved_part_num"] == res["harmonized_df"]["resolved_part_num"]).all()


def test_exports(client, marts):
    res = harmonize_and_evaluate_inbound(get_industrial_scenario_preset("SKU_REVISIONS"), client, marts)
    csv = generate_sap_migo_export(res["harmonized_df"])
    assert csv.splitlines()[0] == "EBELN,BOLNR,MATNR,MENGE,MEINS,BUDAT,LIFNR,BKTXT"
    assert "MANGROVE_HARMONIZED" in csv
    note = generate_expedite_manifest(res["summary"], res["shortage_df"])
    assert "EXPEDITE REVIEW NOTE" in note


def test_webhook_dispatcher_fails_quietly():
    assert dispatch_webhook_alert("TEST", {"rating": 5}, webhook_url="") is False
    assert dispatch_webhook_alert("TEST", {"rating": 5}, webhook_url="https://invalid.domain.example/webhook") is False


def test_domain_auto_onboarding_and_standardized_taxonomy(client):
    from src.exasol_engine.custom_ingestor import harmonize_and_evaluate_inbound, DOMAIN_PROFILES

    # Retail batch with arbitrary e-commerce items
    retail_df = pd.DataFrame({
        "asn_number": ["ASN-RET-01", "ASN-RET-02", "ASN-RET-03"],
        "po_number_ref": ["PO-ORD-101", "PO-ORD-102", "PO-ORD-103"],
        "supplier_id": ["Nike_Direct", "UnderArmour_Hub", "Puma_Logistics"],
        "supplier_part_num": ["1360", "957", "365"],
        "shipped_qty": [10.0, 20.0, 15.0],
        "shipped_uom": ["BOX_100", "EA", "EA"],
        "expected_delivery_date": ["10/24/2026", "2026-10-25", "25/10/2026"],
    })

    assert "RETAIL_DATACO" in DOMAIN_PROFILES
    res = harmonize_and_evaluate_inbound(retail_df, client, domain="RETAIL_DATACO")
    
    assert res["onboarding_meta"] is not None
    assert res["onboarding_meta"]["domain"] == "RETAIL_DATACO"
    assert res["onboarding_meta"]["products_onboarded"] == 3
    assert res["onboarding_meta"]["canonical_taxonomy"] == "RET-CARD-XXXX"
    
    df = res["harmonized_df"]
    # Verify canonical taxonomy standardized: 1360 -> RET-CARD-1360
    assert df.loc[0, "resolved_part_num"] == "RET-CARD-1360"
    assert df.loc[0, "sku_match_method"] == "STANDARDIZED_DOMAIN_TAXONOMY"
    assert df.loc[0, "sku_confidence"] >= 0.95
    # Verify packaging normalized: 10 BOX_100 -> 1000 EA
    assert df.loc[0, "normalized_qty"] == 1000.0
    # Clean passthrough / harmonized status
    assert (df["harmonized_qty"] > 0).all()
