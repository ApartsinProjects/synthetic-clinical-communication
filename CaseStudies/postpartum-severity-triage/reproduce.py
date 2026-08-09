"""
Reproduce: Postpartum message severity triage (Bi-LSTM cascade), from scratch.

WHAT THIS REPRODUCES
--------------------
The from-scratch Bi-LSTM cascade for triaging postpartum patient/caregiver
messages into severity levels 0-3, using the ALREADY-SHIPPED dataset. There is
NO data regeneration, NO LLM/API call, and NO network access. The script only
re-trains and re-evaluates on the shipped file.

DATA
----
`dataset.xlsx` (shipped, in this directory). Free text lives in the
`patient_message` column; the ordinal severity label (0,1,2,3) lives in the
`triage_level` column. A handful of rows are column-shift artifacts (stray
non-numeric labels); those are filtered out, leaving ~2996 clean messages
roughly balanced across the four levels.

Severity semantics: 0 = routine, 1-3 = urgent with increasing severity.

MODEL (Bi-LSTM cascade)
-----------------------
A whitespace/lowercase tokenizer builds a vocabulary from the TRAIN split only.
Two independent PyTorch Bi-LSTM classifiers (embedding_dim=128, hidden_dim=64,
bidirectional) form a cascade:

  Stage 1 (binary, BCEWithLogitsLoss): routine (level 0) vs urgent (levels 1-3).
  Stage 2 (3-way, CrossEntropyLoss):   severity 1 vs 2 vs 3, trained on the
                                        urgent messages only.

Inference: Stage 1 decides routine/urgent. If routine -> predicted level 0.
If urgent -> Stage 2 assigns the 1-3 severity. Combining the two gives a full
0-3 prediction.

CPU-trainable: this is a small Bi-LSTM (no pretrained-weight download). The
BioBERT cascade reported in the paper needs a GPU and is NOT reproduced here.

METRICS PRINTED
---------------
  Stage-1 accuracy and macro-F1 (routine vs urgent).
  Stage-2 accuracy and macro-F1 (severity 1-3, on true-urgent messages).
  Full 0-3 accuracy and macro-F1 (end-to-end cascade).

PAPER NUMBERS (Bi-LSTM)
-----------------------
  Stage-1 accuracy 0.981 / macro-F1 0.974
  Stage-2 severity ~0.807
Full data is shipped, so the full run aims near these figures.

USAGE
-----
  python reproduce.py --smoke   # fast CPU check: ~60 rows, 1-2 epochs (default)
  python reproduce.py           # full run: all rows, more epochs (CPU is fine)
"""

import argparse
import json
import os
import random

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.nn.utils.rnn import pad_sequence

SEED = int(os.environ.get("REPRODUCE_SEED", "12345"))
DATA_FILE = "dataset.xlsx"
TEXT_COL = "patient_message"
LABEL_COL = "triage_level"
PAD, UNK = 0, 1


def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_clean():
    df = pd.read_excel(DATA_FILE)
    df["_lab"] = pd.to_numeric(df[LABEL_COL], errors="coerce")
    mask = df[TEXT_COL].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)
    mask &= df["_lab"].isin([0, 1, 2, 3])
    df = df[mask].copy()
    texts = df[TEXT_COL].astype(str).tolist()
    labels = df["_lab"].astype(int).tolist()
    return texts, labels


def tokenize(text):
    return text.lower().split()


def build_vocab(texts, min_freq=1):
    from collections import Counter

    counter = Counter()
    for t in texts:
        counter.update(tokenize(t))
    vocab = {"<pad>": PAD, "<unk>": UNK}
    for tok, c in counter.items():
        if c >= min_freq:
            vocab[tok] = len(vocab)
    return vocab


def encode(text, vocab, max_len=200):
    ids = [vocab.get(tok, UNK) for tok in tokenize(text)][:max_len]
    if not ids:
        ids = [UNK]
    return torch.tensor(ids, dtype=torch.long)


class BiLSTM(nn.Module):
    def __init__(self, vocab_size, num_out, embedding_dim=128, hidden_dim=64):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, embedding_dim, padding_idx=PAD)
        self.lstm = nn.LSTM(
            embedding_dim, hidden_dim, batch_first=True, bidirectional=True
        )
        self.fc = nn.Linear(hidden_dim * 2, num_out)

    def forward(self, x, lengths):
        e = self.emb(x)
        packed = nn.utils.rnn.pack_padded_sequence(
            e, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, (h, _) = self.lstm(packed)
        h = torch.cat([h[-2], h[-1]], dim=1)  # concat both directions
        return self.fc(h)


def make_batches(seqs, ys, batch_size, shuffle=True):
    idx = list(range(len(seqs)))
    if shuffle:
        random.shuffle(idx)
    for i in range(0, len(idx), batch_size):
        chunk = idx[i : i + batch_size]
        batch = [seqs[j] for j in chunk]
        lengths = torch.tensor([len(s) for s in batch], dtype=torch.long)
        padded = pad_sequence(batch, batch_first=True, padding_value=PAD)
        yb = torch.tensor([ys[j] for j in chunk])
        yield padded, lengths, yb


def train_model(model, seqs, ys, epochs, lr, batch_size, loss_fn, device, binary=False):
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    model.train()
    for ep in range(epochs):
        total = 0.0
        for padded, lengths, yb in make_batches(seqs, ys, batch_size):
            padded, yb = padded.to(device), yb.to(device)
            opt.zero_grad()
            logits = model(padded, lengths)
            if binary:
                loss = loss_fn(logits.squeeze(1), yb.float())
            else:
                loss = loss_fn(logits, yb)
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"    epoch {ep+1}/{epochs}  loss={total:.4f}")
    return model


@torch.no_grad()
def predict(model, seqs, device, binary=False):
    model.eval()
    preds = []
    order = list(range(len(seqs)))
    for i in range(0, len(order), 64):
        chunk = order[i : i + 64]
        batch = [seqs[j] for j in chunk]
        lengths = torch.tensor([len(s) for s in batch], dtype=torch.long)
        padded = pad_sequence(batch, batch_first=True, padding_value=PAD).to(device)
        logits = model(padded, lengths)
        if binary:
            preds.extend((torch.sigmoid(logits.squeeze(1)) >= 0.5).long().cpu().tolist())
        else:
            preds.extend(logits.argmax(1).cpu().tolist())
    return preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="fast CPU check: ~60 rows, 1-2 epochs (default behaviour)")
    ap.add_argument("--full", action="store_true", help="full run on all rows")
    args = ap.parse_args()
    smoke = not args.full  # smoke is the default for verification

    set_seed()
    device = torch.device("cpu")  # small Bi-LSTM; CPU is fine

    texts, labels = load_clean()
    print(f"Loaded {len(texts)} clean messages (levels 0-3).")

    # deterministic 80/20 split
    idx = list(range(len(texts)))
    random.Random(SEED).shuffle(idx)
    texts = [texts[i] for i in idx]
    labels = [labels[i] for i in idx]

    if smoke:
        texts, labels = texts[:60], labels[:60]
        epochs, batch_size = 2, 8
        print("[SMOKE] 60 rows, 2 epochs.")
    else:
        epochs, batch_size = 12, 32
        print(f"[FULL] {len(texts)} rows, {epochs} epochs.")

    n_test = max(1, int(0.2 * len(texts)))
    tr_texts, te_texts = texts[:-n_test], texts[-n_test:]
    tr_labels, te_labels = labels[:-n_test], labels[-n_test:]

    vocab = build_vocab(tr_texts)
    print(f"Vocab size: {len(vocab)}  |  train={len(tr_texts)} test={len(te_texts)}")

    tr_seqs = [encode(t, vocab) for t in tr_texts]
    te_seqs = [encode(t, vocab) for t in te_texts]

    # ---- Stage 1: routine (0) vs urgent (1-3) ----
    tr_bin = [0 if y == 0 else 1 for y in tr_labels]
    te_bin = [0 if y == 0 else 1 for y in te_labels]
    print("\n== Stage 1 (routine vs urgent) ==")
    s1 = BiLSTM(len(vocab), num_out=1)
    train_model(s1, tr_seqs, tr_bin, epochs, 1e-3, batch_size,
                nn.BCEWithLogitsLoss(), device, binary=True)
    s1_pred = predict(s1, te_seqs, device, binary=True)
    s1_acc = accuracy_score(te_bin, s1_pred)
    s1_f1 = f1_score(te_bin, s1_pred, average="macro", zero_division=0)

    # ---- Stage 2: severity 1-3 (trained on urgent messages only) ----
    ur_idx = [i for i, y in enumerate(tr_labels) if y != 0]
    ur_seqs = [tr_seqs[i] for i in ur_idx]
    ur_lab = [tr_labels[i] - 1 for i in ur_idx]  # map 1,2,3 -> 0,1,2
    print("\n== Stage 2 (severity 1-3, urgent only) ==")
    s2 = BiLSTM(len(vocab), num_out=3)
    if len(set(ur_lab)) >= 2:
        train_model(s2, ur_seqs, ur_lab, epochs, 1e-3, batch_size,
                    nn.CrossEntropyLoss(), device)
    else:
        print("    (too few urgent classes in smoke split; skipping training)")

    # Stage-2 metrics on TRUE-urgent test messages
    te_ur_idx = [i for i, y in enumerate(te_labels) if y != 0]
    if te_ur_idx:
        te_ur_seqs = [te_seqs[i] for i in te_ur_idx]
        te_ur_true = [te_labels[i] for i in te_ur_idx]
        s2_pred_raw = predict(s2, te_ur_seqs, device)
        s2_pred = [p + 1 for p in s2_pred_raw]
        s2_acc = accuracy_score(te_ur_true, s2_pred)
        s2_f1 = f1_score(te_ur_true, s2_pred, average="macro", zero_division=0)
    else:
        s2_acc = s2_f1 = float("nan")

    # ---- Full 0-3 cascade ----
    full_pred = []
    s2_all_raw = predict(s2, te_seqs, device)
    for i in range(len(te_seqs)):
        if s1_pred[i] == 0:
            full_pred.append(0)          # routine
        else:
            full_pred.append(s2_all_raw[i] + 1)  # urgent severity 1-3
    full_acc = accuracy_score(te_labels, full_pred)
    full_f1 = f1_score(te_labels, full_pred, average="macro", zero_division=0)

    print("\n================ RESULTS ================")
    print(f"Stage-1 (routine vs urgent):  acc={s1_acc:.3f}  macroF1={s1_f1:.3f}")
    print(f"Stage-2 (severity 1-3):       acc={s2_acc:.3f}  macroF1={s2_f1:.3f}")
    print(f"Full 0-3 cascade:             acc={full_acc:.3f}  macroF1={full_f1:.3f}")
    print("-----------------------------------------")
    print("Paper Bi-LSTM: Stage-1 acc 0.981 / macroF1 0.974 ; Stage-2 severity ~0.807")
    print("(BioBERT cascade needs GPU; not reproduced here.)")
    if smoke:
        print("[SMOKE] cascade trained + evaluated end-to-end. Run without --smoke "
              "(use --full) for near-paper numbers.")

    RESULTS = {
        "bilstm_acc": round(float(full_acc), 4),
        "bilstm_macrof1": round(float(full_f1), 4),
    }
    print("REPRODUCE_RESULT_JSON " + json.dumps(RESULTS))


if __name__ == "__main__":
    main()
