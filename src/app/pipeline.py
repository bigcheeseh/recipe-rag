"""Pure-Python glue between the two model calls: grounding check with one repair,
and the request pipeline that strings extract -> filter+rank -> generate -> validate.

Every request emits one JSON log record (AC-15) that says which recipes were
retrieved and which were cited, so a wrong answer can be blamed on retrieval
(wrong recipes) or generation (right recipes, wrong text) from the log alone."""

import json
import logging
import time
import uuid
from collections.abc import Callable
from typing import Literal, Protocol

from app.llm import TokenUsage, cost_usd
from app.models import Answer, Draft, GeneratorRefusal, Query, Recipe, Refusal, Source, Usage
from app.retrieval import Retriever

log = logging.getLogger("app.request")

Grounding = Literal["ok", "repaired", "refused"]


def validate_grounding(draft: Draft, retrieved_ids: set[str]) -> bool:
    """Every cited id must have been retrieved, and an answer must cite something."""
    cited = set(draft.source_ids)
    if not cited <= retrieved_ids:
        return False
    return draft.answer is None or bool(cited)


def ground(
    draft: Draft, retrieved_ids: set[str], retry: Callable[[], Draft]
) -> tuple[Draft, Grounding]:
    """Accept a grounded draft; otherwise regenerate once; otherwise refuse."""
    if validate_grounding(draft, retrieved_ids):
        return draft, "ok"
    draft = retry()
    if validate_grounding(draft, retrieved_ids):
        return draft, "repaired"
    refusal = GeneratorRefusal(
        reason="insufficient_context",
        message="The retrieved recipes do not support a grounded answer to this question.",
    )
    return Draft(answer=None, refusal=refusal, source_ids=[]), "refused"


class Generator(Protocol):
    """What the pipeline needs from the model layer; LLM satisfies it, tests fake it."""

    model: str
    prompt_hash: str

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]: ...
    def generate(self, question: str, recipes: list[Recipe]) -> tuple[Draft, TokenUsage]: ...


class Pipeline:
    def __init__(self, llm: Generator, retriever: Retriever, recipes: list[Recipe]):
        self.llm, self.retriever = llm, retriever
        self.by_id = {r.id: r for r in recipes}

    def ask(self, question: str, trace_id: str | None = None) -> Answer:
        t0 = time.perf_counter()
        rec: dict = {
            "trace_id": trace_id or uuid.uuid4().hex,
            "question": question,
            "model": self.llm.model,
            "prompt_hash": self.llm.prompt_hash,
            "retrieved": [],
            "grounding": None,
        }
        ms: dict[str, int] = {"extract": 0, "retrieve": 0, "generate": 0}

        query, usage = self.llm.extract_query(question)
        ms["extract"] = _ms(t0)
        rec["query"] = query.model_dump()
        if not query.in_domain:
            return self._finish(None, _out_of_domain(), [], [], usage, ms, t0, rec)

        t1 = time.perf_counter()
        hits = self.retriever.retrieve(query)
        ms["retrieve"] = _ms(t1)
        rec["retrieved"] = [{"id": r.id, "score": round(s, 3)} for r, s in hits]
        retrieved = [r for r, _ in hits]
        if not retrieved:
            return self._finish(None, _nothing_matched(), [], [], usage, ms, t0, rec)

        t2 = time.perf_counter()
        draft, u2 = self.llm.generate(question, retrieved)
        usage = usage + u2

        def retry() -> Draft:
            nonlocal usage
            d, u3 = self.llm.generate(question, retrieved)
            usage = usage + u3
            return d

        draft, rec["grounding"] = ground(draft, {r.id for r in retrieved}, retry)
        ms["generate"] = _ms(t2)
        refusal = None
        if draft.refusal is not None:
            refusal = Refusal(reason=draft.refusal.reason, message=draft.refusal.message)
        # A refusal wins if the model filled both fields (Answer forbids both).
        answer = None if refusal is not None else draft.answer
        return self._finish(answer, refusal, draft.source_ids, draft.conflicts, usage, ms, t0, rec)

    def _finish(
        self,
        answer: str | None,
        refusal: Refusal | None,
        source_ids: list[str],
        conflicts: list[str],
        usage: TokenUsage,
        ms: dict[str, int],
        t0: float,
        rec: dict,
    ) -> Answer:
        sources = [
            Source(recipe_id=r.id, title=r.title, url=r.url)
            for rid in source_ids
            if (r := self.by_id.get(rid)) is not None
        ]
        ms["total"] = _ms(t0)
        out = Answer(
            answer=answer,
            refusal=refusal,
            sources=sources,
            conflicts=conflicts,
            usage=Usage(
                model=self.llm.model,
                tokens_in=usage.total_in,
                tokens_out=usage.tokens_out,
                cost_usd=cost_usd(self.llm.model, usage),
                latency_ms=ms,
            ),
        )
        rec.update(
            cited=[s.recipe_id for s in sources],
            refusal=None if out.refusal is None else out.refusal.reason,
            conflicts=len(out.conflicts),
            tokens_in=usage.total_in,
            tokens_out=usage.tokens_out,
            cache_write=usage.cache_write,
            cache_read=usage.cache_read,
            cost_usd=out.usage.cost_usd,
            latency_ms=ms,
        )
        log.info(json.dumps(rec, ensure_ascii=False))
        return out


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
