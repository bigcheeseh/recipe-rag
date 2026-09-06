# ADR-002: Retrieval strategy — full context by default, BM25 and hybrid behind flags

**Status:** accepted, 2026-09-04; default switched to full context 2026-09-05 (user decision)

## Context

Three ways to get recipes in front of the generator were built behind one
`Retriever` seam and measured on the same 23-question golden set (13
original, 8 harder English, 2 Russian) with the same prompts
(`evals/runs/`, 2026-09-04). Every check is deterministic.

All rows: 29-question golden set (13 original, 8 harder, 2 Russian, 6
corpus-wide), top-k 8 with exact-title promotion, generator refusals
limited to insufficient_context / safety_deferral, rubric judge Opus 5
(clarity / care / language, mean of 1-3, reported only). Runs of
2026-09-04, `evals/runs/2026090420*`.

| Configuration | Pass | Judge c / c / l | Mean USD / question | USD / 1,000 | total p50 ms | total p95 ms | generate p95 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BM25, Sonnet 5 | 25/29 | 2.96 / 2.96 / 3.00 | 0.0148 | 14.75 | 5254 | 10735 | 8441 |
| Hybrid BM25 + Voyage, Sonnet 5 | 26/29 | 2.96 / 3.00 / 3.00 | 0.0169 | 16.86 | 8652 | 67378 | 8317 |
| Full context (cached), Sonnet 5 (default) | **29/29** | 3.00 / 2.96 / 3.00 | 0.0149 | 14.94 | 6284 | 16913 | 14855 |
| BM25, Haiku 4.5 | 25/29 | 2.82 / 2.71 / 2.93 | 0.0047 | 4.66 | 4092 | 7957 | 6377 |
| Hybrid, Haiku 4.5 | 25/29 | 2.89 / 2.82 / 3.00 | 0.0052 | 5.23 | 5009 | 66917 | 5412 |
| Full context (cached), Haiku 4.5 | 26/29 | 2.86 / 2.71 / 3.00 | 0.0046 | 4.62 | 4253 | 6942 | 5953 |

Latency is from the developer machine, one request at a time; deployed
numbers come in Block 7. Hybrid p95 totals are Voyage's free-tier rate
limit, not the vector math. Earlier versions of this table (13 and 23
questions) are in git history.

What the failures are:

- **Corpus-wide questions (g24 quickest recipe, g25 longest stated time,
  g29 quickest in Russian) fail on every retrieval configuration**, on
  both models. A top-8 retriever cannot see recipes it did not retrieve;
  BM25 returned pancakes and cookies for "quickest recipe". Only
  Sonnet + full context answers all three. Haiku + full context misses
  two of them: it picked bruschetta (10 min) over grilled cheese (5 min)
  with every recipe in front of it, and its extractor classed "longest
  stated total time" as out_of_domain on all three Haiku rows.
- **g27 (every vegan recipe at 15 minutes or under) fails on BM25 and
  hybrid** with one citation instead of three. The filter leaves three
  candidates, but the search terms match only one of them and the
  browsing fallback fired only when ranking returned nothing. Fixed
  2026-09-05: when constraints are active the ranked list is padded with
  the remaining filtered candidates up to k. BM25 + Sonnet re-measured at
  26/29 (`evals/runs/20260905T134834Z-bm25-claude-sonnet-5.md`), USD
  0.0157 per question (padding sends more recipes); the three
  corpus-wide questions still fail, as expected.
- Haiku's judge scores dropped to 2.71 on care on two rows: the
  corpus-wide questions drew guesses and empty refusals (1/1 scores).

## Decision

1. **Full context on Sonnet 5 is the default** (`RETRIEVER` unset or
   `full`; user decision, 2026-09-05, superseding the 2026-09-04 choice of
   BM25). It is the only configuration that answers the corpus-wide
   questions (quickest recipe, longest stated time, in either language),
   and those are questions a real user asks. At 48 recipes its cost
   equals BM25's (USD 0.0149 vs 0.0148 per question) because the recipe
   block is prompt-cached, and it is the simplest pipeline: no index, no
   ranking, no top-k to tune. What it pays is tail latency (generation
   p95 14.9 s vs 8.4 s) and a dependence on a warm cache; both are
   recorded in the threshold section below and re-measured on Cloud Run
   in Block 7. BM25 stays as the documented fallback once the corpus
   grows past the threshold.
2. **Hybrid stays behind `RETRIEVER=hybrid`.** It found nothing BM25 missed.
   Retrieval-level comparison on the extracted terms of every in-domain
   question plus three "described, not named" probes gave the same top
   recipe in all 13 cases (DEVLOG, "BM25 first"). The reason is the query
   extraction step, which already rewrites a described dish into its name.
   Code and `data/embeddings.npz` are kept for the day the corpus grows past
   what dish names can key.
3. **BM25 stays behind `RETRIEVER=bm25`.** Zero network calls in
   retrieval, deterministic and unit-testable, and the cheaper choice
   above about 80 recipes. It is what the service switches to when the
   corpus grows. With the g27 padding fix it passes 26/29.
4. **Sonnet 5 stays the default model** (user decision, 2026-09-04).
   Haiku 4.5 passed 23/23 at about a third of the cost, but on the
   browsing question g07 it listed recipes with no stated time by guessing
   durations and presenting them as facts (judge care 1). Sonnet on the
   same question named the two recipes with stated times and said the rest
   are unknown. A recipe service that invents numbers fails its one job,
   so the cost saving does not buy the default. Haiku stays a one-line
   `MODEL` switch for anyone who accepts that trade.
5. **Top-k raised to 8 and exact-title promotion added** (user decision,
   2026-09-04) after g14 flapped on BM25 + Sonnet: two dishes competing
   for five slots let the wrong banana bread variant through. k=8 was
   measured offline to include Banana Bread I in 3 of 3 extractions at
   roughly +1.5k input tokens per question. Title promotion guarantees
   that a recipe named in full in the search terms is never outranked by
   a neighbour that merely mentions it more often (Pad Thai vs Khao Pad
   Thai Fried Rice). Both apply to the hybrid retriever too. The table
   above predates this change; the row that changed is re-measured in
   `evals/runs/` and DEVLOG.

## Where full context stops being viable

Measured: the 48-recipe context is 26,186 cached tokens, about 546 tokens
per recipe.

- **Cost.** A cache read is priced at 0.1x input. Cached full-context input
  costs 546 x N x 0.1 x 2.00 / 1e6 USD per question on Sonnet 5, so it
  matches BM25's roughly 4,500 uncached tokens (USD 0.009) at about
  **80 recipes**. Above that, full context is strictly more expensive, and
  that assumes steady traffic keeping the 5-minute cache warm; each cold
  request pays 1.25x on the whole corpus (USD 0.065 at 48 recipes, measured
  on the first eval question).
- **Latency.** On the 23-question run, generation p50 was close to BM25
  (2902 vs 2824 ms) but p95 was 10523 vs 6737 ms; on the earlier
  13-question run p50 was 4372 vs 2944 ms. Prefill time grows with
  context length.
- **Context window.** Haiku 4.5 is 200K tokens, so about **360 recipes**
  is a hard ceiling for the cheap-model variant. Sonnet 5's 1M window
  allows about 1,800, but cost rules it out long before that.
- **Quality.** Not observed to degrade at 48 recipes. Attention over a
  large undifferentiated context is a known risk that would need its own
  eval before relying on full context at hundreds of recipes.

Practical threshold: full context is a reasonable choice below about 80
recipes with warm traffic, and a poor one above that. This corpus sits just
under the line, which is why the choice is a flag rather than a rewrite.
The trigger to flip the flag back to BM25 is the corpus passing 80
recipes or a measured generation p95 over the latency budget on Cloud Run.

## Consequences

- The pipeline never imports a concrete retriever; `build_retriever` reads
  the flag. Switching strategy is configuration.
- With full context the deployed service must keep the cache warm to hit
  the cost above: the cache lives 5 minutes, so a request after a quiet
  period pays the 1.25x write on the whole corpus (USD 0.065 at 48 recipes).
  Block 7 measures how often that happens at the expected traffic.
- The Voyage embedding rate limit dominates hybrid latency (p95 total
  67 s); any future hybrid default needs a paid tier or a local embedder.
- `evals/run_evals.py --retriever {bm25,hybrid,full} --model ...` reproduces
  every row above.
- Voyage is optional: only the hybrid flag and the embedding build script
  need `VOYAGE_API_KEY`.
