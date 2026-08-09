# Reproducing the application-study results

Every study folder carries a self-contained **`reproduce.py`** that **retrains and
re-evaluates** the study's model on the **already-shipped synthetic data** and prints
each metric next to the paper's reported value. The scripts do **not** regenerate data
and make **no** network or LLM/API calls.

## How to run

```bash
# one-time: install dependencies (classical studies need only the core block)
/c/Python314/python -m pip install -r requirements-reproduce.txt

# run one study
cd diagnosis-from-noisy-self-descriptions
/c/Python314/python reproduce.py            # full reproduction
/c/Python314/python reproduce.py --smoke    # fast pipeline check (tiny subset)

# smoke-check every study end-to-end
/c/Python314/python run_all.py --smoke
```

Every script accepts `--smoke` (a tiny, fast run that only proves the train/eval loop
executes) and a default full run. Seeds are fixed. The encoder studies use a GPU for the
full run when one is available and fall back to CPU.

## What each script reproduces

Values below are the measured reproduction (this machine) vs the paper. "sample" marks a
study that ships only a size-capped 200-line sample, so its numbers reproduce the pipeline,
not the full-data paper figure. "re-eval" marks a study whose model retraining needs an
unshipped pipeline or a GPU-only checkpoint, so the script reproduces the reported numbers
by re-scoring the shipped model predictions.

| # | Study | Model retrained | Metric | Reproduced | Paper | Notes |
|---|-------|-----------------|--------|-----------|-------|-------|
| 1 | diagnosis-from-noisy-self-descriptions | Naive Bayes (TF-IDF) | accuracy, clean/med/heavy | 94.6 / 78.8 / 79.2 | 93.8 / 79.2 / 77.5 | full data |
| 2 | adaptive-diagnostic-questioning | none (LLM benchmark) | MMS; per-round sim | 0.660; 0.627/0.624/0.638 | 0.657; 0.624/0.621/0.635 | re-eval of shipped similarities; ZDA-by-tier not shipped |
| 3 | urgency-triage-from-complaints | TF-IDF + LogReg | accuracy / F1 | 0.725 / 0.718 | 0.810 / 0.653 | sample |
| 4 | administrative-portal-message-triage | DistilBERT (urgency head) | accuracy / macro-F1 | smoke only | 0.810 / 0.810 | sample (~6 train rows shipped); GPU for full |
| 5 | postpartum-severity-triage | Bi-LSTM cascade (from scratch) | Stage-1 acc/F1; full 0-3 acc | 0.995 / 0.993; 0.950 | 0.981 / 0.974; ~0.975 | full data; CPU-trainable |
| 6 | oncology-distress-classification | TF-IDF + class-weighted LogReg | macro-F1 (response; distress) | 0.382; 0.674 | 0.856; 0.805 | sample (train sample holds 4/7 response classes) |
| 7 | medication-question-risk-classification | SVM (TF-IDF, class-weighted) | accuracy / macro-F1 | 0.832 / 0.675 | 0.84 / 0.80 | authentic-text test; rare-class synthetic augmentation not shipped |
| 8 | home-care-status-detection | LightGBM (TF-IDF fusion) | accuracy / macro-F1 | 0.943 / 0.943 | 0.971 / 0.972 | vitals are text-embedded, so text-only runs slightly below the vitals-fusion best |
| 9 | ems-report-routing | TF-IDF + LogReg (baseline) | macro-F1 (care area; specialty) | pipeline check | BioClinicalBERT ~0.29 / ~0.38 | sample; paper model + ASR-noise pipeline unshipped |
| 10 | sbar-completeness-checking | TF-IDF + LogReg | accuracy / macro-F1 | 0.725 / 0.711 | 0.725 / 0.711 | sample |

Classical / CPU studies (1 diagnosis, 3 urgency, 6 oncology, 7 medication, 8 home-care, 10 SBAR) and the metric-recompute (2 adaptive) reproduce fully on CPU. The encoder fine-tunes (4 admin, 5 postpartum, 9 EMS) retrain the model; 4 and 9 are sample-limited for the headline number, while 5 reaches the paper Bi-LSTM on CPU. Where a shipped file is a sample, the script says so at the top and at runtime.

## Seed stability (5-seed sweep)

To confirm the reported metrics are stable to random seed rather than lucky single runs,
each study's reproducible pipeline was re-run across **five seeds** (42, 123, 2024, 7,
2718) by setting the `REPRODUCE_SEED` environment variable, which every `reproduce.py`
now honours (default unchanged when unset). The table gives **mean ± SD** of the
reproduced metric over the five seeds. Standard deviations are small (typically ≤ 0.05),
so the reproducible pipeline is stable to seed. Raw per-seed values are in
[`reproducibility_seed_stability.json`](reproducibility_seed_stability.json).

```bash
# reproduce a single seed
REPRODUCE_SEED=123 /c/Python314/python diagnosis-from-noisy-self-descriptions/reproduce.py
```

| # | Study | Reproduced model | Metric | Mean ± SD (5 seeds) |
|---|-------|------------------|--------|---------------------|
| 1 | diagnosis | Naive Bayes (TF-IDF) | acc clean / med / heavy | 0.940±0.009 / 0.791±0.003 / 0.792±0.007 |
| 3 | urgency | TF-IDF + LogReg | accuracy / F1 | 0.755±0.025 / 0.723±0.011 |
| 4 | administrative-portal | DistilBERT (urgency head) | accuracy / macro-F1 | 0.312±0.024 / 0.170±0.032 &dagger; |
| 5 | postpartum | Bi-LSTM cascade | full acc / macro-F1 | 0.934±0.024 / 0.935±0.024 |
| 6 | oncology | TF-IDF + LogReg | response / distress macro-F1 | 0.382±0.000 / 0.674±0.000 |
| 7 | medication | SVM (TF-IDF) | accuracy / macro-F1 | 0.733±0.055 / 0.564±0.064 |
| 8 | home-care | LightGBM (TF-IDF fusion) | accuracy / macro-F1 | 0.943±0.008 / 0.943±0.008 |
| 9 | ems | TF-IDF baseline | macro-F1 care / specialty | 0.957±0.081 / 0.979±0.014 &Dagger; |
| 10 | sbar | TF-IDF + LogReg | accuracy / class macro-F1 | 0.745±0.040 / 0.732±0.046 |

Rows track the corresponding **baseline** in the paper's tables well where the shipped
data is large enough (e.g. diagnosis Naive Bayes 0.94/0.79/0.79 vs paper 0.938/0.792/0.775;
SBAR LogReg 0.745/0.732 vs paper 0.725/0.711; home-care fusion 0.943 vs 0.971). Two rows
are shown for completeness but are **not** meaningful reproductions of a paper figure:

- **&dagger; administrative-portal** ships only a few training rows, too few to train the
  DistilBERT urgency head, so it collapses toward random (≈1/3 accuracy). The paper's
  0.81 head uses the full unshipped corpus.
- **&Dagger; ems** is a TF-IDF baseline on the shipped clean sample, not the paper's
  BioClinicalBERT + ASR-noise pipeline (Table 15), so its value is not construct-matched.

Oncology (row 6) has zero seed variance because the study ships a **fixed** train/test
split, so the classical baseline is deterministic; its lower value reflects the shipped
sample holding only 4 of 7 response classes (see the table above), not seed sensitivity.
