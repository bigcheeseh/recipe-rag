"""Run the golden set against the in-process app with the real model.

Every check is deterministic (AC-13): no LLM-as-judge. Writes a markdown table to
evals/runs/<timestamp>-<label>.md and exits 1 if any question that passed in the
most recent committed run fails now.

    python evals/run_evals.py --label bm25
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.api import app, load_corpus  # noqa: E402
from app.models import Answer, Recipe  # noqa: E402


def check(expect: dict, status: int, body: dict, corpus: dict[str, Recipe]) -> list[str]:
    """Return the list of failed expectations (empty = pass)."""
    fails: list[str] = []
    want_status = expect.get("http_status", 200)
    if status != want_status:
        return [f"http {status} != {want_status}"]
    if want_status != 200:
        return []
    try:
        a = Answer.model_validate(body)
    except Exception as e:  # noqa: BLE001
        return [f"schema: {e}"][:1]

    cited = [s.recipe_id for s in a.sources]
    text = (a.answer or "").lower()
    message = (a.refusal.message if a.refusal else "").lower()

    for sub in expect.get("cites", []):
        if not any(sub in c for c in cited):
            fails.append(f"cites {sub}: got {cited}")
    if "cites_min" in expect and len(cited) < expect["cites_min"]:
        fails.append(f"cites_min {expect['cites_min']}: got {len(cited)}")
    if "contains" in expect and expect["contains"].lower() not in text:
        fails.append(f"contains {expect['contains']!r}")
    if "mentions" in expect and expect["mentions"].lower() not in text + " " + message:
        fails.append(f"mentions {expect['mentions']!r}")
    if "refusal" in expect:
        got = a.refusal.reason if a.refusal else None
        if got != expect["refusal"]:
            fails.append(f"refusal {expect['refusal']}: got {got}")
    if expect.get("sources_empty") and cited:
        fails.append(f"sources_empty: got {cited}")
    if expect.get("answered") and a.answer is None:
        fails.append(f"answered: got refusal {a.refusal.reason if a.refusal else None}")
    if expect.get("script") == "cyrillic" and not re.search(r"[Ѐ-ӿ]", text + message):
        fails.append("script cyrillic")
    if "conflicts_min" in expect and len(a.conflicts) < expect["conflicts_min"]:
        fails.append(f"conflicts_min {expect['conflicts_min']}: got {len(a.conflicts)}")

    metas = {c: corpus[c].meta for c in cited if c in corpus and corpus[c].meta}
    if "never_cites_allergen" in expect:
        bad = [c for c, m in metas.items() if expect["never_cites_allergen"] in m.allergens]
        if bad:
            fails.append(f"cites {expect['never_cites_allergen']} recipe: {bad}")
    if "requires_diet" in expect:
        bad = [c for c, m in metas.items() if expect["requires_diet"] not in m.diet_tags]
        if bad:
            fails.append(f"not {expect['requires_diet']}: {bad}")
    if "max_minutes_cited" in expect:
        bad = [c for c, m in metas.items() if m.total_minutes > expect["max_minutes_cited"]]
        if bad:
            fails.append(f"over {expect['max_minutes_cited']} min: {bad}")
    return fails


def previous_passes(runs: Path) -> set[str]:
    """Ids that passed in the most recent run committed to git (empty if none)."""
    out = subprocess.run(
        ["git", "ls-files", str(runs)], capture_output=True, text=True, cwd=ROOT, check=False
    )
    files = sorted(f for f in out.stdout.split() if f.endswith(".md"))
    if not files:
        return set()
    passed = set()
    for line in (ROOT / files[-1]).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) > 2 and cells[0].startswith("g") and cells[2] == "PASS":
            passed.add(cells[0])
    return passed


def pct(values: list[int], p: float) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[min(len(s) - 1, int(round(p * (len(s) - 1))))]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retriever", default="bm25", help="bm25 | hybrid | full (sets RETRIEVER)")
    ap.add_argument("--model", default="claude-sonnet-5", help="sets MODEL for this run")
    ap.add_argument("--label", default=None, help="run label; defaults to retriever-model")
    ap.add_argument("--runs", type=Path, default=ROOT / "evals" / "runs")
    args = ap.parse_args(argv)
    os.environ["RETRIEVER"], os.environ["MODEL"] = args.retriever, args.model
    args.label = args.label or f"{args.retriever}-{args.model}"

    golden = yaml.safe_load((ROOT / "evals" / "golden_set.yaml").read_text(encoding="utf-8"))
    corpus = {r.id: r for r in load_corpus(ROOT / "data" / "corpus.json")}
    baseline = previous_passes(args.runs)

    rows, regressions = [], []
    lat: dict[str, list[int]] = {"extract": [], "retrieve": [], "generate": [], "total": []}
    costs: list[float] = []
    with TestClient(app) as client:
        for g in golden:
            r = client.post("/ask", json={"question": g["q"]})
            body = (
                r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            )
            fails = check(g["expect"], r.status_code, body, corpus)
            ok = not fails
            if not ok and g["id"] in baseline:
                regressions.append(g["id"])
            usage = body.get("usage") or {}
            for k in lat:
                if k in usage.get("latency_ms", {}):
                    lat[k].append(usage["latency_ms"][k])
            if "cost_usd" in usage:
                costs.append(usage["cost_usd"])
            refusal = (body.get("refusal") or {}).get("reason") or ""
            rows.append(
                f"| {g['id']} | {g['kind']} | {'PASS' if ok else 'FAIL'} | "
                f"{'; '.join(fails)} | {refusal} | {len(body.get('sources') or [])} | "
                f"{len(body.get('conflicts') or [])} | {usage.get('tokens_in', '')} | "
                f"{usage.get('tokens_out', '')} | {usage.get('cost_usd', 0):.4f} | "
                f"{usage.get('latency_ms', {}).get('total', '')} |"
            )
            print(rows[-1])

    passed = sum("| PASS |" in r for r in rows)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        f"# Eval run {stamp} — {args.label}",
        "",
        f"Model: {json.dumps(usage.get('model', ''))}. Questions: {len(rows)}. "
        f"Passed: {passed}/{len(rows)}. "
        f"Regressions vs last committed run: {regressions or 'none'}.",
        "",
        f"Mean cost per question: {statistics.mean(costs):.4f} USD "
        f"(x1000 = {1000 * statistics.mean(costs):.2f} USD)."
        if costs
        else "No cost data.",
        "",
        "| stage | p50 ms | p95 ms |",
        "| --- | --- | --- |",
        *[f"| {k} | {pct(v, 0.5)} | {pct(v, 0.95)} |" for k, v in lat.items()],
        "",
        "| id | kind | result | failures | refusal | sources | conflicts | tokens_in | "
        "tokens_out | cost_usd | total_ms |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
    ]
    args.runs.mkdir(parents=True, exist_ok=True)
    out = args.runs / f"{stamp}-{args.label}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{passed}/{len(rows)} passed, regressions: {regressions or 'none'} -> {out}")
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
