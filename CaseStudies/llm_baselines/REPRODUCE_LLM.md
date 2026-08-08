# LLM-baseline reproduction (zero-shot / few-shot via OpenRouter)

These scripts re-run the studies' **LLM baselines** (the zero-shot / few-shot / generative
prompts) against **current** models through [OpenRouter](https://openrouter.ai), scoring
against the shipped gold. They complement the offline `reproduce.py` in each study folder
(which retrains the encoders / classical models).

## Running

```bash
export OPENROUTER_API_KEY=sk-or-...        # required; read from env, never stored in source
export OPENAI_API_KEY=sk-...               # only for reproduce_llm_adaptive.py (embeddings)
/c/Python314/python reproduce_llm_zeroshot.py   # postpartum, admin, SBAR, clinical-priority
/c/Python314/python reproduce_llm_stage1.py     # postpartum(richer), medication, casualty
/c/Python314/python reproduce_llm_hebrew.py     # Hebrew decision-span extraction
/c/Python314/python reproduce_llm_adaptive.py   # adaptive multi-turn (needs an embedding key with credit)
```

## These are APPROXIMATE reproductions
- Current models **substitute** the paper's retired `GPT-4` / `GPT-4.1` (e.g. `gpt-4o`, `gpt-4.1`).
- LLM outputs are **non-deterministic**, so numbers will not match to the decimal.
- Casualty and Hebrew use **strict** exact-match scoring that tends to under-count.
- `BART-MNLI` (a local zero-shot NLI model) is not re-run here; it is not an API model.

## Measured vs paper (one representative run)

| Study | task | model | measured | paper | note |
|---|---|---|---|---|---|
| clinical-priority | zero-shot 3-class | Qwen2.5-7B | 0.415 | ~0.34-0.42 | reproduces the weak-zero-shot range |
| admin | zero-shot urgency | Qwen2.5-7B | 0.22 | ~0.34 | weak zero-shot confirmed |
| SBAR | zero-shot completeness | Qwen2.5-7B | 0.28 | (low) | weak zero-shot confirmed |
| postpartum | zero-shot 4-class | gpt-4o-mini | 0.63-0.64 | 0.98 | does not reproduce (paper number optimistic) |
| medication | zero-shot Critical/General | gpt-4.1 | 0.855 | SVM 0.84 / BioBERT 0.92 | strong LLM baseline, beats classical SVM |
| casualty | zero-shot JSON extraction | gpt-4o | 0.47 EM | GPT-4 0.686 EM | lower; non-generative AlephBERT (0.79) still best |
| Hebrew | few-shot span extraction | Qwen2.5-7B | drug 0.347 / overall 0.331 | 0.206 | reproduces the low strict-F1 ballpark |
| adaptive | multi-turn similarity | gpt-4.1 + gpt-4o-mini | see note | MMS 0.657 | metric already reproduces offline via the study's `reproduce.py` (MMS 0.66) |

## Reading
The paper's central claim reproduces: **fine-tuned encoders and non-generative models beat
zero-shot LLMs**. Zero-shot is weak where the paper says (clinical-priority, admin, SBAR),
and the non-generative AlephBERT tops the generative LLMs on casualty. Two anomalies stand
out honestly: postpartum's 0.98 zero-shot does not reproduce (~0.64 with the same model),
and medication's LLM baseline is strong (0.855) on the authentic QA-classification task.
