"""The eval checks are pure functions over a response body. No network."""

from evals.run_evals import check

from tests.conftest import CORPUS

BY_ID = {r.id: r for r in CORPUS}
USAGE = {
    "model": "m",
    "tokens_in": 1,
    "tokens_out": 1,
    "cost_usd": 0.0,
    "latency_ms": {"extract": 0, "retrieve": 0, "generate": 0, "total": 0},
}


def body(answer=None, refusal=None, ids=(), conflicts=()):
    sources = [{"recipe_id": i, "title": i, "url": "u"} for i in ids]
    return {
        "answer": answer,
        "refusal": refusal,
        "sources": sources,
        "conflicts": list(conflicts),
        "usage": USAGE,
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


def test_conflicts_min():
    a = body("x", ids=["carbonara", "risotto"], conflicts=["eggs differ"])
    assert check({"cites_min": 2, "conflicts_min": 1}, 200, a, BY_ID) == []
    assert check({"cites_min": 3, "conflicts_min": 2}, 200, a, BY_ID) == [
        "cites_min 3: got 2",
        "conflicts_min 2: got 1",
    ]
