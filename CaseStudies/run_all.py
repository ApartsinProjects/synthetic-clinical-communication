#!/usr/bin/env python
"""Run every study's reproduce.py and report pass/fail.

    python run_all.py --smoke     # fast: tiny subset per study (recommended for a check)
    python run_all.py             # full reproduction of every study (slow; GPU for encoders)

Each study folder holds a self-contained reproduce.py that retrains and re-evaluates on the
shipped synthetic data (no regeneration, no network). This runner just invokes each in turn
with the same Python interpreter and prints a summary table.
"""
import argparse
import subprocess
import sys
from pathlib import Path

STUDIES = [
    "diagnosis-from-noisy-self-descriptions",
    "adaptive-diagnostic-questioning",
    "urgency-triage-from-complaints",
    "clinical-decision-extraction-hebrew-discharge",
    "administrative-portal-message-triage",
    "clinical-priority-portal-triage",
    "postpartum-severity-triage",
    "oncology-distress-classification",
    "medication-question-risk-classification",
    "home-care-status-detection",
    "ems-report-routing",
    "casualty-record-reconstruction",
    "sbar-completeness-checking",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="pass --smoke to each reproduce.py")
    ap.add_argument("--timeout", type=int, default=1800, help="per-study timeout (seconds)")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    results = []
    for name in STUDIES:
        script = here / name / "reproduce.py"
        if not script.exists():
            results.append((name, "MISSING"))
            continue
        cmd = [sys.executable, str(script)] + (["--smoke"] if args.smoke else [])
        print(f"\n{'='*70}\n>>> {name}{' (smoke)' if args.smoke else ''}\n{'='*70}", flush=True)
        try:
            r = subprocess.run(cmd, cwd=str(script.parent), timeout=args.timeout)
            results.append((name, "PASS" if r.returncode == 0 else f"FAIL ({r.returncode})"))
        except subprocess.TimeoutExpired:
            results.append((name, "TIMEOUT"))

    print(f"\n{'='*70}\nSUMMARY\n{'='*70}")
    for name, status in results:
        print(f"  {status:14s} {name}")
    ok = sum(1 for _, s in results if s == "PASS")
    print(f"\n{ok} / {len(results)} passed")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
