# Cover letter

**To:** The Editor-in-Chief, *International Journal of Medical Informatics*

**Re:** Submission of a Review article

Dear Editor,

We submit our manuscript, **"Clinical Communication Processing with Models Trained on LLM-Generated Synthetic Data: A Structured Survey and Novel Application Case Studies,"** for consideration as a **Review article** in the *International Journal of Medical Informatics*.

**Motivation.** Much of the clinically decisive information in medicine is conveyed through communication — patient narratives, clinician instructions, paramedic-to-hospital handovers, emergency-dispatch calls, nurse handoffs, and patient-portal messages — rather than through structured records. Corpora of such communication are scarce, privacy-sensitive, and costly to annotate, which limits progress in clinical natural language processing. Large language models now make it practical to generate synthetic clinical communication that can train and evaluate downstream models where real data is unavailable. This is a fast-emerging area that has lacked a unifying account.

**Contribution.** Our review organizes it, and grounds the organization in concrete applications:

- A taxonomy of clinical-communication channels and a *clinical source → LLM-generated communication → downstream model* framework that no prior review offers.
- An evaluation-regime analysis (train-on-synthetic / test-on-real) and a coverage comparison against the closest prior reviews.
- Ten application case studies that build clinical NLP systems for channels and a language with no labeled real-world data, distilling reusable design patterns and recurring failure modes.
- A public dataset and reproduction code released on Zenodo (doi:10.5281/zenodo.21820227), with a per-study reproduction script.

**Fit with IJMI.** The journal has published closely related work, including Rujas et al.'s scoping review of reviews on synthetic health data. Our review extends that line by organizing the field around communication *channels* and pairing the survey with application studies, an angle the existing reviews do not cover. We also state plainly the field's central open problem — that most evaluation is still on held-out synthetic data, with train-on-synthetic, test-on-real transfer the decisive next step — and present the evidence that does exist for it.

**Declarations.** The manuscript is original, has not been published previously, and is not under consideration elsewhere. All authors have approved the submission. The authors declare no competing interests. The work received no specific external funding. The manuscript is prepared with continuous line numbering for review.

Thank you for considering our submission.

Sincerely,

Alexander Apartsin (corresponding author), School of Computer Science, Holon Institute of Technology (HIT), Holon, Israel
Yehudit Aperstein, Intelligent Systems, Afeka Academic College of Engineering, Tel-Aviv, Israel
