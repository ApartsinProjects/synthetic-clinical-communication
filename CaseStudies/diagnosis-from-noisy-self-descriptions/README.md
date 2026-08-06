# Diagnosis from Noisy Patient Self-Descriptions

- **Paper section:** 3.1.1
- **Source repository:** https://github.com/lielsheri/Natural-Language-Processing-project

## Motivation

When patients describe symptoms to a doctor they rarely speak in clean, clinical terms. They add personal stories, hesitations, repetitions, emotional reactions, and off-topic tangents. This study examines how this conversational "noise" degrades automated symptom-to-disease classification, and which model families stay robust. The task is a 24-class disease classification from a free-text symptom description; the challenge is to keep diagnostic accuracy despite realistic distraction.

## Data generation protocol

- **Base data:** the Kaggle Symptom-Based Disease Labeling Dataset: 1,200 clean, clinical-style symptom descriptions balanced across 24 disease categories.
- **LLM used:** Llama-3.1-8B served locally through Ollama.
- **Prompting approach:** each clean description was rewritten "as if told by an elderly patient speaking to their doctor," preserving every medical detail while adding speech-like noise (hesitations, ramblings, confusion, tangents, filler words). Output was constrained to the patient monologue only (no doctor voice). Two noise tiers were produced per sample:
  - Medium noise: target ~50-200 words, a few brief anecdotes or off-topic remarks and light confusion.
  - Heavy noise: target ~150-400 words, extended ramblings, repeated phrases, more confusion, and occasional false memories.
- **Counts:** 1,200 clean + 1,200 medium-noise + 1,200 heavy-noise = 3,600 descriptions. The pipeline ran in 50-row chunks with 4 parallel workers.
- **Labeling method:** disease labels are inherited unchanged from the original Kaggle dataset (the rewrite preserves the diagnosis), so no relabeling was needed. The authors verified no missing values, no duplicates, and label balance across sets.

## Data files

| Filename | Description | Rows / size |
|---|---|---|
| `train_clean.csv` | Original clean symptom descriptions. Columns: index, `label`, `text`. | 1,200 rows, 231 KB |
| `train_with_noise.csv` | Wide-format noisy dataset. Columns: index, `label`, `text` (clean), `medium_noise`, `heavy_noise`. | 1,200 rows, 2.74 MB |
| `generate_data.ipynb` | Noise-generation notebook (Ollama + Llama-3.1-8B rewrite pipeline). | 71 KB |

## Models trained and evaluated

Four classifiers, each trained separately on clean, medium-noise, and heavy-noise text with an 80/20 train-test split:

- Naive Bayes (TF-IDF features) - lightweight interpretable baseline.
- BERT-base - fine-tuned, layers 0-3 frozen, AdamP optimizer.
- ClinicalBERT - clinical-domain BERT, AdamP with scheduler, first 165 params frozen.
- FLAN-T5 - instruction-tuned text-to-label model, Adafactor optimizer.

## Results

Accuracy by model and noise level (from the source repository):

| Model | Clean | Medium noise | Heavy noise |
|---|---|---|---|
| Naive Bayes | 93.8% | 79.2% | 77.5% |
| BERT | 98.3% | 86.7% | 79.2% |
| ClinicalBERT | 97.9% | 83.8% | 86.2% |
| FLAN-T5 | 97.1% | **92.5%** | **87.1%** |

Accuracy generally falls as noise increases. FLAN-T5 was the most robust overall, leading on both medium and heavy noise; ClinicalBERT recovered on heavy noise (longer texts reintroduce clinical terms); Naive Bayes degraded most sharply.

## Notes / license

Student coursework (Liel Sheri, Eden Mama). The disease labels and clean descriptions derive from the public Kaggle Symptom-Based Disease Labeling Dataset. Redistribute the data only as the source repository did.
