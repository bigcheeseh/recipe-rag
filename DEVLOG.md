# DEVLOG

Unprompted architectural decisions, measured numbers, and notes on what agent
output was accepted as-is versus rewritten.

## 2026-09-03 — open question: full context on a cheaper model

Raised during Block 1 review: could Haiku 4.5 with the whole corpus in the
prompt beat Sonnet 5 with retrieval on cost and speed?

Back-of-envelope at list prices, token counts unmeasured: Haiku full context
(~40k input tokens at $1/M) is roughly six times the input cost of Sonnet
retrieval (~3.5k tokens at $2/M). With prompt caching of the corpus (cached
reads at ~0.1x) full context on either model becomes competitive with
retrieval. Quality on the conflict and allergy cases is the unknown.

Decision: keep retrieval on Sonnet as the baseline. In Commit 31 the
comparison table gets extra rows: Sonnet full context with caching, Haiku
full context with caching. ADR-002 must state the corpus size at which full
context stops being viable.

## 2026-09-03 — Python 3.11 instead of 3.12

Only 3.11.6 is installed on the dev machine. CLAUDE.md said 3.12; the user
chose to stay on 3.11 rather than install another interpreter.
`requires-python`, the ruff target, and the future Docker base image all
say 3.11. No 3.12-only features are used. The package is installed into the
venv in editable mode (`pip install -e .`) so `app` imports resolve outside
pytest as well.

## 2026-09-03 — corpus review and conflict variants

Ingestion: 61 curated titles, 48 accepted, 13 rejected (all index or
disambiguation pages). Enrichment 48 calls, 67,529 tokens in, 2,639 out,
~USD 0.16. Hand review found 3 metadata errors in 48 records (6%): one
false gluten, one false shellfish (fish confused with shellfish), one
total_minutes that ignored an overnight soak. All corrected and logged in
the manifest.

Conflict variants present in the corpus without adding anything:
- carbonara: 5 egg yolks vs 4 whole eggs; 60 vs 30 minutes
- chocolate chip cookies: 375°F (I, II) vs 350°F (III, vegan, gluten-free)
- banana bread ×3, guacamole ×3, risotto ×3 with smaller differences

The bolognese pair I originally chose for g13 both simmer for one hour, so
there was no conflict to detect. g13 now asks about carbonara eggs. g01
and g03 were narrowed to a specific recipe so they stay plain factual
questions rather than accidental conflict cases. tests/test_corpus.py pins
these facts so a corpus refresh that breaks the golden set fails CI.

## 2026-09-04 — retrieval demo before wiring the LLM

BM25 over 96 section chunks, golden-set questions fed in raw (no query
extraction yet). Every in-domain question puts the right recipe family in
the top 3. Two things worth knowing before Block 5:

- Raw questions carry noise. "How many eggs go into carbonara?" ranks a
  cookie recipe first because "go"/"into"/"eggs" score across many chunks;
  the extracted form "carbonara eggs" ranks both carbonara variants 1–2.
  The extract_query prompt must return bare content terms, not the question.
- Out-of-domain and absent-dish questions ("flat tyre", "Beef Wellington")
  still return five low-score recipes. BM25 has no notion of "nothing
  relevant". Refusals therefore have to come from extract_query (in_domain)
  and from the generator (insufficient_context), never from a score cutoff.
  A score threshold was considered and rejected: BM25 scores are not
  comparable across queries.
- Unknown metadata is treated as failing any active filter. Every corpus
  record currently has metadata, so this only matters for future refreshes.

## 2026-09-04 — Block 5 decisions

- Query extraction adds a probable dish name when the user describes a dish
  without naming it ("pasta with bacon and egg" -> "carbonara bacon egg
  time", observed live). This is the cheap answer to BM25's vocabulary
  problem; the eval will show whether it is enough.
- The generator sometimes fills both `answer` and `refusal` on a safety
  deferral (observed live on the pad thai question). The pipeline lets the
  refusal win rather than failing the request; the test pins this.
- Thinking effort is left at the provider default for both calls, as SPEC
  assumption 4 says. Measured live latency is roughly 2-3 s for extraction
  and 3-5 s for generation on single requests; the eval run will give real
  p50/p95 figures, so nothing is written into SPEC section 6 yet.
- Every response carries an `X-Trace-Id` header matching the log record and
  the error body, so a user report can be tied to one JSON line.
- `prompt_hash` is the SHA-256 of all files under `prompts/`, truncated, so
  the log tells which prompt version produced an answer.
- Open mismatch to resolve in Block 6: SPEC AC-7 says g06 ("vegan main with
  no nuts") should be a safety deferral, but the golden set treats it as a
  filtered recommendation. The golden set is right: it asks for dishes, not
  for a medical judgement. AC-7 should be narrowed to g05.

## 2026-09-04 — BM25 baseline eval

First run: 12/13. g07 ("What can I cook in under 30 minutes?") failed:
the extractor produced `search_terms="quick recipes", max_minutes=30`, the
time filter left 23 recipes, and BM25 matched none of them because no
recipe text contains "quick". Retrieval returned nothing and the pipeline
refused with insufficient_context. Fix (test first): when constraints are
active and ranking finds nothing, the filtered set itself is returned, since
for a browsing question the filter is the answer set. Without constraints
the empty result stands, because there is no defined answer set to fall
back to.

Second run, committed as `evals/runs/20260904T170932Z-bm25.md`: 13/13.
Mean cost USD 0.0111 per question (USD 11.07 per 1,000). Latency on the dev
machine, p50 / p95: extract 1932 / 2484 ms, generate 2944 / 4707 ms, total
5192 / 6299 ms. Retrieval is 0 ms at millisecond resolution. These are not
the deployed numbers SPEC section 6 asks for; those wait for Block 7.

Every check in the runner is a string or set comparison over the response
body plus recipe metadata. There is no model-graded scoring anywhere.
