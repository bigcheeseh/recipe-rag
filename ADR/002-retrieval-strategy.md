# ADR-002: Retrieval strategy — BM25 by default, hybrid and full-context behind flags

**Status:** accepted, 2026-09-04

## Context

Three ways to get recipes in front of the generator were built behind one
`Retriever` seam and measured on the same 23-question golden set (13
original, 8 harder English, 2 Russian) with the same prompts
(`evals/runs/`, 2026-09-04). Every check is deterministic.

| Configuration | Pass | Mean USD / question | USD / 1,000 | total p50 ms | total p95 ms | generate p50 ms |
| --- | --- | --- | --- | --- | --- | --- |
| BM25, Sonnet 5 (default) | 22/23 | 0.0114 | 11.37 | 5086 | 8346 | 2824 |
| Hybrid BM25 + Voyage vectors, Sonnet 5 | 23/23 | 0.0129 | 12.91 | 6503 | 67906 | 3121 |
| Full context (48 recipes, cached), Sonnet 5 | 23/23 | 0.0148 | 14.83 | 4905 | 12601 | 2902 |
| Full context (cached), Haiku 4.5 | 23/23 | 0.0049 | 4.90 | 4032 | 7576 | 2804 |
| BM25, Haiku 4.5 | 23/23 | 0.0042 | 4.17 | 3361 | 8592 | 2174 |

Latency is from the developer machine, one request at a time; deployed
numbers come in Block 7. The hybrid p95 is Voyage's free-tier rate limit
(20 s back-offs on 429), not the vector math (about 300 ms when not
limited). An earlier 13-question version of this table, 13/13 for every
row, is in git history.

One question separates the rows. g14 ("Which takes longer to make, the
Pad Thai or Banana Bread I?") fails on BM25 + Sonnet: the extractor drops
the variant marker "I", "pad thai" pulls two Thai neighbours into the
five slots, and the banana bread that gets through is the walnut variant,
which states no time. Sonnet then refuses with insufficient_context, which
is the correct behaviour on that context. Hybrid and full context surface
Banana Bread I and answer. BM25 + Haiku passed the same question by
answering from the walnut variant's steps, which is less careful, not
better retrieval. So the golden set now measures a real BM25 limitation:
two-dish questions and exact variant names compete for a fixed top-5.

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
   and it is the simplest possible pipeline, but it costs 30% more per
   question at this size and its generation p95 is the worst of the table.
4. **Sonnet 5 stays the default model.** Haiku 4.5 passed 23/23 at about
   a third of the cost. The one place the two differ (g14) is Haiku
   answering where Sonnet declined for lack of a stated time, so the gap is
   caution, not capability, and 23 questions are still too few to rank
   models on wording quality. Haiku stays a one-line `MODEL` switch.
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
