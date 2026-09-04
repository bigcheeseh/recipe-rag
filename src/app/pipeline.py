"""Pure-Python glue between the two model calls: grounding check with one repair,
and the request pipeline that strings extract -> filter+rank -> generate -> validate."""

import time
from collections.abc import Callable
from typing import Protocol

from app.llm import TokenUsage, cost_usd
from app.models import Answer, Draft, Query, Recipe, Refusal, Source, Usage
from app.retrieval import Retriever


def validate_grounding(draft: Draft, retrieved_ids: set[str]) -> bool:
    """Every cited id must have been retrieved, and an answer must cite something."""
    cited = set(draft.source_ids)
    if not cited <= retrieved_ids:
        return False
    return draft.answer is None or bool(cited)


def ground(draft: Draft, retrieved_ids: set[str], retry: Callable[[], Draft]) -> Draft:
    """Accept a grounded draft; otherwise regenerate once; otherwise refuse."""
    if validate_grounding(draft, retrieved_ids):
        return draft
    draft = retry()
    if validate_grounding(draft, retrieved_ids):
        return draft
    return Draft(
        answer=None,
        refusal=Refusal(
            reason="insufficient_context",
            message="The retrieved recipes do not support a grounded answer to this question.",
        ),
        source_ids=[],
    )


class Generator(Protocol):
    """What the pipeline needs from the model layer; LLM satisfies it, tests fake it."""

    model: str

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]: ...
    def generate(self, question: str, recipes: list[Recipe]) -> tuple[Draft, TokenUsage]: ...


class Pipeline:
    def __init__(self, llm: Generator, retriever: Retriever, recipes: list[Recipe]):
        self.llm, self.retriever = llm, retriever
        self.by_id = {r.id: r for r in recipes}

    def ask(self, question: str) -> Answer:
        t0 = time.perf_counter()
        ms: dict[str, int] = {"extract": 0, "retrieve": 0, "generate": 0}

        query, usage = self.llm.extract_query(question)
        ms["extract"] = _ms(t0)
        if not query.in_domain:
            draft = Draft(answer=None, refusal=_out_of_domain(), source_ids=[])
            return self._answer(draft, [], usage, ms, t0)

        t1 = time.perf_counter()
        retrieved = self.retriever.retrieve(query)
        ms["retrieve"] = _ms(t1)
        if not retrieved:
            draft = Draft(answer=None, refusal=_nothing_matched(), source_ids=[])
            return self._answer(draft, [], usage, ms, t0)

        t2 = time.perf_counter()
        draft, u2 = self.llm.generate(question, retrieved)
        usage = usage + u2

        def retry() -> Draft:
            nonlocal usage
            d, u3 = self.llm.generate(question, retrieved)
            usage = usage + u3
            return d

        draft = ground(draft, {r.id for r in retrieved}, retry)
        ms["generate"] = _ms(t2)
        return self._answer(draft, retrieved, usage, ms, t0)

    def _answer(
        self, draft: Draft, retrieved: list[Recipe], usage: TokenUsage, ms: dict, t0: float
    ) -> Answer:
        # A refusal wins if the model filled both fields (Answer forbids both).
        answer = None if draft.refusal is not None else draft.answer
        sources = [
            Source(recipe_id=r.id, title=r.title, url=r.url)
            for rid in draft.source_ids
            if (r := self.by_id.get(rid)) is not None
        ]
        ms["total"] = _ms(t0)
        return Answer(
            answer=answer,
            refusal=draft.refusal,
            sources=sources,
            conflicts=draft.conflicts,
            usage=Usage(
                model=self.llm.model,
                tokens_in=usage.tokens_in,
                tokens_out=usage.tokens_out,
                cost_usd=cost_usd(self.llm.model, usage),
                latency_ms=ms,
            ),
        )


def _ms(since: float) -> int:
    return int((time.perf_counter() - since) * 1000)


def _out_of_domain() -> Refusal:
    return Refusal(
        reason="out_of_domain",
        message="This service answers questions about the recipes in its cookbook corpus only.",
    )


def _nothing_matched() -> Refusal:
    return Refusal(
        reason="insufficient_context",
        message="No recipe in the corpus matches the question and its constraints.",
    )
