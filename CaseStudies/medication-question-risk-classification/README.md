# Medication-Question Risk Classification

- **Paper section:** 3.3.5
- **Source repository:** https://github.com/Dvora-coder/LLM-Medication-QA-Risk-Classifier

## Motivation
Online medication questions often contain early-warning signals of confusion, misuse, harmful drug-drug interactions, and dangerous self-medication. Detecting these high-risk questions is essential for triage, pharmacovigilance, and the safety of medical chatbots. This study frames this as a binary classification: **Critical** (potentially dangerous medication behavior) vs. **General** (informational / low-risk). Example: "Is it safe to take ibuprofen with warfarin?" -> `Critical`. Challenges are noisy layperson phrasing, brand-name variation, context-dependent risk, and severe class imbalance (Critical cases are rare).

## Data generation protocol
The core question set is the public **MedInfo2019-QA-Medications** corpus (~655 questions after cleaning), double-annotated for criticality by two reviewers with Cohen's kappa agreement. Because Critical examples are rare, **GPT-4.1 (via Azure OpenAI) was used for synthetic augmentation**: it generates additional synthetic `Critical` questions to improve rare-class recall, which are then classified with the same prompt-based pipeline. GPT-4.1 also serves as a classifier itself, using a **few-shot, retrieval-augmented prompt** (no fine-tuning): for each question, DPR + FAISS retrieve the top-3 context passages from a hybrid knowledge corpus (DrugBank DDI + WHO Essential Medicines List), which are injected into the prompt. Classical models add a TF-IDF "Critical Similarity" cosine feature, SMOTE oversampling, and SVD dimensionality reduction.

## Data files
| filename | description | rows/size |
|---|---|---|
| `raw_medinfo_qa.xlsx` | Raw MedInfo2019-QA-Medications question set (Question, Focus drug, Question Type, Answer, Section, URL) | 690 rows, 160 KB |
| `labeled_data.xlsx` | Same questions tagged with `Risk_Level` (General/Critical) | ~690 rows, 159 KB |
| `who_eml_export.xlsx` | WHO Essential Medicines List (medicine name, indication), RAG corpus source | 1,577 rows, 42 KB |
| `rag_overlapping_entries.xlsx` | Drug-drug interaction RAG entries (drug1, drug2, interaction, source, text, medicine, indication) | 71,983 rows, 2.6 MB |
| `ddi_data.sample.csv` | First 200 lines of `DDI_data.csv` (raw DrugBank DDI source) | sample of **222,696 rows**; full file 15 MB |
| `generate_data.ipynb` | GPT-4.1 few-shot RAG classification + synthetic `Critical` generation notebook (`GPT4_1.ipynb`) | 636 KB |

**Not copied:** `knowledge_corpus.xlsx` (full RAG corpus, 8.5 MB, exceeds the 5 MB xlsx limit) and the full `DDI_data.csv` (15 MB, sampled above).

## Models trained and evaluated
- **Classical ML** (TF-IDF + Critical Similarity + SVD + SMOTE): SVM (best baseline), Logistic Regression, Gradient Boosting, Random Forest, SGD-L2, KNN.
- **BioBERT** (`dmis-lab/biobert-base-cased-v1.1`) fine-tuned + RAG context.
- **BlueBERT** (`bionlp/bluebert_pubmed_mimic_uncased`) fine-tuned + RAG context.
- **GPT-4.1** (Azure API) - prompt-based classification with RAG context, and a generation+classification variant using synthetic Critical augmentation.
All LLMs use the DPR + FAISS RAG pipeline over the DrugBank + WHO EML corpus.

## Results
| Model | Accuracy | Macro-F1 |
|---|---|---|
| SVM (best classical) | 0.84 | 0.80 |
| Logistic Regression | 0.76 | 0.77 |
| Gradient Boosting | 0.79 | 0.77 |
| SGD Logistic (L2) | 0.79 | 0.79 |
| Random Forest | 0.68 | 0.70 |
| KNN | 0.10 | 0.19 |
| **BioBERT (best)** | **0.92** | **0.90** |
| BlueBERT | 0.92 | 0.90 |
| GPT-4.1 (classify only) | 0.87 | 0.78 |
| GPT-4.1 (generation + classify) | 0.89 | 0.85 |

BioBERT achieved the best overall performance (Acc 0.92, F1 0.90), benefiting from biomedical-domain pretraining. GPT-4.1 improved substantially after synthetic `Critical` augmentation (macro-F1 0.78 -> 0.85, accuracy 0.87 -> 0.89), showing the value of LLM generation for the rare class. RAG context consistently helped all LLMs; KNN failed to generalize on the Critical class.

## Notes / license
Student coursework (HIT). Question set derives from the public MedInfo2019-QA-Medications dataset (Abacha et al., 2019); RAG corpus grounds on DrugBank DDI and the WHO Essential Medicines List. Synthetic Critical questions were generated with GPT-4.1. Redistribute the data only as the source repository did. Presentations (PDF) were not copied.
