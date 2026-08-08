# -*- coding: utf-8 -*-
"""Stage 2: Hebrew clinical-decision span extraction, Qwen few-shot, strict-span F1."""
import os, re, json, time, urllib.request, concurrent.futures as cf
SP = os.path.dirname(os.path.abspath(__file__)); CS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KEY = os.environ["OPENROUTER_API_KEY"]  # export OPENROUTER_API_KEY before running
URL = "https://openrouter.ai/api/v1/chat/completions"

def call(model, prompt, max_tokens=400, temp=0.0, retries=4):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": temp}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"].strip()
        except Exception:
            if a == retries - 1: return "__ERR__"
            time.sleep(1.5 * (a + 1))

def norm(s): return re.sub(r"\s+", " ", str(s).strip())

rows = []
for l in open(os.path.join(CS, "clinical-decision-extraction-hebrew-discharge", "synthetic_data.jsonl"), encoding="utf-8"):
    o = json.loads(l)
    if o.get("target_mentions") and o.get("summary_text_he"): rows.append(o)
rows = rows[:81]  # v2 test size

FEWSHOT = ('Example summary: "\u05d4\u05d5\u05d7\u05dc \u05d8\u05d9\u05e4\u05d5\u05dc \u05d1-Pantoprazole 40 mg \u05e4\u05e2\u05dd \u05d1\u05d9\u05d5\u05dd."\n'
           'Example output: {"drug": ["\u05d4\u05d5\u05d7\u05dc \u05d8\u05d9\u05e4\u05d5\u05dc \u05d1-Pantoprazole 40 mg"], "procedure": []}\n\n')
def prompt(sm):
    return ("Extract clinical DECISION spans from this Hebrew discharge summary. Return a JSON object with two lists: "
            '"drug" (medication-start/stop/change decisions) and "procedure" (procedure/intervention decisions). '
            "Each item must be an EXACT substring copied verbatim from the summary.\n\n" + FEWSHOT +
            f'Summary: "{sm}"\nReply with ONLY the JSON object.')

def parse(r):
    try:
        s = re.search(r"\{.*\}", r or "", re.DOTALL); o = json.loads(s.group(0))
        return set(norm(x) for x in o.get("drug", [])), set(norm(x) for x in o.get("procedure", []))
    except Exception:
        return set(), set()

with cf.ThreadPoolExecutor(max_workers=6) as ex:
    resp = list(ex.map(lambda o: call("qwen/qwen-2.5-7b-instruct", prompt(o["summary_text_he"])), rows))

def prf(tp, np_, ng):
    p = tp / np_ if np_ else 0.0; r = tp / ng if ng else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0

agg = {"drug": [0, 0, 0], "procedure": [0, 0, 0]}  # tp, npred, ngold
for o, rp in zip(rows, resp):
    pd_, pp_ = parse(rp)
    gold = {"drug": set(), "procedure": set()}
    for m in o["target_mentions"]:
        cat = "drug" if "drug" in m.get("label", "") else ("procedure" if "procedure" in m.get("label", "") else None)
        if cat: gold[cat].add(norm(m["mention_text"]))
    for cat, pred in (("drug", pd_), ("procedure", pp_)):
        agg[cat][0] += len(pred & gold[cat]); agg[cat][1] += len(pred); agg[cat][2] += len(gold[cat])

dF = prf(*agg["drug"]); pF = prf(*agg["procedure"])
oF = prf(agg["drug"][0] + agg["procedure"][0], agg["drug"][1] + agg["procedure"][1], agg["drug"][2] + agg["procedure"][2])
out = {"drug_strictF1": round(dF, 3), "procedure_strictF1": round(pF, 3), "overall_strictF1": round(oF, 3),
       "paper_qwen_fewshot": {"drug": 0.209, "procedure": 0.204, "overall": 0.206}, "n": len(rows)}
print("RESULTS_JSON " + json.dumps(out))
print(out)
