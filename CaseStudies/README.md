# Case Studies: LLM-Generated Synthetic Clinical Communication

This directory organizes the datasets, generation scripts, and per-use-case documentation for the
thirteen application studies discussed in Section 3 of the paper. Each subfolder corresponds to one
student coursework project and contains the synthetic data (or size-capped samples of it), the
LLM data-generation script or notebook, and a `README.md` describing the motivation, generation
protocol, data files, models, and results.

Data files larger than 15 MB are included only as 200-line samples (`*.sample.*`), with the original
size and row count recorded in the folder's README. Model weights, presentations, images, and audio
are not redistributed. Each dataset is student coursework and should be redistributed only as the
source repository permits (see each folder's Notes / license section).

**Reproducing results.** Every study folder carries a self-contained `reproduce.py` that retrains and
re-evaluates the study's model on the shipped synthetic data (no data regeneration, no network or LLM
calls), printing each metric next to the paper's value. Install `requirements-reproduce.txt`, then run a
study's `reproduce.py` (add `--smoke` for a fast check) or `run_all.py --smoke` to exercise all thirteen.
See [REPRODUCE.md](REPRODUCE.md) for the per-study reproduction table and caveats.

| # | Folder | Paper section | One-line description |
|---|--------|:---:|----------------------|
| 1 | [diagnosis-from-noisy-self-descriptions](diagnosis-from-noisy-self-descriptions/) | 3.1.1 | Diagnosis from noisy self-descriptions (Llama-3.1-8B noise rewrite; FLAN-T5) |
| 2 | [adaptive-diagnostic-questioning](adaptive-diagnostic-questioning/) | 3.1.2 | Diagnostic-questioning benchmark (GPT-4o-mini; SDPD; reveal tiers) |
| 3 | [urgency-triage-from-complaints](urgency-triage-from-complaints/) | 3.1.3 | Binary ER urgency triage (GPT-4; DistilBERT) |
| 4 | [clinical-decision-extraction-hebrew-discharge](clinical-decision-extraction-hebrew-discharge/) | 3.2.1 | Decision extraction from synthetic Hebrew discharge (GPT-4o-mini; XLM-R / reranker / Gemini) |
| 5 | [administrative-portal-message-triage](administrative-portal-message-triage/) | 3.3.1 | Portal-message triage (local Qwen2.5-0.5B; DistilBERT heads) |
| 6 | [clinical-priority-portal-triage](clinical-priority-portal-triage/) | 3.3.3 | Longitudinal portal priority triage (GPT-4o; ClinicalBERT + safety cascade) |
| 7 | [postpartum-severity-triage](postpartum-severity-triage/) | 3.3.2 | Postpartum severity triage (GPT-4o-mini; BioBERT cascade / Bi-LSTM / GPT-4o-mini) |
| 8 | [oncology-distress-classification](oncology-distress-classification/) | 3.3.4 | Psychosocial response + distress (Gemma2-27B; dual-LLM judge; DistilBERT) |
| 9 | [medication-question-risk-classification](medication-question-risk-classification/) | 3.3.5 | Medication-question risk triage (GPT-4.1 augmentation; BioBERT / BlueBERT) |
| 10 | [home-care-status-detection](home-care-status-detection/) | 3.3.6 | Home-care status detection (GPT; LightGBM fusion) |
| 11 | [ems-report-routing](ems-report-routing/) | 3.4.1 | EMS report routing (GPT-4.1-mini + ASR noise; BioClinicalBERT) |
| 12 | [casualty-record-reconstruction](casualty-record-reconstruction/) | 3.4.2 | Casualty-record reconstruction from radio (GPT-4o; AlephBERT multi-head) |
| 13 | [sbar-completeness-checking](sbar-completeness-checking/) | 3.4.3 | SBAR completeness checking (OpenAI batch; BioClinicalBERT; hierarchical) |
