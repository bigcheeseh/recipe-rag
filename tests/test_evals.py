"""The eval checks are pure functions over a response body. No network."""

from evals.run_evals import check

from tests.conftest import CORPUS

BY_ID = {r.id: r for r in CORPUS}
USAGE = {
    "model": "m",
    "retriever": "bm25",
    "tokens_in": 1,
    "tokens_out": 1,
    "cost_usd": 0.0,
    "latency_ms": {"extract": 0, "retrieve": 0, "generate": 0, "total": 0},
}


def body(answer=None, refusal=None, ids=(), conflicts=()):
    sources = [{"recipe_id": i, "title": i, "url": "u"} for i in ids]
    reason = {"out_of_domain": "out_of_domain", "insufficient_context": "out_of_corpus"}
    return {
        "answer": answer,
        "refusal": refusal,
        "sources": sources,
        "conflicts": list(conflicts),
        "usage": USAGE,
        # assignment minimum contract, as the service serialises it
        "citations": [{"title": i, "url": "u"} for i in ids],
        "refused": refusal is not None,
        "refusal_reason": reason.get(refusal["reason"], "safety") if refusal else None,
    }


def test_factual_pass_and_fail():
    ok = body("Use 5 egg yolks", ids=["carbonara"])
    assert check({"cites": ["carbonara"], "contains": "5"}, 200, ok, BY_ID) == []
    assert check({"cites": ["risotto"], "contains": "6"}, 200, ok, BY_ID) == [
        "cites risotto: got ['carbonara']",
        "contains '6'",
    ]


def test_schema_violation_is_a_failure():
    bad = body(answer="x", ids=[])  # answer without sources
    assert check({}, 200, bad, BY_ID)[0].startswith("schema:")


def test_refusal_and_sources_empty():
    r = body(refusal={"reason": "out_of_domain", "message": "no"})
    assert check({"refusal": "out_of_domain", "sources_empty": True}, 200, r, BY_ID) == []
    a = body("x", ids=["carbonara"])
    assert check({"refusal": "out_of_domain"}, 200, a, BY_ID) == ["refusal out_of_domain: got None"]


def test_mentions_looks_in_refusal_message_too():
    r = body(
        refusal={"reason": "safety_deferral", "message": "contains Peanuts"}, ids=["carbonara"]
    )
    assert check({"mentions": "peanut"}, 200, r, BY_ID) == []


def test_http_status_expectation_short_circuits():
    assert check({"http_status": 422}, 422, {}, BY_ID) == []
    assert check({"http_status": 422}, 200, body("x", ids=["carbonara"]), BY_ID) == [
        "http 200 != 422"
    ]


def test_answered_requires_a_non_null_answer():
    r = body(refusal={"reason": "safety_deferral", "message": "m"}, ids=["carbonara"])
    assert check({"answered": True}, 200, r, BY_ID) == ["answered: got refusal safety_deferral"]
    assert check({"answered": True}, 200, body("x", ids=["carbonara"]), BY_ID) == []


def test_script_cyrillic_checks_answer_or_refusal_message():
    assert check({"script": "cyrillic"}, 200, body("5 желтков", ids=["carbonara"]), BY_ID) == []
    r = body(refusal={"reason": "out_of_domain", "message": "Нет"})
    assert check({"script": "cyrillic"}, 200, r, BY_ID) == []
    assert check({"script": "cyrillic"}, 200, body("5 yolks", ids=["carbonara"]), BY_ID) == [
        "script cyrillic"
    ]


def test_conflicts_min():
    a = body("x", ids=["carbonara", "risotto"], conflicts=["eggs differ"])
    assert check({"cites_min": 2, "conflicts_min": 1}, 200, a, BY_ID) == []
    assert check({"cites_min": 3, "conflicts_min": 2}, 200, a, BY_ID) == [
        "cites_min 3: got 2",
        "conflicts_min 2: got 1",
    ]


def test_judge_agreement_is_per_criterion():
    from evals.run_evals import agreement

    judge = {"g01": "3/3/3", "g02": "2/3/3", "g03": "1/1/3"}
    human = {"g01": "3/3/3", "g02": "3/3/3", "g99": "1/1/1"}  # g03 unscored, g99 unjudged
    rep = agreement(judge, human)
    assert rep["clarity"] == {"n": 2, "exact": 0.5, "mean_abs_diff": 0.5}
    assert rep["care"] == {"n": 2, "exact": 1.0, "mean_abs_diff": 0.0}


def test_render_response_shows_refusal_and_conflicts():
    from evals.run_evals import render_response

    r = body(refusal={"reason": "safety_deferral", "message": "m"}, ids=["carbonara"])
    assert render_response(r) == "REFUSAL (safety_deferral): m"
    a = body("x", ids=["carbonara"], conflicts=["eggs differ"])
    assert render_response(a) == "x\nConflicts: eggs differ"


def test_human_scores_are_read_from_the_answers_table(tmp_path):
    from evals.run_evals import table_column

    f = tmp_path / "a.md"
    f.write_text(
        "| id | question | judge | human | response | note |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| g01 | q | 3/3/3 | 2/3/3 | r | n |\n| g02 | q | 3/2/3 |  | r | n |\n",
        encoding="utf-8",
    )
    assert table_column(f, 2, True) == {"g01": "3/3/3", "g02": "3/2/3"}
    assert table_column(f, 3, True) == {"g01": "2/3/3"}


def test_contract_check_rejects_inconsistent_assignment_fields():
    """The eval verifies the assignment's minimum schema, not only our own model."""
    ok = body("x", ids=["carbonara"])
    ok.update(citations=[{"title": "carbonara", "url": "u"}], refused=False, refusal_reason=None)
    assert check({}, 200, ok, BY_ID) == []
    bad = dict(ok, refused=True)
    assert check({}, 200, bad, BY_ID) == ["contract: refused True != False"]
    missing = dict(ok)
    del missing["citations"]
    assert check({}, 200, missing, BY_ID)[0].startswith("contract:")
