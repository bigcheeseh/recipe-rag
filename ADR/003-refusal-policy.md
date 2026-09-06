# ADR-003: Refusal policy and allergy deferral

**Status:** accepted, 2026-09-05 (behaviour in place since Block 5, 2026-09-04)

## Context

The assignment requires three things of a refusal: it happens whenever the
corpus cannot answer, it is polite, and it is detectable by a machine
without reading prose. It also asks us to decide what "careful" means for
allergy and safety questions and to record that decision.

Two model calls sit in the pipeline (SPEC section 3). Either could refuse,
and a pure-Python validator sits after the second. The policy has to say
who refuses when, and how the reader tells the cases apart.

## Alternatives

**Where the refusal decision lives**

1. One model call that answers or refuses in free text, detected by a
   phrase match. Rejected: the assignment forbids it explicitly, and a
   phrase match is the hidden hardcoded behaviour the brief warns against.
2. A classifier step before retrieval for everything (domain, answerable,
   safety). Rejected: "answerable" cannot be known before retrieval, so the
   classifier would guess.
3. **Chosen: split by who has the evidence.** The extraction call decides
   domain, because it needs no recipes. The generation call decides
   insufficient context and safety, because only it sees the recipes. The
   grounding validator overrides the generator when an answer cites ids
   that were never retrieved.

**What "careful" means for allergies**

1. Answer yes/no from the ingredient list. Rejected: a recipe cannot see
   cross-contamination, brand variation, or trace amounts, so "yes, it is
   nut-free" is a medical claim the data does not support.
2. Refuse outright with no information. Rejected: the reader learns nothing
   they could act on, and the judge rubric scores it 1 on care.
3. **Chosen: report, then defer.** The message names the allergen, states
   exactly what the ingredient list says about it, says the service cannot
   judge medical safety, and warns about trace amounts and
   cross-contamination. It cites the recipe it reported on. A question that
   asks whether a dish *contains* an ingredient is answered normally; only a
   *safety* judgement is deferred.

## Decision

- Three reasons, fixed in the schema: `out_of_domain` (extractor, before
  retrieval, sources empty), `insufficient_context` (empty filter result,
  nothing retrieved, generator says the recipes lack the fact, or grounding
  failed after one repair), `safety_deferral` (generator, cites the
  reported recipe). The generator's output type cannot express
  `out_of_domain`; that removed a class of wrong refusals seen on the
  hybrid and full-context runs (DEVLOG, "Things that broke").
- The assignment's minimum contract is derived from these: `refused` is
  `refusal is not None`, `refusal_reason` maps `insufficient_context` to
  `out_of_corpus` and `safety_deferral` to `safety` (SPEC section 2).
- A refusal is a `200`. Client errors are `422`, upstream failures `502`
  or `504`. A refusal is a correct answer to a question the corpus cannot
  answer, not an error.
- Grounding is enforced in code, not asked of the model: cited ids must be
  a subset of retrieved ids, one regeneration is allowed, then the service
  refuses with `insufficient_context`. The log record carries the outcome
  (`ok`, `repaired`, `refused`).
- Constraint filtering uses "unknown is not safe": a recipe with no
  metadata is excluded whenever an allergen, diet, or time constraint is
  active (SPEC assumption 7).

## Trade-offs, measured

- On the 29-question golden set the policy passes every refusal check on
  Sonnet 5 with full context (ADR-002 table): out-of-domain, not in
  corpus, the allergy deferral, and the two Russian questions.
- The judge rubric scores "care" 2.96 of 3 on Sonnet; the two Haiku rows
  at 2.71 were guesses on corpus-wide questions, not refusal failures.
- The cost of deferring is that a user asking "is this nut-free" gets the
  ingredient facts plus a caveat instead of a yes. That is the intended
  outcome for a service that has only recipe text.

## Conditions that invalidate this decision

- The corpus gains structured allergen data with provenance (manufacturer
  declarations, lab-tested "free-from" labels). Then a bounded yes/no on
  that data becomes defensible and `safety_deferral` narrows to medical
  conditions.
- A measured false-refusal rate on real traffic above a few percent for
  in-domain questions the corpus does answer. Then the extractor's
  domain rule or the generator's rule 1 is too strict and needs its own
  eval slice.
- A product decision to serve dietary advice with a clinician in the loop.
  The deferral then becomes a hand-off, not a stop.
