# SBAR Handover Completeness Checking

- **Paper section:** 3.4.3
- **Source repository:** https://github.com/ilay620/SBAR-Project

## Motivation
SBAR handovers communicate a patient's Situation, Background, Assessment, and Recommendation during clinical transitions, but critical details are often omitted or stated too vaguely. This project evaluates whether NLP models can detect information gaps in SBAR notes at the note level and at the level of specific clinical items. Prediction targets: overall handover completeness class, missing critical items, under-specified critical items, and a weighted completeness score.

## Data generation protocol
A synthetic SBAR dataset was generated through the OpenAI Batch API with GPT-4.1-mini (temperature 0.25). The `full_5k` preset targeted 500 synthetic patient cases with ~10 handover variants each (~5,000 handover examples), each variant carrying structured patient context, the handover note, and completeness annotations (missing / under-specified critical items, completeness class, weighted score). Generation proceeded case-batch then variant-batch; outputs were cleaned in an EDA/cleanup pass, deduplicated, and split into train/validation/grouped-test partitions grouped so variants of a case stay together (grouped test = 741 examples).

## Data files
| Filename | Description | Rows / size |
|---|---|---|
| synthetic_data.sample.jsonl | First 200 rows of the full clean generated examples (sample) | 200 rows sampled; full file 4,952 examples, 33.5 MB |
| modeling_dataset.sample.jsonl | First 200 rows of the final modeling dataset (sample) | 200 rows sampled; full file 4,952 examples, 23.7 MB |
| modeling_dataset.sample.csv | First 200 rows of the modeling table with splits (sample) | 200 rows sampled; full file 4,952 rows, 6.0 MB |
| preds_bioclinicalbert_text_only.csv | Text-only BioClinicalBERT test predictions | 173 KB |
| preds_bioclinicalbert_context_aware.csv | Context-aware BioClinicalBERT test predictions | 173 KB |
| final_model_comparison.csv | Full model comparison table (all families) | 1.6 KB |

Large source files exceeded the 15 MB limit and are included as 200-row samples with full sizes noted. Generation and modeling notebooks are not copied.

## Models trained and evaluated
- Prompt-based Qwen zero-shot and few-shot baselines.
- TF-IDF logistic-regression baseline.
- Text-only BioClinicalBERT.
- Context-aware BioClinicalBERT (structured patient context + handover note).
- Hierarchical requiredness-first BioClinicalBERT extension.
Evaluated on the grouped test set (741 examples) via completeness-class accuracy/macro-F1, item-level missing/under-specified F1, safety-missing recall, score MAE, and score Spearman.

## Results
Note-level completeness class (grouped test, 741 examples):

| Model | Class Accuracy | Class Macro F1 |
|---|---|---|
| Majority baseline | 0.575 | 0.243 |
| Style-only baseline | 0.709 | 0.656 |
| TF-IDF logistic regression | 0.725 | 0.711 |
| BioClinicalBERT text-only | 0.758 | 0.745 |
| BioClinicalBERT context-aware | 0.753 | 0.741 |

Qwen zero-shot / few-shot (on a 180-example balanced primary set) reached 0.408 / 0.499 class macro-F1. The text-only BioClinicalBERT was the strongest completeness-class model; it also led on missing-item micro-F1 (0.706) and safety-missing recall (0.756), while the context-aware variant traded a little class accuracy for slightly higher under-specified F1.

## Notes / license
Student coursework. Data is synthetic and not intended for clinical use. Redistribute data only as the source repository did.
