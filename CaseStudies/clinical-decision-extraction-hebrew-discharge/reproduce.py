#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RE-EVALUATION of shipped clinical-decision-extraction predictions
=================================================================

Study
-----
Extract clinical *decisions* (drug and procedure spans) from synthetic Hebrew
hospital discharge summaries. Two systems are compared on a v2 test split of
81 summaries carrying 185 gold decision spans (drug_decision + procedure_decision):

  * sklearn candidate-reranker  (XLM-R tagger -> candidate generation ->
    handcrafted features -> sklearn reranker that scores/selects candidates)
  * XLM-R BIO tagger            (token-level BIO sequence labeller, argmax decode)

Metrics
-------
  * strict  F1 : exact-span match  (start_char, end_char, label all identical)
  * relaxed F1 : any-character-overlap match, greedy 1-to-1 per label

reported per category (drug_decision, procedure_decision) and overall
(micro-averaged over the two decision categories; problem_context is ignored,
matching the shipped comparison table).

Why this is a RE-EVALUATION, not a retraining
---------------------------------------------
Retraining either system needs the candidate-generation + handcrafted-feature
pipeline (for the sklearn reranker) and the token-tagger training loop (for
XLM-R). Those components are NOT fully shipped in this case-study bundle. This
script therefore RE-SCORES the shipped model predictions against the shipped
gold spans. No training, no LLM/API call, no network access.

Recompute paths
---------------
Each shipped preds file embeds, per summary, both `pred_spans` and the aligned
`gold_spans`, so strict/relaxed F1 can be recomputed directly.

  * XLM-R  -> `preds_xlmr.jsonl` contains one decoded prediction set per summary.
    Recomputing strict F1 from the raw preds reproduces the paper numbers
    exactly, so the XLM-R row uses the RAW-PREDS path.

  * Reranker -> `preds_reranker.jsonl` ships the *ranked candidate pool* (several
    overlapping candidates per decision, each with a `confidence`), NOT the final
    selected span set. The trained sklearn selector/decoder that turns that pool
    into the final prediction is part of the unshipped feature pipeline, so a raw
    re-score of the candidate pool does not reproduce the reported reranker F1.
    The reranker row therefore falls back to the shipped, verified comparison
    table `model_comparison_v2_test.csv` (COMPARISON-CSV path). The raw-pool
    recompute is still printed for transparency.

Paper / target numbers (strict F1)
----------------------------------
  sklearn reranker : drug 0.164 / procedure 0.564 / overall 0.427
  XLM-R BIO        : drug 0.248 / procedure 0.428 / overall 0.326

Data used
---------
  preds_reranker.jsonl          (reranker candidate pool + embedded gold)
  preds_xlmr.jsonl              (XLM-R decoded preds + embedded gold)
  model_comparison_v2_test.csv  (shipped verified comparison table)
  extracted_annotations.sample.jsonl (gold-annotation sample; schema reference only)

Usage
-----
  python reproduce.py [--smoke]

Deps: pandas, numpy (no torch).
"""

import argparse
import json
import os
from collections import Counter

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RERANKER = os.path.join(HERE, "preds_reranker.jsonl")
XLMR = os.path.join(HERE, "preds_xlmr.jsonl")
CSV = os.path.join(HERE, "model_comparison_v2_test.csv")

DECISION_LABELS = ["drug_decision", "procedure_decision"]

# strict F1 targets reported in the paper / comparison table
PAPER = {
    "reranker": {"drug_decision": 0.164, "procedure_decision": 0.564, "overall": 0.427},
    "xlmr": {"drug_decision": 0.248, "procedure_decision": 0.428, "overall": 0.326},
}
TOL = 0.01  # tolerance for declaring a raw-preds recompute a match


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _bounds(span):
    st = span.get("start_char", span.get("start_offset"))
    en = span.get("end_char", span.get("end_offset"))
    return st, en


def _f1(tp, fp, fn):
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0


def evaluate(samples, mode="strict"):
    """Micro F1 per decision label + overall, from embedded pred/gold spans."""
    stats = {lab: [0, 0, 0] for lab in DECISION_LABELS}  # tp, fp, fn
    for rec in samples:
        gold = [g for g in rec.get("gold_spans", []) if g["label"] in DECISION_LABELS]
        pred = [p for p in rec.get("pred_spans", []) if p["label"] in DECISION_LABELS]
        for lab in DECISION_LABELS:
            g = [_bounds(x) for x in gold if x["label"] == lab]
            p = [_bounds(x) for x in pred if x["label"] == lab]
            if mode == "strict":
                gc, pc = Counter(g), Counter(p)
                tp = sum((gc & pc).values())
                fp = sum(pc.values()) - tp
                fn = sum(gc.values()) - tp
            else:  # relaxed: greedy any-overlap 1-to-1 match
                used = [False] * len(g)
                tp = 0
                for ps, pe in p:
                    for i, (gs, ge) in enumerate(g):
                        if not used[i] and ps < ge and gs < pe:
                            used[i] = True
                            tp += 1
                            break
                fp = len(p) - tp
                fn = len(g) - tp
            stats[lab][0] += tp
            stats[lab][1] += fp
            stats[lab][2] += fn
    res = {}
    T = F = N = 0
    for lab in DECISION_LABELS:
        tp, fp, fn = stats[lab]
        res[lab] = _f1(tp, fp, fn)
        T += tp
        F += fp
        N += fn
    res["overall"] = _f1(T, F, N)
    return res


def gold_span_count(samples):
    return sum(
        len([g for g in r.get("gold_spans", []) if g["label"] in DECISION_LABELS])
        for r in samples
    )


def csv_strict(df, col):
    out = {}
    for _, row in df.iterrows():
        if row["match_type"] == "strict":
            out[row["class"]] = float(row[col])
    return out


def fmt_row(label, measured, paper):
    d = measured - paper
    flag = "OK" if abs(d) <= TOL else "  "
    return f"  {label:20s} measured={measured:.4f}  paper={paper:.4f}  d={d:+.4f} {flag}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true",
                    help="quick check on the first 10 summaries only")
    args = ap.parse_args()

    reranker = load_jsonl(RERANKER)
    xlmr = load_jsonl(XLMR)
    df = pd.read_csv(CSV)

    if args.smoke:
        reranker, xlmr = reranker[:10], xlmr[:10]

    print("=" * 74)
    print("RE-EVALUATION of shipped predictions (no training / no LLM / no network)")
    print("=" * 74)
    print(f"summaries: reranker={len(reranker)}  xlmr={len(xlmr)}"
          + ("   [SMOKE: first 10]" if args.smoke else ""))
    print(f"gold decision spans: reranker={gold_span_count(reranker)}  "
          f"xlmr={gold_span_count(xlmr)}   (expected 185 on full split)")
    print()

    # ---- raw-preds recompute for both models --------------------------------
    rr_strict = evaluate(reranker, "strict")
    rr_relax = evaluate(reranker, "relaxed")
    xl_strict = evaluate(xlmr, "strict")
    xl_relax = evaluate(xlmr, "relaxed")

    # ---- XLM-R: raw-preds path (reproduces exactly) -------------------------
    print("-" * 74)
    print("MODEL: XLM-R BIO tagger        PATH = RAW-PREDS (recomputed from preds)")
    print("-" * 74)
    xl_ok = True
    for lab in ["drug_decision", "procedure_decision", "overall"]:
        print(fmt_row("strict " + lab, xl_strict[lab], PAPER["xlmr"][lab]))
        xl_ok = xl_ok and abs(xl_strict[lab] - PAPER["xlmr"][lab]) <= TOL
    print("  relaxed (recomputed): "
          + "  ".join(f"{k}={xl_relax[k]:.4f}" for k in
                      ["drug_decision", "procedure_decision", "overall"]))
    print(f"  => strict F1 reproduced within +/-{TOL}: {xl_ok}")
    print()

    # ---- Reranker: comparison-csv fallback ----------------------------------
    rr_csv = csv_strict(df, "sklearn_candidate_reranker_v2_test")
    print("-" * 74)
    print("MODEL: sklearn candidate-reranker   PATH = COMPARISON-CSV (verified table)")
    print("       (raw candidate pool ships without the unshipped trained selector,")
    print("        so a raw re-score of the pool does not reproduce the reported F1)")
    print("-" * 74)
    for lab in ["drug_decision", "procedure_decision", "overall"]:
        print(fmt_row("strict " + lab, rr_csv[lab], PAPER["reranker"][lab]))
    print("  [transparency] raw candidate-pool re-score (NOT the reported number):")
    print("     strict : "
          + "  ".join(f"{k}={rr_strict[k]:.4f}" for k in
                      ["drug_decision", "procedure_decision", "overall"]))
    print("     relaxed: "
          + "  ".join(f"{k}={rr_relax[k]:.4f}" for k in
                      ["drug_decision", "procedure_decision", "overall"]))
    print()

    # ---- shipped comparison table cross-check -------------------------------
    print("-" * 74)
    print("model_comparison_v2_test.csv (shipped, for cross-check)")
    print("-" * 74)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(df.to_string(index=False))
    print()

    # ---- summary ------------------------------------------------------------
    print("=" * 74)
    print("SUMMARY (strict F1, drug / procedure / overall)")
    print("=" * 74)
    print("  XLM-R    [raw-preds]     : "
          f"{xl_strict['drug_decision']:.3f} / "
          f"{xl_strict['procedure_decision']:.3f} / "
          f"{xl_strict['overall']:.3f}"
          f"   (paper {PAPER['xlmr']['drug_decision']:.3f} / "
          f"{PAPER['xlmr']['procedure_decision']:.3f} / "
          f"{PAPER['xlmr']['overall']:.3f})")
    print("  Reranker [comparison-csv]: "
          f"{rr_csv['drug_decision']:.3f} / "
          f"{rr_csv['procedure_decision']:.3f} / "
          f"{rr_csv['overall']:.3f}"
          f"   (paper {PAPER['reranker']['drug_decision']:.3f} / "
          f"{PAPER['reranker']['procedure_decision']:.3f} / "
          f"{PAPER['reranker']['overall']:.3f})")
    print()
    if not args.smoke and not xl_ok:
        raise SystemExit("XLM-R strict F1 did not reproduce within tolerance")
    print("Done." + ("  [smoke run]" if args.smoke else ""))


if __name__ == "__main__":
    main()
