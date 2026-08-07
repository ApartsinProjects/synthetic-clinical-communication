#!/usr/bin/env python
"""
reproduce.py -- Retrain and re-evaluate the lexical (TF-IDF) baselines for the
oncology synthetic-patient-message case study, using ONLY already-shipped data.

WHAT THIS REPRODUCES
    The paper's "best lexical" baseline: a TF-IDF featurizer feeding a
    class-weighted multinomial Logistic Regression, reported as macro-F1 on two
    tasks over synthetic oncology patient messages:
        * response : 7-class emotional-response classification
                     (anxiety, anger, hope, guilt, sadness, denial, acceptance)
        * distress : 3-level ordinal distress classification (low, medium, high)

DATA (note: TRAIN IS A 200-ROW SAMPLE)
    Trains on ./train.sample.jsonl  -- a 200-row SAMPLE of the full train split
                                       that ships with this case study.
    Evaluates on ./test.jsonl.
    Text field   : "text"
    Label fields : "final_response" (7-class) and "final_distress" (3-level).
    NO data is regenerated; NO LLM / API / network is used. Pure CPU sklearn.
    Because only a 200-row train sample is shipped (and it does not even contain
    all 7 response classes), the numbers printed here are computed ON THE SAMPLE
    and WILL DIFFER from the full-data paper values below.

MODEL
    TfidfVectorizer (word 1-2 grams) -> LogisticRegression(class_weight="balanced").
    Deterministic: fixed random_state / seeds.

METRIC
    Macro-averaged F1 (sklearn f1_score, average="macro"), per task.

PAPER NUMBERS (full-data best lexical / TF-IDF)
    response macro-F1 : 0.856
    distress macro-F1 : 0.805

USAGE
    python reproduce.py            # full 200-row sample train, test.jsonl eval
    python reproduce.py --smoke    # quick smoke run (subsampled, smaller model)
"""

import argparse
import json
import os
import random

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_FILE = os.path.join(HERE, "train.sample.jsonl")
TEST_FILE = os.path.join(HERE, "test.jsonl")
TEXT_FIELD = "text"

# task name -> label field in the JSONL
TASKS = {
    "response (7-class)": "final_response",
    "distress (3-level)": "final_distress",
}
PAPER = {
    "response (7-class)": 0.856,
    "distress (3-level)": 0.805,
}


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_xy(rows, label_field):
    """Return (texts, labels) keeping only rows with non-empty text and label."""
    xs, ys = [], []
    for r in rows:
        text = r.get(TEXT_FIELD)
        label = r.get(label_field)
        if text and label is not None:
            xs.append(text)
            ys.append(label)
    return xs, ys


def make_model(smoke):
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 1) if smoke else (1, 2),
            min_df=1,
            sublinear_tf=True,
            max_features=2000 if smoke else 50000,
        )),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=200 if smoke else 1000,
            C=1.0,
            random_state=SEED,
        )),
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true",
                        help="Fast smoke run (subsample + smaller model).")
    args = parser.parse_args()

    random.seed(SEED)
    np.random.seed(SEED)

    train_rows = load_jsonl(TRAIN_FILE)
    test_rows = load_jsonl(TEST_FILE)

    if args.smoke:
        random.Random(SEED).shuffle(train_rows)
        train_rows = train_rows[:80]

    print("=" * 68)
    print("Oncology synthetic patient messages -- lexical (TF-IDF) baseline")
    print("=" * 68)
    print(f"Mode            : {'SMOKE' if args.smoke else 'full'}")
    print(f"Train file      : {os.path.basename(TRAIN_FILE)}  "
          f"(rows used: {len(train_rows)})")
    print(f"Test file       : {os.path.basename(TEST_FILE)}   "
          f"(rows: {len(test_rows)})")
    print("Model           : TF-IDF + class-weighted LogisticRegression")
    print("Metric          : macro-F1")
    print("-" * 68)
    print("NOTE: training data shipped is a 200-row SAMPLE of the full train")
    print("split, so these macro-F1 numbers are computed ON THE SAMPLE and will")
    print("DIFFER from the full-data paper values.")
    print("-" * 68)

    for task_name, label_field in TASKS.items():
        if label_field not in train_rows[0] and label_field not in test_rows[0]:
            print(f"[skip] {task_name}: label '{label_field}' absent.")
            continue

        Xtr, ytr = build_xy(train_rows, label_field)
        Xte, yte = build_xy(test_rows, label_field)
        if not Xtr or not Xte:
            print(f"[skip] {task_name}: no usable rows for '{label_field}'.")
            continue

        model = make_model(args.smoke)
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        macro_f1 = f1_score(yte, pred, average="macro")

        paper = PAPER.get(task_name)
        n_tr_cls = len(set(ytr))
        n_te_cls = len(set(yte))
        print(f"\nTask: {task_name}")
        print(f"  train classes seen : {n_tr_cls}   test classes : {n_te_cls}")
        print(f"  measured macro-F1  : {macro_f1:.3f}   (on 200-row sample)")
        print(f"  paper  macro-F1    : {paper:.3f}   (full-data best lexical)")
        print(f"  delta (measured-paper): {macro_f1 - paper:+.3f}")

    print("\n" + "=" * 68)
    print("Reminder: sample-trained numbers are expected to be LOWER than the")
    print("full-data paper values (0.856 response / 0.805 distress).")
    print("=" * 68)


if __name__ == "__main__":
    main()
