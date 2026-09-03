from pathlib import Path

import pytest

from app.ingest import Rejected, parse_recipe
from app.models import Recipe

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def carbonara() -> Recipe:
    r = parse_recipe(
        load("carbonara.html"),
        title="Cookbook:Spaghetti alla Carbonara",
        url="https://en.wikibooks.org/wiki/Cookbook:Spaghetti_alla_Carbonara",
        revid=4640105,
    )
    assert isinstance(r, Recipe), r
    return r


def test_normal_page_identity(carbonara):
    assert carbonara.id == "spaghetti-alla-carbonara"
    assert carbonara.title == "Spaghetti alla Carbonara"
    assert carbonara.revid == 4640105
    assert carbonara.url.endswith("Spaghetti_alla_Carbonara")


def test_normal_page_ingredients(carbonara):
    assert len(carbonara.ingredients) == 8
    assert carbonara.ingredients[0].startswith("450 g")
    assert "egg yolks" in carbonara.ingredients[2]
    assert carbonara.ingredients[-1] == "Salt"


def test_normal_page_steps(carbonara):
    assert len(carbonara.steps) >= 5
    assert carbonara.steps[0].startswith("Dice the guanciale")


def test_normal_page_infobox(carbonara):
    assert carbonara.infobox["Time"] == "1 hour"
    assert carbonara.infobox["Servings"] == "6"


def test_no_edit_links_leak(carbonara):
    for line in carbonara.ingredients + carbonara.steps:
        assert "edit source" not in line
        assert "[" not in line


def test_missing_procedure_is_rejected():
    r = parse_recipe(load("no_procedure.html"), title="Cookbook:Plain Toast", url="u", revid=1)
    assert isinstance(r, Rejected)
    assert "Procedure" in r.reason


def test_missing_ingredients_is_rejected():
    html = load("no_procedure.html").replace('id="Ingredients">Ingredients', 'id="Stuff">Stuff')
    r = parse_recipe(html, title="Cookbook:Plain Toast", url="u", revid=1)
    assert isinstance(r, Rejected)
    assert "Ingredients" in r.reason


def test_nested_ingredients_are_flattened_across_subsections():
    r = parse_recipe(
        load("nested_ingredients.html"),
        title="Cookbook:Pancakes with Berry Sauce",
        url="u",
        revid=2,
    )
    assert isinstance(r, Recipe), r
    assert r.ingredients == [
        "200 g flour",
        "2 eggs",
        "300 ml milk",
        "or 300 ml oat milk for a dairy-free version",
        "150 g mixed berries",
        "1 tablespoon sugar",
    ]


def test_paragraph_procedure_is_split_into_steps():
    r = parse_recipe(load("nested_ingredients.html"), title="Cookbook:Pancakes", url="u", revid=2)
    assert isinstance(r, Recipe)
    assert len(r.steps) == 3
    assert r.steps[0].startswith("Whisk")
    assert r.steps[2].endswith("pancakes.")
    assert not any("Leftover" in s for s in r.steps)  # Notes section is not procedure
