# Urgency Triage from Patient Complaints

- **Paper section:** 3.1.3
- **Source repository:** https://github.com/Nofar-Kedmi/LLM-Classifier-for-Patient-Reports

## Motivation

Emergency-room triage must quickly separate patients who need immediate care from those who can wait. This study frames this as binary text classification: given a free-text, first-person complaint describing how a patient feels on arrival, predict urgent (1) vs. non-urgent (0). Because real complaint text at scale is scarce, the project synthesizes patient narratives from structured clinical measurements, then trains classifiers on the generated text - covering both the data-to-text generation task and the downstream classification task.

## Data generation protocol

- **Base data:** the Kaggle Patient Priority Classification Dataset - structured clinical records (age, gender, chest pain type, blood pressure, cholesterol, max heart rate, glucose, BMI, hypertension, heart disease, smoking status, etc.) with an original multi-class `triage` label.
- **LLM used:** GPT-4.
- **Prompting approach:** a structured prompt casts the model as the patient - "You are a patient arriving at the emergency room. Based on the data below, write a short, first-person paragraph (in simple everyday language) describing how you feel and why you came in. Don't use medical terms." This turns each structured row into a natural, layperson complaint that omits clinical jargon.
- **Counts:** ~6,500 rows generated (one free-text complaint per cleaned patient record); 80/20 train-test split for modeling.
- **Labeling method:** the original multi-class triage field was mapped to a binary label (0 = not urgent / can wait or be monitored, 1 = urgent / needs immediate attention). Labels come from the structured source, not the LLM. SMOTE was used to balance classes during training.

## Data files

| Filename | Description | Rows / size |
|---|---|---|
| `synthetic_data.sample.csv` | Sample (first 200 lines) of the main synthetic dataset `df_clean_with_text.csv`: structured features + binary `label` + generated `text_input` complaint. Full file: **~6,552 rows, 1.84 MB** (not copied in full to keep the batch small). | 200-line sample, 70 KB |
| `clean_binary_labels.csv` | Cleaned structured records with the mapped binary label (no free text). | ~6,552 rows, 539 KB |
| `source_structured.csv` | Raw Patient Priority dataset as provided (structured clinical fields + original `triage`). | ~6,962 rows, 772 KB |
| `generate_data.ipynb` | GPT-4 free-text complaint generation notebook. | 33 KB |

## Models trained and evaluated

- TF-IDF + Logistic Regression - classical, interpretable baseline.
- DistilBERT - fine-tuned transformer classifier.
- T5 - fine-tuned text-to-text generative classifier.

Preprocessing: lowercasing, stop-word removal, per-model tokenization/truncation, SMOTE for class balance. Evaluation: accuracy, precision, recall, F1, AUROC, confusion matrices.

## Results

Model performance comparison (from the source repository):

| Metric | TF-IDF + LR | DistilBERT | T5 |
|---|---|---|---|
| Accuracy | 0.8101 | **0.9641** | 0.9314 |
| F1-score | 0.6530 | **0.8262** | 0.5494 |
| Recall | 0.8734 | 0.5939 | 0.5360 |
| Precision | 0.9999 | 0.9999 | 0.7778 |

DistilBERT gave the most balanced and highest overall performance. TF-IDF + LR had the strongest recall (most sensitive to urgent cases). T5 reached good accuracy but was less consistent on F1 and recall.

## Notes / license

Student coursework (Nofar Kedmi, Diana Akoshvili). The structured base data is the public Kaggle Patient Priority Classification Dataset. Redistribute the data only as the source repository did.
