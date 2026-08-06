# Administrative Patient-Portal Message Triage

- **Paper section:** 3.3.1
- **Source repository:** https://github.com/Dor444/-LLM-triage-project

## Motivation

Patient-written portal messages are often short, informal, incomplete, typo-filled, or emotionally phrased. Administrative intake teams must review messages that mix symptoms, administrative requests, missing context, and informal language. This project converts noisy portal text into four structured, auditable routing signals to help staff scan and triage an intake queue, while leaving the actual review decision with a person. It asks whether a synthetic-data workflow plus lightweight fine-tuned classifiers can produce useful routing signals without relying on a large hosted inference service for every message. This is an educational prototype for administrative human review only, not diagnosis or clinical decision-making.

## Data generation protocol

Synthetic noisy portal messages and their structured labels were generated locally with **`Qwen/Qwen2.5-0.5B-Instruct`** (see `generate_data.py`). Controlled prompting produces messages plus a labeled record schema:

```json
{
  "task_id": "example-001",
  "text": "Patient portal message text",
  "labels": {
    "urgency_level": "Green|Yellow|Red",
    "risk_factors": ["..."],
    "insufficient_information": false
  }
}
```

Generation and split summary:

| Stage | Count |
|---|---:|
| Generation tasks | 3,000 |
| Valid examples | 2,799 |
| Failed examples | 201 |
| Success rate | 93.3% |
| Train | 1,958 |
| Validation | 420 |
| Test | 420 |

The full generated JSONL datasets are intentionally excluded from version control in the source repo; the repository ships a small demo file and the 50 saved test examples needed to reproduce the pipeline evaluation.

## Data files

| Filename | Description | Rows / size |
|---|---|---|
| `test.jsonl` | 50 saved test examples with pipeline predictions (from `data/test_from_pipeline_outputs.jsonl`) | 50 rows, 16 KB |
| `sample.jsonl` | Tiny synthetic sample of portal messages for CLI smoke tests | 6 rows, 1.3 KB |
| `generate_data.py` | Local Qwen2.5-0.5B-Instruct synthetic-message generator (`generate_synthetic_data.py`) | 6.9 KB |
| `src/*.py` | Full reusable pipeline: `data_utils.py`, `split_dataset.py`, `train_urgency_model.py`, `train_risk_factor_model.py`, `train_insufficient_info_model.py`, `tune_risk_threshold.py`, `run_prompt_baselines.py`, `inference_pipeline.py`, `evaluate_pipeline.py`, `metrics_utils.py`, `create_visuals.py`, `config.py` | 13 files |
| `results/pipeline_outputs.jsonl` | Unified-pipeline structured outputs on the 50 test examples | 9 rows, 30 KB |
| `results/pipeline_outputs.csv` | Same, tabular | 15 KB |
| `results/model_results_summary.md` | All metrics in one place | 1.5 KB |
| `results/pipeline_evaluation_summary.json` | Aggregate pipeline metrics | 202 B |
| `results/risk_factor_threshold_tuning_results.json` | Risk-factor threshold sweep (selected 0.30) | 730 B |

## Models trained and evaluated

- **DistilBERT (`distilbert-base-uncased`)** fine-tuned separately as three specialist heads: urgency (Green/Yellow/Red), multi-label risk-factor, and insufficient-information.
- **Qwen2.5-0.5B-Instruct** used both as the synthetic-data generator and as zero-shot / few-shot urgency-prompting baselines.
- A unified JSON routing pipeline combines the three DistilBERT heads into one auditable output; selected risk threshold 0.30.

## Results

Fine-tuned specialist heads:

| Task | Model | Key metric |
|---|---|---:|
| Urgency | DistilBERT | Accuracy 0.810, Macro-F1 0.810 |
| Risk-factor (multi-label) | DistilBERT | Micro-F1 0.879, Macro-F1 0.778 (thr 0.30) |
| Insufficient-info | DistilBERT | Accuracy 0.869, Macro-F1 0.795 |

Prompting baselines (urgency): zero-shot Qwen accuracy 0.34 / macro-F1 0.295; few-shot Qwen accuracy 0.25 / macro-F1 0.208.

Unified pipeline on 50 saved test examples:

| Metric | Value |
|---|---:|
| Urgency accuracy | 0.76 |
| Risk exact-match accuracy | 0.92 |
| Insufficient-info accuracy | 0.86 |
| Human review rate | 0.72 |

Key finding: compact fine-tuned DistilBERT heads on locally-generated synthetic data substantially outperform zero-/few-shot Qwen prompting on urgency (0.81 vs 0.34/0.25 accuracy), and the combined pipeline routes 72% of messages to human review with strong per-signal accuracy.

## Notes / license

Student coursework (single-author course project, Dor Istrik). Redistribute data only as the source repository did: full generated datasets are excluded from version control; only the small demo sample and the 50 saved test examples are shipped. Administrative-support prototype only, not for clinical use.
