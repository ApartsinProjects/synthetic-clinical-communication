# EMS Report Routing

- **Paper section:** 3.4.1
- **Source repository:** https://github.com/nofarGIT1/medalert-llm-ems-voice-ed-classification

## Motivation
EMS pre-arrival radio reports let an Emergency Department prepare before a patient arrives, choosing a care area and anticipating specialty support. Such reports are short, variably worded, spoken rapidly, and distorted by ambulance noise and automatic transcription. This study asks whether a classifier trained on both clean reports and noisy ASR transcripts can route reports robustly under ASR noise, predicting two targets: ED Care Area and Primary Specialty Consultation (mapped into 18 categories).

## Data generation protocol
Source cases came from MIMIC-IV-Ext-CDS (v1.0.2, PhysioNet; not redistributed here). The ED care-area target was built with rule-based criteria; the specialty target was derived from LLM-generated specialty referrals and mapped into 18 broader consultation categories. GPT-4.1-mini then generated four EMS pre-arrival report variants per source case (`professional_complete`, `brief_radio_missing_details`, `patient_reported_uncertain`, `distracted_or_disorganized_handoff`), giving 2,139 source cases x 4 = 8,556 synthetic clean reports after leakage checks and two rounds of LLM post-processing. A TTS + ASR augmentation pipeline (Edge-TTS synthetic male voice, speech acceleration, synthetic siren + white-noise injection, Whisper Base transcription) produced noisy ASR transcripts at ~44% average Word Error Rate. Splits were by `source_case_id` to prevent leakage across variants.

## Data files
| Filename | Description | Rows / size |
|---|---|---|
| synthetic_data.sample.csv | First 200 rows of the cleaned clean-report dataset (sample) | 200 rows sampled; full file 8,556 reports (8,557 lines), 15.7 MB |
| results.csv | Full BioClinicalBERT + DistilBERT results across all four training/test setups | 945 B |

Not copied: `ems_asr_noisy_dataset_8556.zip` (2.4 MB zip of noisy ASR transcripts, 8,556 transcripts) and the two large generation/ASR notebooks (2.7 MB and 3.5 MB). The full clean CSV (15.7 MB) exceeded the 15 MB copy limit, so only a 200-row sample is included.

## Models trained and evaluated
- Synthetic report generation: GPT-4.1-mini. TTS: Edge-TTS. ASR: Whisper Base.
- Classifiers: BioClinicalBERT (main clinical model) and DistilBERT (general-language baseline).
- Four setups per target: Clean to Clean; Clean to Noisy ASR; Noisy ASR to Noisy ASR; Clean + Noisy ASR to Noisy ASR (full system). Primary metric: Macro F1.

## Results
Noisy-test Macro F1 (evaluated on the same noisy ASR test set):

| Target | Clean+Noisy (full) | Without Noisy Train | Without Clean Train |
|---|---|---|---|
| ED Care Area | 29.16% | 22.55% | 27.64% |
| Specialty Consultation | 38.33% | 27.74% | 31.21% |

Combined clean + noisy training gave the best noisy-test Macro F1 for both targets. Clean-to-clean reference baseline: 31.86% (ED Care Area), 50.60% (Specialty). Removing noisy training cost 6.61 / 10.59 points; removing clean training cost 1.52 / 7.12 points.

## Notes / license
Student coursework (HIT, B.Sc. Digital Technologies in Medicine). Built on MIMIC-IV-Ext-CDS (credentialed PhysioNet data, not included). Data is synthetic; redistribute only as the source repository did.
