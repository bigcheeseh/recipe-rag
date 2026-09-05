"""Shared fakes: a tiny corpus and a scripted model layer. No test touches the network."""

import pytest

from app.backends import Backends
from app.llm import TokenUsage
from app.models import Draft, GeneratorRefusal, Query, Recipe
from app.retrieval import BM25Retriever, FullContextRetriever, Retriever


def recipe(id_: str, title: str, ingredients: list[str], steps: list[str]) -> Recipe:
    return Recipe(
        id=id_,
        title=title,
        url=f"https://example.org/{id_}",
        revid=1,
        ingredients=ingredients,
        steps=steps,
    )


CORPUS = [
    recipe(
        "carbonara",
        "Spaghetti alla Carbonara",
        ["400 g spaghetti", "5 egg yolks"],
        ["Boil the pasta.", "Whisk the yolks with cheese."],
    ),
    recipe(
        "risotto",
        "Risotto ai Funghi",
        ["300 g arborio rice", "mushrooms"],
        ["Toast the rice.", "Add stock a ladle at a time and stir."],
    ),
    recipe(
        "banana-bread",
        "Banana Bread",
        ["3 bananas", "2 eggs", "flour"],
        ["Mash the bananas.", "Bake at 350°F for one hour."],
    ),
]

USAGE = TokenUsage(tokens_in=100, tokens_out=10)


class FakeLLM:
    """Scripted model. `queries` maps question -> Query; `drafts` is consumed in order."""

    prompt_hash = "fake"

    def __init__(
        self,
        queries: dict[str, Query] | None = None,
        drafts: list[Draft] | None = None,
        model: str = "claude-sonnet-5",
    ):
        self.model = model
        self.queries = queries or {}
        self.drafts = list(drafts or [])
        self.calls: list[str] = []
        self.generate_inputs: list[list[str]] = []
        self.cache_flags: list[bool] = []

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]:
        self.calls.append("extract")
        q = self.queries.get(question, Query(in_domain=True, search_terms=question))
        return q, USAGE

    def generate(
        self, question: str, recipes: list[Recipe], cache: bool = False
    ) -> tuple[Draft, TokenUsage]:
        self.calls.append("generate")
        self.generate_inputs.append([r.id for r in recipes])
        self.cache_flags.append(cache)
        return self.drafts.pop(0), USAGE


def backends(*llms: FakeLLM, retriever: Retriever | None = None) -> Backends:
    """One or more scripted models plus the two zero-network retrievers; bm25 is default."""
    return Backends(
        models=list(llms),
        retrievers={"bm25": retriever or BM25Retriever(CORPUS), "full": FullContextRetriever(CORPUS)},
        default_model=llms[0].model,
        default_retriever="bm25",
    )


def answer(text: str, ids: list[str], conflicts: list[str] | None = None) -> Draft:
    return Draft(answer=text, refusal=None, source_ids=ids, conflicts=conflicts or [])


def refusal(reason: str, ids: list[str] | None = None) -> Draft:
    r = GeneratorRefusal(reason=reason, message=f"{reason} message")  # type: ignore[arg-type]
    return Draft(answer=None, refusal=r, source_ids=ids or [])


@pytest.fixture
def corpus() -> list[Recipe]:
    return CORPUS
