from app.models import Recipe
from app.retrieval import Index, bm25_rank, tokenize


def recipe(id_: str, title: str, ingredients: list[str], steps: list[str]) -> Recipe:
    return Recipe(id=id_, title=title, url="u", revid=1, ingredients=ingredients, steps=steps)


RECIPES = [
    recipe("carbonara", "Spaghetti alla Carbonara", ["400 g spaghetti", "5 egg yolks"],
           ["Boil the pasta.", "Whisk the yolks with cheese."]),
    recipe("risotto", "Risotto ai Funghi", ["300 g arborio rice", "mushrooms"],
           ["Toast the rice.", "Add stock a ladle at a time and stir."]),
    recipe("banana-bread", "Banana Bread", ["3 bananas", "2 eggs", "flour"],
           ["Mash the bananas.", "Bake at 350°F for one hour."]),
    recipe("guacamole", "Guacamole", ["2 avocados", "1 lime"], ["Mash everything together."]),
    recipe("pad-thai", "Pad Thai", ["rice noodles", "peanuts", "2 eggs"],
           ["Soak the noodles.", "Stir-fry and top with peanuts."]),
]
INDEX = Index(RECIPES)


def ids(query: str, candidates=RECIPES, k: int = 5) -> list[str]:
    return [r.id for r, _ in bm25_rank(INDEX, query, candidates, k=k)]


def test_tokenize_lowercases_and_singularises():
    assert tokenize("Egg Yolks, 350°F") == ["egg", "yolk", "350", "f"]


def test_dish_name_wins():
    assert ids("carbonara eggs")[0] == "carbonara"


def test_dish_name_reaches_steps_chunk():
    # "stir" only appears in risotto's steps; "risotto" only in its title.
    assert ids("risotto stir")[0] == "risotto"


def test_singular_query_matches_plural_ingredient():
    assert "banana-bread" in ids("banana egg")[:2]


def test_no_match_returns_nothing():
    assert ids("zzz qqq") == []


def test_only_candidates_are_ranked():
    no_eggs = [r for r in RECIPES if r.id in {"risotto", "guacamole"}]
    assert "carbonara" not in ids("carbonara eggs", candidates=no_eggs)


def test_k_caps_results():
    assert len(ids("eggs", k=2)) == 2
