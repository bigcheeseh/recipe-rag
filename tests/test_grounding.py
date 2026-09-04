"""AC-9: the groundedness validator rejects cited ids that were not retrieved. No network."""

from app.models import Draft, Refusal
from app.pipeline import ground, validate_grounding

RETRIEVED = {"carbonara", "risotto"}


def draft(ids: list[str], answer: str | None = "x") -> Draft:
    refusal = None if answer else Refusal(reason="insufficient_context", message="m")
    return Draft(answer=answer, refusal=refusal, source_ids=ids)


def test_cited_subset_of_retrieved_is_grounded():
    assert validate_grounding(draft(["carbonara"]), RETRIEVED)


def test_uncited_id_is_rejected():
    assert not validate_grounding(draft(["carbonara", "beef-wellington"]), RETRIEVED)


def test_answer_without_any_source_is_rejected():
    assert not validate_grounding(draft([]), RETRIEVED)


def test_refusal_without_sources_is_fine():
    assert validate_grounding(draft([], answer=None), RETRIEVED)


def test_repair_is_tried_once_and_accepted_when_grounded():
    calls: list[int] = []

    def retry() -> Draft:
        calls.append(1)
        return draft(["risotto"])

    out, status = ground(draft(["beef-wellington"]), RETRIEVED, retry)
    assert status == "repaired"
    assert out.source_ids == ["risotto"] and out.answer == "x"
    assert calls == [1]


def test_failed_repair_becomes_insufficient_context():
    calls: list[int] = []

    def retry() -> Draft:
        calls.append(1)
        return draft(["still-wrong"])

    out, status = ground(draft(["beef-wellington"]), RETRIEVED, retry)
    assert status == "refused"
    assert out.answer is None
    assert out.refusal is not None and out.refusal.reason == "insufficient_context"
    assert out.source_ids == []
    assert calls == [1]


def test_grounded_draft_never_triggers_retry():
    out, status = ground(draft(["carbonara"]), RETRIEVED, lambda: draft(["risotto"]))
    assert status == "ok"
    assert out.source_ids == ["carbonara"]
