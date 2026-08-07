"""Reproduce: administrative patient-portal message triage, DistilBERT urgency head.

Reproduces
    The headline urgency model of the "administrative-portal-message-triage" case
    study: a fine-tuned DistilBERT 3-class urgency classifier (Green / Yellow / Red).
    RETRAINS and RE-EVALUATES on already-shipped data only. No data regeneration,
    no LLM / API calls, no network access (models are loaded from the local HF cache;
    run once online beforehand if the base model is not yet cached).

Data (note: SAMPLE)
    Train : sample.jsonl  -- a small SHIPPED SAMPLE of the training set
                             (the paper's full model was trained on far more rows,
                             so the numbers printed here will differ from the paper).
    Test  : test.jsonl
    Each row: {"task_id", "text", "labels": {"urgency_level": "Green|Yellow|Red", ...}}
    Input field  : text
    Label field  : labels.urgency_level  (mapped Green=0, Yellow=1, Red=2)

Model
    distilbert-base-uncased fine-tuned with a sequence-classification head
    (num_labels=3), trained with a simple manual PyTorch loop (tokenizer +
    AutoModelForSequenceClassification + AdamW + a few epochs).

Metric
    Accuracy and macro-F1 on test.jsonl (scikit-learn).

Paper numbers (DistilBERT urgency, full data)
    accuracy 0.810, macro-F1 0.810
    (Reproduced numbers WILL differ: training here uses a small shipped SAMPLE.)

Usage
    python reproduce.py --smoke   # CPU, ~40 rows, <=2 steps -- just checks the loop
    python reproduce.py           # GPU if available, all shipped rows, a few epochs
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch.optim import AdamW
from transformers import AutoModelForSequenceClassification, AutoTokenizer

HERE = Path(__file__).resolve().parent
TRAIN_PATH = HERE / "sample.jsonl"
TEST_PATH = HERE / "test.jsonl"

MODEL_NAME = "distilbert-base-uncased"
MAX_LENGTH = 160
URGENCY_TO_ID = {"Green": 0, "Yellow": 1, "Red": 2}
ID_TO_URGENCY = {v: k for k, v in URGENCY_TO_ID.items()}

PAPER_ACCURACY = 0.810
PAPER_MACRO_F1 = 0.810


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rows.append(
                {
                    "text": obj["text"],
                    "label": URGENCY_TO_ID[obj["labels"]["urgency_level"]],
                }
            )
    return rows


def batched(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def encode(tokenizer, texts: list[str], device: torch.device):
    enc = tokenizer(
        texts,
        truncation=True,
        max_length=MAX_LENGTH,
        padding=True,
        return_tensors="pt",
    )
    return {k: v.to(device) for k, v in enc.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Tiny CPU run: ~40 rows, <=2 optimizer steps, just verifies the loop.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    args = parser.parse_args()

    set_seed(args.seed)
    # No dataset regeneration and no LLM/API calls. The only remote fetch that
    # can occur is the pretrained distilbert-base-uncased checkpoint, which is a
    # required input to fine-tuning; once it is in the local HF cache the script
    # runs fully offline. Set HF_HUB_OFFLINE=1 in the environment to force cache-only.

    if args.smoke:
        device = torch.device("cpu")
        epochs = 1
        batch_size = 8
        max_steps = 2
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        epochs = args.epochs
        batch_size = args.batch_size
        max_steps = None

    train_rows = load_rows(TRAIN_PATH)
    test_rows = load_rows(TEST_PATH)

    if args.smoke:
        # Cap total rows to ~40 to keep the CPU smoke run fast.
        train_rows = train_rows[:20]
        test_rows = test_rows[:20]

    print(
        f"[config] smoke={args.smoke} device={device} epochs={epochs} "
        f"batch_size={batch_size} train_rows={len(train_rows)} test_rows={len(test_rows)}"
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(URGENCY_TO_ID),
        id2label=ID_TO_URGENCY,
        label2id=URGENCY_TO_ID,
    )
    model.to(device)

    optimizer = AdamW(model.parameters(), lr=args.learning_rate)

    # ---- Training loop (manual) ----
    model.train()
    step = 0
    stop = False
    for epoch in range(epochs):
        random.shuffle(train_rows)
        epoch_loss = 0.0
        n_batches = 0
        for batch in batched(train_rows, batch_size):
            inputs = encode(tokenizer, [r["text"] for r in batch], device)
            labels = torch.tensor([r["label"] for r in batch], device=device)
            optimizer.zero_grad()
            out = model(**inputs, labels=labels)
            out.loss.backward()
            optimizer.step()
            epoch_loss += float(out.loss.detach())
            n_batches += 1
            step += 1
            if max_steps is not None and step >= max_steps:
                stop = True
                break
        avg = epoch_loss / max(n_batches, 1)
        print(f"[train] epoch {epoch + 1}/{epochs} avg_loss={avg:.4f} steps={step}")
        if stop:
            print(f"[train] smoke step cap reached ({max_steps}); stopping.")
            break

    # ---- Evaluation ----
    model.eval()
    preds: list[int] = []
    gold: list[int] = []
    with torch.no_grad():
        for batch in batched(test_rows, batch_size):
            inputs = encode(tokenizer, [r["text"] for r in batch], device)
            logits = model(**inputs).logits
            preds.extend(torch.argmax(logits, dim=-1).cpu().tolist())
            gold.extend(r["label"] for r in batch)

    accuracy = accuracy_score(gold, preds)
    macro_f1 = f1_score(gold, preds, average="macro")

    print("=" * 60)
    print("Urgency 3-class (Green/Yellow/Red) reproduction")
    print(f"accuracy = {accuracy:.3f}")
    print(f"macro_f1 = {macro_f1:.3f}")
    print(f"paper (full data): accuracy={PAPER_ACCURACY:.3f} macro_f1={PAPER_MACRO_F1:.3f}")
    print(
        "NOTE: trained on a SMALL SHIPPED SAMPLE (sample.jsonl); numbers are "
        "expected to differ from the full-data paper values above."
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
