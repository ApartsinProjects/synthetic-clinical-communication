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
