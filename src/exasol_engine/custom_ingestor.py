"""Bring-Your-Own-Data (BYOD) ingestion: harmonize an uploaded inbound batch and
measure its effect on the existing Chakan baseline.

Design (so the numbers stay comparable with Tabs 1-7):

* The uploaded rows are layered ON TOP of the baseline ASN feed. Per-component
  baseline inbound quantities (legacy-visible and harmonized), true ATP and the
  production requirement come from the baseline ``bom_risk_mart``. The batch's
  quantities are added and the exact same starvation formula as
  ``VW_BOM_LINE_STARVATION_RISK`` is re-evaluated. An empty batch therefore
  reproduces the baseline KPIs exactly.
* Harmonization (SKU resolution, UOM normalization, date parsing) runs through the
  same three Python UDFs that the Exasol views use. When a live Exasol connection is
  available the rows are staged in a scratch table and the UDFs execute INSIDE Exasol
  (engine = ``EXASOL_UDF``). Otherwise the identical logic in ``harmonizer_core.py``
  runs locally (engine = ``PYTHON_UDF_PARITY``). The engine used is always reported.
* "Legacy ETL" is modelled conservatively: a row is visible to the legacy system only
  if its SKU is already an exact ITEM_MASTER key and its UOM already equals the
  item's base UOM.
"""

from __future__ import annotations

import io
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from src.exasol_engine.harmonizer_core import (
    normalize_uom_quantity,
    parse_asn_date,
    resolve_supplier_sku,
)

CONFIDENCE_THRESHOLD = 0.85

CANONICAL_COLUMNS = [
    "asn_number",
    "po_number_ref",
    "supplier_id",
    "supplier_part_num",
    "shipped_qty",
    "shipped_uom",
    "expected_delivery_date",
]

COLUMN_SYNONYMS = {
    "asn_number": [
        "asn_number", "asn_no", "asn", "dispatch_note", "challan_no", "delivery_note",
        "tracking_no", "shipment_id", "lr_no", "order_item_id", "line_item_id", "shipment_no",
    ],
    "po_number_ref": [
        "po_number_ref", "po_number", "po_no", "po", "purchase_order", "order_no",
        "order_id", "po_ref", "order_number", "ebeln",
    ],
    "supplier_id": [
        "supplier_id", "vendor_id", "supplier", "vendor", "supplier_name",
        "vendor_name", "vendor_code", "department_name", "market", "customer_city", "lifnr",
    ],
    "supplier_part_num": [
        "supplier_part_num", "part_number", "part_no", "sku", "item_code",
        "material_id", "component_code", "vendor_sku", "item_id", "product_card_id",
        "product_id", "product_name", "order_item_cardprod_id", "matnr", "material",
    ],
    "shipped_qty": [
        "shipped_qty", "qty", "quantity", "dispatch_qty", "shipped_quantity",
        "count", "delivered_qty", "dispatch_quantity", "order_item_quantity", "menge",
    ],
    "shipped_uom": [
        "shipped_uom", "uom", "unit", "pack_type", "packaging", "measure_unit",
        "package_type", "unit_of_measure", "meins",
    ],
    "expected_delivery_date": [
        "expected_delivery_date", "eta", "delivery_date", "expected_date",
        "challan_date", "dispatch_date", "date", "arrival_date",
        "shipping_date_dateorders", "shipping_date", "order_date_dateorders", "budat",
    ],
}

PRESET_LABELS = {
    "PACKAGING_CHAOS": "Preset A: Tier-1 OEM Inbound (Fasteners & Bearings — Packaging Chaos, OCR-stripped SKUs, Duplicate)",
    "SKU_REVISIONS": "Preset B: Tier-2 Sub-assembly Inbound (Castings & Gears — SKU Revisions, Vendor Aliases, Bulk Crates)",
    "EV_UNITS_AND_DATES": "Preset C: Tier-1 Powertrain Inbound (EV Laminations & Copper — Weight Unit Inversions, Epoch Dates)",
}

DOMAIN_PROFILES = {
    "AUTOMOTIVE": "🏭 Automotive & EV Powertrain (Chakan Cluster — Default)",
    "RETAIL_DATACO": "📦 Retail, FMCG & E-Commerce (DataCo Compatible)",
    "UNIVERSAL_AUTODISCOVER": "🌐 Universal Custom Enterprise (Auto-Onboard Any File)",
}


# --------------------------------------------------------------------------- parsing
def parse_custom_inbound_stream(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse raw uploaded file bytes (CSV, TSV or Excel) into a DataFrame (in memory only).
    
    Robustly handles heterogeneous character encodings (UTF-8, Latin-1, CP1252, ISO-8859-1)
    common in public Kaggle datasets and legacy enterprise exports.
    """
    fn_lower = filename.lower()
    bio = io.BytesIO(file_bytes)
    if fn_lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(bio)
    
    encodings_to_try = ("utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1")
    if fn_lower.endswith(".tsv"):
        for enc in encodings_to_try:
            try:
                bio.seek(0)
                return pd.read_csv(bio, sep="\t", encoding=enc)
            except UnicodeDecodeError:
                continue
            except Exception:
                break

    # Try common CSV delimiters and encodings
    for enc in encodings_to_try:
        for sep in (",", ";", "\t", "|"):
            try:
                bio.seek(0)
                df = pd.read_csv(bio, sep=sep, encoding=enc)
                if len(df.columns) > 1:
                    return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue

    # Final robust fallback with Latin-1 (accepts any byte stream 0x00-0xFF without failing)
    bio.seek(0)
    return pd.read_csv(bio, encoding="latin1", on_bad_lines="skip")


def detect_and_map_columns(
    df: pd.DataFrame,
    custom_mapping: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Map arbitrary column headers onto the canonical inbound schema."""
    mapping: dict[str, str] = {}
    normalized_cols = {re.sub(r"[^a-z0-9_]", "", str(c).strip().lower().replace(" ", "_")): c for c in df.columns}

    if custom_mapping:
        for canonical, source_col in custom_mapping.items():
            if source_col and source_col in df.columns:
                mapping[canonical] = source_col

    for canonical, synonyms in COLUMN_SYNONYMS.items():
        if canonical in mapping:
            continue
        for syn in synonyms:
            clean_syn = re.sub(r"[^a-z0-9_]", "", syn)
            if clean_syn in normalized_cols:
                mapping[canonical] = normalized_cols[clean_syn]
                break

    mapped_df = pd.DataFrame(index=df.index)
    for canonical in CANONICAL_COLUMNS:
        if canonical in mapping:
            mapped_df[canonical] = df[mapping[canonical]]
        elif canonical == "asn_number":
            mapped_df[canonical] = [f"ASN-BYOD-{i + 1:04d}" for i in range(len(df))]
        elif canonical == "po_number_ref":
            mapped_df[canonical] = ""
        elif canonical == "supplier_id":
            mapped_df[canonical] = "UNKNOWN"
        elif canonical == "supplier_part_num":
            mapped_df[canonical] = ""
        elif canonical == "shipped_qty":
            mapped_df[canonical] = 0.0
        elif canonical == "shipped_uom":
            mapped_df[canonical] = "EA"
        else:
            mapped_df[canonical] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    mapped_df["shipped_qty"] = pd.to_numeric(
        mapped_df["shipped_qty"].astype(str).str.replace(r"[^\d.-]", "", regex=True),
        errors="coerce",
    ).fillna(0.0)
    for str_col in ["asn_number", "po_number_ref", "supplier_id", "supplier_part_num", "shipped_uom", "expected_delivery_date"]:
        mapped_df[str_col] = mapped_df[str_col].astype(str).str.strip()

    return mapped_df.reset_index(drop=True), mapping


# --------------------------------------------------------------------------- privacy
def _tokenize(series: pd.Series, prefix: str, width: int) -> tuple[pd.Series, int]:
    mapping: dict[str, str] = {}
    for value in series.unique():
        mapping[value] = f"{prefix}-{len(mapping) + 1:0{width}d}"
    return series.map(mapping), len(mapping)


def anonymize_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Replace vendor/SKU/PO/ASN identifiers with stable tokens in whichever columns exist.

    Used for the DISPLAYED and EXPORTED copy only. Resolution always runs on the real
    identifiers; masking before resolution would make every SKU unresolvable.
    """
    out = df.copy()
    spec = [
        ("supplier_id", "SUP-ANON", 2, "anonymized_suppliers_count"),
        ("supplier_part_num", "SKU-ANON", 3, "anonymized_skus_count"),
        ("po_number_ref", "PO-ANON", 4, "anonymized_pos_count"),
        ("asn_number", "ASN-ANON", 4, "anonymized_asns_count"),
    ]
    meta: dict[str, Any] = {"privacy_status": "DISPLAY_AND_EXPORT_MASKED"}
    for col, prefix, width, meta_key in spec:
        if col in out.columns:
            out[col], meta[meta_key] = _tokenize(out[col].astype(str), prefix, width)
    return out, meta


def anonymize_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Backward-compatible wrapper around :func:`anonymize_frame`."""
    return anonymize_frame(df)


# --------------------------------------------------------------------------- presets
def get_industrial_scenario_preset(preset_key: str) -> pd.DataFrame:
    """Synthetic inbound batches that reference open POs of the synthetic baseline dataset.

    All suppliers, parts and PO numbers come from the synthetic ERP master, so every
    row can be resolved and valued. ASN numbers are tagged ``ASN-DEMO-*`` and never
    collide with the baseline feed.
    """
    key = preset_key.upper().strip()
    cols = CANONICAL_COLUMNS
    if key == "PACKAGING_CHAOS":
        rows = [
            ("ASN-DEMO-A-01", "PO-2026-8802", "SUP-T2-203", "ENG-BLT-M12-109", 40, "BOX_100", "10/24/2026"),
            ("ASN-DEMO-A-02", "PO-2026-8802", "SUP-T2-203", "M12X15HT109", 30, "BOX_100", "10/24/2026"),
            ("ASN-DEMO-A-03", "PO-2026-8801", "SUP-T2-204", "6204ZZ", 12, "CRATE_50", "10/25/2026"),
            ("ASN-DEMO-A-04", "PO-2026-8801", "SUP-T2-204", "ENG-BRG-6204-01", 500, "EA", "10/24/2026"),
            ("ASN-DEMO-A-05", "PO-2026-8803", "SUP-T2-202", "ENGCRD42CR04", 450, "EA", "24/10/2026"),
            ("ASN-DEMO-A-06", "PO-2026-8816", "SUP-T3-301", "42CRMO4BILLET", 4.5, "MT", "24/10/2026"),
            ("ASN-DEMO-A-01", "PO-2026-8802", "SUP-T2-203", "ENG-BLT-M12-109", 40, "BOX_100", "10/24/2026"),
            ("ASN-DEMO-A-07", "PO-2026-8802", "SUP-T2-203", "ZZ-UNKNOWN-77", 10, "EA", "10/24/2026"),
        ]
    elif key == "SKU_REVISIONS":
        rows = [
            ("ASN-DEMO-B-01", "PO-2026-8810", "SUP-T2-207", "DUCHUB14", 280, "EA", "24/10/2026"),
            ("ASN-DEMO-B-02", "PO-2026-8810", "SUP-T2-207", "AXL-HUB-DUC-14-REV2", 120, "EA", "24/10/2026"),
            ("ASN-DEMO-B-03", "PO-2026-8810", "SUP-T2-207", "AXL-HUB-DUC-14", 80, "EA", "25/10/2026"),
            ("ASN-DEMO-B-04", "PO-2026-8807", "SUP-T2-205", "HSRHEL34", 10, "CRATE_50", "24/10/2026"),
            ("ASN-DEMO-B-05", "PO-2026-8807", "SUP-T2-205", "TRN-GER-HEL-34", 650, "EA", "24/10/2026"),
            ("ASN-DEMO-B-06", "PO-2026-8812", "SUP-T3-302", "FKM85SEAL", 25, "BOX_100", "10/25/2026"),
        ]
    elif key == "EV_UNITS_AND_DATES":
        rows = [
            ("ASN-DEMO-C-01", "PO-2026-8813", "SUP-T2-208", "STALAM01SIL", 2, "MT", "1761264000"),
            ("ASN-DEMO-C-02", "PO-2026-8813", "SUP-T2-208", "EVC-STA-LAM-01", 1500, "KG", "24/10/2026"),
            ("ASN-DEMO-C-03", "PO-2026-8814", "SUP-T3-303", "CUHAIRPIN04", 1.2, "MT", "24/10/2026"),
            ("ASN-DEMO-C-04", "PO-2026-8815", "SUP-T1-104", "EVC-MAG-NDF-48", 30, "BOX_100", "2026-10-25"),
        ]
    else:
        raise ValueError(f"Unknown preset: {preset_key}")
    return pd.DataFrame(rows, columns=cols)


# --------------------------------------------------------------------------- harmonization
def _legacy_visible(raw_sku: str, raw_uom: str, base_uom: str | None, catalog: set[str]) -> bool:
    """Would a legacy ETL accept this row as-is?"""
    return bool(base_uom) and raw_sku in catalog and raw_uom.strip().upper() == str(base_uom).strip().upper()


def _finalize(rows: pd.DataFrame, catalog: set[str]) -> pd.DataFrame:
    """Derive visibility, counted quantity, value and status from resolved rows."""
    expected_cols = [
        "asn_number", "po_number_ref", "supplier_id", "supplier_part_num", "resolved_part_num",
        "sku_match_method", "sku_confidence", "raw_qty", "raw_uom", "normalized_qty",
        "canonical_uom", "unit_cost_inr", "harmonized_eta_date", "transmission_seq",
        "legacy_visible_qty", "harmonized_qty", "line_value_inr", "status",
    ]
    if len(rows) == 0:
        return pd.DataFrame(columns=expected_cols)

    df = rows.copy()
    df["legacy_visible_qty"] = [
        float(q) if (seq == 1 and _legacy_visible(str(s), str(u), b, catalog)) else 0.0
        for q, seq, s, u, b in zip(df["raw_qty"], df["transmission_seq"], df["supplier_part_num"], df["raw_uom"], df["canonical_uom"])
    ]
    df["harmonized_qty"] = [
        float(nq) if (seq == 1 and conf >= CONFIDENCE_THRESHOLD and part in catalog) else 0.0
        for nq, seq, conf, part in zip(df["normalized_qty"], df["transmission_seq"], df["sku_confidence"], df["resolved_part_num"])
    ]
    df["line_value_inr"] = (df["harmonized_qty"] * df["unit_cost_inr"].fillna(0.0)).round(2)

    def status(r: pd.Series) -> str:
        if r["transmission_seq"] > 1:
            return "DUPLICATE_SUPPRESSED"
        if r["harmonized_qty"] == 0.0:
            return "NEEDS_PLANNER_REVIEW"
        if r["legacy_visible_qty"] > 0.0:
            return "CLEAN_PASSTHROUGH"
        return "HARMONIZED_BY_UDF"

    df["status"] = df.apply(status, axis=1)
    return df


def synthesize_domain_catalog(
    batch: pd.DataFrame,
    domain: str = "RETAIL_DATACO",
) -> tuple[dict[str, pd.DataFrame], dict[str, Any], dict[str, str]]:
    """Synthesizes reference enterprise master data and demand schedules for external domains.

    Standardizes raw supplier codes into canonical enterprise taxonomy:
    - RETAIL_DATACO: 'RET-CARD-{id}'
    - UNIVERSAL_AUTODISCOVER: 'CORP-SKU-{id}'

    Returns (synthesized_tables, synthesized_marts, domain_aliases).
    """
    prefix = "RET-CARD" if domain == "RETAIL_DATACO" else "CORP-SKU"
    clean_skus = [
        re.sub(r"[^A-Za-z0-9_-]", "", str(s).strip())
        for s in batch["supplier_part_num"].dropna().unique()
        if str(s).strip() and str(s).strip().lower() != "nan"
    ]
    if not clean_skus:
        clean_skus = [f"ITEM-{i+1:03d}" for i in range(10)]

    domain_aliases: dict[str, str] = {}
    items_data = []
    for raw in clean_skus:
        canonical = f"{prefix}-{raw}" if not raw.startswith(f"{prefix}-") else raw
        domain_aliases[raw] = canonical
        alnum_raw = re.sub(r"[^A-Z0-9]", "", raw.upper())
        if alnum_raw:
            domain_aliases[alnum_raw] = canonical
        items_data.append({
            "internal_part_num": canonical,
            "part_description": f"{'Retail Product' if domain == 'RETAIL_DATACO' else 'Enterprise Component'} {raw}",
            "base_uom": "EA",
            "standard_pack_size_ea": 100.0,
            "unit_weight_kg": 0.5,
            "standard_cost_inr": 1850.0,
        })
    item_master_df = pd.DataFrame(items_data)

    po_data = []
    seen_pos = set()
    for _, r in batch.iterrows():
        po_num = str(r["po_number_ref"]).strip()
        raw_sku = re.sub(r"[^A-Za-z0-9_-]", "", str(r["supplier_part_num"]).strip())
        canonical = domain_aliases.get(raw_sku, f"{prefix}-{raw_sku}")
        if (po_num, canonical) not in seen_pos and po_num and po_num.lower() != "nan":
            seen_pos.add((po_num, canonical))
            po_data.append({
                "po_number": po_num,
                "internal_part_num": canonical,
                "supplier_id": str(r["supplier_id"]),
                "ordered_qty": max(20.0, float(r["shipped_qty"]) * 1.5),
                "ordered_uom": "EA",
                "promised_delivery_date": "2026-10-30",
                "po_line_status": "OPEN",
            })
    if not po_data:
        po_data.append({
            "po_number": "PO-AUTO-001",
            "internal_part_num": items_data[0]["internal_part_num"],
            "supplier_id": "SUP-DOMAIN-01",
            "ordered_qty": 500.0,
            "ordered_uom": "EA",
            "promised_delivery_date": "2026-10-30",
            "po_line_status": "OPEN",
        })
    po_df = pd.DataFrame(po_data)

    unique_sups = [str(s).strip() for s in batch["supplier_id"].dropna().unique() if str(s).strip()]
    sup_df = pd.DataFrame([
        {"supplier_id": s, "default_date_format": "MM/DD/YYYY" if domain == "RETAIL_DATACO" else "YYYY-MM-DD"}
        for s in unique_sups
    ])

    synth_tables = {
        "ITEM_MASTER": item_master_df,
        "PURCHASE_ORDER_LINES": po_df,
        "SUPPLIER_MASTER": sup_df,
    }

    lines = (
        ["DC-NORTH-FULFILLMENT", "DC-SOUTH-FULFILLMENT", "DC-WEST-HUB"]
        if domain == "RETAIL_DATACO"
        else ["PLANT-ALPHA-LINE", "PLANT-BETA-LINE", "PLANT-GAMMA-LINE"]
    )
    bom_rows = []
    top_items = items_data[:min(25, len(items_data))]
    for i, it in enumerate(top_items):
        line = lines[i % len(lines)]
        req = 500.0
        atp = 100.0
        bom_rows.append({
            "schedule_id": f"SCHED-DOM-{i+1:02d}",
            "assembly_line_id": line,
            "parent_part_num": f"PROD-ASSY-{i+1:02d}",
            "component_part_num": it["internal_part_num"],
            "qty_per_assembly": 1.0,
            "planned_output_units": 500,
            "finished_unit_value_inr": 4800.0,
            "gross_required_qty": req,
            "true_pickable_atp_qty": atp,
            "legacy_inbound_qty": 0.0,
            "harmonized_inbound_qty": 0.0,
        })
    bom_df = pd.DataFrame(bom_rows)
    synth_marts = {"bom_risk_mart": bom_df}

    return synth_tables, synth_marts, domain_aliases


def _harmonize_python(
    batch: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    domain_aliases: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Local execution of the same logic as the three Exasol UDFs (parity path)."""
    items = tables["ITEM_MASTER"].set_index("internal_part_num")
    po_part = tables["PURCHASE_ORDER_LINES"].drop_duplicates("po_number").set_index("po_number")["internal_part_num"].to_dict()
    sup_fmt = tables["SUPPLIER_MASTER"].set_index("supplier_id")["default_date_format"].to_dict()
    catalog = set(items.index)

    seq_counter: dict[tuple, int] = {}
    out = []
    for _, r in batch.iterrows():
        sku, uom, po = str(r["supplier_part_num"]), str(r["shipped_uom"]), str(r["po_number_ref"])
        key = (r["asn_number"], po, sku, float(r["shipped_qty"]))
        seq_counter[key] = seq_counter.get(key, 0) + 1

        expected = po_part.get(po)
        if domain_aliases and sku in domain_aliases:
            resolved = domain_aliases[sku]
            method = "STANDARDIZED_DOMAIN_TAXONOMY"
            conf = 0.98
        elif domain_aliases and re.sub(r"[^A-Z0-9]", "", sku.upper()) in domain_aliases:
            resolved = domain_aliases[re.sub(r"[^A-Z0-9]", "", sku.upper())]
            method = "STANDARDIZED_DOMAIN_TAXONOMY"
            conf = 0.96
        else:
            resolved, method, conf = resolve_supplier_sku(sku, po_part_num=expected)

        item = items.loc[resolved] if resolved in items.index else None
        base_uom = None if item is None else str(item["base_uom"])
        norm_qty = (
            normalize_uom_quantity(
                float(r["shipped_qty"]), uom, base_uom,
                pack_size_ea=float(item["standard_pack_size_ea"]), unit_weight_kg=float(item["unit_weight_kg"]),
            )
            if item is not None else float(r["shipped_qty"])
        )
        eta = parse_asn_date(str(r["expected_delivery_date"]), sup_fmt.get(str(r["supplier_id"]), "YYYY-MM-DD"))
        out.append({
            "asn_number": r["asn_number"], "po_number_ref": po, "supplier_id": r["supplier_id"],
            "supplier_part_num": sku, "resolved_part_num": resolved, "sku_match_method": method,
            "sku_confidence": float(conf), "raw_qty": float(r["shipped_qty"]), "raw_uom": uom,
            "normalized_qty": float(norm_qty), "canonical_uom": base_uom,
            "unit_cost_inr": None if item is None else float(item["standard_cost_inr"]),
            "harmonized_eta_date": str(eta), "transmission_seq": seq_counter[key],
        })
    return _finalize(pd.DataFrame(out), catalog)


def _harmonize_exasol(batch: pd.DataFrame, client: Any) -> pd.DataFrame:
    """Run the three UDFs inside Exasol against a scratch staging table."""
    schema = client.schema
    stage = f"BYOD_STAGE_{uuid.uuid4().hex[:10].upper()}"
    stage_df = pd.DataFrame({
        "ROW_ID": np.arange(1, len(batch) + 1),
        "ASN_NUMBER": batch["asn_number"].astype(str).values,
        "PO_NUMBER_REF": batch["po_number_ref"].astype(str).values,
        "SUPPLIER_ID": batch["supplier_id"].astype(str).values,
        "RAW_SKU": batch["supplier_part_num"].astype(str).values,
        "RAW_QTY": batch["shipped_qty"].astype(float).values,
        "RAW_UOM": batch["shipped_uom"].astype(str).values,
        "RAW_ETA": batch["expected_delivery_date"].astype(str).values,
    })
    try:
        client.conn.execute(
            f"CREATE TABLE {schema}.{stage} (ROW_ID DECIMAL(9,0), ASN_NUMBER VARCHAR(80), PO_NUMBER_REF VARCHAR(80), "
            f"SUPPLIER_ID VARCHAR(80), RAW_SKU VARCHAR(120), RAW_QTY DOUBLE, RAW_UOM VARCHAR(40), RAW_ETA VARCHAR(60))"
        )
        client.conn.import_from_pandas(stage_df, (schema, stage))
        sql = f"""
        WITH s AS (
            SELECT st.ROW_ID, st.ASN_NUMBER, st.PO_NUMBER_REF, st.SUPPLIER_ID, st.RAW_SKU, st.RAW_QTY, st.RAW_UOM, st.RAW_ETA,
                   p.internal_part_num AS po_part_num,
                   COALESCE(sm.default_date_format, 'YYYY-MM-DD') AS date_fmt,
                   ROW_NUMBER() OVER (PARTITION BY st.ASN_NUMBER, st.PO_NUMBER_REF, st.RAW_SKU, st.RAW_QTY ORDER BY st.ROW_ID) AS transmission_seq
            FROM {schema}.{stage} st
            LEFT JOIN {schema}.PURCHASE_ORDER_LINES p ON st.PO_NUMBER_REF = p.po_number
            LEFT JOIN {schema}.SUPPLIER_MASTER sm ON st.SUPPLIER_ID = sm.supplier_id
        ),
        r AS (
            SELECT s.*, {schema}.UDF_RESOLVE_SUPPLIER_SKU(s.RAW_SKU, s.po_part_num) FROM s
        )
        SELECT r.ROW_ID, r.ASN_NUMBER, r.PO_NUMBER_REF, r.SUPPLIER_ID, r.RAW_SKU, r.RAW_QTY, r.RAW_UOM,
               r.transmission_seq, r.resolved_part_num, r.sku_match_method, r.sku_confidence,
               im.base_uom AS canonical_uom, im.standard_cost_inr AS unit_cost_inr,
               {schema}.UDF_NORMALIZE_UOM(r.RAW_QTY, r.RAW_UOM, im.base_uom, im.standard_pack_size_ea, im.unit_weight_kg) AS normalized_qty,
               {schema}.UDF_PARSE_ASN_DATE(r.RAW_ETA, r.date_fmt) AS harmonized_eta_date
        FROM r
        LEFT JOIN {schema}.ITEM_MASTER im ON r.resolved_part_num = im.internal_part_num
        ORDER BY r.ROW_ID
        """
        res = client._fetch_df(sql)
    finally:
        try:
            client.conn.execute(f"DROP TABLE IF EXISTS {schema}.{stage}")
        except Exception:
            pass

    res.columns = [c.lower() for c in res.columns]
    res = res.rename(columns={
        "asn_number": "asn_number", "po_number_ref": "po_number_ref", "supplier_id": "supplier_id",
        "raw_sku": "supplier_part_num", "raw_qty": "raw_qty", "raw_uom": "raw_uom",
    })
    res["transmission_seq"] = res["transmission_seq"].astype(int)
    res["harmonized_eta_date"] = res["harmonized_eta_date"].astype(str)
    for c in ("raw_qty", "normalized_qty", "sku_confidence", "unit_cost_inr"):
        res[c] = pd.to_numeric(res[c], errors="coerce")
    catalog = set(client.tables["ITEM_MASTER"]["internal_part_num"])
    return _finalize(res.drop(columns=["row_id"]), catalog)


def harmonize_batch(
    df: pd.DataFrame,
    client: Any,
    domain: str = "AUTOMOTIVE",
    domain_tables: dict[str, pd.DataFrame] | None = None,
    domain_aliases: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Harmonize a batch, in Exasol when a live connection exists and domain is baseline, else via domain parity logic."""
    batch, _ = detect_and_map_columns(df)
    tables = domain_tables if domain_tables is not None else getattr(client, "tables", {})
    client.ensure_data_loaded()
    info: dict[str, Any] = {"engine": "PYTHON_UDF_PARITY", "fallback_reason": None}
    catalog = set(tables["ITEM_MASTER"]["internal_part_num"]) if "ITEM_MASTER" in tables else set()
    if len(batch) == 0:
        return _finalize(pd.DataFrame(), catalog), info

    if domain == "AUTOMOTIVE" and getattr(client, "conn", None) is not None:
        try:
            return _harmonize_exasol(batch, client), {**info, "engine": "EXASOL_UDF"}
        except Exception as exc:  # report, never hide
            info["fallback_reason"] = f"Exasol execution failed ({type(exc).__name__}: {exc}); used local parity logic."
    elif domain != "AUTOMOTIVE":
        info["fallback_reason"] = f"Domain '{domain}': Executed in-memory with synthesized enterprise catalog & canonical taxonomy."
    else:
        info["fallback_reason"] = "No live Exasol connection; used local parity logic (same UDF source)."
    return _harmonize_python(batch, tables, domain_aliases=domain_aliases), info


# --------------------------------------------------------------------------- impact
def _exposure(bom: pd.DataFrame, add_legacy: dict[str, float], add_harm: dict[str, float]) -> pd.DataFrame:
    """Re-evaluate the VW_BOM_LINE_STARVATION_RISK formulas with extra inbound per component."""
    b = bom.copy()
    comp = b["component_part_num"]
    atp = pd.to_numeric(b["true_pickable_atp_qty"], errors="coerce").fillna(0.0)
    legacy_total = atp + pd.to_numeric(b["legacy_inbound_qty"], errors="coerce").fillna(0.0) + comp.map(add_legacy).fillna(0.0)
    net_total = atp + pd.to_numeric(b["harmonized_inbound_qty"], errors="coerce").fillna(0.0) + comp.map(add_harm).fillna(0.0)
    gross = pd.to_numeric(b["gross_required_qty"], errors="coerce").fillna(0.0)
    per = pd.to_numeric(b["qty_per_assembly"], errors="coerce").replace(0, np.nan)
    planned = pd.to_numeric(b["planned_output_units"], errors="coerce").fillna(0.0)
    value = pd.to_numeric(b["finished_unit_value_inr"], errors="coerce").fillna(0.0)

    def risk(total: pd.Series) -> tuple[pd.Series, pd.Series]:
        deficit = (gross - total).clip(lower=0.0).round(2)
        units = np.minimum(planned, np.ceil(deficit / per).fillna(0.0))
        return deficit, (units * value).round(2)

    b["legacy_deficit_qty_b"], b["legacy_risk_inr"] = risk(legacy_total)
    b["net_deficit_qty_b"], b["net_risk_inr"] = risk(net_total)
    return b


def evaluate_batch_impact(harmonized: pd.DataFrame, marts: dict[str, Any]) -> dict[str, Any]:
    """Layer the harmonized batch on the baseline and return before/after exposure."""
    bom = marts["bom_risk_mart"]
    base = _exposure(bom, {}, {})
    add_legacy = harmonized.groupby("resolved_part_num")["legacy_visible_qty"].sum().to_dict()
    add_harm = harmonized.groupby("resolved_part_num")["harmonized_qty"].sum().to_dict()
    after = _exposure(bom, add_legacy, add_harm)

    baseline_legacy = float(base["legacy_risk_inr"].sum())
    baseline_net = float(base["net_risk_inr"].sum())
    legacy_after = float(after["legacy_risk_inr"].sum())
    net_after = float(after["net_risk_inr"].sum())
    threatened = sorted(after.loc[after["net_risk_inr"] > 0, "assembly_line_id"].unique().tolist())

    legacy_val = float((harmonized["legacy_visible_qty"] * harmonized["unit_cost_inr"].fillna(0.0)).sum())
    harm_val = float(harmonized["line_value_inr"].sum())

    shortage = after.loc[after["net_risk_inr"] > 0, [
        "schedule_id", "assembly_line_id", "component_part_num", "gross_required_qty",
        "true_pickable_atp_qty", "net_deficit_qty_b", "net_risk_inr",
    ]].rename(columns={"net_deficit_qty_b": "net_deficit_qty"})

    status_counts = harmonized["status"].value_counts().to_dict()
    summary = {
        "batch_lines": int(len(harmonized)),
        "status_counts": status_counts,
        "baseline_legacy_risk_inr": baseline_legacy,
        "baseline_net_risk_inr": baseline_net,
        "legacy_risk_with_batch_inr": legacy_after,
        "net_risk_with_batch_inr": net_after,
        "false_alarm_cleared_inr": max(0.0, legacy_after - net_after),
        "net_risk_change_vs_baseline_inr": net_after - baseline_net,
        "batch_value_legacy_visible_inr": legacy_val,
        "batch_value_harmonized_inr": harm_val,
        "batch_value_recovered_inr": max(0.0, harm_val - legacy_val),
        "threatened_lines": threatened,
        "avg_confidence": round(float(harmonized["sku_confidence"].mean()), 3) if len(harmonized) else 0.0,
    }
    return {"summary": summary, "shortage_df": shortage.reset_index(drop=True), "harmonized_df": harmonized}


def harmonize_and_evaluate_inbound(
    df: pd.DataFrame,
    client: Any,
    marts: dict[str, Any] | None = None,
    domain: str = "AUTOMOTIVE",
) -> dict[str, Any]:
    """Harmonize an inbound batch and evaluate its impact on baseline or domain exposure."""
    onboarding_meta = None
    if domain != "AUTOMOTIVE":
        synth_tables, synth_marts, domain_aliases = synthesize_domain_catalog(df, domain)
        harmonized, info = harmonize_batch(
            df, client, domain=domain, domain_tables=synth_tables, domain_aliases=domain_aliases
        )
        result = evaluate_batch_impact(harmonized, synth_marts)
        onboarding_meta = {
            "domain": domain,
            "domain_label": DOMAIN_PROFILES.get(domain, domain),
            "products_onboarded": len(synth_tables["ITEM_MASTER"]),
            "pos_synthesized": len(synth_tables["PURCHASE_ORDER_LINES"]),
            "lines_monitored": len(synth_marts["bom_risk_mart"]["assembly_line_id"].unique()),
            "canonical_taxonomy": "RET-CARD-XXXX" if domain == "RETAIL_DATACO" else "CORP-SKU-XXXX",
        }
    else:
        harmonized, info = harmonize_batch(df, client, domain="AUTOMOTIVE")
        marts = marts if marts is not None else client.compute_analytical_marts()
        result = evaluate_batch_impact(harmonized, marts)

    result["engine"] = info
    result["onboarding_meta"] = onboarding_meta
    return result


# --------------------------------------------------------------------------- exports
def generate_sap_migo_export(harmonized_df: pd.DataFrame) -> str:
    """CSV with SAP-style goods-receipt field names (illustrative mapping, not a certified SAP layout)."""
    counted = harmonized_df[harmonized_df["harmonized_qty"] > 0]
    sap_df = pd.DataFrame({
        "EBELN": counted["po_number_ref"],
        "BOLNR": counted["asn_number"],
        "MATNR": counted["resolved_part_num"],
        "MENGE": counted["harmonized_qty"],
        "MEINS": counted["canonical_uom"],
        "BUDAT": counted["harmonized_eta_date"],
        "LIFNR": counted["supplier_id"],
        "BKTXT": "MANGROVE_HARMONIZED",
    })
    return sap_df.to_csv(index=False)


def generate_expedite_manifest(summary: dict[str, Any], shortage_df: pd.DataFrame) -> str:
    """Plain-text expedite note listing components that remain short after harmonization."""
    lines = [
        "# MANGROVE: EXPEDITE REVIEW NOTE",
        f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Lines still at risk after harmonization**: {', '.join(summary.get('threatened_lines', [])) or 'NONE'}",
        f"**Net revenue at risk (with this batch)**: INR {summary.get('net_risk_with_batch_inr', 0.0):,.2f}",
        "",
        "| Schedule | Line | Component | Gross req | True ATP | Net deficit | Revenue at risk (INR) |",
        "| :--- | :--- | :--- | ---: | ---: | ---: | ---: |",
    ]
    if shortage_df is None or len(shortage_df) == 0:
        lines.append("| - | - | none | - | - | - | 0.00 |")
    else:
        for _, row in shortage_df.iterrows():
            lines.append(
                f"| {row['schedule_id']} | {row['assembly_line_id']} | {row['component_part_num']} | "
                f"{row['gross_required_qty']:,.0f} | {row['true_pickable_atp_qty']:,.0f} | "
                f"{row['net_deficit_qty']:,.0f} | {row['net_risk_inr']:,.2f} |"
            )
    lines += ["", "Rows with status NEEDS_PLANNER_REVIEW were NOT counted as inbound stock."]
    return "\n".join(lines)
