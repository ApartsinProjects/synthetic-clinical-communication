# Postpartum Severity Triage (Manchester Triage Cascade)

- **Paper section:** 3.3.2
- **Source repository:** https://github.com/1600noa/C-SecSeverity

## Motivation
Postpartum patient messages must be triaged with high sensitivity to critical warning signs while absorbing a large volume of low-urgency questions. Flat multi-class classifiers tend to fail on the rare critical classes under severe imbalance. This study builds a fully synthetic corpus of postpartum patient/caregiver messages annotated on the Manchester Triage System (MTS) and compares a two-stage cascade architecture against a zero-shot LLM. The cascade first filters routine vs. urgent, then places urgent cases on a severity scale, so the model is not massively penalized for confusing adjacent urgent levels while still isolating life-threatening signs.

## Data generation protocol
Messages were generated with **GPT-4o-mini** (OpenAI API, `temperature=1.3` for lexical diversity). Each record samples a speaker (`patient`/`caregiver`), a target length (`short`/`medium`/`long`), and one of four Manchester triage levels (0-3), each with an explicit clinical description:
- **Level 0 Routine Recovery** - expected post-op symptoms, no danger signs.
- **Level 1 Low Urgency** - mild complications needing guidance (mild redness, baby blues, pain managed by pills).
- **Level 2 Medium Urgency** - symptoms needing prompt assessment within hours (widening redness, foul discharge, low-grade fever).
- **Level 3 Immediate / Life-Threatening** - hemorrhage, chest pain / shortness of breath, suspected thromboembolism.
Eight postpartum warning-sign categories (wound, infection, bleeding, respiratory, severe pain, thromboembolism, mood disorder, urinary) map onto the three urgent MTS levels. The generator produced ~3,000 messages with per-row category flags, character/word counts, and an evidence field. Data were split deterministically 60% train / 15% validation / 25% test (stratified), giving a 750-message unseen test set.

## Data files
| filename | description | rows/size |
|---|---|---|
| `dataset.xlsx` | Full synthetic MTS-labelled corpus (`manchester_postpartum_triage_v1`): message, sender, length target, 8 category flags, `triage_level`, char/word counts, evidence | ~3,000 rows, 17 cols, 689 KB |
| `generate_data.ipynb` | GPT-4o-mini generation notebook (attribute sampling + MTS-level prompts, temperature 1.3) | 31 KB |
| `model_zeroshot_gpt4omini.ipynb` | Zero-shot GPT-4o-mini 4-class triage evaluation on the 750-item test set (JSON-mode) | 47 KB |

## Models trained and evaluated
- **BioBERT cascade** (`dmis-lab/biobert-v1.1`): Stage 1 binary filter (routine vs. urgent, sigmoid/BCE), Stage 2 severity regressor (levels 1-3, MSE loss, rounded to class). *Notebook `BERT NEW VER.ipynb` in source repo (187 KB, not copied).*
- **Custom Bi-LSTM cascade** (PyTorch from scratch, `embedding_dim=128`, `hidden_dim=64`): Stage 1 `BCEWithLogitsLoss`, Stage 2 `MSELoss`, manual early stopping at 4 epochs. *Notebook `Bi-LSTM NEW VER.ipynb` in source repo (191 KB, not copied).*
- **GPT-4o-mini zero-shot** (this repo, `model_zeroshot_gpt4omini.ipynb`): direct 4-class classification via in-context prompting, JSON response format, no fine-tuning.

## Results
Evaluated on the 750-message held-out test set.

| Model | Stage 1 (routine vs urgent) acc / macro-F1 | Stage 2 (severity 1-3) acc / macro-F1 | Full 0-3 accuracy / macro-F1 |
|---|---|---|---|
| BioBERT cascade | 0.979 / 0.970 | 0.995 / 0.995 (MSE 0.009) | 0.975 / 0.974 |
| Bi-LSTM cascade | 0.981 / 0.974 | 0.807 / 0.807 (MSE 0.158) | - |
| GPT-4o-mini (zero-shot, 4-class) | - | - | 0.98 / 0.98 |

The fine-tuned BioBERT cascade and the zero-shot GPT-4o-mini both reach ~0.97-0.98 accuracy on the synthetic corpus; the from-scratch Bi-LSTM matches on the binary filter but drops sharply on the severity regression stage (0.81), showing the transformer's advantage on fine-grained severity.

## Notes / license
Student coursework (HIT, LLM/GenAI course). Corpus is fully synthetic (GPT-4o-mini), no real patient data. Redistribute the data only as the source repository did. The two large cascade model notebooks (BioBERT, Bi-LSTM; 187/191 KB) were read for results but not copied; the Zero-Shot GPT-4o-mini notebook is included. Plots and the presentation PDF were not copied.
