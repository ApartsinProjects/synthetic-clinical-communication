#!/usr/bin/env python
"""
Reproduce: 3-class home-care status detection (no change / improvement / deterioration).

WHAT THIS REPRODUCES
    The home-care status-detection case study: predict the clinical `change` label
    for a patient from two consecutive daily self-report messages (+ age). This is
    a text-only reproduction of the paper's TF-IDF + gradient-boosting fusion model.

DATA (already shipped, no regeneration, no LLM, no network)
    synthetic_data.csv (699 rows). Columns:
        patient_id, age, gender, diagnosis, change (label),
        day1_note, day2_note, reasoning.
    Label `change` classes: no change (260), improvement (220), deterioration (219).
    NOTE ON VITALS: the paper's best model fuses STRUCTURED numeric vitals
    (HR, BP, Temp, RR). The shipped CSV has no separate numeric vital columns;
    the vitals appear only as free text inside day1_note/day2_note (e.g.
    "Vitals: HR: 80, BP: 130/85, Temp: 36.8C, RR: 20."). We therefore reproduce a
    TEXT-BASED APPROXIMATION of the fusion model: TF-IDF over the concatenated
    notes (which incidentally contains the vitals as tokens) plus `age` as a
    numeric feature. A text-only reproduction may differ from the paper's best,
    which had the vitals as clean structured features.

MODEL
    LightGBM classifier over TF-IDF(word 1-2 grams) of day1_note + day2_note,
    with `age` appended as a numeric column. 80/20 stratified split, fixed seed.
    Falls back to sklearn GradientBoostingClassifier if lightgbm is unavailable.

METRIC
    Accuracy and macro-F1 on the held-out 20% test split.

PAPER NUMBERS (best: LightGBM + TF-IDF fusion incl. structured vitals)
    accuracy 0.971, macro-F1 0.972.

USAGE
    python reproduce.py            # full dataset
    python reproduce.py --smoke    # ~150-row subsample (fast smoke test)
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

SEED = 42
PAPER_ACC = 0.971
PAPER_MACRO_F1 = 0.972
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_data.csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true",
                    help="subsample ~150 rows for a fast run")
    args = ap.parse_args()

    df = pd.read_csv(DATA)
    if args.smoke:
        n = min(150, len(df))
        df = df.groupby("change", group_keys=False).apply(
            lambda g: g.sample(max(1, int(round(n * len(g) / len(df)))),
                               random_state=SEED)
        ).reset_index(drop=True)
        print(f"[smoke] subsampled to {len(df)} rows")

    text = (df["day1_note"].fillna("") + " " + df["day2_note"].fillna("")).values
    y = df["change"].values

    X_tr_txt, X_te_txt, y_tr, y_te, idx_tr, idx_te = train_test_split(
        text, y, df.index, test_size=0.20, stratify=y, random_state=SEED
    )

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    Xtr = vec.fit_transform(X_tr_txt)
    Xte = vec.transform(X_te_txt)

    # append age as a numeric feature if present
    if "age" in df.columns:
        age_tr = csr_matrix(df.loc[idx_tr, "age"].fillna(df["age"].median())
                            .values.reshape(-1, 1).astype(float))
        age_te = csr_matrix(df.loc[idx_te, "age"].fillna(df["age"].median())
                            .values.reshape(-1, 1).astype(float))
        Xtr = hstack([Xtr, age_tr]).tocsr()
        Xte = hstack([Xte, age_te]).tocsr()

    try:
        from lightgbm import LGBMClassifier
        clf = LGBMClassifier(n_estimators=400, learning_rate=0.05,
                             num_leaves=31, random_state=SEED, n_jobs=-1,
                             verbose=-1)
        model_name = "LightGBM"
    except Exception as e:
        from sklearn.ensemble import GradientBoostingClassifier
        clf = GradientBoostingClassifier(random_state=SEED)
        model_name = "sklearn GradientBoostingClassifier (lightgbm fallback)"
        print(f"[fallback] lightgbm import failed ({e!r}); using {model_name}")

    clf.fit(Xtr, y_tr)
    pred = clf.predict(Xte)

    acc = accuracy_score(y_te, pred)
    mf1 = f1_score(y_te, pred, average="macro")

    print(f"\nModel: {model_name} + TF-IDF(1-2 grams) fusion (text + age)")
    print(f"Train/test: {Xtr.shape[0]}/{Xte.shape[0]} rows, "
          f"{Xtr.shape[1]} features")
    print("-" * 60)
    print(f"{'':20s}{'measured':>12s}{'paper best':>14s}")
    print(f"{'accuracy':20s}{acc:>12.3f}{PAPER_ACC:>14.3f}")
    print(f"{'macro-F1':20s}{mf1:>12.3f}{PAPER_MACRO_F1:>14.3f}")
    print("-" * 60)
    print("Caveat: the paper's best fuses STRUCTURED vitals (HR/BP/Temp/RR) as")
    print("clean numeric features. The shipped CSV carries vitals only as free")
    print("text inside the notes, so this text-only approximation may differ.")


if __name__ == "__main__":
    main()
