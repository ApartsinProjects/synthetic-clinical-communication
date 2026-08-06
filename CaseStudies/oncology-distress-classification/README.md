# Oncology Psychosocial Response & Distress Classification

- **Paper section:** 3.3.4
- **Source repository:** https://github.com/K21K30/nlp-oncology-psychosocial-response

## Motivation
A cancer diagnosis carries a heavy psychosocial burden, and supportive-care teams increasingly want to triage the emotional state behind patient-generated text. Two questions matter clinically: **which psychosocial response dominates** a message, and **how intense the distress** is. No public labeled dataset exists for this framing, and emotional labels are subjective and expensive to annotate. This project therefore defines a novel two-label task on oncology-related messages, builds a fully synthetic label-leakage-controlled corpus for it, and compares three model families with bootstrap-based evaluation and independent human validation. Task: `f(text) -> (response in {anxiety, sadness, anger, hope, guilt, denial, acceptance}, distress in {low < medium < high})`, distress treated as ordinal.

## Data generation protocol
**Attribute-based synthetic generation with dual-LLM-judge validation and a strict label-leakage ban:**
1. **Attribute space** - each message samples `role`, cancer `stage`, `cancer_type`, `tone`, `channel`, `age_group`, `length`, and a `noisy` flag for diversity/coverage.
2. **Conditional generation** - a local generator (`gemma2:27b` via Ollama) is prompted with the sampled attributes and an intended (response, distress) label, and writes a natural message expressing that state **without ever naming the emotion** (label-leakage ban, so a classifier cannot cheat on a keyword).
3. **Rejection sampling** - generations that drift from the intended label or violate constraints are rejected and regenerated, with non-uniform per-class quotas.
4. **Dual-LLM-judge blind audit** - two independent judges (`gpt-4o-mini` and `qwen2.5:32b`) read the text without the intended label and predict (response, distress). Judge agreement assigns each item a quality tier.
5. **Tiering / relabelling** - strict (both judges confirm intended), silver (partial agreement), consensus (label set to judges' consensus where it differed). model-ready = strict + silver + consensus.

Quality tiers: strict 471, silver 75, consensus-relabelled 727, **model-ready 1273**. Splits (seed 42): test 67 (frozen strict, human-re-annotated), validation 45, train_A 359 (strict), train_B 434 (strict+silver), train_C 1161 (+consensus).

## Data files
| filename | description | rows/size |
|---|---|---|
| `synthetic_data.sample.jsonl` | First 200 lines of `dataset_model_ready.jsonl` (model-ready corpus: text, intended/final response+distress, judge_a/b, quality_tier, attributes) | sample of **1,273 rows**; full file 1.8 MB |
| `train.sample.jsonl` | First 200 lines of `train_C.jsonl` (largest training tier, strict+silver+consensus) | sample of **1,161 rows**; full file 1.6 MB |
| `test.jsonl` | Frozen strict-tier test set (final evaluation only, human-validated) | 67 rows, 97 KB |
| `validation.jsonl` | Validation set (model selection / threshold tuning) | 45 rows, 67 KB |
| `test_human_confirmed.jsonl` | Test items where a blind human annotator confirmed both labels (joint) | 47 rows, 93 KB |
| `raw_seed.csv` | Raw pre-audit generation output (`raw_dataset.csv`) | 800 rows, 204 KB |
| `generate_data.py` | Validated generation w/ rejection sampling + inline dual-judge audit (`p2_validated_gen.py`) | 56 KB |
| `human_check.py` | Blind human annotation + scoring of the test set (`p5_human_check_ml.py`) | 74 KB |

## Models trained and evaluated
Three model families on both tasks:
- **TF-IDF + Logistic Regression** (sparse lexical baseline, class-weighted; distress has nominal 3-class and ordinal two-threshold variants).
- **DistilBERT** (`distilbert-base-uncased`) fine-tuned separately for response (7-class) and distress (3-level), class-weighted cross-entropy, 5 seeds (13/42/73/101/2026), best-val-macro-F1 selection.
- **BART-MNLI** (`facebook/bart-large-mnli`) off-the-shelf zero-shot.
- **Majority class** trivial floor.
Evaluation: macro-F1 primary; distress adds weighted Cohen's kappa, ordinal MAE, severe-error rate; 5,000-resample stratified paired bootstrap with 95% CIs; human agreement (Cohen's / weighted kappa) on the 67-item test.

## Results
Test macro-F1 (67-item test set):

| Task | Best lexical (TF-IDF) | Best transformer (DistilBERT) | Zero-shot (BART) | Reliable conclusion |
|---|---|---|---|---|
| Response (7-class) | **0.856** (tier B) | 0.834 (tier C) | 0.732 | supervised TF-IDF reliably > zero-shot |
| Distress (3-level ordinal) | 0.805 (nominal, tier B) | **0.864** (tier B) | 0.468 | both supervised reliably > zero-shot |

DistilBERT-B on distress: macro-F1 0.864, linear weighted kappa 0.851, ordinal MAE 0.113. Class-weighting gave +0.023 macro-F1 vs. unweighted. The lexical-vs-transformer gap was **not** statistically resolved on the 67-item test (paired bootstrap CIs included 0). More synthetic data was not uniformly better (peak tier depends on task/model). Human validation: response exact agreement 86.6% (kappa 0.84), distress exact 83.6% (weighted kappa 0.80 linear / 0.86 quadratic), with most disagreement at the low/medium distress boundary.

## Notes / license
Student coursework (HIT, LLM/GenAI course), solo author. Corpus is 100% synthetic (no real patient data). Research prototype, **not** validated for clinical triage. Redistribute the data only as the source repository did. The two multi-MB files (`dataset_model_ready.jsonl`, `train_C.jsonl`) were sampled to their first 200 lines to save space; full row counts recorded above. Slides, PDFs, figures, and trained checkpoints were not copied.
