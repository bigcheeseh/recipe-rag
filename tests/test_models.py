import pytest
from pydantic import ValidationError

from app.models import Answer, AskRequest, Refusal, Source, Usage

USAGE = Usage(
    model="test",
    tokens_in=0,
    tokens_out=0,
    cost_usd=0.0,
    latency_ms={"extract": 0, "retrieve": 0, "generate": 0, "total": 0},
)
SOURCE = Source(recipe_id="carbonara", title="Carbonara", url="https://example.org/carbonara")


def test_answer_with_sources_is_valid():
    a = Answer(answer="3 eggs", refusal=None, sources=[SOURCE], usage=USAGE)
    assert a.answer == "3 eggs"
    assert a.conflicts == []


def test_refusal_is_valid():
    r = Refusal(reason="out_of_domain", message="not about food")
    a = Answer(answer=None, refusal=r, sources=[], usage=USAGE)
    assert a.refusal.reason == "out_of_domain"


# invariant 1: exactly one of answer / refusal


def test_both_answer_and_refusal_rejected():
    r = Refusal(reason="insufficient_context", message="x")
    with pytest.raises(ValidationError):
        Answer(answer="x", refusal=r, sources=[SOURCE], usage=USAGE)


def test_neither_answer_nor_refusal_rejected():
    with pytest.raises(ValidationError):
        Answer(answer=None, refusal=None, sources=[], usage=USAGE)


# invariant 2: answer requires sources


def test_answer_without_sources_rejected():
    with pytest.raises(ValidationError):
        Answer(answer="x", refusal=None, sources=[], usage=USAGE)


# invariant 3: out_of_domain requires empty sources


def test_out_of_domain_with_sources_rejected():
    r = Refusal(reason="out_of_domain", message="x")
    with pytest.raises(ValidationError):
        Answer(answer=None, refusal=r, sources=[SOURCE], usage=USAGE)


def test_other_refusals_may_have_sources():
    r = Refusal(reason="safety_deferral", message="x")
    a = Answer(answer=None, refusal=r, sources=[SOURCE], usage=USAGE)
    assert len(a.sources) == 1


def test_unknown_refusal_reason_rejected():
    with pytest.raises(ValidationError):
        Refusal(reason="because", message="x")


# request validation: empty question is rejected before any model call


@pytest.mark.parametrize("q", ["", "   ", "\n\t"])
def test_empty_question_rejected(q):
    with pytest.raises(ValidationError):
        AskRequest(question=q)


def test_overlong_question_rejected():
    with pytest.raises(ValidationError):
        AskRequest(question="x" * 501)


def test_question_is_stripped():
    assert AskRequest(question="  eggs?  ").question == "eggs?"
