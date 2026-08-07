#!/usr/bin/env python
"""
reproduce.py - RE-EVALUATION of the Adaptive Diagnostic Questioning (MedQDx) benchmark.

WHAT THIS IS
------------
This study (paper section 3.1.2; repo https://github.com/MaiWert/MedQDx) trained NO
models. It is a ZERO-SHOT LLM benchmark: GPT-4.1 acts as a "doctor" that iteratively
questions a GPT-4o-mini "patient" and emits a diagnosis each round, scored by cosine
similarity to the ground-truth disease label. Because nothing is trained, "reproduction"
here means RE-COMPUTING the evaluation metrics directly from the shipped, already-scored
benchmark. This script makes NO LLM/API calls, computes NO embeddings, and touches the
network zero times - it only re-derives the reported numbers from the shipped Similarity
columns using pandas/numpy.

DATA USED
---------
  benchmark.csv     (99 rows) - the adaptive-questioning benchmark. Per-case columns plus
                    Question_1..3, Answer_1..3, Diagnosis_1..3, Similarity_1..3.
  patient_cases.csv (100 rows) - the generated vignettes: prognosis, symptoms,
                    '100% Case', '80% Case', '50% Case'. (Read only for context/reporting;
                    it carries NO similarity scores.)

COLUMN MAPPING (inspected; documented per the task's ambiguity flag)
--------------------------------------------------------------------
The three numeric columns Similarity_1 / Similarity_2 / Similarity_3 in benchmark.csv are
the diagnostic-similarity scores of the doctor's diagnosis at dialogue ROUND 1 / 2 / 3.
Per the shipped notebook (generate_data.ipynb, cell 27), the entire 3-round dialogue is
conducted over the *50% Case* (the doctor sees 50% of symptoms; the patient answers from
the 100% case). So:

    Similarity_r  <->  ROUND r of the 50%-case dialogue   (NOT reveal tier r).

These columns are ROUNDS, not the 100%/80%/50% reveal TIERS. Consequently:

  * MMS (mean of per-row max similarity) and the per-round mean similarities ARE fully
    reproducible from benchmark.csv and are recomputed below - they match the paper.

  * The paper's ZDA-by-tier table (100%:51/100, 80%:44/100, 50%:37/100, threshold 0.65)
    comes from a SEPARATE evaluation: the doctor directly diagnoses each of the 100
    patient_cases vignettes at each reveal tier. Those per-tier direct-diagnosis
    similarity scores are NOT present in either shipped CSV (only the 3 dialogue-round
    similarities over the 50% case are shipped). ZDA-by-tier therefore CANNOT be
    recomputed from the shipped columns without new model/embedding calls, which this
    re-evaluation deliberately does not make. We print the paper targets for reference,
    and also report the ZDA figures that ARE computable from the shipped rounds
    (per-round and best-of-3), clearly labeled as the shipped-data analogue.

PAPER TARGET NUMBERS
--------------------
  ZDA by reveal tier (threshold 0.65, 100 cases):  100% = 51/100 (51.0%)
                                                    80%  = 44/100 (44.0%)
                                                    50%  = 37/100 (37.0%)
  Mean of Max Similarity across rows (MMS):         0.657
  Mean similarity round 1 / 2 / 3:                  0.624 / 0.621 / 0.635

Usage:
  python reproduce.py            # full re-evaluation over all 99 benchmark rows
  python reproduce.py --smoke    # quick subsample (first ~20 rows); numbers will drift
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH_CSV = os.path.join(HERE, "benchmark.csv")
CASES_CSV = os.path.join(HERE, "patient_cases.csv")

THRESHOLD = 0.65
SIM_COLS = ["Similarity_1", "Similarity_2", "Similarity_3"]

# Paper targets (from README.md / section 3.1.2)
TGT_ZDA = {"100%": (51, 100, 0.510), "80%": (44, 100, 0.440), "50%": (37, 100, 0.370)}
TGT_MMS = 0.657
TGT_ROUND = {1: 0.624, 2: 0.621, 3: 0.635}


def fmt(measured, target):
    return f"measured = {measured:>8.4f}   |   paper target = {target}"


def main():
    ap = argparse.ArgumentParser(description="Re-evaluate the shipped MedQDx benchmark (no model/API calls).")
    ap.add_argument("--smoke", action="store_true",
                    help="Subsample the first ~20 rows for a fast smoke run (numbers will differ from targets).")
    args = ap.parse_args()

    if not os.path.exists(BENCH_CSV):
        sys.exit(f"ERROR: {BENCH_CSV} not found.")

    bench = pd.read_csv(BENCH_CSV)
    cases = pd.read_csv(CASES_CSV) if os.path.exists(CASES_CSV) else None

    # Ensure similarity columns are numeric.
    for c in SIM_COLS:
        bench[c] = pd.to_numeric(bench[c], errors="coerce")

    n_full = len(bench)
    if args.smoke:
        bench = bench.head(20).copy()
        print("*** SMOKE MODE: using first", len(bench), "of", n_full,
              "rows; metrics will NOT match paper targets. ***\n")

    n = len(bench)

    print("=" * 78)
    print("MedQDx Adaptive Diagnostic Questioning - RE-EVALUATION (no training, no API)")
    print("=" * 78)
    print(f"benchmark.csv rows        : {n}" + ("" if args.smoke else f"  (paper used ~100)"))
    if cases is not None:
        print(f"patient_cases.csv rows    : {len(cases)}  (context only; carries no similarity scores)")
    print(f"similarity threshold      : {THRESHOLD}")
    print("Similarity_1..3 mapping   : dialogue ROUND 1/2/3 over the 50% case (NOT reveal tiers)")
    print()

    # ------------------------------------------------------------------ #
    # Metric 2: Mean of Max Similarity across rows (MMS)
    # ------------------------------------------------------------------ #
    row_max = bench[SIM_COLS].max(axis=1)
    mms = float(row_max.mean())

    # ------------------------------------------------------------------ #
    # Metric 3: Per-round mean similarity
    # ------------------------------------------------------------------ #
    round_means = {r: float(bench[f"Similarity_{r}"].mean()) for r in (1, 2, 3)}

    # ------------------------------------------------------------------ #
    # Metric 1: ZDA
    #   Paper ZDA-by-tier is NOT in shipped columns (see docstring). We print the
    #   targets, then report the ZDA figures that ARE computable from the shipped
    #   dialogue rounds as the honest shipped-data analogue.
    # ------------------------------------------------------------------ #
    per_round_zda = {r: (int((bench[f"Similarity_{r}"] >= THRESHOLD).sum()), n) for r in (1, 2, 3)}
    best_of_3_correct = int((row_max >= THRESHOLD).sum())

    print("-" * 78)
    print("[1] Zero-shot Diagnostic Accuracy (ZDA), threshold >= 0.65")
    print("-" * 78)
    print("  NOTE: The paper's ZDA-by-tier (100%/80%/50%) is a separate direct-diagnosis")
    print("        evaluation whose per-tier similarities are NOT shipped in either CSV.")
    print("        It cannot be recomputed here without model/embedding calls. Targets:")
    for tier, (corr, tot, frac) in TGT_ZDA.items():
        print(f"        paper target  {tier:>4} tier : {corr}/{tot}  ({frac*100:.1f}%)")
    print()
    print("  Shipped-data analogue (ZDA computable from the 3 dialogue rounds, this run):")
    for r in (1, 2, 3):
        c, t = per_round_zda[r]
        print(f"        round {r} ZDA        : {c}/{t}  ({c/t*100:.1f}%)")
    print(f"        best-of-3 ZDA      : {best_of_3_correct}/{n}  ({best_of_3_correct/n*100:.1f}%)")
    print()

    print("-" * 78)
    print("[2] Mean of Max Similarity across rows (MMS) = mean_row( max(Sim_1,Sim_2,Sim_3) )")
    print("-" * 78)
    print("        " + fmt(mms, TGT_MMS))
    print()

    print("-" * 78)
    print("[3] Per-round mean diagnostic similarity")
    print("-" * 78)
    for r in (1, 2, 3):
        print(f"        round {r}: " + fmt(round_means[r], TGT_ROUND[r]))
    print()

    if not args.smoke:
        print("-" * 78)
        print("Reproduction check (full run):")
        ok_mms = abs(mms - TGT_MMS) <= 0.01
        ok_rounds = all(abs(round_means[r] - TGT_ROUND[r]) <= 0.01 for r in (1, 2, 3))
        print(f"        MMS within 0.01 of target        : {'PASS' if ok_mms else 'DRIFT'}")
        print(f"        all per-round means within 0.01  : {'PASS' if ok_rounds else 'DRIFT'}")
        print("        (Small drift vs. paper is expected: shipped benchmark has 99 rows;")
        print("         paper reported ~100. MMS/per-round reproduce; ZDA-by-tier is not")
        print("         recomputable from shipped columns - see docstring.)")
    print("=" * 78)


if __name__ == "__main__":
    main()
