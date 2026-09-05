"""Retrieval: chunk recipes, rank chunks with BM25, collapse hits to parent recipes."""

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from rank_bm25 import BM25Okapi

from app.models import Query, Recipe

Section = Literal["ingredients", "steps"]
SECTIONS: tuple[Section, ...] = ("ingredients", "steps")


@dataclass(frozen=True)
class Chunk:
    recipe_id: str
    section: Section
    text: str


def to_search_text(recipe: Recipe, section: Section) -> str:
    """One searchable string per section. The dish name is prepended so a query that
    names the dish still hits a step that never repeats it ("stir the rice")."""
    lines = recipe.ingredients if section == "ingredients" else recipe.steps
    return "\n".join([recipe.title, *lines])


def chunk_recipes(recipes: list[Recipe]) -> list[Chunk]:
    return [
        Chunk(r.id, section, to_search_text(r, section)) for r in recipes for section in SECTIONS
    ]


_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens with a crude plural strip so "egg" matches "eggs"."""
    out = []
    for w in _WORD.findall(text.lower()):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


class Index:
    """BM25 over section chunks, built once at startup."""

    def __init__(self, recipes: list[Recipe]):
        self.chunks = chunk_recipes(recipes)
        self._bm25 = BM25Okapi([tokenize(c.text) for c in self.chunks])

    def chunk_scores(self, query: str) -> list[float]:
        return list(self._bm25.get_scores(tokenize(query)))


def bm25_rank(
    index: Index, query: str, candidates: list[Recipe], k: int = 5
) -> list[tuple[Recipe, float]]:
    """Best chunk score per candidate recipe, descending; zero-score recipes are dropped."""
    allowed = {r.id: r for r in candidates}
    best: dict[str, float] = {}
    for chunk, score in zip(index.chunks, index.chunk_scores(query), strict=True):
        if chunk.recipe_id in allowed and score > 0:
            best[chunk.recipe_id] = max(best.get(chunk.recipe_id, 0.0), score)
    ranked = sorted(best, key=lambda rid: best[rid], reverse=True)
    return [(allowed[rid], best[rid]) for rid in ranked[:k]]


def apply_filters(recipes: list[Recipe], query: Query) -> list[Recipe]:
    """Hard constraints, applied before ranking so an excluded recipe can never be cited.
    A recipe without metadata is kept only when nothing is being asked of it."""
    out = []
    for r in recipes:
        m = r.meta
        if m is None:
            if not query.constrained:
                out.append(r)
            continue
        if set(query.exclude_allergens) & set(m.allergens):
            continue
        if not set(query.diet) <= set(m.diet_tags):
            continue
        if query.max_minutes is not None and m.total_minutes > query.max_minutes:
            continue
        out.append(r)
    return out


class Retriever(Protocol):
    """The only thing the pipeline depends on. Swap the implementation, not the pipeline."""

    def retrieve(self, query: Query) -> list[tuple[Recipe, float]]: ...


class FullContextRetriever:
    """No ranking: every recipe that passes the filters goes to the generator."""

    def __init__(self, recipes: list[Recipe]):
        self.recipes = recipes

    def retrieve(self, query: Query) -> list[tuple[Recipe, float]]:
        return [(r, 0.0) for r in apply_filters(self.recipes, query)]


TOP_K = 8  # SPEC assumption 6; raised from 5 after g14 (ADR-002 item 5)


def promote_titles(
    terms: str, hits: list[tuple[Recipe, float]], candidates: list[Recipe], k: int
) -> list[tuple[Recipe, float]]:
    """A recipe whose full title appears in the search terms goes first, whatever BM25
    says: "pad thai" must not lose to a fried rice that mentions pad thai three times."""
    named = [r for r in candidates if r.title.lower() in terms.lower()]
    if not named:
        return hits
    scores = {r.id: s for r, s in hits}
    top = max(scores.values(), default=0.0)
    front = [(r, scores.get(r.id, top)) for r in named]
    rest = [(r, s) for r, s in hits if r.id not in {n.id for n in named}]
    return (front + rest)[:k]


def pad_constrained(
    hits: list[tuple[Recipe, float]], candidates: list[Recipe], query: Query, k: int
) -> list[tuple[Recipe, float]]:
    """Constrained question ("vegan under 15 minutes", "what can I cook in 30 minutes?"):
    the filtered set itself is the answer set, so fill the ranked list up to k with the
    filtered recipes the terms did not match. Score 0 marks a padded entry. Unconstrained
    questions have no defined answer set beyond the matches, so they are left alone."""
    if not query.constrained or len(hits) >= k:
        return hits
    seen = {r.id for r, _ in hits}
    rest = [(r, 0.0) for r in candidates if r.id not in seen]
    return hits + rest[: k - len(hits)]


class BM25Retriever:
    def __init__(self, recipes: list[Recipe], k: int = TOP_K):
        self.recipes, self.k = recipes, k
        self.index = Index(recipes)

    def retrieve(self, query: Query) -> list[tuple[Recipe, float]]:
        candidates = apply_filters(self.recipes, query)
        hits = bm25_rank(self.index, query.search_terms, candidates, self.k)
        hits = promote_titles(query.search_terms, hits, candidates, self.k)
        return pad_constrained(hits, candidates, query, self.k)
