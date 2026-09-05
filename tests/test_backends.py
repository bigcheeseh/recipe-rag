"""Backends: the named models and retrievers a request can pick from. No network."""

import pytest

from app.backends import Backends
from app.retrieval import BM25Retriever, FullContextRetriever
from tests.conftest import CORPUS, FakeLLM


def make() -> tuple[Backends, FakeLLM, FakeLLM]:
    sonnet, haiku = FakeLLM(), FakeLLM(model="claude-haiku-4-5")
    b = Backends(
        models=[sonnet, haiku],
        retrievers={"full": FullContextRetriever(CORPUS), "bm25": BM25Retriever(CORPUS)},
        default_model="claude-sonnet-5",
        default_retriever="full",
    )
    return b, sonnet, haiku


def test_pick_returns_defaults_when_nothing_is_named():
    b, sonnet, _ = make()
    llm, name, retriever = b.pick(None, None)
    assert llm is sonnet and name == "full" and isinstance(retriever, FullContextRetriever)


def test_pick_returns_the_named_pair():
    b, _, haiku = make()
    llm, name, retriever = b.pick("claude-haiku-4-5", "bm25")
    assert llm is haiku and name == "bm25" and isinstance(retriever, BM25Retriever)


@pytest.mark.parametrize("model, retriever", [("gpt-9", None), (None, "magic")])
def test_unknown_name_raises_with_the_offending_value(model, retriever):
    b, _, _ = make()
    with pytest.raises(KeyError, match=model or retriever):
        b.pick(model, retriever)


def test_defaults_must_exist():
    with pytest.raises(KeyError):
        Backends([FakeLLM()], {"bm25": BM25Retriever(CORPUS)}, "claude-sonnet-5", "full")


def test_describe_is_stable_and_carries_notes():
    b, _, _ = make()
    d = b.describe()
    assert [m["id"] for m in d["models"]] == ["claude-sonnet-5", "claude-haiku-4-5"]
    assert [r["id"] for r in d["retrievers"]] == ["full", "bm25"]
    assert d["defaults"] == {"model": "claude-sonnet-5", "retriever": "full"}
    assert "cache" in d["retrievers"][0]["note"].lower()
