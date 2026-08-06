# Casualty-Record Reconstruction from Battlefield Radio

- **Paper section:** 3.4.2
- **Source repository:** https://github.com/TheEliyahu/Tactical-NLP-Documentation-Reconstruction

## Motivation
Battlefield paramedics rarely have time to document critical medical information under fire; only about half of encounters are documented and only ~67% of pre-hospital data items survive to hospital handover. This project targets the information-structuring layer: given a noisy Hebrew battlefield radio transcript (ASR-style phonetic corruption, transmission dropouts, military slang, self-corrections, multiple speakers), reconstruct a flat 20-field JSON record aligned with IDF Form 101 (demographics, injury mechanism/site, vitals, conditions, treatments, information reliability). Fields not clearly stated must be output as `"unknown"` (strict zero-hallucination policy).

## Data generation protocol
All data is synthetic (`generate_data.py`, from `src/data_pipeline/generator.py`). A clinical profile is sampled from a constrained attribute space with clinically consistent rules (e.g., amputation implies immediate evacuation priority). GPT-4 (gpt-4o) then converts each profile into a chaotic Hebrew radio dialogue, injecting transmission noise markers, phonetic corruption, slang, and self-corrections at one of three noise levels (Clean / Medium / High). Every generated sample is schema-validated before acceptance. 500 samples were generated and split 400 train / 100 test (`random.seed(42)`, leakage-verified). An additional 50 `gpt-4o-mini` samples were generated later for a data-scaling test (that variant and its 450-sample split are not shipped).

## Data files
| Filename | Description | Rows / size |
|---|---|---|
| synthetic_data.json | Full 500-sample generated dataset (ground-truth profile + noisy Hebrew transcript) | ~500 samples, 1.05 MB |
| train.jsonl | Training split | 400 lines, 841 KB |
| test.jsonl | Held-out test split (never trained on) | 100 lines, 195 KB |
| train_raw.json | Raw train split before Phi-3 formatting | 874 KB |
| scored_finetuned.json | Per-field scored predictions, Phi-3 QLoRA fine-tuned model | 194 KB |
| scored_bert_v3.json | Per-field scored predictions, AlephBERT Multi-Head v3 (final model) | 214 KB |
| generate_data.py | GPT-4 synthetic transcript generator | 11 KB |

Not copied: LoRA/BERT model weights, `.docx` and `.pptx` files.

## Models trained and evaluated
Four approaches on the same 100 held-out test samples, one shared evaluator: GPT-4 zero-shot; GPT-4 one-shot; Phi-3-mini-4k-instruct fine-tuned with QLoRA/PEFT (generative); AlephBERT Multi-Head Classifier (one classification head per field over a shared Hebrew BERT encoder, non-generative).

## Results
| Model | Exact-Match Accuracy | Macro F1 | Hallucinations |
|---|---|---|---|
| GPT-4 zero-shot | 68.60% | 0.698 | 24 |
| GPT-4 one-shot | 67.15% | 0.686 | 32 |
| Phi-3 fine-tuned (QLoRA) | 63.10% | 0.632 | 7 |
| AlephBERT Multi-Head v3 (final) | 79.30% | 0.802 | 16 |

The non-generative AlephBERT multi-head model won overall; early stopping was the single biggest lever in its five-iteration journey. Exact-value fields (oxygen saturation, CAT time) remained a structural weak point for the classification-head approach (6-18%) where generative models scored 79-87%. Adding 50 extra training samples produced a null result within the n=100 statistical noise floor (roughly +/- 8 points at 95% CI).

## Notes / license
Student coursework (HIT NLP course, 2026). Data is fully synthetic LLM-generated Hebrew transcripts (no real battlefield recordings). Redistribute data only as the source repository did.
