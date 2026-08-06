"""
write_manual_generation_prompts.py — Manual Generation Pipeline, Step D

Converts manual_generation_tasks_*.jsonl into prompt batch files that can be
pasted into ChatGPT or Claude.  Each batch file is a Markdown document with
full instructions and a JSON block containing up to batch_size tasks.

Usage:
    python src/write_manual_generation_prompts.py \\
        [--input data/intermediate/manual_generation_tasks_50.jsonl] \\
        [--batch-size 5] \\
        [--output-dir data/api_expansion/manual_generation_prompts] \\
        [--include-few-shot]

Outputs:
    data/api_expansion/manual_generation_prompts/prompt_batch_001.md
    data/api_expansion/manual_generation_prompts/prompt_batch_002.md
    ...
    data/api_expansion/manual_generation_prompts/index.csv
"""

import sys as _sys
from pathlib import Path as _Path
_here = _Path(__file__).resolve()
while _here.name != "code" and _here != _here.parent:
    _here = _here.parent
for _sub in sorted(_here.rglob("*")):
    if _sub.is_dir() and not _sub.name.startswith("__") and str(_sub) not in _sys.path:
        _sys.path.insert(0, str(_sub))

import argparse
import csv
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
import target_quality


# ── Prompt template pieces ─────────────────────────────────────────────────────

_INSTRUCTIONS = """\
## Instructions

You are generating synthetic Hebrew hospital discharge summaries for an academic NLP dataset.

For **each task** in the Tasks section below:

1. Generate one natural Hebrew hospital discharge summary.
2. The summary should sound like a realistic Israeli clinical discharge note, not a translation exercise.
3. The summary should include a brief hospitalization course and discharge / follow-up instructions.
4. Use `clinical_background` items **only as clinical background** — do NOT extract or label them.
5. Include **every** `required_targets` entry that has label `drug_decision` or `procedure_decision`.
6. Do **not** add any new drug decision or procedure decision that was not listed in `required_targets`.
7. You may add generic clinical background text, but it must not introduce new treatment decisions.
8. Follow the `generation_attributes` exactly:
   - `writer_style` — tone and perspective of the author
   - `text_format`  — structural layout of the summary
   - `length_profile` — approximate word count target
   - `language_mix` — Hebrew / English balance for medical terminology
   - `clinical_focus` — which aspects of care to emphasise
   - `noise_level` — stylistic noise in non-target text only
9. Medication, procedure, and problem names may be written in Hebrew, English, or a mix
   according to `language_mix`. Translation is allowed.
10. **Critical**: every `mention_text` you report in `target_mentions` must appear
   **exactly, character-for-character**, inside `summary_text_he` (verbatim substring).
11. If you cannot generate a valid example for a task, return `"status": "failed"` with a reason.

---

## Required Output Format

Return raw valid JSON only.

- Your response must be the exact content of a `.json` file.
- Return only valid JSON file content.
- The response must be valid `.json` file content that can be saved directly as a JSON file.
- The first character of the response must be `[`.
- The last character of the response must be `]`.
- Do not wrap the output in ```json fences.
- Do not add Markdown.
- Do not return prose, explanations, Markdown, or code fences.
- Do not add explanations before or after the JSON.
- The response must be directly pasteable into `manual_generation_outputs/batch_XXX_response.json` without editing.
- If you include anything before or after the JSON array, the output will be considered invalid.
- The output must be a single JSON array with one object per `generation_task_id` in the batch.

Return a **JSON array** — one object per task — with **no Markdown, no explanations, only JSON**.

Each successful task object:
```
{
  "generation_task_id": "<same as input>",
  "source_note_id": "<same as input>",
  "status": "ok",
  "summary_text_he": "<full Hebrew summary text>",
  "target_mentions": [
    {
      "mention_text": "<exact verbatim substring from summary_text_he>",
      "label": "drug_decision",
      "canonical_concept": "<from required_targets>",
      "canonical_action":  "<from required_targets>",
      "source_target_id":  "<target_id from required_targets>"
    }
  ],
  "generation_attributes": { ... }
}
```

Failed task object:
```
{
  "generation_task_id": "<same as input>",
  "source_note_id": "<same as input>",
  "status": "failed",
  "reason": "<short explanation>"
}
```

## Hebrew Naturalness Requirements

- `summary_text_he` must be mostly natural Hebrew.
- It should read like an Israeli hospital discharge note, not a literal translation exercise.
- Use concise clinical Hebrew around each target mention.
- Do NOT paste full `raw_text_en` sentences into `summary_text_he`.
- `raw_text_en` is only source meaning, not text that must be copied.
- Treat `raw_text_en` as semantic evidence only. If it is long or unnatural, summarize the clinical decision in Hebrew.
- Do not copy long English phrases from `raw_text_en` into `summary_text_he`.
- Do not include awkward English fragments from `raw_text_en`.
- Medication names may remain in English when clinically natural, for example Aspirin, Lopressor, amiodarone, Vancomycin.
- Medication names may remain in English, but the surrounding clinical action should be Hebrew.
- Procedure names may remain in English when natural, but surrounding clinical action should be Hebrew when possible.
- Common clinical abbreviations may remain in English when clinically natural, for example INR, CT, MRI, PO, BID.
- Full clinical actions and procedure descriptions should be phrased naturally in Hebrew when possible.
- Every `mention_text` must include action + concept.
- For medications, `mention_text` should include the clinical decision phrase, not only the medication name.
  Good examples include: "הוחלט להתחיל Aspirin", "יש להמשיך Coumadin", "הוחלט להפסיק Lisinopril".
  Good: "הוחלט להתחיל Aspirin", "הוחל טיפול ב-Vancomycin", "יש להמשיך טיפול ב-aspirin", "נרשם Albuterol inhaler לפי צורך".
  Bad: "Aspirin", "Vancomycin", "Prednisone", "Albuterol Sulfate".
- For procedures, `mention_text` should include the performed/planned procedure phrase.
  Good examples include: "בוצעה אקסטובציה", "מתוכננת קולונוסקופיה".
  Good: "בוצעה אקסטובציה ביום הראשון לאחר הניתוח", "הוצא נקז חזה שמאל", "ניתנו נוזלים תוך-ורידיים לתמיכה בלחץ הדם".
  Bad: "extubation", "IV fluids", or a copied raw English sentence.
- Do not include medications or procedures from `clinical_background` as `target_mentions`.
- Do not add extra drugs or procedures just to make the summary realistic.
- Do not include pharmacy boilerplate such as `Sig:`, `Disp:`, `Refills:`, `Tablet(s)`, or `Capsule(s)` unless explicitly required and unavoidable.
- Do not include de-identification placeholders such as `[**...**]`.
- `target_mentions[].mention_text` must be the exact substring that appears inside `summary_text_he`.
- `mention_text` does NOT need to equal `raw_text_en`.
- `mention_text` should usually be the Hebrew or mixed Hebrew-English surface phrase created in the summary.
- `mention_text` should usually be 3-18 words.
- `mention_text` should be clinically meaningful and include action + concept.
- For conditional medication holds, preserve the conditional meaning. Phrase them as "יש להשהות/לא לתת אם..." rather than a permanent discontinuation.
- Do not translate `canonical_concept` or `canonical_action` fields. Keep them exactly from `required_targets`.
- Keep `generation_task_id`, `source_note_id`, `source_target_id`, `canonical_concept`, and `canonical_action` exactly aligned with the input.

## Bad vs Good Examples

Bad:
- `raw_text_en`: "was extubated during postoperative day #1"
- `summary_text_he` contains: "was extubated during postoperative day #1"

Good:
- `summary_text_he` contains: "בוצעה אקסטובציה ביום הראשון לאחר הניתוח"
- `target_mentions[].mention_text`: "בוצעה אקסטובציה ביום הראשון לאחר הניתוח"

Bad:
- `raw_text_en`: "His left chest tube was discontinued..."
- `summary_text_he` contains the full English sentence.

Good:
- `summary_text_he` contains: "הוצא נקז חזה שמאל ובהמשך הוצא גם נקז חזה ימין"
- `target_mentions[].mention_text`: "הוצא נקז חזה שמאל ובהמשך הוצא גם נקז חזה ימין"

Bad:
- `raw_text_en`: "Prednisone 10 mg Tablet Sig: One (1) Tablet PO once a day... Disp:*19 Tablet(s)* Refills:*0*"
- `summary_text_he` copies the pharmacy line with `Sig:`, `Disp:`, and `Refills:`.

Good:
- `summary_text_he` contains: "הוחל טיפול ב-Prednisone במתווה יורד ל-10 ימים"
- `target_mentions[].mention_text`: "הוחל טיפול ב-Prednisone במתווה יורד ל-10 ימים"

Bad:
- `raw_text_en`: "Albuterol Sulfate 90 mcg/Actuation HFA Aerosol Inhaler Sig..."
- `target_mentions[].mention_text`: "Albuterol Sulfate"

Good:
- `summary_text_he` contains: "נרשם Albuterol inhaler לפי צורך בקוצר נשימה"
- `target_mentions[].mention_text`: "נרשם Albuterol inhaler לפי צורך בקוצר נשימה"

Bad:
- `raw_text_en`: "Please take all medications as perscribed. Please refrain from using amoxicillin..."
- This should not be used as a `start` target because it contradicts the action and encourages English copying.

Medication example:
- It is acceptable for `summary_text_he` to contain: "הוחלט להתחיל Aspirin 81 mg po qd"
- `target_mentions[].mention_text` should be: "הוחלט להתחיל Aspirin 81 mg po qd"
- This is acceptable when it is natural under the requested `language_mix`.

## Output Safety Rules

- **No ASCII double quotes** inside `summary_text_he` or `target_mentions[].mention_text`. The character `"` is a JSON string delimiter — if unescaped it corrupts the JSON output.
- For medication doses, use **only English units**: `mg`, `mL`, `mcg`, `units`, `PO`, `IV`, `q12h`. Do **not** use Hebrew dose abbreviations in any form.
- Do **not** write any Hebrew unit abbreviation. Every dose must use English units: `40 mg`, `5 mL`, `500 mcg`. Writing מג, מ"ג, מ״ג, מ"ל, מ״ל, or any Hebrew unit abbreviation is forbidden — it corrupts the JSON output.
- Do **not** invent patient names, ages, exact dates, department names, or identifying demographic details that are not explicitly provided in the input task.
- Before returning your JSON response, internally verify: read back every `mention_text` and confirm it appears character-for-character inside `summary_text_he`.
- For each required target: decide the final mention phrase first, write it into `summary_text_he`, then paste that exact same string into `target_mentions[].mention_text`. Do not paraphrase between the two.
- If `text_format` is `bullet_points`, the summary must contain actual bullet lines starting with `-` or `•`. A plain paragraph does not satisfy this requirement.
- If `length_profile` is `long_180_260_words`, produce approximately 180–260 words. A short paragraph of 50–80 words does not satisfy this requirement.
- If `length_profile` is `medium_120_180_words`, produce approximately 120–180 words.

## Length Rules

- `short_80_120_words`: produce 90–120 words, at least 5 sentences.
- `medium_120_180_words`: produce 130–180 words, at least 7 sentences.
- `long_180_260_words`: produce 190–260 words, at least 9 sentences.
- Do **not** return a 30–70 word summary regardless of the profile. Word count is counted by whitespace-separated tokens.
- If you need to fill length, add clinically neutral hospitalization course details: vital signs, physical exam findings, lab context, follow-up recommendations. Do **not** add new drug or procedure decisions to fill length.

## Mention Quality Rules

- For each required target: (1) decide the exact decision phrase; (2) write that phrase verbatim into `summary_text_he`; (3) copy-paste the **exact same substring** into `target_mentions[].mention_text`. Do not rewrite, normalize, translate, shorten, or paraphrase between step 2 and step 3.
- If unsure whether a phrase will appear verbatim, choose a shorter exact substring from the summary — but it must still contain **both** an action cue and the drug/procedure concept.
- `mention_text` must contain **both** a clinical action cue and the drug/procedure concept. Concept-only mention_text is not acceptable.
  - Good: `"בוצעה אקסטובציה"`, `"הוחלט להתחיל Aspirin"`, `"הופסק טיפול ב-warfarin"`
  - Bad: `"אקסטובציה"`, `"Aspirin"`, `"Vancomycin"`, `"extubation"`

## Action Semantics

Choose Hebrew phrases semantically consistent with `canonical_action`:
- `start`: `הוחל טיפול`, `הוחלט להתחיל`, `נרשם`, `ניתן לראשונה`
- `continue`: `יש להמשיך`, `המשך טיפול`, `הומלץ להמשיך`, `ממשיך`
- `stop`: `הופסק`, `הוחלט להפסיק`, `אין להמשיך`, `בוטל`
- `change`: `שונה מינון`, `הוחלף טיפול`, `בוצעה התאמה`, `הותאם`
- `performed`: `בוצע`, `בוצעה`, `עבר`, `הוכנס`, `הוצא`
- `planned`: `מתוכנן`, `הופנה ל`, `נקבע`, `יופנה`

Do **not** use negation that contradicts `canonical_action`:
- If `canonical_action` is `continue`, do not write that the treatment was not continued, was stopped, or was discontinued.
- If `canonical_action` is `stop`, do not write that treatment is being continued or maintained.
- If `canonical_action` is `start`, do not write that the treatment was not started or not given.

## Marked Span Anchoring

To guarantee exact `mention_text` extraction, surround each required target decision phrase inside `summary_text_he` with this exact marker format:

  [TGT:<source_target_id>]decision phrase[/TGT]

Rules:
- Place **exactly one** `[TGT:<id>]...[/TGT]` pair per required target.
- The `<source_target_id>` must match the `target_id` field in `required_targets` **exactly**, character for character.
- Marker content must include **both** an action cue and the drug/procedure concept.
- **No nested markers.** Do not place a `[TGT:...]` inside another marker.
- **No overlapping markers.** Each character in `summary_text_he` must belong to at most one marker.
- **No extra markers.** Do not mark clinical background, generic follow-up instructions, or anything not listed in `required_targets`.
- You must still populate `target_mentions` as before. The parser will **override** `target_mentions[].mention_text` with the exact text inside the marker — the verbatim requirement is automatically satisfied.
- `target_mentions[].source_target_id` must still match the corresponding marker id.

Example — `target_id = "23000_153785_50538_chunk00_drug_GT_117"`:

  Correct `summary_text_he`:
  "...במהלך האשפוז [TGT:23000_153785_50538_chunk00_drug_GT_117]הוחלט להפסיק טיפול ב-Heparin[/TGT] עקב סיכון לדימום..."

  The parser extracts `"הוחלט להפסיק טיפול ב-Heparin"` as the authoritative `mention_text`.

Pre-return checklist:
1. Every `target_id` in `required_targets` has exactly one `[TGT:<target_id>]...[/TGT]` marker in `summary_text_he`.
2. Every marker's content includes both action cue and concept name.
3. No marker wraps background conditions or generic discharge instructions.
4. No duplicate or extra marker ids.
5. `target_mentions[].source_target_id` matches the corresponding marker id exactly.

---
"""

_FEW_SHOT = """\
## Few-Shot Example

Input task (abbreviated):
```json
{
  "generation_task_id": "gen_EXAMPLE",
  "source_note_id": "example_note",
  "required_targets": [
    {
      "target_id": "ex_drug_1",
      "label": "drug_decision",
      "raw_text_en": "continue warfarin",
      "canonical_concept": "warfarin",
      "canonical_action": "continue"
    }
  ],
  "generation_attributes": {
    "writer_style": "hospital_discharge_formal",
    "text_format": "one_dense_paragraph",
    "length_profile": "short_80_120_words",
    "language_mix": "hebrew_with_english_medications",
    "clinical_focus": "mainly_discharge_recommendations",
    "noise_level": "clean"
  }
}
```

Expected output:
```json
[
  {
    "generation_task_id": "gen_EXAMPLE",
    "source_note_id": "example_note",
    "status": "ok",
    "summary_text_he": "המטופל שוחרר לביתו במצב יציב. יש להמשיך טיפול ב-warfarin במינון הקיים ולבצע בדיקת INR עוד שבועיים. מומלץ להימנע מפעילות גופנית מאומצת.",
    "target_mentions": [
      {
        "mention_text": "להמשיך טיפול ב-warfarin",
        "label": "drug_decision",
        "canonical_concept": "warfarin",
        "canonical_action": "continue",
        "source_target_id": "ex_drug_1"
      }
    ],
    "generation_attributes": {
      "writer_style": "hospital_discharge_formal",
      "text_format": "one_dense_paragraph",
      "length_profile": "short_80_120_words",
      "language_mix": "hebrew_with_english_medications",
      "clinical_focus": "mainly_discharge_recommendations",
      "noise_level": "clean"
    }
  }
]
```

Note: `"להמשיך טיפול ב-warfarin"` appears verbatim inside `summary_text_he` — this is required.

---
"""


def _task_to_prompt_payload(task: dict) -> dict:
    """Build the compact LLM-facing task payload."""
    clinical_background = [
        item["raw_text_en"].strip()
        for item in task.get("input_payload", {}).get("problem_context", [])
        if target_quality.is_clean_background_item(item.get("raw_text_en", ""))
    ][:5]
    return {
        "generation_task_id": task["generation_task_id"],
        "source_note_id":     task["source_note_id"],
        "clinical_background": clinical_background,
        "required_targets":   task["required_targets"],
        "generation_attributes": task["generation_attributes"],
        "constraints":        task["constraints"],
    }


def _render_batch_prompt(
    batch_tasks:     list[dict],
    batch_num:       int,
    total_batches:   int,
    include_few_shot: bool,
) -> str:
    """Render a single batch as a Markdown string."""
    lines = [
        f"# Generation Batch {batch_num:03d} / {total_batches:03d}",
        "",
        f"> Tasks in this batch: {len(batch_tasks)}",
        "",
        _INSTRUCTIONS,
    ]

    if include_few_shot:
        lines.append(_FEW_SHOT)

    task_ids = [t["generation_task_id"] for t in batch_tasks]
    lines.append(f"## Tasks ({', '.join(task_ids)})")
    lines.append("")
    lines.append("Paste this JSON array when sending the prompt:")
    lines.append("")
    lines.append("```json")

    payloads = [_task_to_prompt_payload(t) for t in batch_tasks]
    lines.append(json.dumps(payloads, ensure_ascii=False, indent=2))

    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append(f"*End of batch {batch_num:03d}.*")
    lines.append("")

    return "\n".join(lines)


def run(
    input_path:      Path = config.MANUAL_GENERATION_TASKS_DEFAULT,
    batch_size:      int  = 5,
    output_dir:      Path = config.MANUAL_GENERATION_PROMPTS_DIR,
    include_few_shot: bool = False,
) -> list[Path]:
    """
    Write prompt batch files and an index CSV.
    Returns list of created batch file paths.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Tasks file not found: {input_path}\n"
            "Run sample_generation_tasks.py first."
        )

    tasks: list[dict] = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Split into batches
    batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]
    total_batches = len(batches)

    created_files: list[Path] = []
    index_rows: list[dict]    = []

    for batch_idx, batch_tasks in enumerate(batches):
        batch_num  = batch_idx + 1
        batch_file = output_dir / f"prompt_batch_{batch_num:03d}.md"

        content = _render_batch_prompt(
            batch_tasks,
            batch_num,
            total_batches,
            include_few_shot,
        )
        batch_file.write_text(content, encoding="utf-8")
        created_files.append(batch_file)

        task_ids = [t["generation_task_id"] for t in batch_tasks]
        source_notes = sorted({t["source_note_id"] for t in batch_tasks})
        index_rows.append({
            "batch_file":    batch_file.name,
            "batch_num":     batch_num,
            "n_tasks":       len(batch_tasks),
            "task_ids":      ", ".join(task_ids),
            "source_notes":  ", ".join(source_notes),
            "status":        "pending",
        })

    # Write index CSV
    index_path = output_dir / "index.csv"
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["batch_file", "batch_num", "n_tasks",
                        "task_ids", "source_notes", "status"],
        )
        writer.writeheader()
        writer.writerows(index_rows)

    print(f"\n[write_prompts] Done.")
    print(f"  Tasks          : {len(tasks)}")
    print(f"  Batches        : {total_batches} × up to {batch_size} tasks")
    print(f"  Few-shot       : {include_few_shot}")
    print(f"  Output dir     : {output_dir}")
    print(f"  Index          : {index_path}")
    for fp in created_files:
        print(f"    {fp.name}")

    return created_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write manual generation prompt batch files")
    parser.add_argument("--input",           type=str,
                        default=str(config.MANUAL_GENERATION_TASKS_DEFAULT))
    parser.add_argument("--batch-size",      type=int, default=5)
    parser.add_argument("--output-dir",      type=str,
                        default=str(config.MANUAL_GENERATION_PROMPTS_DIR))
    parser.add_argument("--include-few-shot", action="store_true",
                        help="Include a few-shot example in every batch prompt")
    args = parser.parse_args()
    run(
        input_path=Path(args.input),
        batch_size=args.batch_size,
        output_dir=Path(args.output_dir),
        include_few_shot=args.include_few_shot,
    )
