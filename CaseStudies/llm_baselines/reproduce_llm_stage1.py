# -*- coding: utf-8 -*-
"""OpenRouter LLM baseline reproduction - stage 1: postpartum(richer), medication, casualty."""
import os, re, json, time, urllib.request, concurrent.futures as cf
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

SP = os.path.dirname(os.path.abspath(__file__)); CS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY = os.environ["OPENROUTER_API_KEY"]  # export OPENROUTER_API_KEY before running
URL = "https://openrouter.ai/api/v1/chat/completions"

def call(model, prompt, max_tokens=8, temp=0.0, retries=4):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": max_tokens, "temperature": temp}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"].strip()
        except Exception:
            if a == retries - 1: return "__ERR__"
            time.sleep(1.5 * (a + 1))

def par(fn, items, workers=8):
    out = [None] * len(items)
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
        for f in cf.as_completed(futs): out[futs[f]] = f.result()
    return out

def norm(x): return re.sub(r"[\s_]+", "", str(x).strip().lower())

res = {}

# ---- postpartum richer prompt, 750 sample ----
p = pd.read_excel(os.path.join(CS, "postpartum-severity-triage", "dataset.xlsx")).dropna(subset=["patient_message","triage_level"])
p = p[p["triage_level"].isin([0,1,2,3,0.0,1.0,2.0,3.0])].sample(750, random_state=42)
SYS = ("You are a postpartum triage nurse. Classify the patient message severity:\n"
       "0 = routine (normal recovery, reassurance only)\n"
       "1 = mild (minor issue, non-urgent self-care advice)\n"
       "2 = urgent (needs timely clinical review: wound infection signs, moderate bleeding, persistent pain, urinary problems)\n"
       "3 = emergency (red flags: heavy bleeding, breathing difficulty, chest pain, signs of sepsis/severe infection, thromboembolism, severe mood crisis)\n")
def pp(m): return SYS + f'\nMessage: "{m}"\nReply with only the single digit 0, 1, 2, or 3.'
resp = par(lambda t: call("openai/gpt-4o-mini", pp(t)), list(p["patient_message"].astype(str)))
def dig(r):
    m = re.search(r"[0-3]", r or ""); return int(m.group(0)) if m else -1
yp = [dig(r) for r in resp]; yg = [int(x) for x in p["triage_level"]]
res["postpartum(richer,750)"] = {"acc": round(accuracy_score(yg,yp),3), "macro_f1": round(f1_score(yg,yp,average="macro"),3), "paper": 0.98}
print(res["postpartum(richer,750)"], flush=True)

# ---- medication gpt-4.1 Critical/General ----
m = pd.read_excel(os.path.join(CS, "medication-question-risk-classification", "labeled_data.xlsx")).dropna(subset=["Question","Risk_Level"])
def mp(q): return (f'Classify this consumer medication question as Critical or General. '
                   f'Critical = indicates potentially dangerous medication behavior (harmful drug interaction, misuse, overdose, dangerous self-medication). '
                   f'General = informational or low-risk.\nQuestion: "{q}"\nReply with one word: Critical or General.')
resp = par(lambda q: call("openai/gpt-4.1", mp(q)), list(m["Question"].astype(str)))
def lab(r):
    r=(r or "").lower(); return "Critical" if "critical" in r else ("General" if "general" in r else None)
pairs=[(lab(r),g) for r,g in zip(resp, m["Risk_Level"]) if lab(r)]
res["medication(gpt-4.1,655)"] = {"acc": round(accuracy_score([g for _,g in pairs],[p_ for p_,_ in pairs]),3),
                                  "macro_f1": round(f1_score([g for _,g in pairs],[p_ for p_,_ in pairs],average="macro"),3),
                                  "paper_note":"paper LLM baseline used GPT-4.1+RAG; classical SVM 0.84, BioBERT 0.92"}
print(res["medication(gpt-4.1,655)"], flush=True)


print("\nRESULTS_JSON "+json.dumps(res))
