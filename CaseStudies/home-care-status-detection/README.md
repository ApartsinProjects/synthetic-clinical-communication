# Home-Care Status Detection

- **Paper section:** 3.3.6
- **Source repository:** https://github.com/gabriellem28/LLM-project

## Motivation
A virtual care assistant for home hospitalization that supports remote clinical decision-making. The system reads a patient's free-text symptom descriptions together with physiological vital signs and predicts the current clinical status (No Change, Improvement, Deterioration), aiming to catch early deterioration when no medical staff is physically present.

## Data generation protocol
A fully synthetic dataset was produced with GPT-based prompting (OpenAI `gpt-4o`, temperature 0.9). For each patient a clinical profile is sampled (age, gender, diagnosis drawn from a fixed list of 15 conditions such as Hypertension, COPD, CHF, Pneumonia, UTI, and a target `change` label). GPT is prompted to return a JSON object with two first-person daily narratives ("Day 1", "Day 2"), each written in natural, informal language matching the diagnosis and ending with vitals (HR, BP, Temp in Celsius, RR), plus an objective `reasoning` field explaining how the change is inferred. A second prompt variant injects real-world noise (misspellings, ASR-like errors, broken grammar, irrelevant phrases) to add robustness. The generation loop targeted ~650 clean records plus ~50 noisy records; JSON was extracted and validated, then flattened to tabular form with vital-sign delta features (Day 2 minus Day 1). Labels: 0 = No Change, 1 = Improvement, 2 = Deterioration.

## Data files
| Filename | Description | Rows / size |
|---|---|---|
| synthetic_data.csv | Synthetic patient dataset: free-text Day 1/Day 2 narratives, vitals, deltas, and status labels | 699 records (700 lines), 442 KB |
| generate_data.ipynb | GPT-4o generation notebook (clean + noisy prompt variants, JSON extraction) | 17 KB |

The main modeling notebook (`NLP_Final_Gabrielle_and_Shay.ipynb`, 2.5 MB, EDA + preprocessing + training) is not copied; its results are summarized below.

## Models trained and evaluated
- Text-only: TF-IDF + Logistic Regression; BERT-based classification.
- Vitals-only: XGBoost; LightGBM.
- Fusion (text + vitals): XGBoost, LightGBM, Random Forest; neural nets with BERT embeddings + vitals (Batch Normalization, Dropout, LR tuning).
Evaluation via accuracy, macro-F1, recall, cross-validation, and a held-out test set.

## Results
| Model | Accuracy | F1 Macro |
|---|---|---|
| LightGBM + TF-IDF fusion (best) | 0.971 | 0.972 |

The LightGBM fusion of structured vitals with TF-IDF text features was the best performer; fusion of structured and unstructured signals outperformed single-modality models.

## Notes / license
Student coursework (HIT, Digital Health Technologies, NLP & LLM final project, 2025). Data is fully synthetic. Redistribute data only as the source repository did.
