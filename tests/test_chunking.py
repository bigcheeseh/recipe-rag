from app.models import Recipe
from app.retrieval import Chunk, chunk_recipes, to_search_text

RISOTTO = Recipe(
    id="risotto-ai-funghi",
    title="Risotto ai Funghi",
    url="u",
    revid=1,
    ingredients=["300 g arborio rice", "200 g mushrooms"],
    steps=["Toast the rice in butter.", "Add stock a ladle at a time and stir."],
)


def test_search_text_starts_with_dish_name_in_every_section():
    for section in ("ingredients", "steps"):
        assert to_search_text(RISOTTO, section).startswith("Risotto ai Funghi")


def test_search_text_carries_only_its_own_section():
    ing = to_search_text(RISOTTO, "ingredients")
    steps = to_search_text(RISOTTO, "steps")
    assert "arborio" in ing and "ladle" not in ing
    assert "ladle" in steps and "arborio" not in steps


def test_chunks_point_back_to_parent_recipe():
    chunks = chunk_recipes([RISOTTO])
    assert [c.section for c in chunks] == ["ingredients", "steps"]
    assert all(isinstance(c, Chunk) and c.recipe_id == "risotto-ai-funghi" for c in chunks)
    assert chunks[0].text == to_search_text(RISOTTO, "ingredients")
