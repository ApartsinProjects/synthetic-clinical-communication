# Retrospective PMOS Clinical Priority Portal Triage Using LLMs

- **Paper section:** 3.3.3
- **Source repository:** https://github.com/AlinaKapelovich/Retrospective-PMOS-Clinical-Priority-Triage-Using-LLMs

## Motivation

The project builds a Clinical Decision Support System that triages patient-portal messages related to PMOS (Polyendocrine Metabolic Ovarian Syndrome, the proposed rename of PCOS) into LOW / MEDIUM / HIGH clinical priority. Medical triage faces a dangerous trade-off between under-triage (missing acute emergencies) and alert fatigue (too many false positives). No off-the-shelf public dataset maps to the novel multi-system PMOS criteria, so a synthetic longitudinal dataset was generated, and a context-aware conversational safety cascade was engineered on top of a fine-tuned clinical transformer to guarantee safe routing.

## Data generation protocol

A synthetic dataset of 3,000 longitudinal patient cases was generated with **GPT-4o** using attribute-based text generation. The prompt strategy combined structured clinical attributes (age, past medical history) with varied linguistic profiles (overly polite, vague, anxious tones) to simulate noisy, real-world portal messages, with explicit control over class distribution and deliberately injected "confidently wrong" edge cases. `generate_data.ipynb` (`notebook1_final_dataset_preparation.ipynb`) performs the dataset preparation and longitudinal context fusion, combining `Age + History + Current Message` into a single `combined_text` string (`Age: X | History: Y | Message: Z`) so models evaluate the patient's holistic background rather than an isolated complaint.

Label distribution (3,000 cases): LOW 1,200 / MEDIUM 1,350 / HIGH 450 (deliberate class imbalance reflecting real medical triage).

## Data files

| Filename | Description | Rows / size |
|---|---|---|
| `synthetic_data.csv` | Final GPT-4o synthetic longitudinal PMOS dataset (`patient_id, age, past_medical_history, current_portal_message, clinical_priority`) | 3,000 cases (8,891 CSV lines w/ multiline messages), 1.25 MB |
| `results.csv` | Per-message evaluation output of the master architecture (`label`, `combined_text`, `0_to_1_Score`, `ai_initial_guess`, `ai_confidence`, `final_system_risk`, `ground_truth_str`) | ~2,867 lines, 532 KB |
| `generate_data.ipynb` | Dataset preparation / longitudinal context fusion notebook (`notebook1_final_dataset_preparation.ipynb`) | 1.26 MB |

## Models trained and evaluated

Systematic progression from benchmarking to a domain-specific safety architecture:

- **Zero-shot LLMs** — Qwen, Mistral-7B, `facebook/bart-large-mnli` under zero-shot ordinal regression.
- **DistilBERT** fine-tuned with `sklearn` `compute_class_weight` to focus on the minority HIGH-risk class.
- **Bio_ClinicalBERT** fine-tuned (pre-trained on MIMIC-III clinical notes) — baseline domain model.
- **Master architecture** — Bio_ClinicalBERT + a generative Context-Aware Conversational Safety Cascade: softmax continuous regression on logits extracts a 0-1 confidence; if confidence drops below 99.5% or deterministic red flags fire, the message is intercepted for automated conversational patient verification before routing.

## Results

| Model | Accuracy |
|---|---:|
| Zero-shot (Qwen / Mistral / BART) | ~0.34 - 0.42 |
| DistilBERT fine-tuned | 0.817 |
| Bio_ClinicalBERT fine-tuned (baseline) | 0.828 |
| Master architecture (Bio_ClinicalBERT + safety cascade) | **0.997** |

Key findings: the master architecture reaches 0.997 accuracy with 1.00 recall for emergencies (zero dangerous under-triage). The safety cascade safely converted 29 dangerous baseline errors out of 251 pipeline interventions and introduced 0 new errors (broke zero correct predictions), mathematically guaranteeing emergency capture while autonomously clearing stable patients to mitigate alert fatigue. General zero-shot LLMs were unreliable for clinical routing (~0.34-0.42), frequently classifying HIGH-risk emergencies as LOW/MEDIUM ("confidently wrong").

## Notes / license

Student coursework (final project; team: Alina Kapelovich, Victoria Golovitsky). Redistribute data only as the source repository did. The dataset is fully synthetic (GPT-4o generated); PMOS is a proposed 2024-2026 rename of PCOS used as the clinical framing. Bibliography PDFs, presentation files, and result images from the source repo are not redistributed here.
