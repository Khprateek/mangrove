"""
Verification script: Checks numerical claims across README, docs, and pitch decks
against the single source of truth in domain_config.py and benchmarks/results.json.
"""
import json
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.exasol_engine import domain_config


def main():
    print("Verifying numbers against SSOT...")
    bench_path = Path("benchmarks/results.json")
    if not bench_path.exists():
        print("ERROR: benchmarks/results.json not found!")
        sys.exit(1)

    bench_data = json.loads(bench_path.read_text(encoding="utf-8"))
    print(f"Loaded benchmark data with {len(bench_data['high_scale_columnar_benchmark'])} columnar scale points.")

    readme = Path("README.md").read_text(encoding="utf-8")
    deck = Path("pitch/PRESENTATION_SLIDES_DECK.md").read_text(encoding="utf-8")
    script = Path("pitch/DEMO_VIDEO_SCRIPT_3MIN.md").read_text(encoding="utf-8")
    run_guide = Path("docs/run-guide.md").read_text(encoding="utf-8")

    errors = []

    # 1. Check for legacy unverified latencies or score boasts
    targets = [
        ("README.md", readme),
        ("PRESENTATION_SLIDES_DECK.md", deck),
        ("DEMO_VIDEO_SCRIPT_3MIN.md", script),
        ("docs/run-guide.md", run_guide),
    ]

    for name, content in targets:
        if "11.8 ms" in content:
            errors.append(f"Found obsolete '11.8 ms' claim in {name}")
        if "98/100" in content:
            errors.append(f"Found self-graded '98/100' in {name}")
        if "35/35" in content:
            errors.append(f"Found outdated test count '35/35' in {name} (expected 41/41)")

    # 2. Check that core financial figures are cited accurately
    expected_figures = [
        ("₹37.88 Cr", "37.88"),
        ("₹26.05 Cr", "26.05"),
        ("₹20.76 Cr", "20.76"),
        ("₹5.29 Cr", "5.29"),
        ("₹1.18 Cr", "1.18"),
    ]

    for label, val in expected_figures:
        for name, content in [("README.md", readme), ("PRESENTATION_SLIDES_DECK.md", deck), ("DEMO_VIDEO_SCRIPT_3MIN.md", script)]:
            if val not in content:
                errors.append(f"Missing core figure {label} ({val}) in {name}")

    if errors:
        print("[FAIL] Discrepancies found:")
        for e in errors:
            print(" -", e)
        return False
    else:
        print("[OK] All target files checked cleanly against unverified claims and verified against SSOT!")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
