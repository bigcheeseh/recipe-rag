# ADR-002: Retrieval strategy — BM25 by default, hybrid and full-context behind flags

**Status:** accepted, 2026-09-04

## Context

Three ways to get recipes in front of the generator were built behind one
`Retriever` seam and measured on the same 23-question golden set (13
original, 8 harder English, 2 Russian) with the same prompts
(`evals/runs/`, 2026-09-04). Every check is deterministic.

All rows: top-k 8 with exact-title promotion, generator refusals limited
to insufficient_context / safety_deferral, rubric judge Opus 5 (clarity /
care / language, mean of 1-3, reported only).

| Configuration | Pass | Judge c / c / l | Mean USD / question | USD / 1,000 | total p50 ms | total p95 ms | generate p50 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BM25, Sonnet 5 (default) | 23/23 | 2.95 / 2.95 / 3.00 | 0.0143 | 14.34 | 5267 | 11619 | 3327 |
| Hybrid BM25 + Voyage vectors, Sonnet 5 | 23/23 | 2.95 / 3.00 / 3.00 | 0.0153 | 15.35 | 5546 | 69295 | 2824 |
| Full context (48 recipes, cached), Sonnet 5 | 23/23 | 3.00 / 2.95 / 3.00 | 0.0148 | 14.83 | 5197 | 13235 | 3090 |
| BM25, Haiku 4.5 | 23/23 | 2.95 / 2.91 / 3.00 | 0.0050 | 4.96 | 3409 | 7200 | 2052 |

Latency is from the developer machine, one request at a time; deployed
numbers come in Block 7. The hybrid p95 is Voyage's free-tier rate limit
(20 s back-offs on 429), not the vector math (about 300 ms when not
limited). Earlier versions of this table (13 questions; then 23 questions
at top-k 5, where BM25 + Sonnet was 22/23 on the two-dish question g14)
are in git history. Full context + Haiku was measured only at top-k 5
(23/23, USD 0.0049) and not re-run.

Accuracy no longer separates the rows. The judge differences are one
response each, within noise for 22 graded responses. What separates them
is cost, latency, dependencies, and scaling.

## Decision

1. **BM25 over section chunks stays the default.** Zero network calls in
   retrieval, one provider, deterministic and unit-testable, cheapest input
   tokens per question (about 4-5k), and the fastest total latency.
2. **Hybrid stays behind `RETRIEVER=hybrid`.** It found nothing BM25 missed.
   Retrieval-level comparison on the extracted terms of every in-domain
   question plus three "described, not named" probes gave the same top
   recipe in all 13 cases (DEVLOG 2026-09-04). The reason is the query
   extraction step, which already rewrites a described dish into its name.
   Code and `data/embeddings.npz` are kept for the day the corpus grows past
   what dish names can key.
3. **Full context stays behind `RETRIEVER=full`.** It works at 48 recipes
   and it is the simplest possible pipeline. At top-k 8 its cost is within
   4% of BM25 and its judge scores match; what still argues against it is
   the 80-recipe cost threshold below, a generation p95 that grows with
   the corpus, and dependence on a warm cache.
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

## Consequences

- The pipeline never imports a concrete retriever; `build_retriever` reads
  the flag. Switching strategy is configuration.
- `evals/run_evals.py --retriever {bm25,hybrid,full} --model ...` reproduces
  every row above.
- Voyage is optional: only the hybrid flag and the embedding build script
  need `VOYAGE_API_KEY`.
