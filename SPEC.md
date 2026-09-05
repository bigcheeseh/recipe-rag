# SPEC — Recipe RAG Service

A question-answering service over Wikibooks Cookbook recipes. The user asks a
question in plain English; the service retrieves the relevant recipes and
answers only from them, citing the recipes it used, or refuses with a stated
reason.

This document is the contract. Code that disagrees with it is wrong.

---

## 1. API contract

### `POST /ask`

**Request body** (JSON):

```json
{ "question": "How many eggs does the carbonara use?" }
```

| Field       | Type   | Rules                                                     |
| ----------- | ------ | --------------------------------------------------------- |
| `question`  | string | required; after stripping whitespace must be 1–500 chars |
| `model`     | string | optional; one of the ids listed by `GET /config`; default is the server's `MODEL` |
| `retriever` | string | optional; one of the ids listed by `GET /config`; default is the server's `RETRIEVER` |

An unknown `model` or `retriever` is a `422` before any model call. The
response's `usage.model` and `usage.retriever` always say which pair
answered, so a switched request is auditable from the response and the log.

### `GET /config`

Returns the switchable backends and the defaults, for the UI's selectors:

```json
{
  "models":     [{"id": "claude-sonnet-5", "note": "..."}, ...],
  "retrievers": [{"id": "full", "note": "..."}, ...],
  "defaults":   {"model": "claude-sonnet-5", "retriever": "full"}
}
```

Only backends the server could build are listed: `hybrid` appears only
when `VOYAGE_API_KEY` and the embeddings file are present.

**Response `200`** — always an `Answer` object (schema in section 2), even when
the service refuses. A refusal is a successful, well-formed response, not an
error.

**Error codes**

| Status | When                                                                 | Body                                         |
| ------ | -------------------------------------------------------------------- | -------------------------------------------- |
| `422`  | body fails validation (missing, empty, whitespace-only, too long)    | FastAPI/Pydantic validation detail           |
| `502`  | the model provider returned an error or unparseable structured output after one retry | `{"detail": "upstream model error", "trace_id": "..."}` |
| `504`  | a model call exceeded its timeout                                    | `{"detail": "upstream timeout", "trace_id": "..."}` |
| `500`  | anything else                                                        | `{"detail": "internal error", "trace_id": "..."}` |

A `422` is returned **before any model call**. This is a hard requirement and
is tested.

### `GET /healthz`

Returns `200 {"status": "ok", "recipes": <int>}` once the corpus is loaded and
the retriever is built. Used by the Docker healthcheck and Cloud Run.

---

## 2. Response schema (source of truth)

```python
class Source(BaseModel):
    recipe_id: str
    title: str
    url: str

class Refusal(BaseModel):
    reason: Literal["out_of_domain", "insufficient_context", "safety_deferral"]
    message: str

class Usage(BaseModel):
    model: str
    retriever: str                   # which retriever produced the context
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: dict[str, int]   # keys: extract, retrieve, generate, total

class Citation(BaseModel):
    title: str
    url: str

class Answer(BaseModel):
    answer: str | None
    refusal: Refusal | None
    sources: list[Source]
    conflicts: list[str] = []
    usage: Usage
    # Assignment minimum contract. Computed from the fields above at
    # serialisation time, so the two views can never disagree.
    citations: list[Citation]        # = [(s.title, s.url) for s in sources]
    refused: bool                    # = refusal is not None
    refusal_reason: Literal["out_of_corpus", "out_of_domain", "safety"] | None
```

The assignment's minimum schema (`citations`, `refused`, `refusal_reason`)
is a projection of our richer one. Reason names map one-to-one:
`insufficient_context` → `out_of_corpus`, `safety_deferral` → `safety`,
`out_of_domain` unchanged. The eval harness checks both views on every
response: ours by `Answer.model_validate`, theirs by comparing the three
fields in the body against the values recomputed from `sources` and
`refusal`. A refusal is therefore detectable from `refused: true` alone.

**Invariants** — enforced by a Pydantic model validator and by the first test
in the repository:

1. Exactly one of `answer` / `refusal` is non-`None`.
2. If `answer` is non-`None`, `sources` is non-empty.
3. If `refusal.reason == "out_of_domain"`, `sources` is empty.

Additional rules that hold in practice but are checked by the eval harness
rather than the validator:

- Every `sources[].recipe_id` is one of the ids that were actually retrieved
  for this request (groundedness).
- `conflicts` is non-empty only when two or more sources are cited.

### Refusal reasons

| Reason                 | Meaning                                                                                  | `sources`               |
| ---------------------- | ---------------------------------------------------------------------------------------- | ----------------------- |
| `out_of_domain`        | The question is not about cooking, food, or recipes. Detected by the query-extraction call; retrieval is skipped. | must be empty |
| `insufficient_context` | The question is in-domain but the corpus cannot answer it: filters left zero recipes, retrieval found nothing relevant, or the generated answer cited ids that were not retrieved and one repair attempt also failed. | may list the recipes that were considered, or be empty |
| `safety_deferral`      | The question asks for a medical or safety judgement (allergy safety, food safety for pregnancy, drug interactions). The service reports what the recipe data says and declines the judgement. | must cite the recipes whose ingredients were reported |

---

## 3. Pipeline

```
question
  → extract_query()       LLM #1 → Query {in_domain, search_terms, exclude_allergens, diet, max_minutes}
  → apply_filters()       pure Python over recipe metadata
  → retrieve()            default: every filtered recipe (full context, prompt-cached);
                          RETRIEVER=bm25: top-8 sections expanded to whole recipes (ADR-002)
  → generate()            LLM #2 → structured {answer | refusal, sources, conflicts}
  → validate_grounding()  pure Python: cited ids ⊆ retrieved ids, else one repair, else refuse
  → Answer JSON
```

Anything verifiable without a model is verified without a model. Filters,
ranking, groundedness, and parsing are pure functions with unit tests.

---

## 4. Acceptance criteria

Every criterion is a measurable assertion. "Should work well" is not a
criterion.

### Contract

- AC-1. Every `POST /ask` response with status `200` passes
  `Answer.model_validate`. Any validation failure is a test failure.
- AC-2. `POST /ask` with `{"question": ""}` returns `422` and the model client
  records zero calls.
- AC-3. `POST /ask` with a whitespace-only question returns `422`.
- AC-4. `GET /healthz` returns `200` within the container healthcheck window.

### Refusal

- AC-5. A non-food question (golden `g08`, `g09`) returns
  `refusal.reason == "out_of_domain"` and `sources == []`.
- AC-6. An in-domain question whose answer is not in the corpus (golden `g12`)
  returns `refusal.reason == "insufficient_context"`, never a fabricated answer.
- AC-7. An allergy-safety question (golden `g05`) returns
  `refusal.reason == "safety_deferral"`, the message names the allergen, the
  message mentions trace amounts or cross-contamination, and `sources` cites
  the recipe asked about. A request *for* dishes without an allergen (`g06`)
  is a filtered recommendation, not a deferral: it is covered by AC-11.

### Grounding

- AC-8. For every answered question in the golden set, every cited
  `recipe_id` is in the set of ids retrieved for that request. Checked by
  the eval harness from the structured log.
- AC-9. The groundedness validator rejects a model response citing an id that
  was not retrieved. Unit-tested with a mocked model, zero network.

### Factual and constraint questions

- AC-10. Each plain factual question in the golden set (`g01`–`g04`) cites the
  expected recipe and the answer contains the expected substring.
- AC-11. Each constraint question (`g05`–`g07`) respects its constraint: an
  allergen-exclusion question never cites a recipe whose metadata lists that
  allergen; a time-bound question never cites a recipe whose
  `total_minutes` exceeds the bound.

### Conflicts

- AC-12. Each conflict question (`g10`, `g13`) cites at least two sources and
  returns at least one entry in `conflicts`.

### Eval harness

- AC-13. `evals/run_evals.py` runs the full golden set, checks every `expect`
  field deterministically, writes a markdown table to `evals/runs/`, and
  exits non-zero if any question fails that passed in the previous committed
  run. A rubric judge (`prompts/judge.md`, a different model from the one
  under test) scores clarity, care and language 1-3 per response; the score
  is reported in the table and never gates. Its agreement with human scores
  is measured by `--calibrate` and recorded in DEVLOG before the score is
  used for a decision.
- AC-14. The baseline pass rate on the golden set is recorded in `DEVLOG.md`
  and in the committed run table. Target: TBD until the first run.

### Operations

- AC-15. Every request emits one structured log record containing
  `trace_id`, the raw question, the extracted `Query`, retrieved ids with
  scores, prompt hash, model name, token counts, per-stage latency, and the
  grounding validation result. A single record must be enough to tell a
  retrieval failure (wrong recipes) from a generation failure (right recipes,
  wrong answer).
- AC-16. The API key is read from Secret Manager on Cloud Run and from an
  environment variable locally. It never appears in the image, the Terraform
  state committed to git, or any log line.
- AC-17. Cloud Run `min_instances = 0`.

---

## 5. Edge cases

| Case                                        | Input                                              | Expected behaviour                                                                                                                                       |
| ------------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Empty question                              | `{"question": ""}` or whitespace only              | `422` from request validation. No model call, no retrieval, no log record beyond the access log.                                                         |
| Out-of-domain question                      | "How do I fix a flat tyre?"                        | `200`, `refusal.reason = "out_of_domain"`, `sources = []`, `answer = null`. LLM #2 and retrieval are skipped; `latency_ms.retrieve` and `.generate` are `0`. |
| Recipes disagree about the same dish        | "How many eggs go into carbonara?" with two carbonara variants in the corpus, one using 5 egg yolks and one using 4 whole eggs | `200`, `answer` reports both values attributed to their recipes, `sources` has ≥ 2 entries, `conflicts` has ≥ 1 entry describing the disagreement. |
| Allergy question                            | "Is the pad thai safe for a peanut allergy?"       | `200`, `refusal.reason = "safety_deferral"`. The `message` states what the recipe's ingredient list contains regarding the allergen, states that the service cannot judge medical safety, and warns about trace amounts and cross-contamination. `sources` cites the pad thai recipe. |

---

## 6. Latency budget

Measured at p50 and p95 from the deployed service, warm instance, one
concurrent request. All values `TBD` until measured in Block 7.

| Stage      | Budget (p95) | Measured p50 | Measured p95 |
| ---------- | ------------ | ------------ | ------------ |
| `extract`  | TBD          | TBD          | TBD          |
| `retrieve` | TBD          | TBD          | TBD          |
| `generate` | TBD          | TBD          | TBD          |
| `total`    | TBD          | TBD          | TBD          |
| cold start | TBD          | TBD          | TBD          |

Expectation to be confirmed by measurement: `retrieve` is pure Python over
~50 recipes and should be well under 50 ms; the two model calls dominate.

Pre-deployment reference, measured on the developer machine by the BM25
eval run (`evals/runs/20260904T175824Z-bm25-claude-sonnet-5.md`, 23
questions, one at a time, not the deployed service): extract p50 2142 /
p95 2651 ms, retrieve 0 / 0 ms, generate 2824 / 6737 ms, total 5086 /
8346 ms. The deployed columns above stay TBD until Block 7.

---

## 7. Cost model

**Model:** `claude-sonnet-5` for both calls.
List price at time of writing: $2.00 per 1M input tokens, $10.00 per 1M
output tokens (Anthropic first-party API, no caching).

**Per-question cost:**

```
cost_usd = (tokens_in_extract + tokens_in_generate) * 2.00 / 1e6
         + (tokens_out_extract + tokens_out_generate) * 10.00 / 1e6
```

Token counts are taken from the provider's `usage` object on each response
and summed into `Usage.tokens_in` / `Usage.tokens_out`. `Usage.cost_usd` is
computed from those counts and the prices above. It is never estimated.

The metadata-enrichment call at ingestion is a one-time cost and is recorded
separately in `ingest_manifest.json`, not in per-question `Usage`.

**Target for 1,000 questions:** USD 14.94, from the mean `cost_usd` of the
full-context + Sonnet 5 eval run on the 29-question golden set
(`evals/runs/20260904T201858Z-full-claude-sonnet-5.md`, mean USD 0.0149) multiplied by 1,000, with the
recipe block prompt-cached and the cache warm. BM25 + Sonnet 5 on the same
set measured USD 14.75. ADR-002 lists the other configurations and the
corpus size at which BM25 becomes cheaper.

Prompt caching applies to the recipe block in full-context mode only. Cache
writes are priced at 1.25x and reads at 0.1x the input price; both counts
come from the provider's `usage` object and feed `cost_usd`. A request
that arrives after the 5-minute cache has expired pays the write.

---

## 8. Assumptions

Decisions made without asking. Each is reversible; each is recorded so it can
be challenged.

1. **Provider and model.** Anthropic `claude-sonnet-5` for both the query
   extraction and generation calls, via the official `anthropic` Python SDK.
   Chosen because an API key is available. Enrichment at ingestion uses the
   same model.
2. **Determinism.** CLAUDE.md specifies `temperature=0`. Sonnet 5 rejects the
   `temperature` parameter with a `400`, so it is not sent. Determinism is
   approximated instead by structured output with a strict JSON schema and
   by a stable prompt; the eval harness measures the actual variance.
3. **Structured output.** Both model calls use the provider's structured
   output feature (`output_config.format` with a JSON schema derived from the
   Pydantic model) rather than parsing free text. A response that fails
   schema validation is retried once, then surfaces as `502`.
4. **Thinking.** Adaptive thinking is left at the provider default. If
   measured latency exceeds budget, effort is lowered before the model is
   changed.
5. **Question length.** Capped at 500 characters. Longer questions are
   rejected with `422` rather than truncated.
6. **Retrieval.** Default is full context: every recipe that passes the
   filters is sent to the generator, prompt-cached (ADR-002, 2026-09-05).
   With `RETRIEVER=bm25`, up to eight parent recipes (best section score
   each) are passed; a recipe whose full title appears in the search terms
   is placed first regardless of score. Was five; raised after the
   two-dish question g14 showed two dishes competing for five slots
   (ADR-002 item 5). Fewer than eight is common: zero-score recipes are
   never included.
7. **Filter semantics.** `exclude_allergens` excludes any recipe whose
   metadata lists that allergen. `diet` requires every requested tag to be
   present. `max_minutes` compares against `total_minutes` inclusively.
   A recipe with no metadata value for a filtered field is excluded, on the
   grounds that "unknown" is not "safe".
8. **Corpus.** Roughly 50 recipes from the Wikibooks Cookbook `Category:Recipes`,
   fetched once and committed. The service never fetches at request time.
   Each recipe stores the MediaWiki `revid` so the source version is pinned.
9. **Allergen enum.** `nuts, dairy, eggs, gluten, shellfish, soy`. Peanuts are
   classified under `nuts` even though botanically they are legumes, because
   users asking about allergies treat them the same way. Sesame and fish are
   not tracked; questions about them fall through to the generator's
   ingredient reading and the safety deferral.
10. **Refusal is not an HTTP error.** Refusals return `200` so that clients
    can always parse the same schema. Only malformed requests and upstream
    failures produce error statuses.
11. **Safety deferral scope.** Any question asking whether food is *safe* for
    a medical condition is deferred. Questions asking whether a recipe
    *contains* an ingredient are answered normally from the ingredient list.
12. **Languages.** The corpus is English. Questions may be in any language:
    the extraction call always produces English search terms, and the
    generator answers in the language of the question. Only English and
    Russian are covered by the golden set (`g22`, `g23`); other languages
    are untested.
13. **No authentication** on the endpoint. The deployment is a demo; abuse
    is bounded by the platform's concurrency limits and scale to zero.
14. **Per-request backend switch.** `model` and `retriever` in the request
    body override the server defaults for that request only (user request,
    2026-09-05), so the UI can compare configurations live. Every model in
    the price table is selectable, including Opus 5 at 2.5x Sonnet's price;
    with assumption 13 that means any caller can pick the most expensive
    pair. Acceptable for a demo, and the first thing to restrict behind a
    key if the endpoint outlives it. Prompt caching applies only when the
    retriever marks its context as stable (full context), whatever the model.
