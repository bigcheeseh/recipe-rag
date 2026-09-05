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

import anthropic
import httpx
import yaml
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.api import app, load_corpus  # noqa: E402
from app.llm import TokenUsage, cost_usd  # noqa: E402
from app.models import Answer, Recipe  # noqa: E402

CRITERIA = ("clarity", "care", "language")


class Judgement(BaseModel):
    """Rubric scores from prompts/judge.md. Reported next to the deterministic result,
    never used as the pass/fail gate."""

    clarity: int = Field(ge=1, le=3)
    care: int = Field(ge=1, le=3)
    language: int = Field(ge=1, le=3)
    note: str

    def scores(self) -> str:
        return "/".join(str(getattr(self, c)) for c in CRITERIA)


def render_response(body: dict) -> str:
    if body.get("answer"):
        text = body["answer"]
    else:
        r = body.get("refusal") or {}
        text = f"REFUSAL ({r.get('reason')}): {r.get('message')}"
    if body.get("conflicts"):
        text += "\nConflicts: " + " | ".join(body["conflicts"])
    return text


def judge(
    client: anthropic.Anthropic, model: str, question: str, body: dict
) -> tuple[Judgement, TokenUsage]:
    prompt = (ROOT / "prompts" / "judge.md").read_text(encoding="utf-8")
    prompt = prompt.replace("{question}", question).replace("{response}", render_response(body))
    resp = client.messages.parse(
        model=model,
        max_tokens=4096,  # adaptive thinking counts against this
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
        output_format=Judgement,
    )
    if resp.parsed_output is None:
        raise RuntimeError(f"judge returned no object: stop_reason={resp.stop_reason}")
    u = resp.usage
    return resp.parsed_output, TokenUsage(tokens_in=u.input_tokens, tokens_out=u.output_tokens)


def agreement(judge_scores: dict[str, str], human_scores: dict[str, str]) -> dict[str, dict]:
    """Per criterion: exact-match rate and mean absolute difference over ids scored by both.
    Scores are "c/c/l" strings as written in the answers file."""
    ids = sorted(set(judge_scores) & set(human_scores))
    out: dict[str, dict] = {}
    for i, c in enumerate(CRITERIA):
        pairs = [
            (int(judge_scores[k].split("/")[i]), int(human_scores[k].split("/")[i])) for k in ids
        ]
        n = len(pairs)
        out[c] = {
            "n": n,
            "exact": sum(j == h for j, h in pairs) / n if n else 0.0,
            "mean_abs_diff": sum(abs(j - h) for j, h in pairs) / n if n else 0.0,
        }
    return out


def table_column(table: Path, idx: int, want_scores: bool = False) -> dict[str, str]:
    """Column `idx` of the markdown table rows whose id starts with "g"."""
    out = {}
    for line in table.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) > idx and cells[0].startswith("g"):
            if not want_scores or cells[idx].count("/") == 2:
                out[cells[0]] = cells[idx]
    return out


def judge_summary(model: str, judged: dict[str, Judgement], usage: TokenUsage) -> list[str]:
    if not judged:
        return []
    means = {c: statistics.mean(getattr(j, c) for j in judged.values()) for c in CRITERIA}
    line = ", ".join(f"{c} {m:.2f}" for c, m in means.items())
    return [
        f"Rubric judge ({model}, reported, not gating), mean of 1-3 over {len(judged)} "
        f"responses: {line}. Judge cost USD {cost_usd(model, usage):.4f}.",
        "",
    ]


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
    # The assignment's minimum schema, checked against what the body literally says.
    want = a.model_dump(mode="json")
    for field in ("citations", "refused", "refusal_reason"):
        if field not in body:
            return [f"contract: missing {field}"]
        if body[field] != want[field]:
            return [f"contract: {field} {body[field]} != {want[field]}"]

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


def make_client(url: str | None) -> httpx.Client:
    """In-process app by default; a real HTTP client when a deployed URL is given.
    The deployed run is the assignment's proof, so it goes through the network stack."""
    if url:
        return httpx.Client(base_url=url.rstrip("/"), timeout=httpx.Timeout(180.0))
    return TestClient(app, raise_server_exceptions=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--retriever", default="full", help="full | bm25 | hybrid (sets RETRIEVER)")
    ap.add_argument(
        "--url",
        default=None,
        help="base URL of a deployed service to test instead of the in-process app; "
        "--retriever/--model then only label the run",
    )
    ap.add_argument("--model", default="claude-sonnet-5", help="sets MODEL for this run")
    ap.add_argument("--label", default=None, help="run label; defaults to retriever-model")
    ap.add_argument("--runs", type=Path, default=ROOT / "evals" / "runs")
    ap.add_argument(
        "--judge",
        default=None,
        help="rubric judge model, or 'none'; default claude-opus-5 for every run so scores "
        "are comparable across models (Opus is never the model under test)",
    )
    ap.add_argument(
        "--calibrate",
        type=Path,
        default=None,
        help="an answers file with the human column filled in: print judge agreement, exit",
    )
    args = ap.parse_args(argv)
    if args.calibrate:
        report = agreement(
            table_column(args.calibrate, 2, True), table_column(args.calibrate, 3, True)
        )
        for c, r in report.items():
            print(
                f"{c:9} n={r['n']:2} exact={r['exact']:.0%} mean_abs_diff={r['mean_abs_diff']:.2f}"
            )
        return 0
    os.environ["RETRIEVER"], os.environ["MODEL"] = args.retriever, args.model
    args.label = args.label or f"{args.retriever}-{args.model}" + ("-deployed" if args.url else "")
    if args.judge is None:
        args.judge = "claude-opus-5"
    if args.judge == args.model:
        raise SystemExit("the judge must not be the model under test")
    load_dotenv()  # the app loads it at startup; the judge client is built before that
    judge_client = anthropic.Anthropic() if args.judge != "none" else None

    golden = yaml.safe_load((ROOT / "evals" / "golden_set.yaml").read_text(encoding="utf-8"))
    corpus = {r.id: r for r in load_corpus(ROOT / "data" / "corpus.json")}
    baseline = previous_passes(args.runs)

    rows, regressions, answers = [], [], []
    lat: dict[str, list[int]] = {"extract": [], "retrieve": [], "generate": [], "total": []}
    costs: list[float] = []
    judged: dict[str, Judgement] = {}
    judge_usage = TokenUsage()
    with make_client(args.url) as client:
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
            score = ""
            if judge_client and r.status_code == 200:
                j, ju = judge(judge_client, args.judge, g["q"], body)
                judged[g["id"]], judge_usage, score = j, judge_usage + ju, j.scores()
                flat = render_response(body).replace("\n", " ").replace("|", "/")
                answers.append(f"| {g['id']} | {g['q']} | {score} |  | {flat} | {j.note} |")
            rows.append(
                f"| {g['id']} | {g['kind']} | {'PASS' if ok else 'FAIL'} | "
                f"{'; '.join(fails)} | {refusal} | {len(body.get('sources') or [])} | "
                f"{len(body.get('conflicts') or [])} | {usage.get('tokens_in', '')} | "
                f"{usage.get('tokens_out', '')} | {usage.get('cost_usd', 0):.4f} | "
                f"{usage.get('latency_ms', {}).get('total', '')} | {score} |"
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
        *judge_summary(args.judge, judged, judge_usage),
        "| id | kind | result | failures | refusal | sources | conflicts | tokens_in | "
        "tokens_out | cost_usd | total_ms | judge c/c/l |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
    ]
    args.runs.mkdir(parents=True, exist_ok=True)
    out = args.runs / f"{stamp}-{args.label}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    if answers:
        answers_file = args.runs / f"{stamp}-{args.label}.answers.md"
        header = [
            f"# Answers {stamp} — {args.label}, judged by {args.judge}",
            "",
            "Fill the `human` column with your own clarity/care/language scores (e.g. 3/2/3),",
            "then run `python evals/run_evals.py --calibrate <this file>`.",
            "",
            "| id | question | judge | human | response | judge note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        answers_file.write_text("\n".join(header + answers + [""]), encoding="utf-8")
        print(f"answers for human scoring -> {answers_file}")
    print(f"\n{passed}/{len(rows)} passed, regressions: {regressions or 'none'} -> {out}")
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
