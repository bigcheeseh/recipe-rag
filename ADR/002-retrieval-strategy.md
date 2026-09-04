# ADR-002: Retrieval strategy — BM25 by default, hybrid and full-context behind flags

**Status:** accepted, 2026-09-04

## Context

Three ways to get recipes in front of the generator were built behind one
`Retriever` seam and measured on the same 13-question golden set with the
same prompts (`evals/runs/`, 2026-09-04). Every check is deterministic.

| Configuration | Pass | Mean USD / question | USD / 1,000 | total p50 ms | total p95 ms | generate p50 ms |
| --- | --- | --- | --- | --- | --- | --- |
| BM25, Sonnet 5 (default) | 13/13 | 0.0111 | 11.07 | 5192 | 6299 | 2944 |
| Hybrid BM25 + Voyage vectors, Sonnet 5 | 13/13 | 0.0112 | 11.18 | 25296 | 26276 | 3178 |
| Full context (48 recipes, cached), Sonnet 5 | 13/13 | 0.0122 | 12.24 | 5870 | 7276 | 4372 |
| Full context (cached), Haiku 4.5 | 13/13 | 0.0063 | 6.25 | 4428 | 7551 | 2887 |
| BM25, Haiku 4.5 | 13/13 | 0.0040 | 4.00 | 3675 | 4501 | 2535 |

Latency is from the developer machine, one request at a time; deployed
numbers come in Block 7. The hybrid total is dominated by Voyage's free-tier
rate limit (20 s back-off on 429), not by the vector math (about 300 ms when
not limited).

Accuracy did not separate the options: 13/13 everywhere. The differences
are cost, latency, dependencies, and how each one scales.

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
   and it is the simplest possible pipeline, but it costs more per question
   at this size and adds about 1.4 s to generation.
4. **Sonnet 5 stays the default model.** Haiku 4.5 passed the same 13
   questions at a third of the cost. Thirteen questions are too few to rank
   models on nuance (conflict wording, safety-deferral phrasing), so the
   cheaper model is offered as a one-line `MODEL` switch rather than made
   the default. Revisit when the golden set is larger.

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
- **Latency.** Generation was 4372 ms p50 against 2944 ms for BM25 at 48
  recipes, and prefill time grows with context length.
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
