"""
domain_config.py
Single Source of Truth (SSOT) for Chakan SCM Domain Policies, Tariffs & Coefficients.

Eliminates magic numbers across Exasol SQL views and the Python verification mirror,
providing a unified policy contract for financial ROI and starvation calculations.
"""

# ==============================================================================
# 1. PLANNING HORIZON & TIME WINDOWS
# ==============================================================================
PLANNING_HORIZON_HOURS: float = 48.0
"""Standard production cycle buffer horizon in hours (48-hour Monday-Wednesday shift)."""

# ==============================================================================
# 2. FINANCIAL ROI & MARGIN POLICIES
# ==============================================================================
EBITDA_MARGIN_RATIO: float = 0.15
"""
Protected operating contribution margin ratio (15% EBITDA) on finished vehicles.
In supply chain economics, finished vehicles represent deferred production slots,
while unrecoverable plant idle penalties and operating margin are permanent losses.
"""

AVOIDED_PANIC_FREIGHT_INR: float = 135000.0
"""
Estimated avoided panic freight cost across 3 uncoordinated emergency courier dispatches
(@ ₹45,000 each) previously triggered by false alarms.
"""

HOT_SHOT_BENCHMARK_FREIGHT_INR: float = 45000.0
"""
Dedicated single hot-shot air/road courier charter cost for emergency component rescue.
"""

# ==============================================================================
# 3. EXPEDITED FREIGHT TARIFF BRACKETS
# ==============================================================================
FREIGHT_BASE_INR: float = 25000.0
"""Minimum base dispatch fee for dedicated courier / hot-shot transit."""

FREIGHT_MAX_INR: float = 75000.0
"""Maximum ceiling cap on standard regional air/road emergency charter per component."""

FREIGHT_WEIGHT_TARIFF_INR_PER_KG: float = 4.5
"""Incremental weight tariff per kilogram for expedited component dispatch."""

# ==============================================================================
# 4. HARMONIZATION & CONFIDENCE THRESHOLDS
# ==============================================================================
FUZZY_CONFIDENCE_THRESHOLD: float = 0.85
"""
Jaro-Winkler string similarity threshold for auto-clearing vendor SKU drift.
Matches below 0.85 are quarantined for manual planner override in the review queue.
"""

EXACT_MATCH_CONFIDENCE: float = 1.00
HYPHEN_NORMALIZED_CONFIDENCE: float = 0.98
CATALOG_CROSS_REF_CONFIDENCE: float = 0.95
PO_TOKEN_SIMILARITY_CONFIDENCE: float = 0.89

# ==============================================================================
# 5. ENTERPRISE SCALE LOCATIONS & DATA LOCALITY MODEL
# ==============================================================================
ENTERPRISE_SCALE_TIERS = {
    "Daily Plant Inbound (Current Benchmark)": {
        "asn_rows": 10000,
        "erp_ledger_rows": 500000,
        "network_egress_mb": 125.0,
        "external_etl_network_sec_1gbps": 1.0,
        "exasol_egress_mb": 0.0,
        "exasol_egress_sec": 0.0,
    },
    "Regional Multi-Plant Cluster (Pune-Chakan)": {
        "asn_rows": 100000,
        "erp_ledger_rows": 2500000,
        "network_egress_mb": 625.0,
        "external_etl_network_sec_1gbps": 5.0,
        "exasol_egress_mb": 0.0,
        "exasol_egress_sec": 0.0,
    },
    "OEM National Supply Chain (All India Plants)": {
        "asn_rows": 1000000,
        "erp_ledger_rows": 10000000,
        "network_egress_mb": 2500.0,
        "external_etl_network_sec_1gbps": 20.0,
        "exasol_egress_mb": 0.0,
        "exasol_egress_sec": 0.0,
    },
}
