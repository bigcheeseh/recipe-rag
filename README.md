# Recipe Q&A Service

Answers questions about 48 Wikibooks Cookbook recipes, only from those
recipes, with citations, and refuses in a machine-readable way when the
recipes cannot answer. FastAPI backend, one-page TypeScript UI, Claude
Sonnet 5 for the two model calls.

- Deployed UI: https://recipe-rag-jbgq.onrender.com/ and API:
  `POST https://recipe-rag-jbgq.onrender.com/ask`
  (`GET /healthz`, `GET /config`, OpenAPI at `/docs`)
- Container-level access for reviewers: `GET /ops` behind a token (see Deployment)
- Specification: [SPEC.md](SPEC.md). Decisions: [ADR/](ADR). Working log: [DEVLOG.md](DEVLOG.md).
- Agent instructions and notes: [CLAUDE.md](CLAUDE.md) (as given, unchanged) and the
  DEVLOG.md.

## What is not production grade yet

Stopped before production grade in these places; each is a known gap, not an oversight.

- No authentication or rate limit on `/ask`. A public demo with a paid model behind it
  needs at least a per-IP limit and a daily spend cap before real traffic.
- One region, one instance, sleeping when idle. Fine for review traffic; a real service
  wants two instances for zero-downtime deploys and a warm one for the p95.
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

## Switching model and retrieval

Two selectors on the page, each with a tooltip stating the measured trade-off, send
`model` and `retriever` with the question. The API accepts the same two fields, and
`GET /config` lists what the running server can offer and its defaults:

```
curl -s localhost:8080/ask -H 'Content-Type: application/json' \
  -d '{"question": "Quickest recipe?", "model": "claude-haiku-4-5", "retriever": "bm25"}'
```

Server defaults come from `MODEL` and `RETRIEVER` in the environment. `hybrid` is offered
only when `VOYAGE_API_KEY` and `data/embeddings.npz` are present. The response's
`usage.model` and `usage.retriever` and the request log say which pair answered, so a
switched request is never ambiguous. Selectable models are Sonnet 5 and Haiku 4.5.
Because the endpoint has no authentication, any caller can pick the dearer pair (SPEC
assumption 14); that is the first thing to restrict if this outlives the demo.

## Deployment

**Where:** Render, one free web service in `frankfurt`, built from the committed
[render.yaml](render.yaml) and the same [Dockerfile](Dockerfile) used locally.
Until 2026-09-07 this ran on Fly.io; Fly's trial ended and the account then refused
every write, including deleting the app, so the service moved. [fly.toml](fly.toml)
stays in the repository: the image is identical on both hosts, and the move plus the
alternatives considered (Cloud Run with and without Terraform, Fly, Render) are in
[ADR-004](ADR/004-deployment-target.md).

**How a new deployment happens:** two things run on every push to `main`, independently.
[.github/workflows/ci.yml](.github/workflows/ci.yml) is the test gate: ruff, mypy,
pytest, the TypeScript build, and a Docker build. Render rebuilds the image and rolls
the service because the blueprint sets `autoDeployTrigger: commit`. No step happens in
a UI after the one-time creation of the service from the blueprint, which is the single
manual action in this setup and is the reason Render lost the original decision in
ADR-004. The deploy is idempotent: the same commit deployed twice yields the same
service. `GET /ops` reports the deployed commit, so what is running is checkable from
outside.

**Secrets:** the Anthropic key is read from the environment. Locally that is `.env`
(gitignored); on Render it is an environment variable marked `sync: false` in the
blueprint, which means Render asks for the value once and stores it encrypted rather
than reading it from the repository. The image contains no key, and the request log
never prints one.

**Container-level access:** the assignment offers two options, a dashboard invitation or
access to logs and container status. This service takes the second, so that access does
not depend on the host's seat model; on Fly it was forced, because a personal
organisation cannot hold members. `GET /ops` serves instance id, region, deployed
commit, uptime, recipe count, and the tail of the structured request log, protected by
the token in `OPS_TOKEN`. Nothing to install: open

```
https://recipe-rag-jbgq.onrender.com/ops?token=<token>&limit=200
```

in a browser, or send the token as `Authorization: Bearer <token>`. The token is handed
to reviewers separately and is rotated by editing the variable in the Render dashboard;
removing it makes the endpoint return 404. The buffer is the last 500 log records, held
in memory and lost when the instance sleeps, with any `token=` redacted. From the
owner's side the same data is in the Render dashboard under Logs and Events.

## Cost & Latency

**Models.** `claude-sonnet-5` for both calls: query extraction and answer generation.
Haiku 4.5 was measured at about a third of the cost, but on browsing questions it
presented guessed cooking times as facts, and with the whole corpus in front of it it
still picked the wrong "quickest" recipe (ADR-002). A recipe service that invents
numbers fails its one job, so the cheaper model is a one-line switch (`MODEL`), not the
default. Opus 5 is used only as the eval judge.

**Cost per question, measured** on the deployed service, 29-question golden set, Sonnet 5,
full context with the recipe block prompt-cached (`evals/runs/20260907T170625Z-full-claude-sonnet-5-render.md`):

| | USD |
| --- | --- |
| Mean per question | 0.0163 |
| Per 1,000 questions | 16.29 |
| First question on a fresh instance (cache write, measured on Render, 2026-09-07) | 0.0760 |

Cost is a property of the models, not of the host: three deployed runs measured 12.61,
15.87 and 16.29 per 1,000 questions, and the spread comes from answer length and from
how many questions pay a cache write, not from the machine underneath. The cold figure
is the 1.25x cache write on the whole corpus. The cache lives five minutes, so at review
traffic most requests will be cold; at steady traffic almost none are. BM25 top-8 on the
same set costs 15.66 per 1,000 with no cache dependence.

**When the model or the retrieval changes.**

- Cheaper model: only if an eval slice shows Haiku no longer guessing on browsing and
  corpus-wide questions (it fails 3 of 29 today with full context).
- More capable model: Sonnet passes 29/29; there is no measured need.
- Retrieval: full context is cheaper than BM25 below about 80 recipes with a warm cache
  and more expensive above it (ADR-002). The flag is `RETRIEVER=bm25`.

**Latency, measured** on the deployed service, one request at a time (full table with
budgets in SPEC.md section 6):

| | p50 | p95 |
| --- | --- | --- |
| extract | 2.0 s | 2.4 s |
| generate | 3.9 s | 13.3 s |
| total | 5.9 s | 14.8 s |
| first request after 17 minutes without traffic (one sample) | 0.59 s | |
| warm health request | 0.56 s | |

The idle sample is the surprise: Render documents a 15-minute spin-down with a wake of
roughly a minute, but after 17 idle minutes the instance answered in 0.59 s, so it had
not been spun down. The likely reason is the health check the blueprint configures,
which keeps probing the service. This is one sample over one idle period and is not
evidence that a spin-down never happens; a reviewer arriving after a long gap may still
pay the documented wake. On Fly the same measurement was a genuine cold start of 6.5 s.

**Current bottleneck:** the generation call. Extraction is about 2 s and retrieval
is 0 ms in full-context mode, so everything above that is the model reading 30k cached
tokens of recipes and writing a structured answer. The p95 is one question, "which
recipe has the longest stated time", where the model walks every recipe's times.
Next optimisation, in order: lower
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
