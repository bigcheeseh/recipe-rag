# DEVLOG

Working notes: what I decided on my own, what the numbers said, and what the agent got sent back. Newest at the bottom.

## Setup

Python 3.11, not 3.12. That's what was on the machine and nothing in the project needs 3.12, so I didn't install another interpreter. Anthropic models throughout, for the plain reason that I already had an Anthropic API key and no OpenAI one; that also decided Voyage instead of `text-embedding-3-small` for the vector experiment, since Anthropic has no embedding model. CLAUDE.md is committed as it was given; the departures from it are all in here.

Corpus: 61 curated Wikibooks titles, 48 accepted, 13 rejected (index and disambiguation pages). Enrichment cost about USD 0.16. Reading the output by hand found 3 wrong records out of 48: one false gluten, one fish tagged as shellfish, one total time that ignored an overnight soak. Fixed by hand, logged in the manifest. The corpus already had conflicts without me adding any: two carbonaras (5 yolks vs 4 whole eggs, 60 vs 30 minutes), five cookie recipes split between 375°F and 350°F, three banana breads, three guacamoles, three risottos. My original conflict question about bolognese simmer time turned out to be no conflict at all (both say one hour), so it became a carbonara question instead. A test pins these corpus facts so a refresh that breaks the golden set fails CI.

## BM25 first

Started with BM25 over section chunks (ingredients and steps indexed separately, whole recipe sent to the model). Before wiring any LLM I fed the golden questions in raw and learned two things. Raw questions are noisy: "How many eggs go into carbonara?" ranked a cookie recipe first because "go", "into" and "eggs" score everywhere, while "carbonara eggs" ranks both carbonaras 1–2. So the extractor has to return bare content terms. And BM25 has no idea of "nothing relevant": "flat tyre" still returns five low-score recipes. Refusals therefore come from the extractor (`in_domain`) and the generator (`insufficient_context`), never from a score cutoff, because BM25 scores aren't comparable across queries.

First baseline run: 12/13. "What can I cook in under 30 minutes?" produced `max_minutes=30` and search terms "quick recipes", the filter left 23 recipes, and BM25 matched none of them because no recipe says "quick". Fix, test first: when constraints are active and ranking finds nothing, the filtered set is the answer set. Second run 13/13, USD 0.0111 per question.

Hybrid (BM25 + Voyage vectors, RRF) was next: also 13/13, and on every probe the top recipe was identical to BM25's; vectors only reordered positions 2–5. The reason is upstream: the extractor already rewrites "pasta with bacon and egg" into "carbonara", so there's no vocabulary gap left for embeddings to close on 48 recipes. Meanwhile hybrid adds a second provider, a network call per request, and on Voyage's free tier a 3-per-minute cap that made retrieval 20 s p50. Kept behind a flag, off.

## The pivot: BM25 → full context

The question that nagged from day one was whether retrieval was needed at all. The whole corpus is about 27k tokens. With prompt caching (writes at 1.25x, reads at 0.1x) putting all of it in the system prompt costs about the same as sending five recipes uncached. So I built a retriever seam and measured instead of guessing.

The options on the table:

- **BM25 top-k, Sonnet 5.** Cheapest dependency-wise, fast, but it only sees what the query terms hit.
- **Hybrid BM25 + vectors.** Same top hits as BM25 here, plus a provider and a rate limit. No reason to pay for it at this corpus size.
- **Full context, Sonnet 5.** Every recipe in the prompt, cached. Simplest pipeline, no retrieval failures possible, but the model reads 27k tokens per answer.
- **Full context, Haiku 4.5.** About a third of the cost. Tempting.

On the first 13 questions every configuration passed and the decision was a coin toss, so I grew the golden set. At 23 questions BM25 started flapping on a two-dish comparison (the wrong banana bread in the top-5); k=8 plus an exact-title promotion fixed that, at +25% cost per question. Still nothing separated the options on accuracy.

Then I added six corpus-wide questions: quickest recipe, longest stated time, how many cookie recipes, vegan under 15 minutes, anything soaked overnight, quickest in Russian. That's where it split. On 29 questions:

- Sonnet + full context: 29/29
- Sonnet + BM25 or hybrid: 25–26/29, failing exactly the questions that need the whole corpus
- Haiku + full context: 26/29, and its extractor classed "longest stated total time" as out of domain

Cost at 48 recipes was a wash (USD 0.0149 full vs 0.0148 BM25 per question). Latency was not: generation p95 14.9 s vs 8.4 s, because the model actually walks all the recipes for the corpus-wide questions. I switched the default to full context on Sonnet anyway. Reasons in order: it's the only configuration that answers everything, it costs the same, and it's the simplest pipeline. BM25 and hybrid stay behind `RETRIEVER=`. The flip-back trigger is in ADR-002: around 80 recipes the cached full context gets dearer than top-8, and the p95 grows with the corpus.

Haiku as default I rejected on quality, not on the score. On the browsing question it listed recipes with no stated time and invented durations for them, presented as facts. Sonnet named the two recipes with times and said the rest are unknown. A recipe service that makes up numbers fails at its one job, whatever it saves. Haiku stays as a one-line switch.

Full context is the right call here only because the corpus is small: 48 recipes fit in about 30k tokens, and a cached read of that costs less than the retrieval it replaces. It does not generalise. With a real corpus (thousands of recipes, or anything that no longer fits a cache block) I would go back to retrieval, but not the plain top-k I started with. What I'd build: an LLM or a dedicated parser turns the question into a structured search plan first, and that plan is split into meaningful small sub-queries, one per thing the user is actually asking about. "How do I cook carbonara, and what about rice with mushrooms?" is two queries, carbonara and mushroom risotto, each fetched from a vector index on its own, each filtered by metadata, then re-ranked together before generation. The two-dish comparison question already showed why on this corpus: one BM25 query for both dishes let the wrong banana bread crowd out the right one, and top-8 only papered over it. Splitting the query fixes that at any corpus size; widening k does not.

## How the evals work

One golden set, 29 questions in `evals/golden_set.yaml`, each with an `expect` block that a script can check without any model: which recipe ids must be cited (`cites`, `cites_min`), a substring the answer must contain, the exact refusal reason, that sources are empty for out-of-domain, that a conflict list is non-empty, a 422 for the empty question, a Cyrillic script check for the Russian questions, and three metadata checks that look up the cited recipes in the corpus (never cites a recipe with the excluded allergen, every cited recipe carries the required diet tag, every cited recipe is under the time limit). Coverage: plain facts, diet and allergen and time constraints, two refusals, two conflicts, the empty question, a dish that isn't in the corpus, a prompt injection, and six corpus-wide questions. Every response is also validated against the Pydantic contract before any check runs, so a malformed body is a fail, not a crash.

The runner sends the whole set through the app (in-process, or over the network with `--url`), writes a table per run to `evals/runs/`, and exits non-zero if any question that passed in the last committed run now fails. That's the regression gate; the committed run files are the history. `--only` reruns a few ids and prints without writing, so a partial run can't become the baseline.

Retrieval is measured on the same set, not separately, because a retrieval failure shows up as a wrong or missing citation on a question where the right recipe exists. The log line for each request carries the retrieved ids with scores next to the cited ids, so for any failing row I can tell whether the right recipe never reached the model (retrieval) or reached it and was ignored (generation). The one purely retrieval-level probe I ran was the hybrid vs BM25 comparison: the top-ranked recipe for the extracted terms of every in-domain question plus three "described, not named" dishes, which came out identical for all 13.

Final 3x2 matrix on 29 questions (dev machine, Opus judge, full table in ADR-002), pass rate and mean USD per question:

| | Sonnet 5 | Haiku 4.5 |
| --- | --- | --- |
| BM25 top-8 | 25/29, 0.0148 | 25/29, 0.0047 |
| Hybrid | 26/29, 0.0169 | 25/29, 0.0052 |
| Full context, cached | 29/29, 0.0149 | 26/29, 0.0046 |

So Haiku is about a third of Sonnet's price on every retriever (USD 4.62 vs 14.94 per 1,000 on full context) and fails the same corpus-wide questions plus the ones where it guesses. Deployed, Sonnet full context came down to USD 0.0126 per question because the cache stayed warm across the run.

## The judge

The deterministic checks prove facts, citations and refusals, but they can't see wording, and wording was the one thing still separating Sonnet from Haiku. So I lifted my own "no LLM-as-judge" rule with three conditions: the score is reported, never gating; the judge is never the model under test (Opus 5 grades everything); and it's meant to be calibrated against human scores before it decides anything. The calibration hasn't been done, so the rubric means are the judge's opinion, not a measurement.

It earned its keep once. The judge caught Sonnet answering an English question in Spanish because a recipe title was Spanish; the string checks only looked for Cyrillic. Rule 7 in the generate prompt got tightened. It also caught Haiku inventing a gram conversion inside an otherwise correct allergy deferral.

## Things that broke and got fixed with a number

- A long answer overran `max_tokens=1024`, the SDK raised, the app returned 500, the runner died. Now 4096, truncation retried once, a 500 is a failed row.
- Hybrid and full context both refused "Beef Wellington" as `out_of_domain`. The generator had picked that reason from the shared enum even though only the extractor should ever say it. The generator's output type now has two refusal reasons, so it can't.
- A constrained question whose terms matched only one of three filtered candidates returned one recipe. Now the filtered set pads the hit list up to k. BM25 went 25 → 26/29.
- First deployed run: 28/29. "Every vegan recipe under 15 minutes" got three recipes from the filter and the model said only "Pancakes (Vegan)" was vegan, judging by the title, because the rendered recipe text never included the metadata the filter had used. Passed locally by luck. The context now leads each recipe with diet, allergens, estimated time and cuisine.
- That fix flipped another question: "longest stated time" now answered hummus (our 870-minute estimate counting an overnight soak) instead of the bolognese whose own Time line says 2 hours. The metadata line became "Estimated total time" and rule 8 says a recipe's own "Time:" line is its stated time. Final deployed run 29/29.

## Deployment

The real assignment text arrived after Block 6 and accepted `fly.toml` as IaC, so Terraform for Cloud Run was my own over-engineering and I dropped it for Fly.io (ADR-004). The launch flow failed to allocate an IPv6, so release 1 had no public address; `fly ips allocate-v4 --shared` and `allocate-v6` fixed it. It also created two machines; scaled to one. Measured on the deployed service: USD 0.0126 per question (12.61 per 1,000), first question on a cold machine USD 0.0717 for the cache write, total p50 5.5 s / p95 14.5 s, cold start 6.5 s on one sample. The SPEC latency budgets were empty until then; I set each to the measured p95 rounded up so a future run has something to fail against.

Deploys: CI is the test gate only, and Fly's GitHub integration is meant to deploy on push. The first three releases were `fly deploy` by hand; the first push-triggered release gets noted here once it shows up in `fly releases`.

## Model and retriever switch

Added a `Backends` registry so the UI and the API can pick model and retriever per request, with the measured trade-offs as tooltips. Caching became a per-call flag driven by the retriever, since one process now serves both full and top-k contexts. The agent offered Opus in the list too; I hadn't asked for it and it's the judge only, so it went. Also considered copying a multi-agent workflow from another project and decided against it: nothing to parallelise in six modules, and it fights the block-and-stop review this project is graded on. Two single-agent slash commands instead.

## Accepted vs rewritten

Accepted as the agent wrote it, after reading the diff: the Pydantic models and their validators, the HTML parser, the filters, BM25 over section chunks, the groundedness check, the structured request log, the eval runner, the Dockerfile, and the UI. All of it small enough to read in one sitting, and the tests were written first where CLAUDE.md said so.

Sent back or replaced: the Cloud Run + Terraform infra (my own plan, dropped for `fly.toml` once the real brief arrived); Opus in the model selector (removed, judge only); Haiku as the default (rejected on invented durations, not on the score); a proposed multi-agent workflow (declined, nothing to parallelise); the bolognese conflict question (no conflict existed, became carbonara); three enrichment records (fixed by hand); the generator's refusal enum (it could say `out_of_domain`, now it can't); the 1024 token cap; and the "no LLM-as-judge" rule itself, which I lifted with the conditions above. Every number in the docs I either watched being measured or re-ran myself.

Still owed: judge calibration against human scores.
