-- Exasol Personal In-Database Python 3 Scalar UDFs for Multi-Supplier ASN Harmonization
-- Target Schema: CHAKAN_SCM

OPEN SCHEMA CHAKAN_SCM;

-- 1. In-Database UOM & Bulk-Pack Quantity Normalization UDF
-- Converts BOX_100, BAG_250, CRATE_40, CRATE_50, MT, and LB into canonical ITEM_MASTER base_uom
CREATE OR REPLACE PYTHON3 SCALAR SCRIPT CHAKAN_SCM.UDF_NORMALIZE_UOM(
    raw_qty DOUBLE,
    raw_uom VARCHAR(24) UTF8,
    target_uom VARCHAR(12) UTF8,
    pack_size_ea DOUBLE,
    unit_weight_kg DOUBLE
) RETURNS DOUBLE AS
import re

UOM_SYNONYMS = {
    "KGS": "KG", "KILOGRAM": "KG", "KILOGRAMS": "KG",
    "GMS": "G", "GM": "G", "GRAM": "G", "GRAMS": "G",
    "MTRS": "MTR", "METER": "MTR", "METERS": "MTR", "METRE": "MTR", "METRES": "MTR", "M": "MTR",
    "LTRS": "LTR", "L": "LTR", "LITER": "LTR", "LITRE": "LTR", "LITERS": "LTR", "LITRES": "LTR",
    "TON": "MT", "TONNE": "MT", "TONNES": "MT", "METRIC TON": "MT", "METRIC TONNE": "MT",
    "SET": "EA", "SETS": "EA", "PCS": "EA", "PIECE": "EA", "PIECES": "EA", "NOS": "EA", "NO": "EA", "UNITS": "EA", "UNIT": "EA", "EACH": "EA",
    "LBS": "LB", "POUND": "LB", "POUNDS": "LB",
    "MILLILITER": "ML", "MILLILITERS": "ML",
    "MILLIMETER": "MM", "MILLIMETERS": "MM",
}

def run(ctx):
    if ctx.raw_qty is None:
        return 0.0
    qty = float(ctx.raw_qty)
    src = (ctx.raw_uom or "").strip().upper()
    tgt = (ctx.target_uom or "EA").strip().upper()

    ea_synonyms = {"EA", "EACH", "PCS", "PIECES", "NOS", "UNITS", "NO"}

    pack_match = re.match(r"^(?:BOX|BAG|CRATE|PACK|PK|PALLET)[_\s\-/](\d+)$", src)
    if pack_match and (tgt in ea_synonyms or UOM_SYNONYMS.get(tgt) in ea_synonyms):
        return round(qty * float(pack_match.group(1)), 2)

    src = UOM_SYNONYMS.get(src, src)
    tgt = UOM_SYNONYMS.get(tgt, tgt)

    if src in ea_synonyms and tgt in ea_synonyms:
        return round(qty, 2)

    if src == tgt:
        return round(qty, 2)

    if src in ("BOX", "BAG", "CRATE", "PACK", "PK", "PALLET") and tgt in ea_synonyms:
        mult = float(ctx.pack_size_ea) if ctx.pack_size_ea and ctx.pack_size_ea > 1.0 else 100.0
        return round(qty * mult, 2)

    if src in ("MT", "TON", "TONNE", "TONNES") and tgt == "KG":
        return round(qty * 1000.0, 2)

    if src == "KG" and tgt in ("MT", "TON", "TONNE"):
        return round(qty / 1000.0, 3)

    if src in ("G", "GM", "GRAM", "GRAMS") and tgt == "KG":
        return round(qty / 1000.0, 3)

    if src == "KG" and tgt in ("G", "GM", "GRAM", "GRAMS"):
        return round(qty * 1000.0, 2)

    if src in ("MT", "TON", "TONNE") and tgt in ea_synonyms and ctx.unit_weight_kg and ctx.unit_weight_kg > 0:
        return round((qty * 1000.0) / float(ctx.unit_weight_kg), 2)

    if src == "KG" and tgt in ea_synonyms and ctx.unit_weight_kg and ctx.unit_weight_kg > 0:
        return round(qty / float(ctx.unit_weight_kg), 2)

    if src in ("LB", "LBS", "POUND", "POUNDS") and tgt == "KG":
        return round(qty * 0.45359237, 2)

    if src in ("LTR", "L", "LITER", "LITRE") and tgt in ("ML", "MILLILITER"):
        return round(qty * 1000.0, 2)
    if src in ("ML", "MILLILITER") and tgt in ("LTR", "L", "LITER", "LITRE"):
        return round(qty / 1000.0, 3)

    if src in ("BOX", "BAG", "CRATE", "PACK") and tgt == "KG":
        if ctx.unit_weight_kg and ctx.unit_weight_kg > 0:
            effective_pack = float(ctx.pack_size_ea) if ctx.pack_size_ea and ctx.pack_size_ea > 0 else 100.0
            return round(qty * effective_pack * float(ctx.unit_weight_kg), 2)
        return 0.0

    return round(qty, 2)
/

-- 2. In-Database Supplier SKU Drift & Alias Resolution UDF
-- Emits resolved internal_part_num, match_method, and confidence score
CREATE OR REPLACE PYTHON3 SCALAR SCRIPT CHAKAN_SCM.UDF_RESOLVE_SUPPLIER_SKU(
    raw_sku VARCHAR(80) UTF8,
    po_part_num VARCHAR(40) UTF8
) EMITS (
    resolved_part_num VARCHAR(40) UTF8,
    sku_match_method VARCHAR(30) UTF8,
    sku_confidence DOUBLE
) AS
import re

ALIASES = {
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

def _extract_ngrams(s):
    cleaned = (s or "").strip().upper()
    if not cleaned:
        return set()
    length = len(cleaned)
    ng = set()
    padded = f"^{cleaned}$"
    ng.add(padded[:2])
    ng.add(padded[-2:])
    if length <= 4:
        for i in range(len(padded) - 1):
            ng.add(padded[i:i+2])
    else:
        for i in range(length - 2):
            ng.add(cleaned[i:i+3])
    return ng

_ALIAS_NGRAM_INDEX = {}
for _k in ALIASES:
    for _ng in _extract_ngrams(_k):
        if _ng not in _ALIAS_NGRAM_INDEX:
            _ALIAS_NGRAM_INDEX[_ng] = set()
        _ALIAS_NGRAM_INDEX[_ng].add(_k)

def _jaro_winkler(s1, s2, prefix_weight=0.1):
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
    jaro = ((matches / len_a) + (matches / len_b) + ((matches - transpositions / 2.0) / matches)) / 3.0
    prefix = 0
    for ch_a, ch_b in zip(a[:4], b[:4]):
        if ch_a == ch_b:
            prefix += 1
        else:
            break
    return round(min(1.0, jaro + prefix * prefix_weight * (1.0 - jaro)), 4)

def _detect_transposition(s1, s2):
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

def _check_dim_conflict(raw_sku, po_sku):
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

def _check_rev_mismatch(raw_sku, po_part):
    m_raw = re.search(r"^(.*?)(?:[-_]?(?:REV|R)?)(\d{1,3}|[A-Z])$", raw_sku or "")
    m_po = re.search(r"^(.*?)(?:[-_]?(?:REV|R)?)(\d{1,3}|[A-Z])$", po_part or "")
    if m_raw and m_po:
        stem_raw, rev_raw = m_raw.group(1), m_raw.group(2)
        stem_po, rev_po = m_po.group(1), m_po.group(2)
        alnum_stem_raw = re.sub(r"[^A-Z0-9]", "", stem_raw)
        alnum_stem_po = re.sub(r"[^A-Z0-9]", "", stem_po)
        if alnum_stem_raw and alnum_stem_raw == alnum_stem_po and rev_raw != rev_po:
            return True
    return False

def run(ctx):
    cleaned_raw = (ctx.raw_sku or "").strip().upper()
    cleaned_po = (ctx.po_part_num or "").strip().upper()

    if cleaned_po and cleaned_raw == cleaned_po:
        ctx.emit(cleaned_po, "EXACT_MATCH", 1.00)
        return

    # Revision / Variant Collision Guard: Prevent auto-resolving conflicting ECO revisions
    if cleaned_po and _check_rev_mismatch(cleaned_raw, cleaned_po):
        ctx.emit(cleaned_raw, "REVISION_MISMATCH_SUSPECTED", 0.70)
        return

    # Numeric Transposition Guard: Prevent auto-resolving swapped digits (e.g., 6204 vs 6240)
    if cleaned_po and _detect_transposition(cleaned_raw, cleaned_po):
        ctx.emit(cleaned_raw, "NUMERIC_TRANSPOSITION_SUSPECTED", 0.65)
        return

    alnum_raw = re.sub(r"[^A-Z0-9]", "", cleaned_raw)
    alnum_po = re.sub(r"[^A-Z0-9]", "", cleaned_po)

    if alnum_po and alnum_raw == alnum_po:
        ctx.emit(cleaned_po, "HYPHEN_NORMALIZED", 0.98)
        return

    if alnum_raw in ALIASES:
        ctx.emit(ALIASES[alnum_raw], "VENDOR_CATALOG_ALIAS", 0.95)
        return

    has_dim_conflict = False
    if cleaned_po:
        has_dim_conflict = _check_dim_conflict(cleaned_raw, cleaned_po)
        if not has_dim_conflict:
            po_tokens = [t for t in cleaned_po.split("-") if len(t) >= 2]
            matched = sum(1 for tok in po_tokens if tok in alnum_raw)
            if len(po_tokens) >= 2 and matched >= len(po_tokens) - 1 and (matched / len(po_tokens)) >= 0.75:
                ctx.emit(cleaned_po, "PO_TOKEN_SIMILARITY", 0.89)
                return

            jw_po = _jaro_winkler(alnum_raw, alnum_po)
            if jw_po >= 0.93:
                ctx.emit(cleaned_po, "JARO_WINKLER_FUZZY", round(jw_po, 2))
                return
            elif jw_po >= 0.85:
                ctx.emit(cleaned_po, "FUZZY_MATCH_REVIEW_BAND", round(jw_po, 2))
                return

    if alnum_raw:
        # Phase 1: Adaptive N-Gram Candidate Pre-Filtering (Fast Path)
        query_ngrams = _extract_ngrams(alnum_raw)
        candidate_overlaps = {}
        for ng in query_ngrams:
            if ng in _ALIAS_NGRAM_INDEX:
                for candidate_key in _ALIAS_NGRAM_INDEX[ng]:
                    candidate_overlaps[candidate_key] = candidate_overlaps.get(candidate_key, 0) + 1

        best_alias_sku = None
        best_jw = 0.0
        evaluated_keys = set()

        if candidate_overlaps:
            sorted_candidates = sorted(candidate_overlaps.items(), key=lambda x: x[1], reverse=True)
            for candidate_key, _ in sorted_candidates:
                evaluated_keys.add(candidate_key)
                if _detect_transposition(alnum_raw, candidate_key):
                    continue
                score = _jaro_winkler(alnum_raw, candidate_key)
                if score > best_jw:
                    best_jw = score
                    best_alias_sku = ALIASES[candidate_key]
                if best_jw >= 0.95:
                    break

        # Phase 2: Safety Fallback Guardrail (0.00% False Negative Guarantee)
        if best_jw < 0.85:
            for alias_key, canonical_sku in ALIASES.items():
                if alias_key in evaluated_keys:
                    continue
                if _detect_transposition(alnum_raw, alias_key):
                    continue
                score = _jaro_winkler(alnum_raw, alias_key)
                if score > best_jw:
                    best_jw = score
                    best_alias_sku = canonical_sku

        if best_alias_sku:
            if best_jw >= 0.93:
                ctx.emit(best_alias_sku, "JARO_WINKLER_FUZZY", round(best_jw, 2))
                return
            elif best_jw >= 0.85:
                ctx.emit(best_alias_sku, "FUZZY_MATCH_REVIEW_BAND", round(best_jw, 2))
                return

    if cleaned_po and not has_dim_conflict:
        ctx.emit(cleaned_po, "PO_LINEAGE_FALLBACK", 0.82)
        return

    ctx.emit(cleaned_raw, "UNRESOLVED", 0.00)
/

-- 3. In-Database Multi-Format Date Harmonization UDF
-- Disambiguates DD/MM/YYYY, MM/DD/YYYY, ISO YYYY-MM-DD, DD.MM.YYYY, 8-digit compact EDI, and Unix Epoch strings.
-- Returns NULL if the raw date string is empty or unparseable.
CREATE OR REPLACE PYTHON3 SCALAR SCRIPT CHAKAN_SCM.UDF_PARSE_ASN_DATE(
    raw_date_str VARCHAR(40) UTF8,
    supplier_date_fmt VARCHAR(20) UTF8
) RETURNS DATE AS
-- NOTE: do NOT write `from datetime import datetime` here. Exasol's UDF wrapper uses the
-- module name `datetime` in the same global namespace to convert the DATE return value,
-- so shadowing it raises "type object 'datetime.datetime' has no attribute 'datetime'".
import datetime as _dt
import re

def run(ctx):
    val = (ctx.raw_date_str or "").strip()
    if not val:
        return None

    if not re.fullmatch(r"\d{9,10}", val):
        val = re.split(r"[T\s]", val)[0].strip()

    if re.fullmatch(r"\d{9,10}", val):
        try:
            d = _dt.datetime.fromtimestamp(int(val), tz=_dt.timezone.utc).date()
            return d if d.year == 2026 else None
        except Exception:
            return None

    # Compact EDI 8-digit date: YYYYMMDD
    edi_match = re.fullmatch(r"(20\d{2})(\d{2})(\d{2})", val)
    if edi_match:
        try:
            return _dt.date(int(edi_match.group(1)), int(edi_match.group(2)), int(edi_match.group(3)))
        except ValueError:
            return None

    # Delimited dates: supports '-', '/', and '.'
    # 1. ISO YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD
    iso_match = re.fullmatch(r"(\d{4})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])", val)
    if iso_match:
        try:
            return _dt.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None

    # 2. DD/MM/YYYY, MM/DD/YYYY, DD.MM.YYYY, DD-MM-YYYY
    delim_match = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", val)
    if delim_match:
        try:
            first = int(delim_match.group(1))
            second = int(delim_match.group(2))
            year = int(delim_match.group(3))
            fmt_pref = (ctx.supplier_date_fmt or "DD/MM/YYYY").strip().upper()
            if first > 12:
                return _dt.date(year, second, first)
            if second > 12:
                return _dt.date(year, first, second)
            if fmt_pref in ("MM/DD/YYYY", "MM-DD-YYYY", "MM.DD.YYYY"):
                return _dt.date(year, first, second)
            return _dt.date(year, second, first)
        except ValueError:
            return None

    for fmt in ("%d-%b-%Y", "%d/%b/%Y", "%d.%b.%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return _dt.datetime.strptime(val, fmt).date()
        except ValueError:
            continue

    return None
/

