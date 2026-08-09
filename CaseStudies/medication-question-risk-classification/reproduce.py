#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reproduce.py -- Medication-Question Risk Classification (Case study 3.3.5)

WHAT THIS REPRODUCES
    The paper's best CLASSICAL baseline: a binary risk classifier for medication
    questions -- Critical (potentially dangerous medication behavior) vs.
    General (informational / low-risk). This script RETRAINS and RE-EVALUATES
    on the already-shipped labeled data. There is NO data regeneration, NO
    LLM/API call, and NO network access.

DATA (shipped alongside this script)
    labeled_data.xlsx  -- the MedInfo2019-QA-Medications question set tagged with
                          a binary `Risk_Level` label.
        * text column  : "Question"
        * label column : "Risk_Level" in {Critical, General}
    Class balance is imbalanced (~543 General / ~112 Critical).

MODEL
    TF-IDF (word unigram) features -> linear Support Vector Machine (SVC).
    Class imbalance is handled with SVM class_weight='balanced' (default). The
    paper's SMOTE-oversampling variant is available via --smote when
    imbalanced-learn is installed (it falls back to class_weight if not).
    Evaluation uses an 80/20 stratified split with a fixed seed (42).

METRICS
    Accuracy and macro-averaged F1 on the held-out 20% test split, printed as
    measured-vs-paper.

PAPER NUMBERS (SVM, best classical baseline; README Results table)
    Accuracy 0.84   Macro-F1 0.80
This is the paper's authentic-text baseline; the script aims to land near it.
CAVEAT: measured accuracy lands right at the paper value (~0.83), but macro-F1
    falls short of 0.80. The paper's classical baseline was trained with GPT-4.1
    synthetic `Critical` augmentation (to lift rare-class recall); that augmented
    set is NOT shipped here, so this authentic-text-only run cannot match the
    rare-class F1 the augmentation buys. With only ~22 Critical test items, a
    handful of errors swings macro-F1 substantially.

USAGE
    python reproduce.py            # full run (class_weight='balanced')
    python reproduce.py --smote    # use SMOTE oversampling instead
    python reproduce.py --smoke    # quick smoke test (subsampled, still deterministic)
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, classification_report

SEED = int(os.environ.get("REPRODUCE_SEED", "42"))
HERE = os.path.dirname(os.path.abspath(__file__))
DATA_XLSX = os.path.join(HERE, "labeled_data.xlsx")

TEXT_COL = "Question"
LABEL_COL = "Risk_Level"
POSITIVE = "Critical"  # rare / high-risk class

PAPER_ACC = 0.84
PAPER_F1 = 0.80


def load_data():
    df = pd.read_excel(DATA_XLSX)
    if TEXT_COL not in df.columns or LABEL_COL not in df.columns:
        raise SystemExit(
            f"Expected columns '{TEXT_COL}' and '{LABEL_COL}' in {DATA_XLSX}; "
            f"found {list(df.columns)}"
        )
    df = df[[TEXT_COL, LABEL_COL]].copy()
    df[TEXT_COL] = df[TEXT_COL].astype(str).str.strip()
    df[LABEL_COL] = df[LABEL_COL].astype(str).str.strip()
    # keep only the two valid labels, drop empties
    df = df[df[LABEL_COL].isin(["Critical", "General"])]
    df = df[df[TEXT_COL].str.len() > 0]
    df = df.dropna(subset=[TEXT_COL, LABEL_COL]).reset_index(drop=True)
    return df


def build_estimator(use_smote=False):
    """TF-IDF + linear SVM. Default handles imbalance with class_weight='balanced'
    (best here). --smote switches to SMOTE oversampling (the paper's variant)
    when imbalanced-learn is available, else falls back to class_weight."""
    tfidf = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 1),
        sublinear_tf=True,
        min_df=2,
        stop_words="english",
    )
    C = 5.0
    if use_smote:
        try:
            from imblearn.over_sampling import SMOTE
            from imblearn.pipeline import Pipeline as ImbPipeline

            svm = SVC(kernel="linear", C=C, random_state=SEED)
            est = ImbPipeline(
                steps=[
                    ("tfidf", tfidf),
                    ("smote", SMOTE(random_state=SEED, k_neighbors=5)),
                    ("svm", svm),
                ]
            )
            return est, "SMOTE + linear SVM (C=5)"
        except Exception:
            pass  # fall through to class_weight
    svm = SVC(kernel="linear", C=C, class_weight="balanced", random_state=SEED)
    est = Pipeline(steps=[("tfidf", tfidf), ("svm", svm)])
    return est, "linear SVM (C=5, class_weight='balanced')"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="quick deterministic smoke test on a stratified subsample",
    )
    ap.add_argument(
        "--smote",
        action="store_true",
        help="use SMOTE oversampling (paper variant) instead of class_weight",
    )
    args = ap.parse_args()

    np.random.seed(SEED)

    df = load_data()

    if args.smoke:
        # deterministic stratified subsample; keep both classes
        n = min(len(df), 240)
        df, _ = train_test_split(
            df, train_size=n, stratify=df[LABEL_COL], random_state=SEED
        )
        df = df.reset_index(drop=True)

    X = df[TEXT_COL].values
    y = df[LABEL_COL].values

    print(f"Loaded {len(df)} labeled questions"
          f" ({(y == 'General').sum()} General / {(y == 'Critical').sum()} Critical)")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )

    est, desc = build_estimator(use_smote=args.smote)
    print(f"Model: TF-IDF + {desc}")
    est.fit(X_tr, y_tr)
    y_pred = est.predict(X_te)

    acc = accuracy_score(y_te, y_pred)
    macro_f1 = f1_score(y_te, y_pred, average="macro")

    print()
    print("=" * 56)
    print("  Medication-Question Risk Classification -- results")
    print("=" * 56)
    print(f"  Test set: {len(y_te)} questions (20% stratified hold-out)")
    print()
    print(f"  {'metric':<12}{'measured':>12}{'paper (SVM)':>16}")
    print(f"  {'accuracy':<12}{acc:>12.3f}{PAPER_ACC:>16.2f}")
    print(f"  {'macro-F1':<12}{macro_f1:>12.3f}{PAPER_F1:>16.2f}")
    print("=" * 56)
    print()
    print("Per-class report:")
    print(classification_report(y_te, y_pred, digits=3, zero_division=0))

    RESULTS = {
        "svm_acc": round(float(acc), 4),
        "svm_macrof1": round(float(macro_f1), 4),
    }
    print("REPRODUCE_RESULT_JSON " + json.dumps(RESULTS))

    return acc, macro_f1


if __name__ == "__main__":
    main()
