# JHIR submission package

Target: **Journal of Healthcare Informatics Research** (Springer), **Review Article**.
Q1, IF 4.6; hybrid (publish free via the subscription route; open access optional, APC ~$3,590 only if elected).

## Why JHIR (vs IJMI)
JHIR is arguably the best **format** fit for this survey-plus-case-studies hybrid: its scope spans Analytics
(generative AI / ML for clinical text), Systems, and Human-centered Computing ("intelligent communication with
healthcare stakeholders"), and it has accommodated combined review-and-case-study papers. IJMI remains the
strong Elsevier alternative (see ../IJMI/).

## Files
| File | Purpose |
|---|---|
| `manuscript.docx` | Submission manuscript, Springer conventions. Line-numbered, double-spaced. Keywords + a **Statements and Declarations** section (Funding, Competing interests, Data availability, Author contributions, Ethics approval). **No Elsevier-style Highlights** (Springer does not use them). Numbered references. |
| `manuscript.pdf` | Reference PDF render. |
| `cover_letter.docx` / `.md` | Cover letter to the Editor-in-Chief, tailored to JHIR's three tracks. |

Built from `paper.html` via the `html2doc` skill (`review-manuscript` profile). Data/code on Zenodo
(concept DOI 10.5281/zenodo.21820227).

## Springer submission notes
- Article type: **Review Article**.
- Submit as **Word**, plain font (10-pt Times Roman); the built file follows this.
- **Author Contributions** and **Competing Interests** must also be entered in the submission interface, not only in the manuscript.
- Springer's exact Word template (zip) sits behind a JS-gated page: https://www.springer.com/gp/authors-editors/journal-author/word-template-zip-154-kb-/22044 — the built manuscript already follows Springer's plain-format requirements, so the .dotx is optional.

## VERIFY before submitting
- **Reference style** — CONFIRMED: JHIR uses numbered citations in square brackets `[n]`, which the manuscript already uses. No conversion needed.
- The introduction now frames the work across JHIR's three tracks (analytics / systems / human-centered computing).
- **CRediT / Author contributions** wording — adjust to actual contributions.
- **Funding / Competing interests / Ethics** — currently "none / not applicable"; update if needed.
- **Corresponding author** contact details — add in the submission interface.
