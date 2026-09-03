"""Guards on the committed corpus: the golden set depends on these facts."""

import json
import re
from pathlib import Path

import pytest

from app.models import Recipe

CORPUS = Path(__file__).parents[1] / "data" / "corpus.json"


@pytest.fixture(scope="module")
def corpus() -> dict[str, Recipe]:
    rs = [Recipe.model_validate(r) for r in json.loads(CORPUS.read_text(encoding="utf-8"))]
    return {r.id: r for r in rs}


def test_every_recipe_has_metadata(corpus):
    assert all(r.meta is not None for r in corpus.values())


@pytest.mark.parametrize(
    "recipe_id",
    ["spaghetti-alla-carbonara", "carbonara-pasta", "risotto-ai-funghi", "pad-thai",
     "guacamole-i", "banana-bread-i", "chocolate-chip-cookies-i", "chocolate-chip-cookies-iii"],
)
def test_golden_set_ids_exist(corpus, recipe_id):
    assert recipe_id in corpus


def test_beef_wellington_is_absent(corpus):
    assert not any("wellington" in r.id for r in corpus.values())


def _oven_temps(r: Recipe) -> set[str]:
    return {m for s in r.steps for m in re.findall(r"(\d{3})\s*°?\s*F", s)}


def test_cookie_variants_disagree_on_oven_temperature(corpus):
    assert "375" in _oven_temps(corpus["chocolate-chip-cookies-ii"])
    assert _oven_temps(corpus["chocolate-chip-cookies-iii"]) == {"350"}


def test_carbonara_variants_disagree_on_eggs(corpus):
    a = " ".join(corpus["spaghetti-alla-carbonara"].ingredients)
    b = " ".join(corpus["carbonara-pasta"].ingredients)
    assert "5 egg yolks" in a
    assert "4 free-range eggs" in b


def test_pad_thai_lists_nuts_for_the_allergy_question(corpus):
    assert "nuts" in corpus["pad-thai"].meta.allergens


def test_some_recipe_is_vegan_and_nut_free(corpus):
    metas = [r.meta for r in corpus.values()]
    assert any("vegan" in m.diet_tags and "nuts" not in m.allergens for m in metas)


def test_some_recipe_is_under_30_minutes(corpus):
    assert any(r.meta.total_minutes <= 30 for r in corpus.values())
