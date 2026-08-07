#!/usr/bin/env python
"""
reproduce.py -- Clinical-priority triage of patient portal messages.

REPRODUCES
    The DistilBERT fine-tune baseline reported for the clinical-priority-portal-triage
    case study. This script RETRAINS and RE-EVALUATES on the ALREADY-SHIPPED synthetic
    data. There is NO data regeneration, NO LLM/API call, and NO network access at
    runtime (aside from the one-time HuggingFace download of the base model weights,
    which HF caches locally).

DATA
    synthetic_data.csv (FULL shipped dataset, 3000 rows). Columns:
        patient_id, age, past_medical_history, current_portal_message, clinical_priority
    Input text  : current_portal_message
    Label       : clinical_priority  -- 3 classes {LOW: 1200, MEDIUM: 1350, HIGH: 450}
    Split       : 80/20 stratified on the label, fixed seed.

MODEL
    distilbert-base-uncased fine-tuned for 3-way sequence classification via a SIMPLE
    manual PyTorch training loop (AdamW), not the HF Trainer.

METRIC
    Accuracy and macro-F1 on the held-out 20% test split.

PAPER NUMBER
    DistilBERT (fine-tuned) baseline: accuracy 0.817.
    On GPU with the full shipped data and a few epochs, the full run should land in that
    ballpark.

SAFETY-CASCADE NOTE (out of scope for this script)
    The paper's headline "master" system reaches accuracy ~0.997 by layering a SEPARATE
    safety cascade (a rule/keyword-driven escalation stage) ON TOP of the DistilBERT
    classifier. That cascade is intentionally NOT reproduced here: this script reproduces
    only the standalone fine-tuned DistilBERT baseline (0.817), not the 0.997 master.

USAGE
    python reproduce.py --smoke      # default: CPU, ~40 rows, ~2 steps, sanity check
    python reproduce.py --full       # GPU if available, full data, a few epochs
"""

import argparse
import random

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SEED = 42
MODEL_NAME = "distilbert-base-uncased"
DATA_CSV = "synthetic_data.csv"
TEXT_COL = "current_portal_message"
LABEL_COL = "clinical_priority"


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class TextDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--smoke", action="store_true",
                    help="Tiny CPU sanity run (~40 rows, ~2 steps). Default if no mode given.")
    ap.add_argument("--full", action="store_true",
                    help="Full run: GPU if available, full data, a few epochs.")
    args = ap.parse_args()

    # Default to smoke for safe verification.
    smoke = args.smoke or not args.full

    set_seed()

    if smoke:
        device = torch.device("cpu")
        n_rows = 40
        max_steps = 2
        epochs = 1
        batch_size = 8
        max_len = 64
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        n_rows = None          # full data
        max_steps = None       # no cap
        epochs = 3
        batch_size = 16
        max_len = 256

    print(f"[mode] {'SMOKE' if smoke else 'FULL'} | device={device}")

    # --- Load shipped data ---
    df = pd.read_csv(DATA_CSV)
    df = df[[TEXT_COL, LABEL_COL]].dropna().reset_index(drop=True)

    classes = sorted(df[LABEL_COL].unique())
    label2id = {c: i for i, c in enumerate(classes)}
    id2label = {i: c for c, i in label2id.items()}
    df["y"] = df[LABEL_COL].map(label2id)
    print(f"[data] {len(df)} rows | classes={classes}")

    if smoke:
        # Take a small stratified-ish subset for the smoke test.
        df = (df.groupby("y", group_keys=False)
                .apply(lambda g: g.sample(min(len(g), max(4, n_rows // len(classes))),
                                          random_state=SEED))
                .reset_index(drop=True))
        print(f"[data] smoke subset: {len(df)} rows")

    texts = df[TEXT_COL].astype(str).tolist()
    labels = df["y"].tolist()

    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, labels, test_size=0.2, random_state=SEED, stratify=labels
    )
    print(f"[split] train={len(X_tr)} test={len(X_te)}")

    # --- Tokenize ---
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def encode(text_list):
        return tokenizer(text_list, truncation=True, padding="max_length",
                         max_length=max_len, return_tensors="pt")

    train_ds = TextDataset(encode(X_tr), y_tr)
    test_ds = TextDataset(encode(X_te), y_te)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    # --- Model ---
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(classes), id2label=id2label, label2id=label2id
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

    # --- Train (manual loop) ---
    model.train()
    step = 0
    for epoch in range(epochs):
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            optimizer.zero_grad()
            out = model(**batch)
            out.loss.backward()
            optimizer.step()
            step += 1
            if step % 10 == 0 or (smoke and step <= max_steps):
                print(f"[train] epoch={epoch} step={step} loss={out.loss.item():.4f}")
            if max_steps is not None and step >= max_steps:
                break
        if max_steps is not None and step >= max_steps:
            break

    # --- Evaluate ---
    model.eval()
    preds, golds = [], []
    with torch.no_grad():
        for batch in test_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            logits = model(**batch).logits
            preds.extend(logits.argmax(dim=-1).cpu().numpy().tolist())
            golds.extend(batch["labels"].cpu().numpy().tolist())

    acc = accuracy_score(golds, preds)
    macro_f1 = f1_score(golds, preds, average="macro")

    print("=" * 50)
    print(f"RESULT ({'SMOKE' if smoke else 'FULL'})")
    print(f"  accuracy  = {acc:.4f}")
    print(f"  macro-F1  = {macro_f1:.4f}")
    if not smoke:
        print("  paper DistilBERT baseline accuracy = 0.817")
    print("=" * 50)


if __name__ == "__main__":
    main()
