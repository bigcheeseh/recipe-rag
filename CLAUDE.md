# CLAUDE.md — Recipe RAG Service

Working instructions for the coding agent. Read in full before the first commit.

---

## 0. Context and working rules

We are building a RAG service over Wikibooks Cookbook recipes as a take-home
assignment. What is graded is **not the amount of code** but: spec before code,
ADRs with real numbers, an eval harness, commit discipline, unit economics,
and a working deployment.

### Hard rules

1. **Do not run ahead.** We work in blocks. After each block: STOP, show the
   diff, wait for confirmation. Never start the next block on your own.
2. **Never squash.** Granular history is a graded artifact. One commit = one
   meaningful change.
3. **Test before implementation** in the five pairs marked `TDD` below.
   Elsewhere, normal order is fine.
4. **No silent stubs.** If something is missing or ambiguous, ask. Hidden
   hardcoded behaviour is the worst possible outcome.
5. **Minimalism.** Do not add dependencies, abstractions, layers, or
   "for later" code. Target is ~300 lines of logic. If you are writing more,
   stop and ask.
6. **Never invent numbers.** Latency and cost figures must be measured.
   Until measured, write `TBD`.
7. Record every unprompted architectural decision in `DEVLOG.md`.

### Stack (do not change without asking)

Python 3.12 · FastAPI · Pydantic v2 · `rank_bm25` · `httpx` · `beautifulsoup4` ·
pytest · ruff · Docker · Cloud Run + Terraform.

**Deliberately absent:** vector database, SQLite, LangChain, embeddings at the
start. Embeddings are introduced only if the eval shows BM25 is insufficient.

---

## 1. Target architecture

```
question
  → extract_query()       LLM #1, temperature=0 → structured constraints
  → apply_filters()       pure Python, metadata
  → bm25_rank()           top-5 within the filtered set
  → generate()            LLM #2, structured output
  → validate_grounding()  pure Python
  → JSON
```

Core idea: **anything verifiable without an LLM is verified without an LLM.**
Filters, ranking, groundedness, parsing — pure functions with real tests.

### Layout

```
├── SPEC.md
├── ADR/{001,002,003}.md
├── README.md
├── CLAUDE.md
├── DEVLOG.md
├── data/{corpus.json,ingest_manifest.json}
├── prompts/{extract_query.md,generate.md,enrich.md}
├── src/app/
│   ├── models.py       # Pydantic: Request, Answer, Refusal, Source, Query, Meta
│   ├── ingest.py       # run manually, never at request time
│   ├── retrieval.py    # filters + bm25
│   ├── generate.py     # prompt, client, validation
│   └── api.py
├── evals/{golden_set.yaml,run_evals.py,runs/}
├── tests/
├── Dockerfile, compose.yaml
└── infra/main.tf
```

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
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: dict[str, int]   # extract, retrieve, generate, total

class Answer(BaseModel):
    answer: str | None
    refusal: Refusal | None
    sources: list[Source]
    conflicts: list[str] = []
    usage: Usage
```

**Invariants (validator + the very first test):**
- exactly one of `answer` / `refusal` is non-`None`
- if `answer` is non-`None`, `sources` must be non-empty
- if `refusal.reason == "out_of_domain"`, `sources` must be empty

---

## BLOCK 1 — Spec. No code.

### Commit 1 — `docs: add SPEC.md with API contract and acceptance criteria`

`SPEC.md` must contain:
- `POST /ask` contract — request, response, error codes
- The full response schema from section 2 above
- Acceptance criteria: measurable assertions, not aspirations
- The four edge cases with expected behaviour:
  - empty question → `422`, before any model call
  - out-of-domain question → `refusal: out_of_domain`, `sources: []`
  - recipes disagreeing about the same dish → non-empty `conflicts`,
    ≥2 sources
  - allergy question → answer from ingredient data + `safety_deferral`
    on the medical judgement, with a caveat about trace amounts
- Latency budget per stage (`TBD` for now, filled in from measurements)
- Cost model: per-question formula, target figure for 1,000 questions
- An **Assumptions** section — everything we decided ourselves rather than asked

### Commit 2 — `docs: add golden set of 13 evaluation questions`

`evals/golden_set.yaml`. No runner yet. Format:

```yaml
- id: g01
  q: "How many eggs does the carbonara use?"
  expect: {cites: [carbonara], contains: "3"}

- id: g05
  q: "Is the pad thai safe for a peanut allergy?"
  expect: {refusal: safety_deferral, mentions: "peanut", cites: [pad-thai]}

- id: g08
  q: "How do I fix a flat tyre?"
  expect: {refusal: out_of_domain, sources_empty: true}

- id: g11
  q: ""
  expect: {http_status: 422}

- id: g13
  q: "How long should the bolognese simmer?"
  expect: {cites_min: 2, conflicts_min: 1}
```

**Requirement for every question:** it must be checkable deterministically —
a substring, a field, a source id. Never "the answer should be good."
Coverage: plain factual ×4, constraint (diet / time / allergen) ×3,
refusal ×2, conflict ×2, empty ×1, answerable-but-not-in-corpus ×1.

### Commit 3 — `chore: project scaffold`

`pyproject.toml`, ruff, pytest, `.gitignore`, `.env.example`, empty `DEVLOG.md`.

**STOP. Show SPEC.md and the golden set.**

---

## BLOCK 2 — Contract

### Commit 4 — `test: response schema invariants` `TDD` — must fail
The three invariants from section 2, plus empty question → 422.

### Commit 5 — `feat: request and response models`
`models.py`. Tests green. No logic beyond validators.

### Commit 6 — `feat: POST /ask stub returning static response`

### Commit 7 — `test: API contract against stub`
`TestClient`, response shape. Zero model calls.

**STOP.**

---

## BLOCK 3 — Corpus

### Commit 8 — `test: recipe HTML parser with fixtures` `TDD`
Three saved HTML files in `tests/fixtures/`: a normal one, one missing the
Procedure section, one with unusual ingredient markup.

### Commit 9 — `feat: parse Wikibooks recipe HTML into structured records`
BeautifulSoup, split on `<h2>`: `Ingredients` → `<li>`, `Procedure` → `<li>`/`<p>`.
Missing either section → reject with a reason, not an exception.

### Commit 10 — `feat: fetch recipe pages via MediaWiki API`
```
api.php?action=query&list=categorymembers&cmtitle=Category:Recipes&cmlimit=100
api.php?action=parse&page=<title>&prop=text|revid&format=json
```
Cache HTML to disk. Rate limit ≥100ms. Keep `revid` — it pins the source version.

### Commit 11 — `feat: LLM metadata enrichment for allergens and diet tags`
One call per recipe, `temperature=0`, structured output:

```python
class Meta(BaseModel):
    allergens: list[Literal["nuts","dairy","eggs","gluten","shellfish","soy"]]
    diet_tags: list[Literal["vegan","vegetarian","pescatarian"]]
    cuisine: str
    total_minutes: int
```

**Enums are mandatory.** Free text here breaks the filters.
Prompt lives in `prompts/enrich.md`, not in code.

### Commit 12 — `data: add corpus of ~50 recipes with manifest`
Run ingestion, **review the output by hand**, correct obvious metadata errors
manually. Commit `corpus.json` + `ingest_manifest.json`
(accepted / rejected / reasons / date / revids).
Put the numbers in the commit message: how many accepted, how many rejected, why.

### Commit 13 — `data: add conflicting recipe variants`
Ensure the corpus contains 2+ variants of the same dish with genuinely
diverging parameters (time, ingredients). Otherwise the conflict case has
nothing to find.

**STOP. Show the manifest and three corpus records.**

---

## BLOCK 4 — Retrieval

### Commit 14 — `test: chunking and search text rendering` `TDD`
`to_search_text(recipe, section)` — pure function. Assert the dish name is
duplicated into every section's text.

### Commit 15 — `feat: parent-child chunking`
Index by section (ingredients / steps separately), but pass the whole recipe
to the model. Rationale → ADR-001.

### Commit 16 — `test: BM25 ranks expected recipe first` `TDD`
Fixture corpus of 5 recipes, no network.

### Commit 17 — `feat: BM25 retrieval`
`rank_bm25`, index built at startup from `corpus.json`.

### Commit 18 — `test: allergen, diet and time filters` `TDD`

### Commit 19 — `feat: metadata filters applied before ranking`
```python
def apply_filters(recipes, q):
    return [r for r in recipes
            if not (set(q.exclude_allergens) & set(r.meta.allergens))
            and all(d in r.meta.diet_tags for d in q.diet)
            and (q.max_minutes is None or r.meta.total_minutes <= q.max_minutes)]
```
Empty after filtering → signal for `insufficient_context`.

**STOP.**

---

## BLOCK 5 — Generation

### Commit 20 — `feat: query extraction with structured output`
LLM #1, `temperature=0`, prompt in `prompts/extract_query.md`:

```python
class Query(BaseModel):
    in_domain: bool
    search_terms: str
    exclude_allergens: list[str] = []
    diet: list[str] = []
    max_minutes: int | None = None
```
`in_domain=false` → refuse immediately, skip retrieval entirely.

### Commit 21 — `feat: answer generation with structured output`
LLM #2. Prompt in `prompts/generate.md`. Context = top-5 full recipes with `id`.
Instructions: cite only the supplied ids; when recipes for the same dish
disagree, populate `conflicts` rather than silently picking one.

### Commit 22 — `test: groundedness validator rejects uncited ids` `TDD`
Mocked model responses. No real calls.

### Commit 23 — `feat: groundedness validation with single repair attempt`
```python
if not {s.recipe_id for s in ans.sources} <= retrieved_ids:
    ans = retry_once() or refuse("insufficient_context")
```

### Commit 24 — `feat: wire pipeline into /ask`

### Commit 25 — `feat: structured logging with trace_id and per-stage timings`
Log: `trace_id`, raw question, extracted constraints, retrieved ids + scores,
prompt hash, model, tokens, per-stage latency, validation result.
Goal: a single record must distinguish a **retrieval failure** (wrong docs)
from a **generation failure** (right docs, bad answer).

**STOP.**

---

## BLOCK 6 — Evals. This is where numbers appear.

### Commit 26 — `feat: eval runner validating responses against contract`
`evals/run_evals.py`:
- runs the whole golden set
- validates every response via `Answer.model_validate` — failure = fail
- checks the expect fields: `cites`, `contains`, `refusal`, `mentions`,
  `sources_empty`, `cites_min`, `conflicts_min`, `http_status`
- writes a markdown table to `evals/runs/<timestamp>.md`
- exits non-zero on regression

**No LLM-as-judge.** Every check is deterministic.

### Commit 27 — `eval: baseline run — BM25 only`
Run it, commit the table, put the headline numbers in `DEVLOG.md`.

### Commit 28 — `feat: optional vector retrieval with RRF fusion`
Only now. `text-embedding-3-small`, `embeddings.npy`, RRF `k=60`.
Behind a flag, off by default.

### Commit 29 — `eval: hybrid vs BM25 comparison`
If hybrid gives no improvement, **keep the code behind the flag, do not delete
it.** A negative result with a number is the best material for ADR-002.

### Commit 30 — `feat: full-context baseline behind flag`
Whole corpus in the prompt, no retrieval.

### Commit 31 — `eval: retrieval vs full-context — accuracy, latency, cost`
Table of all three approaches. This is the core of ADR-002.

**STOP. Show the comparison table.**

---

## BLOCK 7 — Deployment

### Commit 32 — `build: multistage Dockerfile and compose`
`python:3.12-slim`, non-root, healthcheck. Keep the image small — Artifact
Registry has its own free tier.

### Commit 33 — `infra: Cloud Run service and Secret Manager via Terraform`
`min_instances = 0` — mandatory, otherwise you are billed 24/7.
API key via Secret Manager, never a plaintext env var.

### Commit 34 — `ci: lint, test, build, deploy on main`

### Commit 35 — `docs: record measured cold start and p95 latency`
Real figures from the deployed service. Fill in the `TBD`s in SPEC.md.

---

## BLOCK 8 — Written deliverables

### Commits 36–38 — ADRs
- `ADR-001` parent-child chunking
- `ADR-002` retrieval method (with the table from commit 31)
- `ADR-003` refusal policy and allergy deferral

**Every ADR must contain:**
alternatives considered · criteria · trade-offs with real numbers ·
**the condition under which the decision becomes invalid**.

That last item is what gets checked first. Example:
> This decision is invalid if the corpus grows beyond ~5k chunks, if concurrent
> writes become a requirement, or if the share of queries with no lexical
> overlap exceeds X% (measured: Y%).

### Commit 39 — `docs: README`
Sections: local run (Docker), deployment target and why that provider,
Cost & Latency (per-question and per-1,000 cost, model choice, conditions
triggering a move to a cheaper or more capable model), current bottleneck and
what gets optimised next, and one paragraph on diagnosing a bad answer in
production.

### Commit 40 — `docs: DEVLOG notes on accepted vs rewritten agent output`
Be honest: what was accepted as-is, what was rewritten and why.
Failed attempts with numbers are worth more than a tidy narrative.

---

## Final check

- [ ] `git log --oneline` shows SPEC and the golden set first
- [ ] five `TDD` pairs: the test commit physically precedes the code commit
- [ ] every ADR has a number and an invalidation condition
- [ ] `run_evals.py` passes against the deployed URL
- [ ] the latest eval run is committed
- [ ] no unmeasured number appears anywhere in the README
- [ ] `prompts/` holds all three prompts as separate files