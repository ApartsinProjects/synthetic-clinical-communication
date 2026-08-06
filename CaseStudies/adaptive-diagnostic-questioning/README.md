# Adaptive Diagnostic Questioning

- **Paper section:** 3.1.2
- **Source repository:** https://github.com/MaiWert/MedQDx

## Motivation

Patients rarely present a complete clinical picture up front, so physicians reach a diagnosis through adaptive, targeted questioning. Existing LLM medical benchmarks instead evaluate on fully revealed cases and never measure a model's ability to conduct strategic inquiry under partial information. This study addresses this gap: an LLM "doctor" must iteratively question an LLM "patient" starting from only partial case information and produce a diagnosis after each round, so the benchmark measures whether the model can adapt its questioning, refine hypotheses, and converge on the ground-truth diagnosis.

## Data generation protocol

- **Base data:** the Symptom-Disease Prediction Dataset (SDPD) from Mendeley: 4,961 rows, 132 one-hot symptom columns, 41 unique diseases (`prognosis`). After cleaning (dropping duplicates, constant columns, and cases with fewer than 5 symptoms), a random sample of 100 disease cases was used.
- **LLM used:** GPT-4o-mini (via Azure OpenAI) for patient-case generation and for the patient persona; GPT-4.1 (Azure OpenAI) as the doctor/diagnostician in benchmark creation and evaluation. Diagnosis similarity uses embedding-based cosine similarity and string-similarity (difflib / scikit-learn).
- **Prompting approach:**
  - Case generation: `call_gpt4o_mini(...)` turns each structured symptom set into three natural-language clinical vignettes at three symptom-reveal tiers - 100% (all symptoms), 80% (~80% of symptoms), and 50% (~50% of symptoms).
  - Benchmark creation: a doctor-patient dialogue loop over the 50% case. For three rounds the doctor asks a diagnostic question, the patient LLM answers from the case, and the doctor emits a diagnosis; each diagnosis is scored by cosine similarity against the true `prognosis`.
- **Counts:** 100 patient cases (each with 100%/80%/50% versions); benchmark of 99 diagnostic cases across 3 question-answer-diagnosis rounds.
- **Labeling method:** ground truth is the SDPD `prognosis` label carried through generation. Reveal-tier fidelity was validated with Jaccard overlap between original and extracted symptoms, checking the expected 100% >= 80% >= 50% confidence gradient.

## Data files

| Filename | Description | Rows / size |
|---|---|---|
| `patient_cases.csv` | Generated patient vignettes. Columns: `prognosis`, `symptoms`, `100% Case`, `80% Case`, `50% Case`. | 100 rows, 158 KB |
| `benchmark.csv` | Full diagnostic-questioning benchmark: per-case columns plus `Question_1..3`, `Answer_1..3`, `Diagnosis_1..3`, `Similarity_1..3`. | 99 rows, 215 KB |
| `generate_data.ipynb` | Benchmark-creation notebook (doctor-patient simulation loop). | 165 KB |

## Models trained and evaluated

No models were trained. The benchmark evaluates hosted LLMs zero-shot: GPT-4.1 as the doctor/diagnostician and GPT-4o-mini as the patient. Metrics: Zero-shot Diagnostic Accuracy (ZDA, similarity above threshold), Mean of Max Similarity across rows (MMS), and per-round mean diagnostic similarity across the 100%/80%/50% reveal tiers.

## Results

Zero-shot Diagnostic Accuracy of GPT-4.1 by symptom-reveal tier (similarity threshold 0.65, 100 cases):

| Reveal tier | Correct | ZDA |
|---|---|---|
| 100% Case | 51/100 | 51.0% |
| 80% Case | 44/100 | 44.0% |
| 50% Case | 37/100 | 37.0% |

Adaptive-questioning similarity metrics:

| Metric | Value |
|---|---|
| Mean of Max Similarity across rows | 0.657 |
| Mean similarity, round 1 | 0.624 |
| Mean similarity, round 2 | 0.621 |
| Mean similarity, round 3 | 0.635 |

Accuracy falls as fewer symptoms are revealed, confirming the difficulty of diagnosis under partial information; adaptive questioning nudges similarity upward by the third round.

## Notes / license

Student coursework (Mai Werthaim, Maya Kimhi); repository declares an MIT license. The underlying SDPD is a public Mendeley dataset. Redistribute the data only as the source repository did.
