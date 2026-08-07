#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reproduce: Casualty-Record Reconstruction from Battlefield Radio (paper section 3.4.2)

WHAT THIS SCRIPT DOES (and does NOT do)
---------------------------------------
This is a RE-EVALUATION of the *shipped model predictions*, not a retraining run.
Reproducing the AlephBERT Multi-Head classifier end-to-end would require a GPU and a
training pipeline (encoder + per-field classification heads, tokenizer, checkpoints)
that is NOT fully shipped in this case-study folder. Instead, this script reproduces
the paper's results table by RE-SCORING the predictions that ARE shipped:
per-field Exact-Match Accuracy, Macro F1 (across fields), and a Hallucination count,
over the 100 held-out test samples. No training, no LLM / API calls, no network.

TASK
----
Given a noisy Hebrew battlefield-radio transcript, reconstruct a flat 20-field JSON
casualty record (IDF Form 101 aligned: demographics, injury mechanism/site, vitals,
conditions, treatments, information reliability). Fields not clearly stated must be
output as "unknown" (strict zero-hallucination policy).

DATA USED (shipped, this folder)
--------------------------------
  scored_bert_v3.json   -> 100 test samples, each with:
                             ground_truth  (gold 20-field record)
                             target_output (model prediction)
                             metadata.scores {accuracy, f1_score, precision, recall}
  scored_finetuned.json -> same structure, 100 samples.
  test.jsonl            -> gold held-out split (100 rows; provided for reference /
                            cross-checking; the scored_*.json files already carry the
                            gold under "ground_truth").

SCORED-FILE -> MODEL MAPPING (verified by matching the paper's numbers)
----------------------------------------------------------------------
  scored_bert_v3.json   = "AlephBERT Multi-Head v3 (final)"  (non-generative classifier)
  scored_finetuned.json = "Phi-3 fine-tuned (QLoRA)"         (generative)
The mapping is confirmed empirically: aggregating each file's stored per-sample scores
reproduces exactly the paper's AlephBERT-v3 row (79.30% / 0.802 / 16) and Phi-3 row
(63.10% / 0.632 / 7). scored_finetuned.json holds the Phi-3 QLoRA fine-tuned model
(the only fine-tuned generative model in the paper whose numbers it matches).

METRICS (recomputed here from predictions vs gold)
--------------------------------------------------
  Exact-Match Accuracy : fraction of the 20 fields whose predicted value exactly
                         matches gold (case/space-normalized; list fields compared as
                         order-insensitive sets), averaged over samples. The shipped
                         files also store this per-sample under metadata.scores.accuracy;
                         we aggregate the stored scores (authoritative) AND independently
                         recompute exact-match from prediction-vs-gold as a cross-check.
  Macro F1             : per-sample token/field F1 stored under metadata.scores.f1_score,
                         averaged over the 100 samples.
  Hallucinations       : count (field x sample) where GOLD is "unknown" (scalar
                         "unknown" or list ["unknown"]) but the model predicts a
                         concrete non-unknown value. Directly enforces the strict
                         zero-hallucination policy: inventing information for a field
                         that should be "unknown".

PAPER TARGET NUMBERS (README "Results" table)
---------------------------------------------
  Model                             Exact-Match   Macro F1   Hallucinations
  AlephBERT Multi-Head v3 (final)   79.30%        0.802      16
  Phi-3 fine-tuned (QLoRA)          63.10%        0.632       7

DEPENDENCIES: pandas, numpy only (no torch).
USAGE:
  python reproduce.py            # full 100-sample re-evaluation
  python reproduce.py --smoke    # subsample rows for a fast smoke run
"""

import argparse
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# scored file -> (model label, paper accuracy %, paper macro-F1, paper hallucinations)
MODELS = {
    "scored_bert_v3.json": ("AlephBERT Multi-Head v3 (final)", 79.30, 0.802, 16),
    "scored_finetuned.json": ("Phi-3 fine-tuned (QLoRA)", 63.10, 0.632, 7),
}


def _norm(v):
    """Normalize a field value for exact-match comparison.

    Lists -> order-insensitive tuple of normalized tokens; scalars -> lowercased,
    stripped string.
    """
    if isinstance(v, list):
        return tuple(sorted(str(x).strip().lower() for x in v))
    return str(v).strip().lower()


def _is_unknown(v):
    """True if the gold/pred value is 'unknown' (scalar 'unknown' or list ['unknown'],
    or an empty list)."""
    seq = v if isinstance(v, list) else [v]
    if len(seq) == 0:
        return True
    return all(str(x).strip().lower() == "unknown" for x in seq)


def evaluate(records):
    """Return (metrics_dict, per_sample_dataframe) for one model's scored records."""
    rows = []
    for e in records:
        gold = e["ground_truth"]
        pred = e["target_output"]
        scores = e.get("metadata", {}).get("scores", {})

        keys = list(gold.keys())
        n_fields = len(keys)

        # Independent exact-match recompute (prediction vs gold).
        n_correct = sum(
            1 for k in keys if _norm(pred.get(k, "unknown")) == _norm(gold[k])
        )
        em_recomputed = n_correct / n_fields if n_fields else np.nan

        # Hallucinations: gold == unknown but prediction is concrete.
        halluc = sum(
            1
            for k in keys
            if _is_unknown(gold[k]) and not _is_unknown(pred.get(k, "unknown"))
        )

        rows.append(
            {
                "example_id": e.get("metadata", {}).get("example_id", ""),
                "stored_accuracy": scores.get("accuracy", np.nan),
                "stored_f1": scores.get("f1_score", np.nan),
                "em_recomputed": em_recomputed,
                "hallucinations": halluc,
                "n_fields": n_fields,
            }
        )

    df = pd.DataFrame(rows)
    metrics = {
        "n_samples": int(len(df)),
        # Aggregate stored per-sample scores (authoritative paper metric).
        "exact_match_pct": float(df["stored_accuracy"].mean() * 100.0),
        "macro_f1": float(df["stored_f1"].mean()),
        # Independent cross-check of exact-match from predictions vs gold.
        "exact_match_recomputed_pct": float(df["em_recomputed"].mean() * 100.0),
        "hallucinations": int(df["hallucinations"].sum()),
    }
    return metrics, df


def load_records(path, smoke=False, smoke_n=20):
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    if smoke:
        records = records[:smoke_n]
    return records


def main():
    ap = argparse.ArgumentParser(
        description="Re-evaluate shipped casualty-record predictions vs gold."
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="Subsample rows (first 20) for a fast smoke run.",
    )
    ap.add_argument(
        "--smoke-n", type=int, default=20, help="Rows to keep in --smoke mode."
    )
    args = ap.parse_args()

    if args.smoke:
        print(f"[SMOKE MODE] using first {args.smoke_n} samples per file\n")

    print("=" * 78)
    print("Casualty-Record Reconstruction -- RE-EVALUATION of shipped predictions")
    print("(re-scoring only; no retraining, no LLM/API, no network)")
    print("=" * 78)

    header = (
        f"\n{'Model':<34}{'ExactMatch%':>12}{'MacroF1':>10}"
        f"{'Halluc':>8}   (measured vs paper)"
    )
    print(header)
    print("-" * 78)

    all_ok = True
    for fname, (label, p_acc, p_f1, p_hall) in MODELS.items():
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            print(f"{label:<34}  MISSING FILE: {fname}")
            all_ok = False
            continue

        records = load_records(path, smoke=args.smoke, smoke_n=args.smoke_n)
        m, _df = evaluate(records)

        print(f"{label}")
        print(f"  file: {fname}   (n={m['n_samples']})")
        print(
            f"    Exact-Match Accuracy : measured {m['exact_match_pct']:6.2f}%"
            f"   | paper {p_acc:6.2f}%"
        )
        print(
            f"      (recomputed EM     : {m['exact_match_recomputed_pct']:6.2f}%"
            f"   independent pred-vs-gold cross-check)"
        )
        print(
            f"    Macro F1             : measured {m['macro_f1']:6.3f} "
            f"    | paper {p_f1:6.3f}"
        )
        print(
            f"    Hallucinations       : measured {m['hallucinations']:6d}  "
            f"    | paper {p_hall:6d}"
        )

        # Tolerance check (skip in smoke mode, where the subsample won't match paper).
        if not args.smoke:
            acc_ok = abs(m["exact_match_pct"] - p_acc) <= 0.5
            f1_ok = abs(m["macro_f1"] - p_f1) <= 0.005
            hall_ok = m["hallucinations"] == p_hall
            status = "OK" if (acc_ok and f1_ok and hall_ok) else "MISMATCH"
            if status != "OK":
                all_ok = False
            print(
                f"    -> match: acc={'Y' if acc_ok else 'N'} "
                f"f1={'Y' if f1_ok else 'N'} "
                f"halluc={'Y' if hall_ok else 'N'}  [{status}]"
            )
        print()

    print("-" * 78)
    if args.smoke:
        print("Smoke run complete (subsampled; numbers not expected to match paper).")
    elif all_ok:
        print("SUCCESS: all measured metrics reproduce the paper targets.")
    else:
        print("WARNING: one or more metrics did not match the paper targets.")
    print("=" * 78)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
