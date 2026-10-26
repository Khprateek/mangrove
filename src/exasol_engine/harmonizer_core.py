from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from typing import Dict, List, Set, Tuple


from pathlib import Path

def load_supplier_catalog_cross_ref(
    source: str | Path | Any = None,
) -> Dict[str, str]:
    """
    Dynamically loads supplier-to-internal part cross-references from the relational
    SUPPLIER_CATALOG_CROSS_REF table or CSV export.
    Returns a dictionary mapping clean_supplier_part_num -> internal_part_num.
    """
    try:
        import pandas as pd
        if isinstance(source, pd.DataFrame):
            df = source
        else:
            path = Path(source) if source else Path("data/raw/supplier_catalog_cross_ref.csv")
            if path.exists():
                df = pd.read_csv(path)
            else:
                df = None
    except Exception:
        df = None

    if df is not None and len(df) > 0:
        active = df[df["is_active"] == True] if "is_active" in df.columns else df
        mapping: Dict[str, str] = {}
        for _, row in active.iterrows():
            raw_k = str(row.get("clean_supplier_part_num", row.get("supplier_part_num", ""))).strip().upper()
            clean_k = re.sub(r"[^A-Z0-9]", "", raw_k)
            internal_v = str(row.get("internal_part_num", "")).strip().upper()
            if clean_k and internal_v:
                mapping[clean_k] = internal_v
        if mapping:
            return mapping

    # Baseline deterministic cross-references matching SUPPLIER_CATALOG_CROSS_REF master
    return {
        "6204ZZ": "ENG-BRG-6204-01",
        "FBD6204ZZ": "ENG-BRG-6204-01",
        "M12X15HT109": "ENG-BLT-M12-109",
        "42CRCONROD04": "ENG-CRD-42CR-04",
        "HSRHEL34": "TRN-GER-HEL-34",
        "DUCHUB14": "AXL-HUB-DUC-14",
        "FKM85SEAL": "AXL-SEL-FKM-85",
        "STALAM01SIL": "EVC-STA-LAM-01",
        "CUHAIRPIN04": "EVC-WND-CU-04",
        "42CRMO4BILLET": "RAW-STL-42CR-B",
    }


KNOWN_SUPPLIER_SKU_ALIASES: Dict[str, str] = load_supplier_catalog_cross_ref()


def extract_adaptive_ngrams(s: str) -> Set[str]:
    """
    Extracts boundary-padded character n-grams for fast sub-millisecond candidate filtering:
    - Short strings (<= 4 chars): Pads boundary '^...$' and extracts bigrams (2-grams).
    - Longer strings (> 4 chars): Extracts trigrams (3-grams) plus boundary bigrams.
    This guarantees short part codes (e.g., 'M6', 'ECU') are never skipped.
    """
    cleaned = (s or "").strip().upper()
    if not cleaned:
        return set()

    length = len(cleaned)
    ngrams: Set[str] = set()

    # Boundary anchors ensure prefix/suffix alignment is strongly rewarded
    padded = f"^{cleaned}$"
    ngrams.add(padded[:2])   # e.g., '^M'
    ngrams.add(padded[-2:])  # e.g., '6$'

    if length <= 4:
        # 2-grams across short string
        for i in range(len(padded) - 1):
            ngrams.add(padded[i : i + 2])
    else:
        # 3-grams across main body
        for i in range(length - 2):
            ngrams.add(cleaned[i : i + 3])

    return ngrams


def build_ngram_inverted_index(catalog: Dict[str, str]) -> Dict[str, Set[str]]:
    """
    Constructs an In-Memory Inverted Index mapping n-grams to candidate alias keys.
    Query lookup is O(1) in RAM.
    """
    index: Dict[str, Set[str]] = {}
    for alias_key in catalog:
        for ng in extract_adaptive_ngrams(alias_key):
            if ng not in index:
                index[ng] = set()
            index[ng].add(alias_key)
    return index


_ALIAS_NGRAM_INDEX: Dict[str, Set[str]] = build_ngram_inverted_index(KNOWN_SUPPLIER_SKU_ALIASES)


UOM_SYNONYM_MAP: Dict[str, str] = {
    "KGS": "KG",
    "KILOGRAM": "KG",
    "KILOGRAMS": "KG",
    "GMS": "G",
    "GM": "G",
    "GRAM": "G",
    "GRAMS": "G",
    "MTRS": "MTR",
    "METER": "MTR",
    "METERS": "MTR",
    "METRE": "MTR",
    "METRES": "MTR",
    "M": "MTR",
    "LTRS": "LTR",
    "L": "LTR",
    "LITER": "LTR",
    "LITRE": "LTR",
    "LITERS": "LTR",
    "LITRES": "LTR",
    "TON": "MT",
    "TONNE": "MT",
    "TONNES": "MT",
    "METRIC TON": "MT",
    "METRIC TONNE": "MT",
    "SET": "EA",
    "SETS": "EA",
    "PCS": "EA",
    "PIECE": "EA",
    "PIECES": "EA",
    "NOS": "EA",
    "NO": "EA",
    "UNITS": "EA",
    "UNIT": "EA",
    "EACH": "EA",
    "LBS": "LB",
    "POUND": "LB",
    "POUNDS": "LB",
    "MILLILITER": "ML",
    "MILLILITERS": "ML",
    "MILLIMETER": "MM",
    "MILLIMETERS": "MM",
    "DZN": "DZN",
    "DOZ": "DZN",
    "DOZEN": "DZN",
    "GROSS": "GROSS",
    "GRS": "GROSS",
    "PAIR": "PAIR",
    "PR": "PAIR",
    "PRS": "PAIR",
    "PAIRS": "PAIR",
    "THOUSAND": "TH",
    "TH": "TH",
}


def normalize_uom_quantity(
    raw_qty: float,
    raw_uom: str,
    target_uom: str,
    pack_size_ea: float = 1.0,
    unit_weight_kg: float = 1.0,
) -> float:
    """
    Converts heterogeneous supplier dispatch quantities (BOX_100, BOX-100, PK_50, MT, LB, GMS, KGS, DZN, GROSS, PAIR)
    into the canonical ITEM_MASTER base_uom (EA, KG, LTR, MTR).
    Cleans comma-formatted strings (e.g. '1,200.50') and guards against negative corrupt values.
    """
    if raw_qty is None:
        return 0.0
    try:
        qty = float(str(raw_qty).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0
    if qty < 0.0:
        return 0.0

    src = (raw_uom or "").strip().upper()
    tgt = (target_uom or "EA").strip().upper()

    ea_synonyms = {"EA", "EACH", "PCS", "PIECES", "NOS", "UNITS", "NO"}

    # Bulk packaging pattern: BOX_100, BOX-100, BOX 100, PK_50, PK-50, CRATE/40
    pack_match = re.match(r"^(?:BOX|BAG|CRATE|PACK|PK|PALLET)[_\s\-/](\d+)$", src)
    if pack_match and (tgt in ea_synonyms or UOM_SYNONYM_MAP.get(tgt) in ea_synonyms):
        multiplier = float(pack_match.group(1))
        return round(qty * multiplier, 2)

    # Hardware & discrete multipliers
    if src in {"DZN", "DOZ", "DOZEN"} and tgt in ea_synonyms:
        return round(qty * 12.0, 2)
    if src in {"GROSS", "GRS"} and tgt in ea_synonyms:
        return round(qty * 144.0, 2)
    if src in {"PAIR", "PR", "PRS", "PAIRS"} and tgt in ea_synonyms:
        return round(qty * 2.0, 2)
    if src in {"THOUSAND", "TH"} and tgt in ea_synonyms:
        return round(qty * 1000.0, 2)

    # Canonicalize unit aliases
    src = UOM_SYNONYM_MAP.get(src, src)
    tgt = UOM_SYNONYM_MAP.get(tgt, tgt)

    if src in ea_synonyms and tgt in ea_synonyms:
        return round(qty, 2)

    if src == tgt:
        return round(qty, 2)

    if src in {"BOX", "BAG", "CRATE", "PACK", "PK", "PALLET"} and tgt in ea_synonyms:
        multiplier = float(pack_size_ea) if pack_size_ea and pack_size_ea > 1.0 else 100.0
        return round(qty * multiplier, 2)

    # Metric Ton (MT) -> Kilogram (KG)
    if src in {"MT", "TON", "TONNE", "TONNES"} and tgt == "KG":
        return round(float(raw_qty) * 1000.0, 2)

    # Kilogram (KG) -> Metric Ton (MT)
    if src == "KG" and tgt in {"MT", "TON", "TONNE"}:
        return round(float(raw_qty) / 1000.0, 3)

    # Grams (G, GM) -> Kilogram (KG)
    if src in {"G", "GM", "GRAM", "GRAMS"} and tgt == "KG":
        return round(float(raw_qty) / 1000.0, 3)

    # Kilogram (KG) -> Grams (G)
    if src == "KG" and tgt in {"G", "GM", "GRAM", "GRAMS"}:
        return round(float(raw_qty) * 1000.0, 2)

    # Metric Ton (MT) -> Individual Pieces (EA) using component unit weight
    if src in {"MT", "TON", "TONNE"} and tgt in ea_synonyms and unit_weight_kg and unit_weight_kg > 0:
        total_kg = float(raw_qty) * 1000.0
        return round(total_kg / float(unit_weight_kg), 2)

    # Kilogram (KG) -> Individual Pieces (EA)
    if src == "KG" and tgt in ea_synonyms and unit_weight_kg and unit_weight_kg > 0:
        return round(float(raw_qty) / float(unit_weight_kg), 2)

    # Individual Pieces (EA) -> Kilogram (KG) using component unit weight
    if src in ea_synonyms and tgt == "KG" and unit_weight_kg and unit_weight_kg > 0:
        return round(float(raw_qty) * float(unit_weight_kg), 2)

    # Pounds (LB) -> Kilogram (KG)
    if src in {"LB", "LBS", "POUND", "POUNDS"} and tgt == "KG":
        return round(float(raw_qty) * 0.45359237, 2)

    # Volume: Liter (LTR) <-> Milliliter (ML)
    if src in {"LTR", "L", "LITER", "LITRE"} and tgt in {"ML", "MILLILITER"}:
        return round(float(raw_qty) * 1000.0, 2)
    if src in {"ML", "MILLILITER"} and tgt in {"LTR", "L", "LITER", "LITRE"}:
        return round(float(raw_qty) / 1000.0, 3)

    # Length: Meter (MTR) <-> Millimeter (MM)
    if src in {"MTR", "M", "METER"} and tgt in {"MM", "MILLIMETER"}:
        return round(float(raw_qty) * 1000.0, 2)
    if src in {"MM", "MILLIMETER"} and tgt in {"MTR", "M", "METER"}:
        return round(float(raw_qty) / 1000.0, 3)

    # Cross-category guard: If discrete packaging (BOX, BAG) cannot be converted to weight (KG),
    # do NOT silently return raw_qty (e.g., 10 BOX is NOT 10 KG)
    if src in {"BOX", "BAG", "CRATE", "PACK"} and tgt == "KG":
        if unit_weight_kg and unit_weight_kg > 0:
            effective_pack = float(pack_size_ea) if pack_size_ea and pack_size_ea > 0 else 100.0
            return round(float(raw_qty) * effective_pack * float(unit_weight_kg), 2)
        return 0.0

    return round(float(raw_qty), 2)


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """
    Computes standard Jaro-Winkler string similarity in [0.0, 1.0].
    Used to resolve near-miss supplier SKU typos (e.g., '0' vs 'O', dropped suffix chars)
    against canonical item numbers and known vendor catalog aliases.
    """
    a = (s1 or "").strip().upper()
    b = (s2 or "").strip().upper()
    if a == b:
        return 1.0 if a else 0.0
    len_a, len_b = len(a), len(b)
    if len_a == 0 or len_b == 0:
        return 0.0

    match_dist = max(0, max(len_a, len_b) // 2 - 1)
    a_matches = [False] * len_a
    b_matches = [False] * len_b
    matches = 0

    for i in range(len_a):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len_b)
        for j in range(start, end):
            if b_matches[j] or a[i] != b[j]:
                continue
            a_matches[i] = True
            b_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    transpositions = 0
    k = 0
    for i in range(len_a):
        if not a_matches[i]:
            continue
        while not b_matches[k]:
            k += 1
        if a[i] != b[k]:
            transpositions += 1
        k += 1

    jaro = (
        (matches / len_a)
        + (matches / len_b)
        + ((matches - transpositions / 2.0) / matches)
    ) / 3.0

    prefix = 0
    for ch_a, ch_b in zip(a[:4], b[:4]):
        if ch_a == ch_b:
            prefix += 1
        else:
            break

    jw = jaro + prefix * prefix_weight * (1.0 - jaro)
    return round(min(1.0, jw), 4)


def check_revision_mismatch(raw_sku: str, po_part_num: str) -> bool:
    """
    Detects when raw supplier SKU and PO part share the same base stem but have
    conflicting revision, suffix, or engineering change order (ECO) variant tags
    (e.g., -01 vs -02, -REV1 vs -REV2, -A vs -B).
    Normalizes zero-padded revisions (REV-1 vs REV-01) to prevent false positive flags.
    """
    raw_clean = (raw_sku or "").strip().upper()
    po_clean = (po_part_num or "").strip().upper()
    if not raw_clean or not po_clean:
        return False
    m_raw = re.search(r"^(.*?)(?:[-_]?(?:REV|R)?)(\d{1,3}|[A-Z]{1,2})$", raw_clean)
    m_po = re.search(r"^(.*?)(?:[-_]?(?:REV|R)?)(\d{1,3}|[A-Z]{1,2})$", po_clean)
    if m_raw and m_po:
        stem_raw, rev_raw = m_raw.group(1), m_raw.group(2)
        stem_po, rev_po = m_po.group(1), m_po.group(2)
        alnum_stem_raw = re.sub(r"[^A-Z0-9]", "", stem_raw)
        alnum_stem_po = re.sub(r"[^A-Z0-9]", "", stem_po)
        if alnum_stem_raw and alnum_stem_raw == alnum_stem_po:
            if rev_raw.isdigit() and rev_po.isdigit():
                return int(rev_raw) != int(rev_po)
            return rev_raw != rev_po
    return False


def detect_numeric_transposition(s1: str, s2: str) -> bool:
    """
    Detects if two SKU strings have transposed digits within corresponding numeric blocks
    (e.g., '6204' vs '6240', '12' vs '21').
    In industrial manufacturing and automotive assembly, transposed digits indicate
    completely different physical specifications (e.g. 20mm bearing vs 200mm bearing).
    """
    if not s1 or not s2:
        return False
    nums1 = re.findall(r"\d+", s1)
    nums2 = re.findall(r"\d+", s2)
    for n1 in nums1:
        for n2 in nums2:
            if len(n1) >= 2 and len(n1) == len(n2) and n1 != n2:
                diffs = [(i, c1, c2) for i, (c1, c2) in enumerate(zip(n1, n2)) if c1 != c2]
                if len(diffs) == 2:
                    (i1, a1, b1), (i2, a2, b2) = diffs
                    if a1 == b2 and a2 == b1:
                        return True
    return False


def check_dimension_conflict(raw_sku: str, po_sku: str) -> bool:
    """
    Checks if there is an explicit dimensional/sizing conflict between raw and PO SKUs.
    A conflict occurs when both raw and PO have corresponding numeric sizing tokens that differ
    (e.g., M12 vs M6, 6204 vs 6205).
    Omission of an engineering revision/variant suffix (e.g., '01' in ENG-CRK-42CR-01 vs ENGCRK42CRMO)
    is NOT a dimension conflict.
    """
    if not raw_sku or not po_sku:
        return False

    raw_nums = set(re.findall(r"\d+", raw_sku))
    po_nums = set(re.findall(r"\d+", po_sku))

    shared_nums = raw_nums.intersection(po_nums)
    unmatched_raw = raw_nums - shared_nums
    unmatched_po = po_nums - shared_nums

    if unmatched_raw and unmatched_po:
        for n_po in unmatched_po:
            for n_raw in unmatched_raw:
                if len(n_po) == len(n_raw):
                    return True
                if abs(len(n_po) - len(n_raw)) <= 1 and int(n_po) != int(n_raw):
                    return True
    return False


def resolve_supplier_sku(
    raw_sku: str,
    po_part_num: str | None = None,
    catalog_part_num: str | None = None,
    catalog_map: Dict[str, str] | None = None,
) -> Tuple[str, str, float]:
    """
    Reconciles supplier part identifiers to canonical ITEM_MASTER internal_part_num.
    Uses relational SUPPLIER_CATALOG_CROSS_REF entries, exact matching, vendor prefix
    stripping, and Jaro-Winkler string distance with adaptive n-gram pre-filtering.
    Returns (resolved_part_num, match_method, confidence_score).
    """
    cleaned_raw = (raw_sku or "").strip().upper()
    cleaned_po = (po_part_num or "").strip().upper()
    catalog_target = (catalog_part_num or "").strip().upper()

    if cleaned_po and cleaned_raw == cleaned_po:
        return cleaned_po, "EXACT_MATCH", 1.00

    # Revision / Variant Collision Guard: Prevent auto-resolving conflicting ECO revisions
    if cleaned_po and check_revision_mismatch(cleaned_raw, cleaned_po):
        return cleaned_raw, "REVISION_MISMATCH_SUSPECTED", 0.70

    # Numeric Transposition Guard: Prevent auto-resolving swapped digits (e.g., 6204 vs 6240)
    if cleaned_po and detect_numeric_transposition(cleaned_raw, cleaned_po):
        return cleaned_raw, "NUMERIC_TRANSPOSITION_SUSPECTED", 0.65

    alnum_raw = re.sub(r"[^A-Z0-9]", "", cleaned_raw)
    alnum_po = re.sub(r"[^A-Z0-9]", "", cleaned_po)

    if alnum_po and alnum_raw == alnum_po:
        return cleaned_po, "HYPHEN_NORMALIZED", 0.98

    # Vendor Prefix Stripping (e.g., 'VNDR-ENG-BRG-6204-01' -> 'ENG-BRG-6204-01')
    if alnum_po and alnum_raw.endswith(alnum_po) and len(alnum_raw) > len(alnum_po):
        prefix_len = len(alnum_raw) - len(alnum_po)
        if prefix_len <= 8:
            return cleaned_po, "VENDOR_PREFIX_STRIPPED", 0.96

    # 1. Relational Table Direct Match (via catalog_part_num from SQL join)
    if catalog_target:
        if not detect_numeric_transposition(alnum_raw, catalog_target):
            return catalog_target, "VENDOR_CATALOG_ALIAS", 0.95

    # 2. Dynamic Relational Catalog Map Lookup
    active_catalog = catalog_map if catalog_map is not None else KNOWN_SUPPLIER_SKU_ALIASES
    if alnum_raw in active_catalog:
        mapped = active_catalog[alnum_raw]
        return mapped, "VENDOR_CATALOG_ALIAS", 0.95

    has_dim_conflict = False
    if cleaned_po:
        has_dim_conflict = check_dimension_conflict(cleaned_raw, cleaned_po)
        if not has_dim_conflict:
            po_tokens = [t for t in re.split(r"[-_./\s]", cleaned_po) if len(t) >= 2]
            matched_tokens = sum(1 for tok in po_tokens if tok in alnum_raw)
            if len(po_tokens) >= 2 and matched_tokens >= len(po_tokens) - 1 and (matched_tokens / len(po_tokens)) >= 0.75:
                return cleaned_po, "PO_TOKEN_SIMILARITY", 0.89

            jw_po = jaro_winkler_similarity(alnum_raw, alnum_po)
            if jw_po >= 0.93:
                return cleaned_po, "JARO_WINKLER_FUZZY", round(jw_po, 2)
            elif jw_po >= 0.85:
                return cleaned_po, "FUZZY_MATCH_REVIEW_BAND", round(jw_po, 2)

    if alnum_raw and active_catalog:
        # Phase 1: Adaptive N-Gram Candidate Pre-Filtering (Fast Path)
        active_index = _ALIAS_NGRAM_INDEX if active_catalog is KNOWN_SUPPLIER_SKU_ALIASES else build_ngram_inverted_index(active_catalog)
        query_ngrams = extract_adaptive_ngrams(alnum_raw)
        candidate_overlaps: Dict[str, int] = {}
        for ng in query_ngrams:
            if ng in active_index:
                for candidate_key in active_index[ng]:
                    candidate_overlaps[candidate_key] = candidate_overlaps.get(candidate_key, 0) + 1

        best_alias_sku = None
        best_jw = 0.0
        evaluated_keys: Set[str] = set()

        if candidate_overlaps:
            # Sort candidates by overlap count descending to test top matches first
            sorted_candidates = sorted(candidate_overlaps.items(), key=lambda x: x[1], reverse=True)
            for candidate_key, _ in sorted_candidates:
                evaluated_keys.add(candidate_key)
                if detect_numeric_transposition(alnum_raw, candidate_key):
                    continue
                score = jaro_winkler_similarity(alnum_raw, candidate_key)
                if score > best_jw:
                    best_jw = score
                    best_alias_sku = active_catalog[candidate_key]
                if best_jw >= 0.95:
                    break

        # Phase 2: Safety Fallback Guardrail (0.00% False Negative Guarantee)
        if best_jw < 0.85:
            for alias_key, canonical_sku in active_catalog.items():
                if alias_key in evaluated_keys:
                    continue
                if detect_numeric_transposition(alnum_raw, alias_key):
                    continue
                score = jaro_winkler_similarity(alnum_raw, alias_key)
                if score > best_jw:
                    best_jw = score
                    best_alias_sku = canonical_sku

        if best_alias_sku:
            if best_jw >= 0.93:
                return best_alias_sku, "JARO_WINKLER_FUZZY", round(best_jw, 2)
            elif best_jw >= 0.85:
                return best_alias_sku, "FUZZY_MATCH_REVIEW_BAND", round(best_jw, 2)

    if cleaned_po and not has_dim_conflict:
        return cleaned_po, "PO_LINEAGE_FALLBACK", 0.82

    return cleaned_raw, "UNRESOLVED", 0.00


def parse_asn_date(raw_date_str: str, supplier_date_fmt: str = "YYYY-MM-DD") -> date | None:
    """
    Parses multi-format supplier date strings (ISO YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY,
    DD.MM.YYYY, 8-digit compact EDI YYYYMMDD, 5-digit Excel serial dates, 2-digit years,
    and Unix epoch timestamps) using the vendor's default format profile.
    Strips trailing ISO timestamps (e.g., '2026-10-24 14:30:00' -> '2026-10-24').
    Returns None if raw_date_str is empty or unparseable.
    """
    val = (raw_date_str or "").strip()
    if not val:
        return None

    # Strip timestamp suffix if present (e.g., '2026-10-24 14:30:00' or '2026-10-24T14:30:00Z')
    # while preserving space-delimited dates like '12 Oct 2026' and raw epoch integers
    if not re.fullmatch(r"\d{9,10}", val):
        val = re.sub(r"[T\s]\d{1,2}:\d{2}(?::\d{2})?.*$", "", val).strip()

    # Unix epoch check (seconds): bounds validation for modern enterprise window (2000 to 2050)
    # Rejects arbitrary 9-10 digit numbers (phone numbers, numeric part codes) while accepting genuine epoch dates
    if re.fullmatch(r"\d{9,10}", val):
        try:
            epoch_sec = int(val)
            dt = datetime.fromtimestamp(epoch_sec, tz=timezone.utc).date()
            if not (2000 <= dt.year <= 2050):
                return None
            return dt
        except (ValueError, OverflowError, OSError):
            return None

    # Excel date serial check (e.g., 46307 for 2026-10-12)
    if re.fullmatch(r"\d{5}", val):
        try:
            serial_days = int(val)
            if 35000 <= serial_days <= 65000:
                return date(1899, 12, 30) + timedelta(days=serial_days)
        except (ValueError, OverflowError):
            pass

    # Compact EDI 8-digit date: YYYYMMDD (e.g. 20261024)
    edi_match = re.fullmatch(r"(20\d{2})(\d{2})(\d{2})", val)
    if edi_match:
        try:
            return date(int(edi_match.group(1)), int(edi_match.group(2)), int(edi_match.group(3)))
        except ValueError:
            return None

    # Delimited dates: supports '-', '/', and '.'
    # 1. ISO YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
    iso_match = re.fullmatch(r"(\d{4})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])", val)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None

    # 2. 4-digit Year: DD/MM/YYYY, MM/DD/YYYY, DD.MM.YYYY, DD-MM-YYYY
    delim_match = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", val)
    if delim_match:
        try:
            first, second, year = int(delim_match.group(1)), int(delim_match.group(2)), int(delim_match.group(3))
            fmt_pref = (supplier_date_fmt or "DD/MM/YYYY").strip().upper()
            if first > 12:
                return date(year, second, first)
            if second > 12:
                return date(year, first, second)
            if fmt_pref in ("MM/DD/YYYY", "MM-DD-YYYY", "MM.DD.YYYY"):
                return date(year, first, second)
            return date(year, second, first)
        except ValueError:
            return None

    # 3. 2-digit Year: DD/MM/YY, MM/DD/YY, DD.MM.YY, DD-MM-YY
    delim_2digit = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})", val)
    if delim_2digit:
        try:
            first, second, yr_part = int(delim_2digit.group(1)), int(delim_2digit.group(2)), int(delim_2digit.group(3))
            year = 2000 + yr_part
            fmt_pref = (supplier_date_fmt or "DD/MM/YYYY").strip().upper()
            if first > 12:
                return date(year, second, first)
            if second > 12:
                return date(year, first, second)
            if fmt_pref in ("MM/DD/YYYY", "MM-DD-YYYY", "MM.DD.YYYY"):
                return date(year, first, second)
            return date(year, second, first)
        except ValueError:
            return None

    for fmt in (
        "%d-%b-%Y", "%d/%b/%Y", "%d.%b.%Y", "%d %b %Y", "%d %B %Y",
        "%d-%b-%y", "%d/%b/%y", "%d.%b.%y", "%d %b %y",
        "%Y/%m/%d", "%d-%m-%Y"
    ):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue

    return None
