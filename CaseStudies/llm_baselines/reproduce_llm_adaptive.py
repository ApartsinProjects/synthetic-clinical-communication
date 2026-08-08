# -*- coding: utf-8 -*-
"""Stage 3: adaptive diagnostic-questioning multi-turn benchmark (40-case sample).
Doctor=gpt-4.1, Patient=gpt-4o-mini via OpenRouter; diagnosis similarity via OpenAI embeddings.
Reproduces MMS / per-round mean similarity (paper MMS 0.657; per-round 0.624/0.621/0.635)."""
import os, re, json, time, math, urllib.request, concurrent.futures as cf
import pandas as pd
SP = os.path.dirname(os.path.abspath(__file__)); CS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORKEY = os.environ["OPENROUTER_API_KEY"]  # export OPENROUTER_API_KEY before running
OAKEY = os.environ.get("OPENAI_API_KEY", "")
OR = "https://openrouter.ai/api/v1/chat/completions"

def chat(model, msgs, max_tokens=120, temp=0.2, retries=4):
    body = json.dumps({"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": temp}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(OR, data=body, headers={"Authorization": "Bearer " + ORKEY, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"].strip()
        except Exception:
            if a == retries - 1: return ""
            time.sleep(1.5 * (a + 1))

def embed(text, retries=3):
    body = json.dumps({"model": "text-embedding-3-small", "input": text[:2000]}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
                headers={"Authorization": "Bearer " + OAKEY, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=60))["data"][0]["embedding"]
        except Exception:
            if a == retries - 1: return None
            time.sleep(1.0 * (a + 1))

def cos(a, b):
    if not a or not b: return 0.0
    s = sum(x * y for x, y in zip(a, b)); na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return s / (na * nb) if na and nb else 0.0

def one_case(row):
    dx_full = row["prognosis"]; case50 = str(row["50% Case"]); case100 = str(row["100% Case"])
    gold_emb = embed(dx_full)
    history = f"Partial case information:\n{case50}"
    sims = []
    for _ in range(3):
        q = chat("openai/gpt-4.1", [{"role": "system", "content": "You are a physician taking a history. Ask ONE focused diagnostic question."},
                                    {"role": "user", "content": history + "\n\nAsk one question."}], max_tokens=60)
        ans = chat("openai/gpt-4o-mini", [{"role": "system", "content": "You are the patient. Answer the doctor briefly and only from your case."},
                                          {"role": "user", "content": f"Your full case:\n{case100}\n\nDoctor asks: {q}\nAnswer briefly."}], max_tokens=60)
        history += f"\nQ: {q}\nA: {ans}"
        dx = chat("openai/gpt-4.1", [{"role": "system", "content": "Give your single most likely diagnosis as a short disease name only."},
                                     {"role": "user", "content": history + "\n\nMost likely diagnosis (name only):"}], max_tokens=15)
        sims.append(cos(embed(dx), gold_emb))
    return sims

a = pd.read_csv(os.path.join(CS, "adaptive-diagnostic-questioning", "patient_cases.csv")).dropna(subset=["prognosis", "50% Case", "100% Case"]).sample(40, random_state=42)
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    allsims = list(ex.map(one_case, [r for _, r in a.iterrows()]))

mms = sum(max(s) for s in allsims) / len(allsims)
per = [sum(s[i] for s in allsims) / len(allsims) for i in range(3)]
out = {"n": len(allsims), "MMS": round(mms, 3), "per_round": [round(x, 3) for x in per],
       "paper": {"MMS": 0.657, "per_round": [0.624, 0.621, 0.635]},
       "note": "40-case sample; gpt-4.1/gpt-4o-mini + text-embedding-3-small (different embedding than paper), so absolute scale differs"}
print("RESULTS_JSON " + json.dumps(out)); print(out)
