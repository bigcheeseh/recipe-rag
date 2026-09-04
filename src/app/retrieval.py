"""Retrieval: chunk recipes, rank chunks with BM25, collapse hits to parent recipes."""

import re
from dataclasses import dataclass
from typing import Literal

from rank_bm25 import BM25Okapi

from app.models import Recipe

Section = Literal["ingredients", "steps"]


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
        Chunk(r.id, section, to_search_text(r, section))
        for r in recipes
        for section in ("ingredients", "steps")
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


def bm25_rank(index: Index, query: str, candidates: list[Recipe], k: int = 5) -> list[Recipe]:
    """Best chunk score per candidate recipe, descending; zero-score recipes are dropped."""
    allowed = {r.id: r for r in candidates}
    best: dict[str, float] = {}
    for chunk, score in zip(index.chunks, index.chunk_scores(query), strict=True):
        if chunk.recipe_id in allowed and score > 0:
            best[chunk.recipe_id] = max(best.get(chunk.recipe_id, 0.0), score)
    ranked = sorted(best, key=lambda rid: best[rid], reverse=True)
    return [allowed[rid] for rid in ranked[:k]]
