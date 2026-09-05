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

## 2026-09-04 — hybrid (BM25 + Voyage vectors, RRF) vs BM25

Committed run `evals/runs/20260904T171901Z-hybrid.md`: 13/13, same as
BM25. Retrieval-level comparison on the extracted search terms of all
in-domain golden questions plus three "described, not named" probes
("pasta with bacon and egg", "creamy italian rice with mushrooms",
"mexican avocado dip"): the top-ranked recipe was identical for every one
of the 13 probes; hybrid only reordered positions 2-5 and padded short
lists with weak neighbours (e.g. pico-de-gallo behind guacamole). The
reason is upstream: query extraction already rewrites a described dish
into its name, so the vector side has no vocabulary gap left to close on
this corpus.

Costs of hybrid that BM25 does not have: a second provider and key, one
network call per request (about 300 ms measured when not rate limited),
and on Voyage's free tier a 3-requests-per-minute cap that turned the
retrieve stage into 20 s p50 in the eval run (the client backs off 20 s on
429). Per-question model cost is unchanged (USD 0.0112 vs 0.0111).

Decision: hybrid stays behind `RETRIEVER=hybrid`, off by default, code and
embeddings kept. It becomes worth revisiting when the corpus grows enough
that dish names stop being unique keys, or when questions arrive without
the extraction step. Feeds ADR-002.

## 2026-09-04 — retrieval vs full-context comparison (Block 6 close)

Five configurations, all 13/13 on the golden set. Table and thresholds in
ADR-002. Headline numbers (mean USD per question / total p50 ms):
BM25+Sonnet 0.0111 / 5192; hybrid+Sonnet 0.0112 / 25296 (Voyage free-tier
rate limit); full+Sonnet 0.0122 / 5870; full+Haiku 0.0063 / 4428;
BM25+Haiku 0.0040 / 3675.

Full context with prompt caching works as expected: the first question
wrote 26,186 tokens to the cache, every later one read them back. Cost
accounting now prices cache writes at 1.25x and reads at 0.1x of input,
and `Usage.tokens_in` reports total input including cached tokens, so the
number in the response matches what the provider billed for.

The prompt structure changed for this: rules and recipes moved to the
system prompt (recipes in their own block so it can carry `cache_control`),
the question is the user message. Same prompt text, so all five runs are
comparable. The BM25 baseline was not re-run after this change; the first
BM25 row in ADR-002 is the earlier prompt layout. The Haiku BM25 row uses
the new layout and also passed 13/13, so the layout did not move accuracy.

Decision: BM25 + Sonnet 5 stays the default. Hybrid and full context stay
behind flags. Haiku is a documented `MODEL` switch, not the default, until
the golden set is large enough to rank models on wording quality.

## 2026-09-04 — golden set grown to 23; first question that separates configs

Added eight harder English questions (two-dish comparison, negative fact,
described dish, two constraints at once, contains-vs-safe, near-miss dish,
doubling arithmetic, prompt injection) and two Russian ones (factual and
allergen constraint, checked for a Cyrillic answer). Prompts now force
English search terms and answer in the question's language; SPEC
assumption 12 updated.

Two questions had to be corrected against the corpus before they were
fair: g16 asked for a time conflict between the two carbonaras, but only
one states a time, so it now checks the stated "1 hour"; g14 first
compared against Risotto ai Funghi, which states no time, and Sonnet
refused correctly, so it now compares against banana bread.

Two bugs surfaced and were fixed: a long answer (g17 listed five recipes)
overran `max_tokens=1024`, the SDK raised a validation error the wrapper
did not catch, and the eval runner died with the app's 500. Now: cap 4096,
truncation is caught and retried once, then 502; the runner records a
500 as a failed row.

Results on 23 questions: BM25+Sonnet 22/23, every other configuration
23/23. The failing question is g14, and the cause is BM25's fixed top-5
under a two-dish query (details in ADR-002). This is the first time the
golden set has separated the options, which is what it is for. The fix is
a decision (k=8 vs exact-title boost), left open.

## 2026-09-04 — rubric judge added (user decision, lifts the "no LLM-as-judge" rule)

The deterministic checks prove facts, citations and refusals but cannot
grade wording, which is the one thing that still separates Sonnet from
Haiku. The user chose to add a model-graded score with three conditions:
it is reported, never gating; the judge is never the model under test
(Opus 5 grades Sonnet, Sonnet grades Haiku); and it is calibrated against
human scores before it is used for a decision. The runner writes an
`.answers.md` file with a blank `human` column; `--calibrate` prints
per-criterion exact agreement and mean absolute difference. Judge cost is
reported separately and is not part of `Usage.cost_usd`.

## 2026-09-04 — first judged runs (BM25, Sonnet vs Haiku)

Deterministic result: both 23/23 this time (Sonnet's g14 answered where the
previous run refused; generation is not deterministic on that borderline
question). Rubric means, clarity / care / language:
Sonnet (judged by Opus 5) 3.00 / 2.95 / 2.91; Haiku (judged by Sonnet 5)
2.91 / 2.82 / 3.00. Judge cost USD 0.13 and 0.05 per run.

What the judge found that the string checks could not:
- Sonnet answered g14 (an English question) in Spanish. Rule 7 of
  prompts/generate.md ("write in the language of the question") was added
  for the Russian questions and is evidently too loose. Tightened to name
  English as the default and forbid switching. The deterministic `script`
  check only covers Cyrillic, so this slip was invisible to it.
- Haiku's safety deferral quoted "¾ cup (340 g)" of peanuts; the recipe
  says 175 ml. A fabricated conversion inside an otherwise correct
  deferral. The judge scored care 2 for lecturing and did not flag the
  number, because the rubric excludes facts by design. Worth knowing when
  reading Haiku answers: the substring checks pass, the details drift.
- Haiku's g07 answer presented guessed timings for recipes with no stated
  time as if they were facts (care 1). Sonnet on the same question listed
  the two recipes with stated times and said the others are unknown.

Calibration is still pending: the `.answers.md` files have an empty
`human` column. Until they are scored, the means above are the judge's
opinion, not a measurement.

## 2026-09-04 — language fix confirmed; g14 flaps on BM25 + Sonnet

Re-run after tightening rule 7 (`evals/runs/20260904T184934Z-bm25-claude-sonnet-5.md`):
language 3.00 on all 22 judged responses, care 2.91, clarity 3.00. The
Spanish slip did not recur.

g14 refused again (22/23) and the runner now exits 1, because the previous
committed run had passed it. Three runs on the same retrieval give
answer, refusal, answer: on the walnut variant, which states no total
time, Sonnet is on the fence between quoting "bake at least 1 hour" and
declining. The gate is doing its job by flapping, but the flap is a
retrieval problem (wrong banana bread variant in the top-5), not a
generation one. Decision pending: k=8 or an exact-title boost, see
ADR-002 item 5.

## 2026-09-04 — top-k 8 and exact-title promotion (user chose both)

Both fixes from ADR-002 item 5 went in test-first. Title promotion is a
guarantee, not a scoring tweak: "pad thai" must return Pad Thai first even
though Khao Pad Thai Fried Rice mentions the phrase more often. It only
helps when the extractor keeps the full title, which it did not always do
for "Banana Bread I"; k=8 is what makes that question stable.

## 2026-09-04 — BM25 + Sonnet with top-k 8: 23/23, no regression

`evals/runs/20260904T190742Z-bm25-claude-sonnet-5.md`: 23/23, g14 answered
with Banana Bread I in context. Judge means clarity 2.95, care 2.95,
language 3.00. Cost rose from USD 0.0114 to 0.0142 per question (+25%),
which is the price of three more recipes in every generation call; total
p50 5011 ms, p95 12067 ms. SPEC section 7 target updated to USD 14.23 per
1,000. The pre-k=8 Sonnet answers file was dropped so calibration uses
responses from the current retrieval; Haiku is re-run under k=8 for the
same reason.

## 2026-09-04 — BM25 + Haiku with top-k 8: 23/23

`evals/runs/20260904T191023Z-bm25-claude-haiku-4-5.md`: 23/23, USD 0.0050
per question (Sonnet on the same retrieval: 0.0142). Judge means (Sonnet 5
as judge) clarity 2.91, care 2.86, language 3.00, against Sonnet's
2.95 / 2.95 / 3.00 graded by Opus 5. The three Haiku responses below 3/3/3
are the same pattern as before: lecturing in the safety deferral, guessed
timings on the browsing question, and a vague multi-option answer to the
Russian constraint question.

Calibration files now: exactly one per model, both from the current
prompts and top-k 8. Judge-vs-human agreement is not measured yet.

## 2026-09-04 — one judge for every run

The first judged runs used Opus 5 to grade Sonnet and Sonnet 5 to grade
Haiku, which made the two score columns incomparable (different graders,
possibly different strictness). The runner now defaults to Opus 5 for
every run and refuses a judge equal to the model under test. The Haiku
run is re-judged by Opus so the Sonnet/Haiku comparison uses one grader.

## 2026-09-04 — Sonnet vs Haiku, both judged by Opus 5

Same prompts, same retrieval (BM25, top-k 8), same grader:
Sonnet 23/23, clarity 2.95, care 2.95, language 3.00, USD 0.0142/question.
Haiku 23/23, clarity 2.95, care 2.91, language 3.00, USD 0.0050/question.
Opus was slightly kinder to Haiku than Sonnet had been (care 2.91 vs
2.86), which is exactly why one grader is required. The remaining gap is
one response: Haiku's browsing answer (g07) lists recipes with no stated
time by guessing durations, care 1. Sonnet on the same question names the
two recipes with stated times and says the rest are unknown.

Files for human calibration, one per model, both from the current
prompts, retrieval and grader:
- evals/runs/20260904T190742Z-bm25-claude-sonnet-5.answers.md
- evals/runs/20260904T191546Z-bm25-claude-haiku-4-5.answers.md

## 2026-09-04 — model decision: Sonnet 5 stays the default

The user judged Haiku's g07 behaviour (durations guessed for recipes that
state none, presented as a list of facts) a serious problem. A recipe
service that invents numbers fails its one job, whatever the cost saving.
Sonnet 5 remains the default; Haiku remains `MODEL=claude-haiku-4-5` for
anyone who accepts that trade. Hybrid and full context are re-measured
under top-k 8 with the Opus judge so ADR-002's table is consistent.

## 2026-09-04 — generator could refuse out_of_domain; now it cannot

Hybrid and full-context runs both failed g12 (Beef Wellington) with
`out_of_domain`. The extractor was not at fault (6/6 in_domain when
probed); the generator, seeing many recipes and none matching, picked
`out_of_domain` from the shared Refusal enum. That reason belongs to the
extractor alone: the generator always has recipes in front of it, so its
only honest refusals are insufficient_context and safety_deferral. The
Draft schema now uses a two-value GeneratorRefusal, so the structured
output cannot express the wrong reason, and rule 1 of generate.md says a
missing dish is insufficient_context. All three Sonnet configurations are
re-run under the new schema.

## 2026-09-04 — final Block 6 table: all three Sonnet configurations 23/23

After the generator-refusal fix, BM25 / hybrid / full on Sonnet 5 all pass
23/23 with Opus-judged means within one response of each other
(ADR-002 table rebuilt). Costs USD 0.0143 / 0.0153 / 0.0148 per question.
Retrieval strategy no longer moves accuracy or wording on this corpus;
BM25 stays the default on cost, latency and dependencies.

Calibration files, one per model, current prompts and schema:
- evals/runs/20260904T193941Z-bm25-claude-sonnet-5.answers.md
- evals/runs/20260904T191546Z-bm25-claude-haiku-4-5.answers.md
  (Haiku run predates the refusal-schema change; the change only removed a
  refusal option Haiku never used, so its responses are unaffected.)

## 2026-09-04 — 3x2 matrix on 29 questions: full context separates from retrieval

Six corpus-wide questions added (quickest recipe, longest stated time,
cookie count, vegan under 15 min, soaked overnight, quickest in Russian).
Full matrix, all judged by Opus 5, table in ADR-002. Headline:
Sonnet + full context 29/29; every retrieval configuration 25-26/29,
failing exactly the questions that need the whole corpus; Haiku fails
them even with the whole corpus (26/29 on full context), and its
extractor classes "longest stated total time" as out_of_domain.

Cost at 48 recipes is a wash: Sonnet full 0.0149 vs BM25 0.0148 per
question. Latency is not: full context generate p95 14.9 s vs 8.4 s.

One retrieval bug surfaced (g27): a constrained browsing question whose
terms match only one of three filtered candidates returns one recipe,
because the fallback to the filtered set fires only on zero hits. Fix is
to pad up to k with the remaining candidates. Not applied yet.

Answers files: removed. Calibration was never done and the golden set has
changed twice since they were written; regenerate when scoring is
actually going to happen.

## 2026-09-05 — default switched to full context on Sonnet 5

User decision after the 3x2 matrix: `RETRIEVER` unset now means full
context, with BM25 and hybrid behind the flag. Reasons, in order: it is
the only configuration that answers the corpus-wide questions (29/29 vs
25-26/29); at 48 recipes it costs the same as BM25 with the recipe block
cached (0.0149 vs 0.0148 USD per question); it is the simplest pipeline.
Known costs: generation p95 14.9 s vs 8.4 s, and a cold cache pays 1.25x
on the whole corpus. Both go on the Block 7 measurement list, and the
80-recipe threshold in ADR-002 is the trigger to flip back.

Changed: `build_retriever` default, `.env.example`, SPEC pipeline
diagram, cost target (USD 14.94 per 1,000 from the 29-question full
context run) and assumption 6, ADR-002 decision items 1 and 3. The g27
padding fix for BM25 is still owed; it no longer affects the default path.
