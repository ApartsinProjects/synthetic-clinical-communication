"""
reproduce.py -- Urgency triage from first-person complaint text (binary).

WHAT THIS REPRODUCES
    Binary emergency-room urgency triage (urgent=1 / non-urgent=0) from
    first-person free-text patient complaints. Retrains and re-evaluates the
    paper's TF-IDF + Logistic Regression baseline on ALREADY-SHIPPED synthetic
    data. No data regeneration, no LLM/API calls, no network access.

DATA (NOTE: SAMPLE)
    synthetic_data.sample.csv -- a 200-row SAMPLE (199 usable rows) of the full
    synthetic set used in the paper. Free-text column: `text_input`. Binary
    label column: `label` (0 = non-urgent, 1 = urgent). Because this is only a
    small sample, the measured numbers WILL DIFFER from the full-data paper
    values reported below; that is expected.

MODEL
    TF-IDF (word 1-2 grams) -> LogisticRegression. 80/20 stratified split,
    fixed random seed (42).

METRIC
    Accuracy and binary F1 (positive class = urgent).

PAPER NUMBERS (TF-IDF + LR, computed on the FULL synthetic set)
    accuracy = 0.8101, F1 = 0.6530

USAGE
    /c/Python314/python reproduce.py            # shipped 200-row sample
    /c/Python314/python reproduce.py --smoke    # further subsample (fast check)
"""

import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

SEED = int(os.environ.get("REPRODUCE_SEED", "42"))
TEXT_COL = "text_input"
LABEL_COL = "label"
DATA_FILE = "synthetic_data.sample.csv"

# Paper targets (full synthetic set)
PAPER_ACC = 0.8101
PAPER_F1 = 0.6530


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce TF-IDF + LR binary urgency triage on shipped sample."
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Further subsample the shipped sample for a fast smoke test.",
    )
    args = parser.parse_args()

    np.random.seed(SEED)

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, DATA_FILE)
    df = pd.read_csv(path)
    df = df.dropna(subset=[TEXT_COL, LABEL_COL]).reset_index(drop=True)
    df[LABEL_COL] = df[LABEL_COL].astype(int)

    if args.smoke:
        # Further subsample (stratified) for a quick check.
        df, _ = train_test_split(
            df,
            train_size=min(120, len(df)),
            stratify=df[LABEL_COL],
            random_state=SEED,
        )
        df = df.reset_index(drop=True)

    X = df[TEXT_COL].astype(str).values
    y = df[LABEL_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )

    clf = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=SEED)),
        ]
    )
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, pos_label=1)

    print("=" * 68)
    print("Urgency triage (binary) -- TF-IDF + LogisticRegression")
    print("=" * 68)
    print(f"Data file      : {DATA_FILE}"
          + ("  [--smoke: further subsampled]" if args.smoke else ""))
    print(f"Rows used      : {len(df)}  (train={len(X_train)}, test={len(X_test)})")
    print(f"Class balance  : non-urgent={int((y == 0).sum())}, urgent={int((y == 1).sum())}")
    print("-" * 68)
    print(f"{'Metric':<12}{'Measured (sample)':>20}{'Paper (full)':>18}")
    print(f"{'Accuracy':<12}{acc:>20.4f}{PAPER_ACC:>18.4f}")
    print(f"{'F1 (urgent)':<12}{f1:>20.4f}{PAPER_F1:>18.4f}")
    print("=" * 68)
    print("NOTE: Numbers above are computed on the SHIPPED 200-row SAMPLE, not")
    print("the full synthetic set. They will differ from the full-data paper")
    print("values (acc 0.8101, F1 0.6530); the sample is provided for a")
    print("self-contained, network-free reproducibility check only.")

    RESULTS = {
        "lr_acc": round(float(acc), 4),
        "lr_f1": round(float(f1), 4),
    }
    print("REPRODUCE_RESULT_JSON " + json.dumps(RESULTS))


if __name__ == "__main__":
    main()
