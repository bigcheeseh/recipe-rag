# Recipe Q&A Service

Answers questions about 48 Wikibooks Cookbook recipes, only from those
recipes, with citations, and refuses in a machine-readable way when the
recipes cannot answer. FastAPI backend, one-page TypeScript UI, Claude
Sonnet 5 for the two model calls.

- Deployed UI and API: **TBD** (filled in once `fly deploy` has run)
- Container-level access for reviewers: **TBD** (Fly.io organisation invitation; see Deployment)
- Specification: [SPEC.md](SPEC.md). Decisions: [ADR/](ADR). Working log: [DEVLOG.md](DEVLOG.md).
- Agent instructions and notes: [CLAUDE.md](CLAUDE.md) (as given, unchanged) and the
  "accepted vs rewritten" section of DEVLOG.md.

## What is not production grade yet

Stopped before production grade in these places; each is a known gap, not an oversight.

- No authentication or rate limit on `/ask`. A public demo with a paid model behind it
  needs at least a per-IP limit and a daily spend cap before real traffic.
- One region, one machine, scale to zero. Fine for review traffic; a real service
  wants two machines for zero-downtime deploys and a warm instance for the p95.
- No alerting. Logs are structured but nobody is paged on error rate or spend.
- The judge scores in the eval runs are reported, never gating, and not yet
  calibrated against human scores (the runner has the `--calibrate` path for it).
- Corpus refresh is a manual `python -m app.ingest` plus a review of the metadata.

## Run locally

Docker, with a `.env` file (copy `.env.example`, set `ANTHROPIC_API_KEY`):

```
docker compose up --build
```

Then open http://localhost:8080 for the UI, or:

```
curl -s localhost:8080/ask -H 'Content-Type: application/json' \
  -d '{"question": "How many eggs go into carbonara?"}'
```

Without Docker (Python 3.11, Node 24):

```
python -m venv .venv && .venv/Scripts/activate      # or source .venv/bin/activate
pip install -r requirements.txt
(cd ui && npm ci && npm run build)                  # optional, only for the page
uvicorn app.api:app --app-dir src --port 8080
```

Tests, lint, types, and the eval harness:

```
pytest && ruff check . && mypy src
python evals/run_evals.py                # in-process app, real model, Opus judge
python evals/run_evals.py --url https://<deployed-host>   # the deployed service
```

Every eval run writes a table to `evals/runs/` and exits non-zero on a regression
against the last committed run. Rebuild the corpus from scratch with
`python -m app.ingest` (MediaWiki API, cached HTML, manifest of accepted and rejected pages).

## Deployment

**Where:** Fly.io, one machine in `ams`, from the committed [fly.toml](fly.toml) and the
same [Dockerfile](Dockerfile) used locally. Reasons and the alternatives considered
(Cloud Run with and without Terraform, Render) are in [ADR-004](ADR/004-deployment-target.md).
In short: it is one container with no state, Fly needs one file and one command,
the machine stops when idle so review traffic costs nothing, and reviewers get
container-level access by invitation.

**How a new deployment happens:** every push to `main` runs
[.github/workflows/ci.yml](.github/workflows/ci.yml): ruff, mypy, pytest, the
TypeScript build, a Docker build, and then `flyctl deploy --remote-only`. The job needs
one GitHub secret, `FLY_API_TOKEN`. Running the deploy twice produces the same result.
By hand it is the same command:

```
fly secrets set ANTHROPIC_API_KEY=...   # once; stored encrypted by Fly, never in git or the image
fly deploy
```

**Secrets:** the Anthropic key is read from the environment. Locally that is `.env`
(gitignored); on Fly it is the secret above. The image contains no key, and the request
log never prints one.

**Container-level access:** TBD (the reviewers' addresses are invited to the Fly
organisation, which shows machine status, releases, and live logs; `fly logs` and
`fly status` give the same from the CLI).

## Cost & Latency

**Models.** `claude-sonnet-5` for both calls: query extraction and answer generation.
Haiku 4.5 was measured at about a third of the cost, but on browsing questions it
presented guessed cooking times as facts, and with the whole corpus in front of it it
still picked the wrong "quickest" recipe (ADR-002). A recipe service that invents
numbers fails its one job, so the cheaper model is a one-line switch (`MODEL`), not the
default. Opus 5 is used only as the eval judge.

**Cost per question, measured** on the 29-question golden set, Sonnet 5, full context
with the recipe block prompt-cached (`evals/runs/20260904T201858Z-full-claude-sonnet-5.md`):

| | USD |
| --- | --- |
| Mean per question, cache warm | 0.0149 |
| Per 1,000 questions, cache warm | 14.94 |
| First request after a cold cache (measured in the local container, 2026-09-05) | 0.0726 |

The cold figure is the 1.25x cache write on the whole corpus. The cache lives five
minutes, so at review traffic most requests will be cold; at steady traffic almost none
are. BM25 top-8 on the same set costs 14.75 per 1,000 with no cache dependence.

**When the model or the retrieval changes.**

- Cheaper model: only if an eval slice shows Haiku no longer guessing on browsing and
  corpus-wide questions (it fails 3 of 29 today with full context).
- More capable model: Sonnet passes 29/29; there is no measured need.
- Retrieval: full context is cheaper than BM25 below about 80 recipes with a warm cache
  and more expensive above it (ADR-002). The flag is `RETRIEVER=bm25`.

**Latency, measured.** Deployed numbers are TBD until the first deploy; the
pre-deployment reference from the developer machine, one request at a time, is in
SPEC.md section 6. On the golden set with full context, total p50 was 6.3 s and
generation p95 14.9 s, against 8.4 s for BM25.

**Current bottleneck:** the generation call. Extraction is about 2 to 3 s and retrieval
is 0 ms in full-context mode, so everything above that is the model reading 26k cached
tokens of recipes and writing a structured answer. Next optimisation, in order: lower
the generator's thinking effort and measure the p95 change; stream the answer to the UI
so the perceived wait drops even if the total does not; only then consider BM25 top-8 as
the default again, which trades the three corpus-wide questions for 6 s off the p95.

## Diagnosing a bad answer in production

Every request writes one JSON log line (logger `app.request`) keyed by the `trace_id`
that is also returned in the `X-Trace-Id` header and shown in the UI footer. The line
carries the raw question, the extracted query (domain flag, search terms, filters), the
retrieved recipe ids with scores, the ids the model cited, the grounding result
(`ok`, `repaired`, or `refused`), the prompt hash, the model name, token counts including
cache reads and writes, cost, and per-stage latency. Given a complaint, find the trace
id, and the line answers the first question on its own: if the right recipe is not in
`retrieved`, it is a retrieval or filter failure (check the extracted filters, then the
recipe's metadata); if it is retrieved but not cited or the text is wrong, it is a
generation failure (re-run the question in the eval harness with the same prompt hash,
add it to the golden set, and fix the prompt against that). The prompt hash ties the
answer to the exact prompt files that produced it, so a regression after a prompt edit
is visible in the log before anyone reports it.
