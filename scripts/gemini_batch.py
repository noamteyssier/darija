"""Full-mode example sentences for verbs through the Gemini Batch API (one request per verb).

usage: GEMINI_API_KEY=... python3 scripts/gemini_batch.py [--level 1] [--ids kteb,shaf] [--limit 10] [--out PATH]

Submits one inline batch job, polls until it finishes, and saves {id: sentences} to --out in the same
shape as data/raw/examples/sonnet-full.json. Prints token usage, an estimated cost and the time taken.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

import build_examples as b

MODEL = "gemini-3.8-flash"
API = "https://generativelanguage.googleapis.com/v1beta"
BATCH_IN, BATCH_OUT = 0.375, 1.875  # USD per 1M tokens, through 2026


def call(method, url, body=None):
    req = urllib.request.Request(
        url, json.dumps(body).encode() if body is not None else None,
        {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"]}, method=method)
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url}: {e.read().decode()}")


def request(v, only=None):
    text = b.describe(v, True)
    if only is not None:
        head, lines = text.split("\n\nSlots:\n")
        text = head + "\n\nSlots:\n" + "\n".join(l for l in lines.split("\n") if int(l.split(":")[0]) in only)
    prompt = "Write one sentence per slot for each verb below. Return every verb by its id.\n\n" + \
        f"id: {v['id']}\n{text}"
    return {"request": {
        "system_instruction": {"parts": [{"text": b.STYLE}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generation_config": {"response_mime_type": "application/json", "response_json_schema": b.SCHEMA}},
        "metadata": {"key": v["id"]}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level")
    ap.add_argument("--ids")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--job", help="collect an already submitted batch (batches/...) instead of submitting")
    ap.add_argument("--redo", help='JSON file {"verb id": [slot, ...]}: rewrite only those slots in --out')
    ap.add_argument("--out", default=str(b.ROOT / "data/raw/examples/gemini-full.json"))
    a = ap.parse_args()

    redo = json.loads(open(a.redo).read()) if a.redo else None
    verbs = json.loads((b.ROOT / "data/verbs.json").read_text())["verbs"]
    if redo:
        verbs = [v for v in verbs if v["id"] in redo]
    if a.level:
        verbs = [v for v in verbs if str(v["level"]) == a.level]
    if a.ids:
        verbs = [v for v in verbs if v["id"] in set(a.ids.split(","))]
    verbs = verbs[:a.limit]

    t0 = time.time()
    if a.job:
        name = a.job
    else:
        name = call("POST", f"{API}/models/{MODEL}:batchGenerateContent", {"batch": {
            "display_name": "darija-examples",
            "input_config": {"requests": {"requests": [request(v, redo and set(redo[v["id"]])) for v in verbs]}}}})["name"]
        print(f"submitted {len(verbs)} verbs as {name}")
    while True:
        st = call("GET", f"{API}/{name}")
        state = st.get("metadata", {}).get("state") or st.get("state")
        print(f"{time.time() - t0:6.0f}s {state}", flush=True)
        if state.split("_STATE_")[1] in ("SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"):
            break
        time.sleep(30)
    took = time.time() - t0
    if not state.endswith("SUCCEEDED"):
        sys.exit(json.dumps(st, indent=1))

    dest = st.get("response") or st.get("dest") or {}
    rows = dest.get("inlinedResponses", {}).get("inlinedResponses") or dest.get("inlinedResponses") or []
    by_id = {v["id"]: v for v in verbs}
    got, tin, tout, tthink, ok, total = {}, 0, 0, 0, 0, 0
    for r in rows:
        key = r.get("metadata", {}).get("key")
        if "response" not in r:
            print("error:", key, r.get("error"))
            continue
        u = r["response"].get("usageMetadata", {})
        tin += u.get("promptTokenCount", 0)
        tout += u.get("candidatesTokenCount", 0)
        tthink += u.get("thoughtsTokenCount", 0)
        out = json.loads(r["response"]["candidates"][0]["content"]["parts"][-1]["text"])
        sents = out["verbs"][0]["sentences"]
        got[key] = sents
        by_slot = {x["slot"]: x for x in sents}
        for s in b.slots(by_id[key], True):
            if redo and s["slot"] not in redo[key]:
                continue
            total += 1
            x = by_slot.get(s["slot"])
            ok += bool(x and b.has_form(x, s) and not b.bad_script(x))
    out_path = __import__("pathlib").Path(a.out)
    if redo:
        merged = b.read(out_path, {})
        for key, sents in got.items():
            by_slot = {x["slot"]: x for x in merged.get(key, [])}
            by_slot.update({x["slot"]: x for x in sents if x["slot"] in redo[key]})
            merged[key] = sorted(by_slot.values(), key=lambda x: x["slot"])
        got = merged
    b.write(out_path, got)
    cost = tin * BATCH_IN / 1e6 + (tout + tthink) * BATCH_OUT / 1e6
    print(f"\n{len(got)}/{len(verbs)} verbs in {took:.0f}s, {ok}/{total} sentences pass checks")
    print(f"tokens: in {tin}, out {tout}, thinking {tthink}; batch cost ${cost:.4f} (${cost / max(1, len(got)):.4f}/verb)")
    print(f"saved to {a.out}")


if __name__ == "__main__":
    main()
