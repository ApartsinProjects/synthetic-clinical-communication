"""Reproduce: 24-class disease classification from symptom self-descriptions.

WHAT THIS REPRODUCES
    The CLASSICAL baseline of the "diagnosis from noisy self-descriptions"
    case study: a Multinomial Naive Bayes classifier over TF-IDF features,
    trained and evaluated SEPARATELY at three text-noise levels (clean,
    medium, heavy). It RETRAINS and RE-EVALUATES on the already-shipped
    data; it does NOT regenerate data, call any LLM/API, or use the network.

DATA (already shipped, not regenerated)
    train_with_noise.csv -- 1200 rows, 24 disease classes (50 each).
      Columns:
        label        : disease name (target, 24 classes)
        text         : clean symptom self-description
        medium_noise : medium-noise (rambling/dialect) rewrite
        heavy_noise  : heavy-noise (very rambling, tangential) rewrite
      (Also present: an unnamed index column, ignored.)

MODEL
    TF-IDF (word 1-2 grams, English stopwords) -> Multinomial Naive Bayes,
    one independent pipeline per noise level. 80/20 stratified split,
    fixed seed (RANDOM_STATE = 42).

METRIC
    Top-1 accuracy on the held-out 20% test split, per noise level.

PAPER (Naive Bayes) TARGET NUMBERS
    clean  93.8%
    medium 79.2%
    heavy  77.5%

USAGE
    python reproduce.py            # full data (fast, CPU)
    python reproduce.py --smoke    # subsample ~200 rows, still runs

DEPENDENCIES
    scikit-learn, pandas, numpy   (no network, no LLM/API)
"""

import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

RANDOM_STATE = int(os.environ.get("REPRODUCE_SEED", "42"))
DATA_FILE = "train_with_noise.csv"

# noise level label -> source text column
NOISE_COLUMNS = {
    "clean": "text",
    "medium": "medium_noise",
    "heavy": "heavy_noise",
}

# paper Naive Bayes targets (fractions)
PAPER_TARGETS = {
    "clean": 0.938,
    "medium": 0.792,
    "heavy": 0.775,
}


def evaluate_noise_level(df, text_col, smoke=False):
    """Train + evaluate one MNB-over-TFIDF pipeline for a single text column."""
    X = df[text_col].astype(str).values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    stop_words="english",
                    sublinear_tf=True,
                ),
            ),
            ("clf", MultinomialNB()),
        ]
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    return accuracy_score(y_test, y_pred)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Subsample ~200 rows for a fast sanity run (still trains/evaluates).",
    )
    args = parser.parse_args()

    np.random.seed(RANDOM_STATE)

    df = pd.read_csv(DATA_FILE)

    if args.smoke:
        # Stratified-ish subsample to ~200 rows, keeping all 24 classes present.
        # Keep up to 9 rows per class (all 24 classes present) -> ~200 rows.
        keep = [
            g.sample(min(len(g), 9), random_state=RANDOM_STATE)
            for _, g in df.groupby("label")
        ]
        df = pd.concat(keep).reset_index(drop=True)
        print(f"[smoke] subsampled to {len(df)} rows across "
              f"{df['label'].nunique()} classes\n")

    print(f"Loaded {len(df)} rows, {df['label'].nunique()} classes "
          f"from {DATA_FILE}\n")

    print(f"{'Noise':<8} {'Measured':>10} {'Paper':>8}   Delta")
    print("-" * 40)
    measured = {}
    for level, col in NOISE_COLUMNS.items():
        acc = evaluate_noise_level(df, col, smoke=args.smoke)
        measured[level] = acc
        paper = PAPER_TARGETS[level]
        print(f"{level:<8} {acc * 100:>9.1f}% {paper * 100:>7.1f}%   "
              f"{(acc - paper) * 100:+.1f}%")

    RESULTS = {
        "nb_clean": round(float(measured["clean"]), 4),
        "nb_medium": round(float(measured["medium"]), 4),
        "nb_heavy": round(float(measured["heavy"]), 4),
    }
    print("REPRODUCE_RESULT_JSON " + json.dumps(RESULTS))


if __name__ == "__main__":
    main()
