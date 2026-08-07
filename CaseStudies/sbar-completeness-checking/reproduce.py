"""Reproduce: SBAR handover note-level completeness classification (TF-IDF + LogReg).

WHAT THIS REPRODUCES
    The note-level completeness classifier from the SBAR case study. Each SBAR
    handover note is labeled with a completeness class (high / medium / low) and
    a bag-of-words TF-IDF Logistic Regression model predicts that class from the
    note text alone. This is the paper's `tfidf_note_class` baseline.

DATA (already-shipped sample; no regeneration, no LLM/API, no network)
    modeling_dataset.sample.csv -- a 200-row SAMPLE (199 usable rows) of the full
    modeling dataset. Text column: `model_text` (the SBAR note). Label column:
    `completeness_class` (high / medium / low). All training and evaluation here
    run ONLY on this shipped sample.

MODEL
    TfidfVectorizer (word 1-2 grams) -> LogisticRegression (multinomial, lbfgs),
    trained on an 80/20 stratified split with fixed seed. CPU only.

METRIC
    Accuracy and macro-F1 on the held-out 20% test split.

PAPER NUMBERS (full-data, grouped test set `grouped_test_all_741`,
    from final_model_comparison.csv, model `tfidf_note_class`):
        accuracy = 0.725,  macro-F1 = 0.711
    NOTE: this script runs on the 200-row SAMPLE, so the measured numbers are
    computed on a tiny sample and are expected to DIFFER from the full-data paper
    values. The point is to show the pipeline reproduces end-to-end on shipped data.

USAGE
    python reproduce.py           # default: full shipped sample (199 rows)
    python reproduce.py --smoke   # fast subset for a quick smoke test

DEPENDENCIES
    scikit-learn, pandas, numpy
"""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

SEED = 42
DATA_FILE = "modeling_dataset.sample.csv"

# Paper baseline (tfidf_note_class, full grouped test set of 741 notes)
PAPER_ACC = 0.725
PAPER_MACRO_F1 = 0.711


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run on a small subset for a fast smoke test.",
    )
    args = parser.parse_args()

    np.random.seed(SEED)

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, DATA_FILE)
    df = pd.read_csv(path)

    text_col = "model_text"
    label_col = "completeness_class"
    df = df[[text_col, label_col]].dropna().reset_index(drop=True)

    if args.smoke:
        # Small stratified subset for a quick run.
        df, _ = train_test_split(
            df,
            train_size=min(80, len(df) - 1),
            stratify=df[label_col],
            random_state=SEED,
        )
        df = df.reset_index(drop=True)

    X = df[text_col].values
    y = df[label_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED
    )

    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=SEED,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")

    mode = "SMOKE (subset)" if args.smoke else "SAMPLE (full shipped 200-row sample)"
    print("=" * 68)
    print("SBAR note-level completeness classification -- TF-IDF + LogReg")
    print("=" * 68)
    print(f"Mode                : {mode}")
    print(f"Rows used           : {len(df)}  (train={len(X_train)}, test={len(X_test)})")
    print(f"Classes             : {sorted(set(y))}")
    print("-" * 68)
    print(f"Measured accuracy   : {acc:.3f}")
    print(f"Measured macro-F1   : {macro_f1:.3f}")
    print("-" * 68)
    print(f"Paper accuracy      : {PAPER_ACC:.3f}   (tfidf_note_class, full data)")
    print(f"Paper macro-F1      : {PAPER_MACRO_F1:.3f}   (tfidf_note_class, full data)")
    print(f"Delta accuracy      : {acc - PAPER_ACC:+.3f}")
    print(f"Delta macro-F1      : {macro_f1 - PAPER_MACRO_F1:+.3f}")
    print("=" * 68)
    print(
        "NOTE: numbers above are computed on the 200-row SAMPLE shipped in this\n"
        "      directory, not the full dataset. They are expected to DIFFER from\n"
        "      the full-data paper values (accuracy 0.725, macro-F1 0.711)."
    )


if __name__ == "__main__":
    main()
