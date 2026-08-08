# -*- coding: utf-8 -*-
"""OpenRouter zero-shot LLM baseline reproduction (classification tier).
Reads OPENROUTER_API_KEY from the environment; no key in source. Approximate (current models, non-deterministic).
"""
import os, re, json, sys, time, urllib.request, urllib.error, concurrent.futures as cf
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

SP = os.path.dirname(os.path.abspath(__file__))
CS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY = os.environ["OPENROUTER_API_KEY"]  # export OPENROUTER_API_KEY before running
URL = "https://openrouter.ai/api/v1/chat/completions"

def call(model, prompt, max_tokens=8, temp=0.0, retries=4):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": temp}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(URL, data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=90))
            return r["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if a == retries - 1:
                return "__ERR__"
            time.sleep(1.5 * (a + 1))

def parse(resp, classes):
    r = (resp or "").lower()
    for c in classes:
        if str(c).lower() in r:
            return c
    m = re.search(r"[0-3]", r)
    if m:
        for c in classes:
            if str(c) == m.group(0):
                return c
    return None

def run(name, model, prompts, golds, classes, workers=8, limit=None):
    if limit:
        prompts, golds = prompts[:limit], golds[:limit]
    preds = [None] * len(prompts)
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(call, model, p): i for i, p in enumerate(prompts)}
        for f in cf.as_completed(futs):
            preds[futs[f]] = parse(f.result(), classes)
    ok = [(p, g) for p, g in zip(preds, golds) if p is not None]
    fail = len(preds) - len(ok)
    yp = [p for p, g in ok]; yg = [g for p, g in ok]
    acc = accuracy_score(yg, yp) if ok else 0.0
    f1 = f1_score(yg, yp, average="macro") if ok else 0.0
    print(f"[{name}] model={model} n={len(prompts)} parsed={len(ok)} unparsed={fail} "
          f"acc={acc:.3f} macroF1={f1:.3f}", flush=True)
    return {"study": name, "model": model, "n": len(prompts), "acc": round(acc, 3), "macro_f1": round(f1, 3)}

def main():
    res = []

    # postpartum: GPT-4o-mini zero-shot, 4-class triage (paper acc/f1 ~0.98)
    p = pd.read_excel(os.path.join(CS, "postpartum-severity-triage", "dataset.xlsx")).dropna(subset=["patient_message", "triage_level"])
    p = p[p["triage_level"].isin([0, 1, 2, 3, 0.0, 1.0, 2.0, 3.0])]
    prompts = [f"Triage this postpartum patient message by severity: 0=routine, 1=mild, 2=urgent, 3=emergency. "
               f"Message: \"{t}\"\nReply with only the digit 0, 1, 2, or 3." for t in p["patient_message"].astype(str)]
    golds = [int(x) for x in p["triage_level"]]
    res.append(run("postpartum", "openai/gpt-4o-mini", prompts, golds, [0, 1, 2, 3]))

    # admin: Qwen zero-shot urgency Green/Yellow/Red (paper acc/f1 ~0.34 zero-shot small-Qwen; 0.81 fine-tuned DistilBERT)
    rows = [json.loads(l) for l in open(os.path.join(CS, "administrative-portal-message-triage", "test.jsonl"), encoding="utf-8")]
    prompts = [f"Classify the urgency of this patient portal message as Green (routine), Yellow (semi-urgent), or Red (urgent). "
               f"Message: \"{o['text']}\"\nReply with one word: Green, Yellow, or Red." for o in rows]
    golds = [o["labels"]["urgency_level"] for o in rows]
    res.append(run("admin", "qwen/qwen-2.5-7b-instruct", prompts, golds, ["Green", "Yellow", "Red"]))

    # sbar: Qwen zero-shot completeness low/medium/high (sample) (paper Qwen zero-shot baseline)
    s = pd.read_csv(os.path.join(CS, "sbar-completeness-checking", "modeling_dataset.sample.csv")).dropna(subset=["model_text", "completeness_class"])
    prompts = [f"Rate the clinical completeness of this SBAR handover note as low, medium, or high. "
               f"Note: \"{t}\"\nReply with one word: low, medium, or high." for t in s["model_text"].astype(str)]
    golds = list(s["completeness_class"])
    res.append(run("sbar(sample)", "qwen/qwen-2.5-7b-instruct", prompts, golds, ["low", "medium", "high"]))


    print("\nRESULTS_JSON " + json.dumps(res))

if __name__ == "__main__":
    main()
