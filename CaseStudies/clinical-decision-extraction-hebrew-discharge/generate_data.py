"""
build_api_batch_requests.py — OpenAI Batch API envelope around the v1 prompt pipeline.

Converts existing generation tasks (manual_generation_tasks_*.jsonl) into OpenAI Batch API
request files (JSONL).  Prompt semantics are identical to the v1 manual generation pipeline:
same _INSTRUCTIONS, same _FEW_SHOT, same _task_to_prompt_payload() function.

Only the delivery envelope changes:
  manual pipeline  → Markdown file pasted into ChatGPT/Claude (N tasks per batch)
  this script      → JSONL with one chat-completion request per task (Batch API format)

custom_id format: <batch_id>__<generation_task_id>
  Example: pilot_005__gen_0002
  Both parts are recoverable by splitting on the first '__'.

Usage:
    python src/build_api_batch_requests.py \\
        --batch-id   pilot_005 \\
        --n          5 \\
        --model      gpt-4o-mini \\
        --output-dir data/api_expansion/batches/pilot_005 \\
        [--input     data/intermediate/manual_generation_tasks_50.jsonl] \\
        [--dry-run]

Outputs (all written to --output-dir):
    batch_requests.jsonl   — JSONL, one Batch API request object per line
    prompt_preview.md      — human-readable prompt for the first task

--dry-run is the default behaviour: no API calls are ever made by this script.
The flag exists to make intent explicit in CI or automation contexts.
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
import json
from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(_SRC))

# Reuse v1 prompt components directly — no copy/paste, no reimplementation.
from write_manual_generation_prompts import (
    _INSTRUCTIONS,
    _task_to_prompt_payload,
)
import config

# ── Defaults ───────────────────────────────────────────────────────────────────

DEFAULT_TASKS_PATH  = config.MANUAL_GENERATION_TASKS_DEFAULT
DEFAULT_MODEL       = "gpt-4o-mini"
DEFAULT_MAX_TOKENS  = 1800
DEFAULT_TEMPERATURE = 0.7
API_EXPANSION_ROOT  = config.ROOT / "data" / "api_expansion" / "batches"
CUSTOM_ID_SEP       = "__"


# ── custom_id helpers ──────────────────────────────────────────────────────────

def make_custom_id(batch_id: str, generation_task_id: str) -> str:
    """Return '<batch_id>__<generation_task_id>'."""
    return f"{batch_id}{CUSTOM_ID_SEP}{generation_task_id}"


def parse_custom_id(custom_id: str) -> tuple[str, str]:
    """
    Split '<batch_id>__<generation_task_id>' into (batch_id, generation_task_id).

    Raises ValueError if the separator is not present.
    """
    if CUSTOM_ID_SEP not in custom_id:
        raise ValueError(
            f"custom_id {custom_id!r} does not contain separator {CUSTOM_ID_SEP!r}. "
            "Expected format: '<batch_id>__<generation_task_id>'."
        )
    batch_id, task_id = custom_id.split(CUSTOM_ID_SEP, 1)
    return batch_id, task_id


# ── prompt builders ────────────────────────────────────────────────────────────

def _build_system_message() -> str:
    """System message: _INSTRUCTIONS only, matching the v1 manual prompt structure.

    The v1 manual prompts (data/api_expansion/manual_generation_prompts/prompt_batch_*.md) do not include
    a few-shot example block. _FEW_SHOT is intentionally excluded here to keep the API
    prompt behavior consistent with the original pipeline.
    """
    return _INSTRUCTIONS


def _build_user_message(task: dict) -> str:
    """
    User message: single-task JSON payload built by the v1 _task_to_prompt_payload().

    One task per API call (vs. up to batch_size per manual Markdown prompt) for
    independent retries and unambiguous single-object response parsing.
    """
    payload = _task_to_prompt_payload(task)
    return (
        "Generate one Hebrew hospital discharge summary for the following task.\n\n"
        "Return a JSON array with exactly one object.\n\n"
        "```json\n"
        + json.dumps([payload], ensure_ascii=False, indent=2)
        + "\n```"
    )


# ── request builder ────────────────────────────────────────────────────────────

def task_to_batch_request(
    task: dict,
    batch_id: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> dict:
    """Convert one generation task to an OpenAI Batch API request object."""
    return {
        "custom_id": make_custom_id(batch_id, task["generation_task_id"]),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": _build_system_message()},
                {"role": "user",   "content": _build_user_message(task)},
            ],
        },
    }


# ── preview writer ─────────────────────────────────────────────────────────────

def _write_preview(
    task: dict,
    batch_id: str,
    model: str,
    max_tokens: int,
    temperature: float,
    preview_path: Path,
) -> None:
    """Write a human-readable Markdown prompt preview for one task."""
    custom_id  = make_custom_id(batch_id, task["generation_task_id"])
    system_msg = _build_system_message()
    user_msg   = _build_user_message(task)

    lines = [
        f"# Prompt Preview — {custom_id}",
        "",
        f"> batch_id: `{batch_id}` | generation_task_id: `{task['generation_task_id']}`",
        f"> Model: `{model}` | max_tokens: {max_tokens} | temperature: {temperature}",
        "> Dry-run only — no API call was made.",
        "",
        "---",
        "",
        "## custom_id",
        "",
        f"`{custom_id}`",
        "",
        f"Parsed: `batch_id = {batch_id}` | `generation_task_id = {task['generation_task_id']}`",
        "",
        "---",
        "",
        "## System Message",
        "",
        "```",
        system_msg.strip(),
        "```",
        "",
        "---",
        "",
        "## User Message",
        "",
        "```",
        user_msg.strip(),
        "```",
        "",
        "---",
        "",
        "## Expected Response Schema",
        "",
        "```json",
        json.dumps(
            [
                {
                    "generation_task_id": task["generation_task_id"],
                    "source_note_id": task["source_note_id"],
                    "status": "ok",
                    "summary_text_he": "<Hebrew summary text>",
                    "target_mentions": [
                        {
                            "mention_text": "<exact verbatim substring from summary_text_he>",
                            "label": "drug_decision | procedure_decision",
                            "canonical_concept": "<from required_targets>",
                            "canonical_action": "<from required_targets>",
                            "source_target_id": "<target_id from required_targets>",
                        }
                    ],
                    "generation_attributes": task.get("generation_attributes", {}),
                }
            ],
            ensure_ascii=False,
            indent=2,
        ),
        "```",
    ]
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.write_text("\n".join(lines), encoding="utf-8")


# ── main entry point ───────────────────────────────────────────────────────────

def run(
    batch_id: str,
    input_path: Path = DEFAULT_TASKS_PATH,
    n: int | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    output_dir: Path | None = None,
    dry_run: bool = True,
) -> list[dict]:
    """
    Build Batch API request JSONL and a human-readable prompt preview.

    Writes to output_dir (default: data/api_expansion/batches/<batch_id>/):
      batch_requests.jsonl
      prompt_preview.md

    No API calls are made regardless of dry_run — this script only builds files.
    dry_run=True is the default and the flag is present for explicit documentation only.
    """
    input_path = Path(input_path)
    if output_dir is None:
        output_dir = API_EXPANSION_ROOT / batch_id
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

    if n is not None:
        tasks = tasks[:n]

    requests: list[dict] = [
        task_to_batch_request(task, batch_id, model, max_tokens, temperature)
        for task in tasks
    ]

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path  = output_dir / "batch_requests.jsonl"
    preview_path = output_dir / "prompt_preview.md"

    with open(output_path, "w", encoding="utf-8") as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    if tasks:
        _write_preview(tasks[0], batch_id, model, max_tokens, temperature, preview_path)

    example_custom_id = requests[0]["custom_id"] if requests else "n/a"

    print(f"\n[build_api_batch_requests] Done — no API calls made.")
    print(f"  batch_id         : {batch_id}")
    print(f"  Tasks processed  : {len(tasks)}")
    print(f"  Model            : {model}")
    print(f"  Max tokens       : {max_tokens}")
    print(f"  Temperature      : {temperature}")
    print(f"  Output dir       : {output_dir}")
    print(f"  Batch requests   : {output_path}")
    print(f"  Prompt preview   : {preview_path}")
    print(f"  Example custom_id: {example_custom_id}")
    print(f"  custom_id format : <batch_id>__<generation_task_id>")
    print(f"  Prompt source    : write_manual_generation_prompts._INSTRUCTIONS only (v1 reuse; no few-shot)")
    print(f"  Payload builder  : write_manual_generation_prompts._task_to_prompt_payload (v1 reuse)")

    return requests


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build OpenAI Batch API request JSONL from generation tasks. No API calls made."
    )
    parser.add_argument(
        "--batch-id", required=True,
        help="Batch identifier, e.g. pilot_005 or batch_300_001. Used in custom_id and output path.",
    )
    parser.add_argument(
        "--input", type=str, default=str(DEFAULT_TASKS_PATH),
        help="Path to manual_generation_tasks_*.jsonl",
    )
    parser.add_argument(
        "--n", type=int, default=None,
        help="Number of tasks to include (default: all).",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help="OpenAI model name (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
        help="max_tokens per request (default: 1800).",
    )
    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help="Sampling temperature (default: 0.7).",
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Output directory (default: data/api_expansion/batches/<batch_id>/).",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Dry-run mode (default: True). This script never submits to the API.",
    )
    args = parser.parse_args()
    run(
        batch_id=args.batch_id,
        input_path=Path(args.input),
        n=args.n,
        model=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        dry_run=args.dry_run,
    )
