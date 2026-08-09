# JHIR acceptance punch-list

## Reviewer-level bottom line

The manuscript has a credible JHIR-shaped core: a communication-centered organizing framework, a cross-channel structured review, and a set of concrete applications that make the framework operational rather than purely conceptual. The fastest route from **major revision** to **accept** is not to add more case studies. It is to remove the few places where the manuscript currently overstates what its evidence establishes, make the Review methodology auditable, clarify exactly what the ten cases are, and make the framework itself visibly do analytical work.

The most important correction is non-negotiable: **the medication-question study is R+S→R under the manuscript's own Section 2.3 taxonomy, not S→R.** The study starts from 5,000 labeled real forum questions, adds synthetic critical questions to the training data, and evaluates on held-out authentic questions. That is precisely **real + synthetic training → real testing (R+S→R)**. It is the manuscript's only real-test application anchor, but it is **not** a pure train-on-synthetic/test-on-real demonstration. Several current sentences incorrectly turn it into “proof of synthetic-to-real transfer.” A JHIR reviewer will catch this immediately because the paper itself defines the regimes correctly only a few pages earlier.

What follows is ordered by acceptance leverage, highest first.

---

## 1. Correct the medication study everywhere: it is R+S→R, not S→R, and it is not “proof of synthetic-to-real transfer”

### (i) Specific problem

Section 2.3 explicitly defines:

- **S→S** = train synthetic, test synthetic;
- **S→R** = train synthetic, test real;
- **R+S→R** = train real plus synthetic, test real;
- **R→R** = train real, test real.

Section 3.2.4 then says that two reviewers label **5,000 real forum questions**, GPT-4.1 generates additional synthetic critical questions **to rebalance the training set**, and the held-out test questions are authentic patient-authored text. By the paper's own taxonomy, the augmented models are therefore **R+S→R**.

The manuscript nevertheless misclassifies the study in several high-visibility places:

- Abstract: “proof of synthetic-to-real transfer.”
- Abstract: the ten studies are called a “graded validation ladder,” with the medication study at the top as synthetic-to-real evidence.
- Section 2.3: the text says nine are S→S and one reports authentic text, leaving the reader to infer that the exception is S→R.
- Section 3.4: the medication result is explicitly called “train-on-synthetic-augmented, test-on-real (S→R).”
- Table 17: the medication study is labeled **S→R**.
- Conclusion: the discussion treats the medication study as the closest exception to the missing S→R evidence.

There is a second inconsistency tied to the same issue. The Abstract and Introduction say that the application studies concern settings with **“no labeled real-world data.”** That cannot be true of the medication study, which explicitly begins with 5,000 labeled real questions. The broader claim is also too categorical for studies seeded from labeled real datasets.

### (ii) Exactly what to change

**A. Abstract — replace the transfer claim.**

Replace the current wording beginning with “The ten studies form a graded validation ladder...” with something close to:

> “The ten studies span a graded real-world-grounding spectrum. Nine report their headline evaluation on held-out synthetic communication. One medication-question study augments labeled real training data with synthetic critical cases and evaluates on authentic patient-authored text (R+S→R), providing a real-test augmentation anchor but not a pure S→R demonstration. Pure train-on-synthetic/test-on-authentic validation therefore remains an open requirement.”

Do **not** use “proof of synthetic-to-real transfer.”

**B. Section 2.3 — make the count explicit.**

Replace the current summary with:

> “Across the ten application studies in Section 3, nine report headline results in the S→S regime. The medication-question study (Section 3.2.4) uses real-plus-synthetic training and authentic patient-authored testing (R+S→R). None of the ten application studies provides a pure S→R evaluation.”

That sentence is much stronger scientifically because it makes the boundary unambiguous.

**C. Figure 1 — show all relevant regimes.**

The figure caption currently emphasizes S→S and S→R. Because the only real-test case in the manuscript is actually R+S→R, the organizing figure should show at least **S→S, S→R, R+S→R, and R→R** as evaluation branches, or explicitly state that the framework distinguishes these regimes downstream.

**D. Section 3.4 — fix both terminology and interpretation.**

Replace:

> “...a genuine train-on-synthetic-augmented, test-on-real (S→R) result.”

with:

> “...a real-plus-synthetic training, test-on-real (R+S→R) result. It demonstrates evaluation against authentic communication and the use of synthetic data for rare-class augmentation, but it does not establish transfer from synthetic-only training.”

Then change “three grounding levels” to **“three real-world-grounding levels”** and explicitly state that these are **not equivalent validation levels**.

**E. Table 17 — correct row 7.**

Change the medication row from:

> Authentic data used: “Real labeled test set...” / Regime: “S→R”

to something like:

> Authentic data used: “Real labeled corpus used for training and testing; synthetic critical examples added to training only”
>
> Metric tested on: “Authentic patient text”
>
> Regime: **“R+S→R (headline); R→R comparator where reported”**

The current “real labeled test set” wording is itself incomplete because the study uses real labeled data on the training side as well.

**F. Conclusion — state the gap cleanly.**

Use:

> “Within the ten application cases, real-text testing is represented by one R+S→R augmentation study; none provides pure S→R evidence. Establishing synthetic-only training transfer to authentic communication, particularly for EMS, dispatch, handoff, and portal channels, therefore remains the most important external-validation step.”

**G. Remove the blanket “no labeled real-world data” claim.**

In the Abstract, Introduction, and Section 3 opening, replace variants of “channels and languages with no labeled real-world data” with:

> “channels and tasks for which task-specific authentic communication is scarce, restricted, highly imbalanced, or unavailable.”

Also replace “four seed generation from real structured data” with **“four seed generation from real datasets or de-identified records”**; not all four sources are naturally described as structured data.

### (iii) Why this raises accept odds

This is the single most important credibility repair. The current version defines the taxonomy correctly and then violates it in its flagship external-validity claim. Correcting it tells the reviewer that the authors understand the distinction between **synthetic augmentation** and **synthetic-only transfer**, which is central to the entire paper. It weakens one promotional sentence but materially strengthens the manuscript's scientific trustworthiness.

---

## 2. Make the medication study a genuinely auditable real-world anchor

### (i) Specific problem

Once the medication case is correctly classified as R+S→R, it becomes even more important because it is the **only application case whose headline evaluation is on authentic patient-authored text**. Yet the current description is too compressed for that burden.

The manuscript says “Two reviewers first label 5,000 real forum questions,” but does not report in the main text:

- the exact source citation for MedInfo2019;
- the real-data class distribution;
- the train/validation/test split sizes;
- whether the split was fixed **before** synthetic augmentation;
- whether synthetic generation had any access to held-out test questions;
- the labeling rubric;
- who the two reviewers were in terms of relevant expertise;
- inter-rater agreement;
- disagreement adjudication;
- deduplication or near-duplicate checks between generated training questions and authentic test questions.

The current sentence that the SVM “isolates that real-only signal” is also too strong. A real-only SVM versus an augmented BioBERT/BlueBERT comparison changes **both the training data and the model architecture**, so it does not isolate the causal benefit of synthetic augmentation for the encoder models.

### (ii) Exactly what to change

Add a compact reproducibility paragraph to **Section 3.2.4**, or a case-specific supplement referenced from that section, with the following items:

1. **Directly cite the authentic dataset** rather than relying only on the separate arXiv study citation. State the license/access condition.
2. Report **N real total, N real train, N validation, N authentic test**, and class counts for Critical/General in each split.
3. State explicitly: **“The authentic test split was fixed before synthetic generation and was not used in prompting, example selection, model selection, or augmentation.”** Use this sentence only if it is factually true.
4. State how synthetic critical questions were generated: exact generator/version, prompt source, number generated, filtering, deduplication, and final number admitted to training.
5. Report the two-reviewer annotation procedure: rubric, independent versus joint labeling, agreement statistic if available, and adjudication procedure.
6. State whether near-duplicate detection was run between augmented training items and the authentic test set. If it was, report the method and threshold. If it was not, run a simple lexical/embedding duplicate audit using the existing data; this is a high-value reanalysis and does not require new data collection.
7. If the existing code permits it, add a **same-architecture R→R comparator** for BioBERT or BlueBERT trained on the real training subset without synthetic augmentation. That is the cleanest way to quantify augmentation benefit. If you do not want to add this re-run, then remove any wording implying that the 0.90 encoder result itself proves augmentation improved performance.
8. Keep the GPT-4.1 0.78→0.85 comparison only if “classify only” and “generate + classify” are genuinely comparable on the same authentic test split and differ only by augmentation-related use of synthetic data. Explain the comparison precisely.

Revise the sentence:

> “the classical SVM baseline ... isolates that real-only signal”

to:

> “the SVM provides a real-data-only reference point, although model-family differences prevent it from isolating the incremental effect of synthetic augmentation.”

### (iii) Why this raises accept odds

The paper's strongest real-world evidence should also be its cleanest methodological description. A reviewer who trusts this one case will be more willing to accept the authors' disciplined framing of the other nine as feasibility/grounding cases. A reviewer who finds split ambiguity or data leakage in the sole authentic-text anchor will downgrade the whole manuscript.

---

## 3. Stop saying the ten selected cases “validate the framework”; say they instantiate, operationalize, and stress-test it

### (i) Specific problem

The Abstract and Introduction say “we validate the framework through ten ... application case studies.” That is methodologically too strong for the way the cases were selected. Section 2 explicitly says the cases were selected from graduate coursework **to span the communication channels** and are not a systematic sample. Cases deliberately selected to fit the proposed organizing dimensions cannot independently validate that taxonomy.

The word **“validation”** is also overloaded elsewhere: framework validation, real-world validation, synthetic-to-real validation, and the “validation ladder.” That blurs distinct ideas.

### (ii) Exactly what to change

Replace every occurrence of:

> “validate the framework through ten ... case studies”

with:

> “instantiate and stress-test the framework across ten illustrative application case studies”

or:

> “operationalize the framework through ten cross-channel application cases.”

In the Abstract, a strong replacement is:

> “We operationalize the framework through ten illustrative application case studies selected to span communication channels, source types, generation strategies, downstream tasks, and evaluation regimes.”

In the Introduction, add one explicit sentence defining what the cases do and do not establish:

> “The cases are used to demonstrate that the framework can consistently describe heterogeneous pipelines and expose their evidence gaps; they are not presented as an external validation sample of the taxonomy.”

Rename the phrase **“graded validation ladder”** to **“graded real-world-grounding spectrum”** or **“grounding ladder.”**

In Section 3.4 add:

> “These levels describe proximity to authentic data, not equivalent levels of external validation: a real-data source with synthetic communication and synthetic testing remains an S→S evaluation.”

Finally, give the framework simple, falsifiable utility criteria. For example, just before Section 3:

> “We use the framework as an organizing instrument with three practical tests: whether it can (1) map each pipeline unambiguously by source, communication channel, generation controls, downstream use, and evaluation regime; (2) expose missing evidence, especially authentic-text transfer; and (3) support cross-case synthesis of recurring design patterns and failure modes.”

### (iii) Why this raises accept odds

This change converts a vulnerable empirical claim into a defensible methodological contribution. “Instantiate” and “operationalize” are exactly what the cases actually do. The framework then becomes useful because it organizes evidence and reveals gaps, not because the authors claim to have statistically validated a taxonomy using examples selected to cover it.

---

## 4. Clarify what the ten studies actually are: framework evidence, course-derived demonstrations, prior publications, or standalone new projects

### (i) Specific problem

The manuscript currently sends three conflicting signals:

- Section 2 says the cases were **selected from graduate coursework** and are feasibility demonstrations.
- Section 3 says **“Each is a novel contribution in its own right.”**
- The Acknowledgments say students' course projects **“supplied the application studies.”**

At least some cases are also connected to separate publications cited in the manuscript (for example the diagnostic-questioning and medication-question studies). This creates unnecessary ambiguity about:

- whether Section 3 contains ten new original studies;
- whether some are summaries/reanalyses of already published work;
- whether unpublished student work is being republished as author-owned original research;
- whether the article is truly a Review or a package of multiple original research reports;
- whether contributor/authorship and permission issues have been handled.

For a Review submission, “ten novel contributions in their own right” is the wrong framing. It invites the editor to ask why ten original studies are embedded in a Review and why the underlying student contributors are not individually visible.

### (ii) Exactly what to change

**A. Rename Section 3.**

Use:

> **3. Illustrative Application Case Studies**

or:

> **3. Applying the Framework: Ten Illustrative Cases**

**B. Delete the sentence “Each is a novel contribution in its own right.”**

Replace the Section 3 opening with:

> “The ten cases are illustrative applications used to operationalize the framework across heterogeneous clinical-communication settings. They are not a systematic sample and are not treated here as ten independent full-scale empirical studies; their role is to show how the framework captures source provenance, communication form, generation controls, downstream use, and evaluation regime in concrete systems.”

If you want to preserve novelty, say:

> “Several cases contain previously unpublished application results; where a case has been reported separately, the corresponding publication is cited.”

Only use that sentence after you have made the provenance explicit.

**C. Add a provenance/status column to Table 7 or a new Supplementary Table.**

For every case, state:

- origin: course-derived / author-developed / other;
- prior publication status: previously published, preprint, or unpublished;
- what is reused here: dataset, pipeline, result, or only problem formulation;
- what is new in this manuscript: reanalysis, framework mapping, additional reproduction, or concise case synthesis;
- contributor attribution.

Do not leave the reader to infer this from scattered citations.

**D. Fix the Acknowledgments wording.**

The current phrase that students “supplied the application studies” raises an authorship question. Replace it with a factual statement that distinguishes project origin from the work reported in this paper. For example, **if true**:

> “Several application cases originated in supervised projects in the LLMs in Healthcare course. For the present manuscript, the authors curated the cases, verified the reported artifacts, performed the cross-case synthesis, and are responsible for the analyses reported here. Contributors to separately published studies are credited in those publications.”

If students performed substantial unpublished analysis that is reproduced here, do not solve that merely by rewriting the acknowledgment. Check contribution/authorship criteria and obtain appropriate permission/credit.

**E. Explicitly identify overlap with prior publications.**

For any case already published or posted as a preprint, add a one-sentence disclosure such as:

> “This case summarizes and reframes results reported in [reference] for the present cross-case framework analysis; no claim of independent replication is made here.”

### (iii) Why this raises accept odds

This removes a likely editorial objection before it is raised. It keeps the article squarely in the Review category, prevents duplicate-publication ambiguity, and eliminates a potential authorship/provenance concern created by the current “students supplied the studies” wording.

---

## 5. Upgrade the review-method paragraph into an auditable “Review Scope and Methods” subsection

### (i) Specific problem

The manuscript calls itself a **“structured survey”** in the title and a **“structured narrative review”** in the body, but the current method description is one paragraph. It names databases and broad years, but does not provide enough information to reproduce even a structured narrative search.

Missing elements include:

- exact date of the final search;
- complete search strings or query blocks;
- language restrictions;
- document-type/preprint policy;
- record counts;
- duplicate handling;
- title/abstract versus full-text screening procedure;
- who screened;
- how disagreements or borderline scope decisions were resolved;
- how forward/backward citation chaining was terminated;
- the final included-study set.

This matters because later sections make semi-quantitative statements such as “fourteen representative works,” “ten,” “nine,” “five,” etc., and the Introduction says “No prior review...” Those statements are stronger than the current narrative-search documentation supports.

### (ii) Exactly what to change

Create a visible subsection near the start of Section 2:

> **2.0 Review Scope and Methods**

Include, in compact form:

1. Databases/sources: PubMed/MEDLINE, ACL Anthology, arXiv, plus citation chaining and named venue browsing.
2. Exact search window and **last search date**.
3. The concept blocks used in the queries: e.g., synthetic/generative/LLM terms × clinical/health terms × communication/dialogue/message/handoff/dispatch/EMS/portal terms.
4. A pointer to **Supplementary Table S1** containing the exact search strings for each database.
5. Inclusion criteria stated operationally, not only conceptually.
6. Exclusion criteria, including structured/tabular-only synthetic records and papers in which the LLM only classifies existing communication.
7. Screening procedure: number of reviewers, independent/joint screening, and conflict resolution.
8. Record counts: retrieved, deduplicated, screened, full-text assessed, included. A lightweight flow figure is useful, but a table is sufficient if you do not want to invoke a full systematic-review framework.
9. Treatment of preprints and multiple versions of the same work.
10. Explicit statement that the review is **structured narrative/scoping-style rather than exhaustive/systematic**.

Do not call it PRISMA-compliant unless you actually follow and report PRISMA requirements.

Then revise the quantitative paragraph in Section 2.4. Either:

- state **“Within the literature included in this structured review...”** before giving counts; or
- remove the counts and describe concentration qualitatively.

Likewise replace:

> “No prior review organizes...”

with:

> “We did not identify a prior review that organizes...”

unless the strengthened search is sufficiently comprehensive to support a stronger absence claim.

### (iii) Why this raises accept odds

This is the highest-leverage change for the **Review** identity of the paper. It does not require a new clinical experiment. It turns “structured” from a rhetorical adjective into a reproducible method, which makes the literature synthesis, novelty claim, and gap analysis much harder to dismiss.

---

## 6. Directly position against the recent JHIR scoping review already cited as reference [20]

### (i) Specific problem

The manuscript cites a 2026 **Journal of Healthcare Informatics Research** paper, Rao, Liu, et al., “A Scoping Review of Synthetic Data Generation by Language Models in Biomedical Research and Application,” as reference [20]. Yet Table 1, which is explicitly labeled “Coverage of the closest prior reviews,” omits it.

For a submission to JHIR, this omission will be conspicuous. The handling editor is likely to ask: **What does this manuscript add beyond the synthetic-data scoping review JHIR has already published?** The current paper probably has a good answer—communication-channel organization, source→communication→model framing, evaluation-regime separation, and cross-channel applications—but it needs to answer that question explicitly.

Table 1 also uses “Own application studies?” as a comparison column. That is not the strongest scientific distinction because it gives the present manuscript a structural advantage by definition.

### (ii) Exactly what to change

**A. Add Rao et al. [20] to Table 1.**

Use only distinctions you can substantiate from that paper, but the row should be present.

**B. Add one explicit paragraph in the Introduction immediately before Table 1.**

Suggested structure:

> “The closest venue-specific comparator is the recent JHIR scoping review by Rao et al. [20], which surveys LLM-based synthetic data across biomedical research and applications. The present review deliberately narrows the unit of analysis to clinical communication and asks a different set of questions: which clinical source is transformed into which communication channel, which communication properties are controlled, how the generated communication is used by a downstream model, and under which synthetic/real evaluation regime utility is established. This channel- and pipeline-level focus exposes gaps—particularly EMS, dispatch, handoff, and authentic-text transfer—that are obscured when synthetic clinical text is treated as a single modality.”

Adjust the wording after checking [20] so that every contrast is fair.

**C. Redesign Table 1 columns.**

Prefer objective contribution dimensions such as:

- scope of synthetic modalities;
- explicit clinical-communication channel taxonomy;
- downstream-model/training focus;
- distinguishes S→S / S→R / R+S→R evaluation;
- coverage of EMS/dispatch/handoff/portal channels.

Drop or de-emphasize “Own application studies?”

### (iii) Why this raises accept odds

This is JHIR-specific positioning. It tells the editor immediately why the journal should publish a second review in a nearby area. Omitting JHIR's own recent scoping review from the “closest prior reviews” table invites a novelty challenge that is easy to prevent.

---

## 7. Make the reproducibility claim precise; distinguish frozen-dataset reproducibility from end-to-end LLM-generation reproducibility

### (i) Specific problem

The Section 3 opening says:

- reported metrics are single-run point estimates;
- every study has a reproduction script;
- a five-seed rerun confirms the metrics are stable, “standard deviations typically below 0.05”;
- therefore the single-run figures are “a reporting choice rather than a fragile one.”

The Data and Code Availability section repeats the broad five-seed claim.

However, the main tables visibly report mean±SD only for selected rows/cases, especially classical baselines and a few reproduced pipelines, while many headline neural/LLM results remain single point estimates. The wording therefore sounds broader than the evidence displayed in the manuscript.

There is also an important reproducibility distinction currently missing: rerunning a downstream classifier over an **archived synthetic dataset** is not the same as exactly reproducing the **LLM generation process**. Hosted LLM APIs, model revisions, sampling behavior, and non-determinism can make exact regeneration impossible even when prompts and seeds are recorded.

### (ii) Exactly what to change

**A. Remove the defensive sentence.**

Delete:

> “...so the single-run figures are a reporting choice rather than a fragile one.”

Replace with neutral evidence reporting.

**B. Add a Supplementary Reproducibility Table, one row per case.**

Columns should include:

- case/section;
- source dataset and version;
- synthetic dataset archived? yes/no;
- generator exact model name/snapshot;
- generation date/API or local checkpoint;
- prompt archived? yes/no;
- temperature/top-p/other sampling parameters;
- generation filtering/auditing;
- train/validation/test split and seed;
- downstream model/checkpoint;
- core hyperparameters;
- software/environment file;
- code path/command;
- immutable repository release/commit;
- five-seed downstream rerun available? yes/no;
- mean±SD for the reproduced metric;
- end-to-end regeneration tested? yes/no;
- data redistribution restrictions.

**C. If five-seed runs exist for all ten, show them.**

Do not summarize them only as “typically below 0.05.” Put the per-case means and SDs in a table. If five-seed runs exist only for some pipelines or baselines, narrow the global claim to exactly those cases.

**D. Separate two reproducibility levels in the Data and Code Availability section.**

Use wording like:

> “The archived synthetic datasets permit deterministic rerunning of downstream training/evaluation subject to the stated seeds and software environment. The generation prompts and parameters are also archived; exact end-to-end regeneration may depend on availability and versioning of the original LLM service.”

**E. Surface exact generator identities in the manuscript.**

“GPT,” “OpenAI batch,” or “model prompting” are not enough. The home-care and SBAR cases in particular should name the exact model/version in the main text or reproducibility supplement.

### (iii) Why this raises accept odds

JHIR readers will accept heterogeneous feasibility cases more readily if every case is traceable and reproducible. Precise reproducibility language also avoids a common generative-AI credibility problem: claiming exact reproducibility for pipelines whose generation stage depends on mutable hosted models.

---

## 8. Make the “framework” visibly more than a pipeline diagram plus a channel list

### (i) Specific problem

The paper's stated primary contribution is an organizing framework, but the current framework is distributed across Figure 1, the channel taxonomy, the RQs, and later evaluation-regime discussion. A skeptical reviewer can reasonably say: **this is a useful pipeline and taxonomy, but where is the integrated framework artifact?**

The paper already contains the ingredients. They need to be assembled into one explicit structure.

### (ii) Exactly what to change

Add a compact **Framework Matrix** immediately after Figure 1 or at the end of Section 1. Define six axes:

1. **Clinical source provenance** — real structured/de-identified records, real text, public benchmark, manually designed scenario, fully synthetic scenario.
2. **Communication channel/context** — patient–clinician, portal, remote-care, EMS, dispatch, handoff, instructions; participants, medium, urgency.
3. **Controlled communication properties** — role, intent, uncertainty, missingness, noise, code-switching, register, temporal detail.
4. **Generation strategy** — prompt/scenario/template/multi-agent/RAG/refinement/augmentation.
5. **Downstream use** — training, augmentation, evaluation/benchmarking, robustness testing.
6. **Evaluation/grounding regime** — S→S, S→R, R+S→R, R→R, cross-generator/human-written variants.

Then extend **Table 7** so the ten cases map onto these dimensions. The current columns—channel, generator, headline result—do not fully demonstrate the framework. A better Table 7 would include at least:

> Case | Source provenance | Channel | Controlled property | Synthetic-data role | Downstream task | Evaluation regime | Authentic-data touchpoint

Move detailed headline metrics to the individual case tables or a separate result-summary table if space becomes tight.

Add one sentence after the matrix:

> “The value of the framework is that source realism, communication realism, and evaluation realism are recorded separately rather than collapsed into a single ‘synthetic versus real’ label.”

That sentence directly supports the corrected Section 3.4 grounding analysis.

### (iii) Why this raises accept odds

It makes the central contribution tangible. A reviewer should be able to point to one figure/table and say, “This is the framework the paper contributes.” It also naturally resolves the synthetic/real ambiguity that currently causes the medication-study classification error.

---

## 9. Strengthen the human-centered-computing positioning—or stop presenting it as an established contribution

### (i) Specific problem

The Introduction says the work spans three healthcare-informatics concerns, including **“human-centered computing, in the clinician and patient communication these systems ultimately serve.”** That is presently too thin. Studying text produced by humans does not by itself constitute a human-centered-computing contribution.

The manuscript has no clinician/patient usability study, workflow evaluation, user-centered design study, or human-factors experiment. That is not fatal for a Review article, but the paper should either:

1. make the sociotechnical/human-centered dimension analytically substantive; or
2. soften the claim to “human-centered relevance/implications.”

### (ii) Exactly what to change

**A. Revise the Introduction claim.**

Preferred wording:

> “The framework has human-centered implications because clinical communication is shaped by participant roles, workflow position, time pressure, uncertainty, and the consequences of missed or false escalation; we do not claim usability or human-factors validation of the application cases.”

**B. Add human/workflow variables to the channel taxonomy.**

Extend Table 2 with two or three columns:

- **Workflow decision/action supported**;
- **Primary human user/recipient**;
- **Automation boundary / human confirmation** or **error consequence**.

For example:

- portal triage → care-team routing/prioritization → human review before clinical action;
- EMS pre-arrival → ED preparation/specialty routing → decision support under time pressure;
- SBAR completeness → outgoing/incoming staff → flag missing elements, not autonomously reconstruct them;
- medication questions → escalation queue → false negative can miss a safety risk, false positive increases workload.

**C. Add a short subsection in Section 4 or 5: “Human-centered and sociotechnical deployment.”**

Cover four concrete points already latent in the manuscript:

1. communication realism includes pragmatics and role, not just lexical fluency;
2. error costs differ by channel and should determine thresholds/metrics;
3. synthetic corpora can underrepresent culturally specific phrasing, code-switching, distress, and omission patterns;
4. the appropriate deployment target is usually decision support with human confirmation, not autonomous action.

**D. In the conclusion, say what human validation is still needed.**

One sentence is enough:

> “For deployment, authentic-text transfer must be complemented by clinician/patient evaluation of workflow fit, error consequences, and communication realism.”

### (iii) Why this raises accept odds

This gives the JHIR framing real depth without requiring a new human-subject experiment. It shows that the communication taxonomy is not merely a list of text genres; it captures the sociotechnical context in which an NLP output becomes clinically meaningful.

---

## 10. Align the title and scope with what the ten cases actually do: some use synthetic data for evaluation, not training

### (i) Specific problem

The title says:

> “Clinical Communication Processing with **Models Trained on** LLM-Generated Synthetic Data...”

The Introduction similarly defines the object of study as systems “trained, wholly or in part,” on synthetic data. But Section 3.1.2 explicitly says the adaptive diagnostic-questioning case is **an evaluation benchmark rather than a trained classifier**. Section 2.4 also treats benchmark construction as an in-scope use.

That creates an avoidable scope inconsistency.

### (ii) Exactly what to change

The cleanest title is:

> **Clinical Communication Processing Using LLM-Generated Synthetic Data: A Framework, Structured Survey, and Ten Application Case Studies**

or, if you want “communication” to remain the focal noun:

> **LLM-Generated Synthetic Data for Clinical Communication Processing: A Framework, Structured Survey, and Ten Application Case Studies**

Then change the scope sentence in Section 1 from:

> “NLP systems ... trained, wholly or in part, on such synthetic data”

to:

> “NLP systems and evaluation frameworks that use such synthetic communication for training, augmentation, robustness testing, or benchmarking.”

Update Figure 1 accordingly: downstream synthetic data can feed **training/augmentation** or **evaluation/benchmarking**.

### (iii) Why this raises accept odds

It removes a simple but visible logical inconsistency and broadens the paper exactly as the existing content already does. No scientific work is required—only accurate scope language.

---

## 11. Separate “real-source grounding” from “real-communication validation” throughout Section 3.4

### (i) Specific problem

Section 3.4 is a good addition, but its current three-level narrative still risks inflating the evidentiary value of cases that start from real records. A model can generate text from MIMIC-derived cases and still be evaluated only on synthetic language. That gives **clinical-content grounding**, not evidence that the generated communication distribution matches actual EMS/portal/handoff language or that the downstream model transfers to it.

The current text says the four real-seeded studies have labels/content “anchored in reality,” which is fair, but the surrounding “validation ladder” language can make these studies sound closer to external validation than they are.

### (ii) Exactly what to change

Recast Section 3.4 around **three independent questions**, not a single ladder:

1. **Is the source clinically grounded in authentic data?**
2. **Is the communication itself authentic or synthetic?**
3. **Is the evaluation performed on authentic or synthetic communication?**

Then say:

> “These dimensions should not be collapsed. Real-source grounding strengthens clinical-content provenance, but only authentic communication in the evaluation set directly tests transfer across the synthetic-to-real language gap.”

In Table 17, consider splitting “Authentic data used” into:

- Source grounding;
- Training communication;
- Test communication;
- Regime.

That format makes the medication case automatically read as:

> real source/real training + synthetic augmentation / real test / R+S→R

and the EMS case as:

> real clinical source / synthetic training / synthetic test / S→S.

### (iii) Why this raises accept odds

This is conceptually cleaner than a one-dimensional “validation ladder” and directly reinforces the paper's framework contribution. It also prevents reviewers from accusing the manuscript of dressing real-source seeding up as external validation.

---

## 12. Tighten every performance claim so it says exactly where the evidence was measured

### (i) Specific problem

Several sentences slide from **synthetic-benchmark performance** to language that sounds like real-world competence. Because nine of ten cases are S→S, this is a recurring acceptance risk.

Examples:

- Section 3.2.1: “the fine-tuned heads ... route reliably” and a local generator “can bootstrap a competent triage model.” The evidence is synthetic test performance.
- Section 3.3.1: noisy synthetic training “improves robustness.” The test is still synthetic; it does not establish robustness to authentic EMS speech/transcripts.
- Table 18: deliberate degradation is said to train models that “hold up on degraded real-world input.” The cases cited do not provide real-world degraded test input.
- Section 3.2.5: fusion is said to “confirm” that message text adds signal beyond vitals, but both modalities and their coupling were synthetically constructed.
- Introduction: “the model does not invent clinical truth” contradicts the later hallucination section.
- Section 2.2.1: synthetic text is described as shareable without consent/de-identification burdens, while Section 4 correctly notes that synthetic outputs can retain privacy risk and governance constraints.

### (ii) Exactly what to change

Apply a manuscript-wide evidence-language pass using these replacements:

**Portal case:**

> “The fine-tuned heads achieve strong held-out synthetic performance...”

rather than “route reliably” or “competent triage model.”

**EMS case:**

> “Within the synthetic noisy-channel evaluation, training with degraded variants improves robustness to similarly degraded inputs.”

Do not imply authentic radio/ASR transfer.

**Table 18 degradation pattern:**

Replace:

> “hold up on degraded real-world input”

with:

> “improve performance on degraded synthetic inputs designed to approximate channel noise; authentic-channel validation remains required.”

**Home-care case:**

Replace “confirming that the message adds signal beyond the vitals alone” with:

> “showing, within this synthetic benchmark, that the generated message contributes predictive signal beyond the generated vital-sign deltas.”

**Introduction factual-control sentence:**

Replace:

> “the source defines the intended facts and the generator realizes them in language; the model does not invent clinical truth”

with:

> “the source is intended to define the clinical facts and the generator realizes them in language, but source-to-text fidelity must still be verified because generation can introduce omissions, contradictions, or hallucinated details.”

**Privacy sentence:**

Replace categorical sharing language with:

> “Fully synthetic communication with no patient-level source can reduce privacy and de-identification burdens, while source-conditioned generation still requires leakage, licensing, and governance review.”

### (iii) Why this raises accept odds

A reviewer is much more likely to accept strong synthetic results when the paper is disciplined about where those results stop. The current limitations section is already appropriately cautious; the fix is to make the case-study prose match that caution.

---

## 13. Fix the visible internal counting and labeling errors before submission

### (i) Specific problem

There are several simple inconsistencies that undermine confidence because the paper's core contribution is organization/taxonomy:

1. Section 3.2 says **“The six studies below”**, but Sections 3.2.1–3.2.5 contain **five** studies.
2. Section 3.3 says **“The three studies below”**, but Sections 3.3.1–3.3.2 contain **two** studies.
3. Section 2.4 says **“nine of the ten studies target portal messaging and these pre-hospital and handoff channels.”** By the paper's own Section 3 organization, five are in 3.2 and two are in 3.3, so the natural count is **seven**, not nine.
4. Table 7 numbers “Adaptive diagnostic questioning (3.1.2)” as #1 and “Diagnosis from noisy self-descriptions (3.1.1)” as #2, which is unnecessarily out of section order.
5. Section 3.2 is titled “Telemedicine and Patient-Portal Messaging,” but its opening sentence defines the whole group as asynchronous patient writing, which does not describe telemedicine generally. The five cases are more accurately portal/remote-care messaging applications.
6. Section 2.3 says macro-F1 is the headline metric “throughout Section 3,” although the cases also use accuracy, micro-F1, weighted kappa, recall, and benchmark-specific outcomes.

### (ii) Exactly what to change

- “six studies” → **“five studies.”**
- “three studies” in Section 3.3 → **“two studies.”**
- “nine of ten” → **“seven of ten”** if the intended grouping is Sections 3.2+3.3; otherwise rewrite the grouping so the count is transparent.
- Reorder Table 7 into manuscript section order.
- Consider renaming 3.2 to **“Patient-Portal and Remote-Care Messaging”** unless a genuinely synchronous telemedicine case is present.
- Replace the macro-F1 sentence with:

> “Macro-F1 is emphasized for imbalanced multiclass tasks, while task-appropriate metrics such as accuracy, recall, weighted kappa, and exact match are retained where they better reflect the target.”

### (iii) Why this raises accept odds

These are fast fixes with disproportionate credibility benefit. In a framework/review paper, incorrect counts and labels make reviewers question whether the synthesis was carefully audited.

---

## 14. Standardize the ten case-study summaries so they can be compared rather than read as ten differently shaped mini-papers

### (i) Specific problem

The Section 3 opening itself says the exposition “varies with the study, leaning on prose, a results table, or a figure as best fits the material.” That makes the section readable, but it works against the paper's framework claim. A framework paper should apply the **same analytical template** to heterogeneous cases.

At present, some cases report generator details, others do not; some give test N, others do not; some state the evaluation regime only later in Table 17; some emphasize clinical motivation while others emphasize model comparisons.

### (ii) Exactly what to change

Use the same seven-line template in every case, either as prose labels or a compact standardized box:

1. **Clinical communication problem**
2. **Source provenance**
3. **Synthetic generation and controlled properties**
4. **Synthetic-data role** — training / augmentation / evaluation
5. **Downstream task and baselines**
6. **Evaluation regime and test provenance**
7. **Main result + validity boundary**

For example, every case should contain a sentence of the form:

> “Evaluation regime: S→S; both training and test communication are synthetic, although the source labels derive from MIMIC-IV-ED.”

or:

> “Evaluation regime: R+S→R; authentic labeled questions are used in training and testing, and synthetic critical questions augment training only.”

Use Table 7 as the cross-case summary and move nonessential model-detail tables/figures to the supplement if necessary to preserve the Review article's center of gravity.

### (iii) Why this raises accept odds

Standardization demonstrates the framework rather than merely asserting it. It also shortens reviewer effort: the evidence boundary of each case becomes visible in seconds.

---

## 15. Strengthen statistical/reporting discipline without turning the Review into a new experimental paper

### (i) Specific problem

The case-study evidence is heterogeneous and often presented as single point estimates. That is acceptable for illustrative feasibility cases if clearly labeled, but the manuscript occasionally compares model differences as though they were stable rankings. High-stakes tasks also need class-specific operating characteristics, not only aggregate F1.

The medication case is especially important: for a rare “Critical” class, a 0.90 macro-F1 does not tell the reader the false-negative rate on the safety-relevant class.

### (ii) Exactly what to change

Using existing predictions/reruns where available:

- report test-set N and class support for every case;
- report mean±SD for the five-seed results you already say exist;
- add 95% bootstrap confidence intervals where predictions are already saved and this can be computed without new model runs;
- for safety/triage cases, report **critical/urgent-class recall and precision** alongside macro-F1;
- for ordinal distress/severity, retain weighted kappa and state why it is appropriate;
- avoid declaring a model “best” when the difference is only a single-run point estimate without uncertainty;
- explicitly separate **feasibility comparison** from **benchmark ranking**.

For the Section 3 opening, use:

> “The case studies are intended as feasibility demonstrations rather than a unified benchmark; cross-model point differences are therefore interpreted descriptively unless repeated-run uncertainty is reported.”

### (iii) Why this raises accept odds

This prevents a reviewer from turning a Review paper into a demand for a full multi-seed benchmark study. You acknowledge the evidentiary level and add the uncertainty information that is already cheap to expose from existing artifacts.

---

## 16. Tighten ethics/data-governance wording, especially around authentic forum questions, MIMIC-derived sources, and student-derived cases

### (i) Specific problem

The declarations currently say:

> “Ethics approval. Not applicable. The study uses LLM-generated synthetic data and publicly available datasets; it involves no human participants or identifiable patient data.”

That statement is too sweeping relative to the manuscript itself:

- the medication case uses **authentic patient-authored forum questions**;
- MIMIC data are de-identified and governed/access-controlled, not simply equivalent to unrestricted public text;
- two human reviewers label 5,000 real questions;
- course projects supplied or motivated application cases.

None of this necessarily means new IRB approval was required, but the declaration should accurately describe the provenance rather than implying the paper uses only synthetic content.

### (ii) Exactly what to change

Use a more precise declaration, subject to the actual institutional facts:

> “No new patient recruitment or prospective human-subject data collection was performed for this review. The application cases use combinations of LLM-generated synthetic data, existing public consumer-question datasets, and de-identified/access-controlled research datasets under their original governance terms. No identifiable clinical records were newly collected for this study.”

Then, where required, state separately:

- ethics/governance status of each source dataset follows its original release;
- MedInfo2019 terms/license and whether verbatim examples may be redistributed;
- MIMIC access requirements;
- whether student-derived project artifacts were reused with permission;
- synthetic artifacts generated from restricted sources are shared only where licenses permit.

Do not say synthetic data automatically eliminates privacy risk; the manuscript's own Section 4 correctly argues the opposite.

### (iii) Why this raises accept odds

Precise governance language is especially important in healthcare informatics. It prevents an editor from finding an ethics statement that appears inconsistent with the paper's own description of authentic data use.

---

## 17. Make the literature synthesis look less self-referential and more clinically anchored

### (i) Specific problem

Section 2.4 introduces several “generic NLP problem settings” from adjacent domains, including nonclinical work on reminiscences, maritime distress, semantic text comparison, educational sentiment, and other author-associated projects. These analogies can be useful, but in the current Review they risk diluting the healthcare-informatics synthesis and creating the impression that adjacent self-citations are being used to fill sparse clinical evidence.

The quantitative counts in the same section also mix “representative” references with a narrative-search sample, which makes them look more systematic than they are.

### (ii) Exactly what to change

- Keep adjacent-domain work only where it explains a transferable method that has no adequate clinical analogue.
- Label it explicitly as **“adjacent methodological precedent,” not clinical evidence**.
- Lead every task subsection/table row with external clinical literature where available.
- Prune nonessential self-citations from the main narrative, especially where they are not needed to establish the review's clinical claim.
- If you retain task counts, write **“within the included review corpus”** and ensure the review-method section defines that corpus.

### (iii) Why this raises accept odds

A JHIR reviewer should come away seeing a synthesis of healthcare-informatics evidence, with adjacent NLP work used sparingly as methodological context. This also strengthens the perceived independence of the survey contribution.

---

## 18. Do one final front-to-back wording pass so the Abstract, Introduction, Section 3.4, and Conclusion tell exactly the same evidence story

### (i) Specific problem

The manuscript has already been reframed toward JHIR, but the highest-level story is still inconsistent in four places:

- **Abstract:** framework “validated”; medication = “proof” of S→R.
- **Introduction:** ten novel cases with no labeled real data; framework “validated.”
- **Section 3:** each case is a novel standalone contribution; almost all S→S.
- **Section 3.4/Conclusion:** real-world grounding is acknowledged, but the medication case is still mislabeled and real-source grounding is partly mixed with real-text validation.

A reviewer should not have to reconcile these versions.

### (ii) Exactly what to change

Use one consistent three-part claim everywhere:

1. **Framework contribution:** the paper organizes synthetic clinical communication by source → communication channel/properties → downstream use → evaluation regime.
2. **Review contribution:** the structured review maps a fragmented literature into that framework and identifies under-covered channels/evidence gaps.
3. **Case-study contribution:** ten illustrative applications operationalize the framework and reveal recurring design patterns; nine are S→S, while one is R+S→R; **none is pure S→R**, so authentic-transfer evidence remains the principal open validation requirement.

A concise Abstract-ready version is:

> “We introduce a source-to-communication-to-model framework paired with a taxonomy of clinical-communication channels and use it to structure the literature by source provenance, controlled communication properties, downstream task, and evaluation regime. Ten illustrative application cases operationalize the framework across patient, portal, EMS, and handoff settings and expose recurring design patterns such as fine-tuned small encoders, controlled degradation, and rare-class augmentation. Nine cases report headline evaluation on synthetic communication; one medication-question case uses real-plus-synthetic training and authentic patient-authored testing (R+S→R). Thus the cases establish cross-channel feasibility and real-test augmentation evidence, while pure S→R transfer remains the principal validation gap.”

For the Conclusion, mirror that language rather than introducing any stronger claim.

### (iii) Why this raises accept odds

Editors often decide from the Abstract, Introduction, and Conclusion whether a revision has actually resolved a conceptual criticism. If all three state the same disciplined evidence hierarchy, the paper will read as intentionally designed rather than retroactively caveated.

---

# Recommended order of execution

For speed, make the revision in this order:

1. **Global taxonomy/claim repair:** R+S→R correction, remove “proof,” remove “validate the framework,” rename “validation ladder,” fix “no labeled real-world data.”
2. **Section 3 identity repair:** rename as illustrative applications, add provenance/status, standardize evaluation-regime statements, fix student/previous-publication disclosure.
3. **Review methods:** add reproducible search subsection, exact search appendix, counts, screening procedure, and soften absence/prevalence claims as needed.
4. **Reproducibility:** add one per-case reproducibility table; expose five-seed results actually available; distinguish archived-data reruns from end-to-end regeneration.
5. **Framework/HCC:** add the integrated framework matrix and human/workflow axis.
6. **JHIR-specific literature positioning:** add Rao et al. [20] to Table 1 and make the distinction explicit.
7. **Consistency cleanup:** counts, title/scope, metrics wording, ethics language, synthetic-evaluation qualifiers.

None of the first six requires collecting new patient data or adding another application study. The only potentially useful computational addition is a same-model real-only comparator for the medication case and/or a train/test duplicate audit, both using data already described in the manuscript.

---

# If you only do 3 things

1. **Fix the external-validity story completely.** Reclassify the medication case as **R+S→R**, state explicitly that **none of the ten cases is pure S→R**, replace “proof of synthetic-to-real transfer” with “real-test augmentation anchor,” and relabel the “validation ladder” as a real-world-grounding spectrum.

2. **Make the paper unmistakably a Review with illustrative framework cases.** Replace “validate the framework” with “instantiate/operationalize/stress-test,” delete “each is a novel contribution in its own right,” add a one-row-per-case provenance/publication-status disclosure, and resolve the “students supplied the application studies” authorship/provenance ambiguity.

3. **Make the evidence auditable.** Expand the review search method enough to reproduce the structured literature corpus, add the recent JHIR scoping review [20] to the closest-review comparison, and add a per-case reproducibility table that shows exactly what data, generator, prompt, split, seed, code, and real/synthetic evaluation regime produced each headline result.