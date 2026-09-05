"""The named models and retrievers a request may pick from (SPEC assumption 14).

Built once at startup from the environment; a request names a pair or gets the defaults.
This is the only place that knows the notes shown as tooltips in the UI."""

from typing import Protocol

from app.llm import TokenUsage
from app.models import Draft, Query, Recipe
from app.retrieval import Retriever


class Generator(Protocol):
    """What the pipeline needs from the model layer; LLM satisfies it, tests fake it."""

    model: str
    prompt_hash: str

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]: ...
    def generate(
        self, question: str, recipes: list[Recipe], cache: bool = False
    ) -> tuple[Draft, TokenUsage]: ...


# Selectable per request. Opus 5 is priced in llm.PRICES for the eval judge only.
MODEL_NOTES = {
    "claude-sonnet-5": (
        "Default. Passed 29/29 on the golden set with full context. USD 2 / 10 per M tokens."
    ),
    "claude-haiku-4-5": (
        "About a third of the cost. Guesses on browsing and corpus-wide questions "
        "(26/29). USD 1 / 5 per M tokens."
    ),
}
RETRIEVER_NOTES = {
    "full": (
        "Every recipe that passes the filters goes to the model, prompt-cached. "
        "Best accuracy; longest generation tail."
    ),
    "bm25": (
        "Lexical top-8 over section chunks, no network in retrieval. "
        "Misses questions that need the whole corpus."
    ),
    "hybrid": (
        "BM25 fused with Voyage vectors by reciprocal rank. Found nothing BM25 missed; "
        "slowest on the free tier."
    ),
}


class Backends:
    def __init__(
        self,
        models: list[Generator],
        retrievers: dict[str, Retriever],
        default_model: str,
        default_retriever: str,
    ):
        self.models = {m.model: m for m in models}
        self.retrievers = retrievers
        if default_model not in self.models:
            raise KeyError(f"default model {default_model!r} is not one of {list(self.models)}")
        if default_retriever not in retrievers:
            raise KeyError(
                f"default retriever {default_retriever!r} is not one of {list(retrievers)}"
            )
        self.default_model, self.default_retriever = default_model, default_retriever

    def pick(self, model: str | None, retriever: str | None) -> tuple[Generator, str, Retriever]:
        """Resolve a request's choice to (generator, retriever name, retriever).
        KeyError names the offending value; the API turns it into a 422."""
        model = model or self.default_model
        retriever = retriever or self.default_retriever
        if model not in self.models:
            raise KeyError(f"unknown model {model!r}; choose one of {list(self.models)}")
        if retriever not in self.retrievers:
            raise KeyError(
                f"unknown retriever {retriever!r}; choose one of {list(self.retrievers)}"
            )
        return self.models[model], retriever, self.retrievers[retriever]

    def describe(self) -> dict:
        """Payload of GET /config: ids in insertion order, notes for tooltips, defaults."""
        return {
            "models": [{"id": m, "note": MODEL_NOTES.get(m, "")} for m in self.models],
            "retrievers": [{"id": r, "note": RETRIEVER_NOTES.get(r, "")} for r in self.retrievers],
            "defaults": {"model": self.default_model, "retriever": self.default_retriever},
        }
