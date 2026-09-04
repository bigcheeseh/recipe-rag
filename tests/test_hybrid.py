"""Hybrid retrieval: BM25 and vector ranks fused with RRF. Fake embedder, no network."""

import numpy as np

from app.embeddings import HybridRetriever, rrf
from app.models import Query
from app.retrieval import chunk_recipes
from tests.conftest import CORPUS

# A toy embedding space: one axis per dish. The query "pasta with bacon and egg" shares
# no words with any recipe, but the fake embedder maps it onto the carbonara axis.
AXES = {"carbonara": 0, "risotto": 1, "banana-bread": 2}
ALIASES = {"pasta with bacon and egg": "carbonara", "creamy rice with mushrooms": "risotto"}


def fake_embed(texts: list[str], input_type: str) -> np.ndarray:
    out = np.zeros((len(texts), 3))
    for i, t in enumerate(texts):
        key = ALIASES.get(t.lower(), next((d for d in AXES if d in t.lower()), None))
        if key:
            out[i, AXES[key]] = 1.0
    return out


def vectors_for(recipes):
    chunks = chunk_recipes(recipes)
    keys = [f"{c.recipe_id}:{c.section}" for c in chunks]
    # Chunk texts start with the title, so the fake embedder finds the dish name.
    return fake_embed([c.text for c in chunks], "document"), keys


def test_rrf_rewards_agreement_and_keeps_singletons():
    fused = rrf([["a", "b", "c"], ["b", "c"]], k=60)
    assert fused["b"] > fused["c"] > fused["a"]  # two mid ranks beat one top rank
    assert fused["b"] == 1 / 62 + 1 / 61


def test_vector_side_finds_a_described_dish_bm25_misses():
    vectors, keys = vectors_for(CORPUS)
    r = HybridRetriever(CORPUS, vectors, keys, fake_embed)
    got = r.retrieve(Query(in_domain=True, search_terms="pasta with bacon and egg"))
    assert got[0][0].id == "carbonara"


def test_both_sides_agree_on_a_named_dish():
    vectors, keys = vectors_for(CORPUS)
    r = HybridRetriever(CORPUS, vectors, keys, fake_embed)
    got = r.retrieve(Query(in_domain=True, search_terms="risotto rice"))
    assert got[0][0].id == "risotto"


def test_filters_apply_to_both_sides():
    vectors, keys = vectors_for(CORPUS)
    r = HybridRetriever(CORPUS, vectors, keys, fake_embed)
    # No recipe in the fixture has metadata, so any constraint empties the candidate set.
    assert r.retrieve(Query(in_domain=True, search_terms="carbonara", max_minutes=10)) == []


def test_vectors_must_match_corpus_chunks():
    vectors, keys = vectors_for(CORPUS)
    try:
        HybridRetriever(CORPUS[:2], vectors, keys, fake_embed)
    except ValueError as e:
        assert "chunk" in str(e)
    else:
        raise AssertionError("stale embeddings were accepted")
