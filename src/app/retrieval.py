"""Retrieval: chunk recipes, rank chunks with BM25, collapse hits to parent recipes."""

from dataclasses import dataclass
from typing import Literal

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
