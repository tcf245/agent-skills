#!/usr/bin/env python3
"""jev — pre-filter large inputs with TypeSafe Jev so only the useful part reaches an LLM context.

Reads items on stdin (JSON array, JSONL, or plain text lines), asks Jev one typed question
per item (in parallel), and prints a short JSONL result. A one-line summary goes to stderr.

  jev filter   -q "Is this about X?"                 keep items with P(yes) >= --threshold
  jev rank     -q "How well does it fit?" -l L0 L1 L2 sort by Score (levels low -> high)
  jev classify -q "Which bucket?" -o a="desc" -o b   label each item with a Choice
  jev lines    -q "Which line shows the failure?"    locate relevant lines in a text log

Common flags: --context TEXT|@file (shared background, e.g. what the user wants),
--top N, --fields a,b (output projection), --max-chars N, --model, --workers.
Key: $TYPESAFE_API_KEY, else macOS Keychain service `typesafe-api-key` (account `eric`).
Stdlib only.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://api.typesafe.ai/v1/systemone"
MAX_CHOICE_OPTIONS = 255


class Retryable(Exception):
    pass


# --- transport ---------------------------------------------------------------

def api_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key
    try:
        return subprocess.run(
            ["security", "find-generic-password", "-s", "typesafe-api-key", "-a", "eric", "-w"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        sys.exit("jev: no API key (set TYPESAFE_API_KEY or add Keychain item typesafe-api-key)")


def with_retry(post, body, tries=4, sleep=time.sleep):
    for attempt in range(tries):
        try:
            return post(body)
        except Retryable:
            if attempt == tries - 1:
                raise
            sleep(0.5 * 2 ** attempt)


def make_call(model, key):
    def post(body):
        req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST", headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529):
                raise Retryable(str(e.code))
            raise SystemExit("jev: HTTP %s %s" % (e.code, e.read().decode(errors="replace")[:300]))
        except urllib.error.URLError as e:
            raise Retryable(str(e))

    def call(state, questions, model=model):
        return with_retry(post, {"state": state, "model": model, "questions": questions})
    return call


# --- input / output ----------------------------------------------------------

def parse_items(text):
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except ValueError:
        pass
    lines = [l for l in text.splitlines() if l.strip()]
    try:
        return [json.loads(l) for l in lines]
    except ValueError:
        return lines


def project(item, fields, max_chars):
    if isinstance(item, dict) and fields:
        return {f: item.get(f) for f in fields}
    if isinstance(item, str) and max_chars and len(item) > max_chars:
        return item[:max_chars] + "…"
    return item


def _state(item, context):
    return {"context": context, "item": item} if context else {"item": item}


def _fan_out(items, context, questions, call, workers):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda it: call(_state(it, context), questions), items))


def _stats(n, responses, **extra):
    s = {"n": n,
         "input_tokens": sum((r.get("usage") or {}).get("input_tokens") or 0 for r in responses),
         "output_tokens": sum((r.get("usage") or {}).get("output_tokens") or 0 for r in responses)}
    s.update(extra)
    return s


# --- operations --------------------------------------------------------------

def run_filter(items, question, call, context=None, threshold=0.5, top=None,
               true=None, false=None, workers=8):
    q = {"type": "noul", "instructions": question}
    if true or false:
        q["criteria"] = {"true": true or "Yes.", "false": false or "No."}
    resp = _fan_out(items, context, {"q": q}, call, workers)
    rows = [{"i": i, "p": round(r["answers"]["q"]["noul"], 3)} for i, r in enumerate(resp)]
    rows = sorted((r for r in rows if r["p"] >= threshold), key=lambda r: -r["p"])
    return rows[:top] if top else rows, _stats(len(items), resp)


def run_rank(items, question, levels, call, context=None, top=None, min_score=None, workers=8):
    q = {"type": "score", "instructions": question, "criteria": list(levels)}
    resp = _fan_out(items, context, {"q": q}, call, workers)
    rows = [{"i": i, "score": round(r["answers"]["q"]["score"], 2),
             "conf": round(r["answers"]["q"].get("confidence") or 0, 2)} for i, r in enumerate(resp)]
    if min_score is not None:
        rows = [r for r in rows if r["score"] >= min_score]
    rows.sort(key=lambda r: -r["score"])
    return rows[:top] if top else rows, _stats(len(items), resp)


def run_classify(items, question, options, call, context=None, workers=8):
    q = {"type": "choice", "instructions": question, "criteria": options}
    resp = _fan_out(items, context, {"q": q}, call, workers)
    rows = [{"i": i, "choice": r["answers"]["q"]["choice"],
             "conf": round(r["answers"]["q"].get("confidence") or 0, 2)} for i, r in enumerate(resp)]
    return rows, _stats(len(items), resp)


def run_lines(lines, question, call, context=None, window=200, around=2,
              exists_min=0.5, line_min=0.1, workers=8):
    """Semantic line search: each window is one request (Choice over line ids + Noul 'exists')."""
    if window > MAX_CHOICE_OPTIONS:
        raise ValueError("window must be <= %d (Choice option limit)" % MAX_CHOICE_OPTIONS)
    lines = [str(l) for l in lines]
    lid = lambda i: "L%04d" % i
    starts = list(range(0, len(lines), window))

    def ask(start):
        idx = range(start, min(start + window, len(lines)))
        state = {"log": "\n".join("%s| %s" % (lid(i), lines[i]) for i in idx)}
        if context:
            state["context"] = context
        return call(state, {
            "where": {"type": "choice", "criteria": {lid(i): None for i in idx},
                      "instructions": "Which line of `log` best answers: %s" % question},
            "exists": {"type": "noul",
                       "instructions": "Does any line of `log` answer: %s" % question}})

    with ThreadPoolExecutor(workers) as ex:
        resp = list(ex.map(ask, starts))
    rows = []
    for r in resp:
        a = r["answers"]
        if a["exists"]["noul"] < exists_min:
            continue
        for k, p in a["where"]["probabilities"].items():
            if p >= line_min:
                i = int(k[1:])
                rows.append({"line": i, "p": round(p, 3), "text": lines[i],
                             "context": lines[max(0, i - around): i + around + 1]})
    rows.sort(key=lambda r: r["line"])
    hit = sum(1 for r in resp if r["answers"]["exists"]["noul"] >= exists_min)
    return rows, _stats(len(lines), resp, windows=len(starts), windows_hit=hit)


# --- CLI ---------------------------------------------------------------------

def _context(arg):
    if arg and arg.startswith("@"):
        with open(arg[1:]) as f:
            return f.read()
    return arg


def _options(pairs):
    out = {}
    for p in pairs:
        name, _, desc = p.partition("=")
        out[name] = desc or None
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jev", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-q", "--question", required=True)
    common.add_argument("-c", "--context", help="shared background text, or @file")
    common.add_argument("--top", type=int)
    common.add_argument("--fields", help="comma list of item fields to echo back")
    common.add_argument("--max-chars", type=int, default=200, help="truncate echoed text items")
    common.add_argument("--model", default="jev-latest")
    common.add_argument("--workers", type=int, default=8)
    common.add_argument("--input", help="read items from file instead of stdin")

    f = sub.add_parser("filter", parents=[common])
    f.add_argument("--threshold", type=float, default=0.5)
    f.add_argument("--true")
    f.add_argument("--false")
    r = sub.add_parser("rank", parents=[common])
    r.add_argument("-l", "--levels", nargs="+", required=True, help="Score levels, worst to best")
    r.add_argument("--min-score", type=float)
    c = sub.add_parser("classify", parents=[common])
    c.add_argument("-o", "--option", action="append", required=True, help="name=description")
    ln = sub.add_parser("lines", parents=[common])
    ln.add_argument("--window", type=int, default=200)
    ln.add_argument("--around", type=int, default=2)
    ln.add_argument("--line-min", type=float, default=0.1)
    a = ap.parse_args(argv)

    raw = open(a.input).read() if a.input else sys.stdin.read()
    call = make_call(a.model, api_key())
    ctx = _context(a.context)
    t0 = time.time()
    if a.cmd == "lines":
        rows, st = run_lines(raw.splitlines(), a.question, call, context=ctx, window=a.window,
                             around=a.around, line_min=a.line_min, workers=a.workers)
        rows = rows[:a.top] if a.top else rows
    else:
        items = parse_items(raw)
        if a.cmd == "filter":
            rows, st = run_filter(items, a.question, call, context=ctx, threshold=a.threshold,
                                  top=a.top, true=a.true, false=a.false, workers=a.workers)
        elif a.cmd == "rank":
            rows, st = run_rank(items, a.question, a.levels, call, context=ctx, top=a.top,
                                min_score=a.min_score, workers=a.workers)
        else:
            rows, st = run_classify(items, a.question, _options(a.option), call, context=ctx,
                                    workers=a.workers)
            rows = rows[:a.top] if a.top else rows
        fields = a.fields.split(",") if a.fields else None
        for row in rows:
            row["item"] = project(items[row["i"]], fields, a.max_chars)
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))
    extra = "".join(" · %s=%s" % (k, v) for k, v in st.items()
                    if k not in ("n", "input_tokens", "output_tokens"))
    print("jev %s: %d in → %d out · jev tokens %d/%d%s · %.1fs" % (
        a.cmd, st["n"], len(rows), st["input_tokens"], st["output_tokens"], extra,
        time.time() - t0), file=sys.stderr)


if __name__ == "__main__":
    main()
