# ADR-001: Parent-child chunking

**Status:** accepted, 2026-09-04

## Context

Each recipe is one page with two sections that matter for questions: the
ingredient list and the procedure. Questions tend to target one of them
("how many eggs", "what oven temperature"). Whole-recipe documents are
short (median well under 1,000 tokens), so chunking is not about fitting a
context window.

## Decision

Retrieval unit is a **section chunk** (ingredients or steps) that points
back to its parent recipe. BM25 scores chunks; results are collapsed to
parents by best chunk score, and the **whole parent recipe** is passed to
the generator.

Every chunk begins with the dish name, so "risotto" still matches a steps
chunk whose text only says "stir the rice".

## Consequences

- A short ingredient list is not drowned out by a long procedure when the
  question is about ingredients; BM25 length normalisation works per section.
- The generator always sees the complete recipe, so an answer about a
  step can still cite the ingredient it depends on.
- Two chunks per recipe: 96 chunks for 48 recipes. Trivial index size.
- Alternative rejected: one document per recipe. Simpler, but the two
  sections have very different lengths and vocabulary, which skews BM25.
- Alternative deferred: no retrieval at all, full corpus in context. To be
  measured in Commit 31 against this baseline (see DEVLOG, "The pivot").

## Addendum, 2026-09-04: retrieval seam

The pipeline depends only on `Retriever.retrieve(query) -> list[Recipe]`.
`BM25Retriever` is the current implementation (filters, then BM25). An
embedding retriever or a full-context "return everything that passes the
filters" retriever implements the same method, so the Commit 31 comparison
is a flag choosing the class, not a change to the pipeline.
