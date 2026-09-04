from app.models import Meta, Query, Recipe
from app.retrieval import apply_filters


def recipe(id_: str, meta: Meta | None) -> Recipe:
    return Recipe(id=id_, title=id_, url="u", revid=1, ingredients=["x"], steps=["y"], meta=meta)


PAD_THAI = recipe(
    "pad-thai", Meta(allergens=["nuts", "eggs"], diet_tags=[], cuisine="Thai", total_minutes=20)
)
DAL = recipe(
    "dal",
    Meta(allergens=[], diet_tags=["vegan", "vegetarian"], cuisine="Indian", total_minutes=780),
)
OMELET = recipe(
    "omelet",
    Meta(allergens=["eggs", "dairy"], diet_tags=["vegetarian"], cuisine="French", total_minutes=10),
)
UNKNOWN = recipe("unknown", None)
ALL = [PAD_THAI, DAL, OMELET, UNKNOWN]


def ids(query: Query, recipes=ALL) -> list[str]:
    return [r.id for r in apply_filters(recipes, query)]


def q(**kw) -> Query:
    return Query(in_domain=True, search_terms="", **kw)


def test_no_constraints_keeps_everything_including_unknown_meta():
    assert ids(q()) == ["pad-thai", "dal", "omelet", "unknown"]


def test_allergen_exclusion_drops_any_match():
    assert ids(q(exclude_allergens=["nuts"])) == ["dal", "omelet"]
    assert ids(q(exclude_allergens=["eggs"])) == ["dal"]


def test_diet_requires_every_tag():
    assert ids(q(diet=["vegetarian"])) == ["dal", "omelet"]
    assert ids(q(diet=["vegan"])) == ["dal"]


def test_max_minutes_is_inclusive():
    assert ids(q(max_minutes=20)) == ["pad-thai", "omelet"]
    assert ids(q(max_minutes=10)) == ["omelet"]


def test_unknown_meta_is_dropped_whenever_a_constraint_is_active():
    # A recipe we cannot vouch for must never be offered as "nut-free" or "under 30 min".
    assert "unknown" not in ids(q(exclude_allergens=["soy"]))
    assert "unknown" not in ids(q(diet=["pescatarian"]))
    assert "unknown" not in ids(q(max_minutes=1000))


def test_bm25_retriever_filters_then_ranks():
    from app.retrieval import BM25Retriever, Retriever

    r: Retriever = BM25Retriever(ALL)
    got = r.retrieve(Query(in_domain=True, search_terms="dal omelet", exclude_allergens=["eggs"]))
    assert [x.id for x in got] == ["dal"]
