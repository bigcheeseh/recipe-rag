import anthropic
import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.models import Answer, Query
from app.pipeline import Pipeline
from app.retrieval import BM25Retriever
from tests.conftest import CORPUS, FakeLLM, answer, refusal

OUT_OF_DOMAIN = "How do I fix a flat tyre?"
EGGS = "How many eggs in the carbonara?"


def make_client(llm: FakeLLM) -> TestClient:
    app = create_app(Pipeline(llm, BM25Retriever(CORPUS), CORPUS))
    return TestClient(app).__enter__()  # run lifespan


def test_healthz_reports_loaded_recipes():
    r = make_client(FakeLLM()).get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "recipes": 3}


def test_answer_is_grounded_and_priced():
    llm = FakeLLM(drafts=[answer("5 egg yolks", ["carbonara"])])
    r = make_client(llm).post("/ask", json={"question": EGGS})
    assert r.status_code == 200
    body = r.json()
    a = Answer.model_validate(body)
    assert a.answer == "5 egg yolks"
    assert [s.recipe_id for s in a.sources] == ["carbonara"]
    assert a.sources[0].url == "https://example.org/carbonara"
    assert set(a.usage.latency_ms) == {"extract", "retrieve", "generate", "total"}
    assert a.usage.tokens_in == 200 and a.usage.tokens_out == 20  # two calls
    assert a.usage.cost_usd == pytest.approx(200 * 2 / 1e6 + 20 * 10 / 1e6)
    assert llm.calls == ["extract", "generate"]
    assert llm.generate_inputs[0][0] == "carbonara"  # retrieval fed the generator


def test_out_of_domain_skips_retrieval_and_generation():
    llm = FakeLLM(queries={OUT_OF_DOMAIN: Query(in_domain=False, search_terms="")})
    a = Answer.model_validate(
        make_client(llm).post("/ask", json={"question": OUT_OF_DOMAIN}).json()
    )
    assert a.refusal is not None and a.refusal.reason == "out_of_domain"
    assert a.sources == []
    assert a.usage.latency_ms["retrieve"] == 0 and a.usage.latency_ms["generate"] == 0
    assert llm.calls == ["extract"]


def test_nothing_retrieved_refuses_without_calling_generator():
    llm = FakeLLM(queries={"zzz": Query(in_domain=True, search_terms="zzz")})
    a = Answer.model_validate(make_client(llm).post("/ask", json={"question": "zzz"}).json())
    assert a.refusal is not None and a.refusal.reason == "insufficient_context"
    assert llm.calls == ["extract"]


def test_ungrounded_answer_is_repaired_once():
    llm = FakeLLM(drafts=[answer("x", ["beef-wellington"]), answer("y", ["carbonara"])])
    a = Answer.model_validate(make_client(llm).post("/ask", json={"question": EGGS}).json())
    assert a.answer == "y"
    assert llm.calls == ["extract", "generate", "generate"]


def test_refusal_wins_when_model_fills_both_fields():
    d = refusal("safety_deferral", ["carbonara"])
    d.answer = "should be dropped"
    a = Answer.model_validate(
        make_client(FakeLLM(drafts=[d])).post("/ask", json={"question": EGGS}).json()
    )
    assert a.answer is None and a.refusal is not None
    assert a.refusal.reason == "safety_deferral"
    assert [s.recipe_id for s in a.sources] == ["carbonara"]


@pytest.mark.parametrize("q", ["", "   ", "\n"])
def test_empty_question_is_422_before_any_model_call(q):
    llm = FakeLLM()
    assert make_client(llm).post("/ask", json={"question": q}).status_code == 422
    assert llm.calls == []


def test_missing_question_is_422():
    assert make_client(FakeLLM()).post("/ask", json={}).status_code == 422


def test_overlong_question_is_422():
    assert make_client(FakeLLM()).post("/ask", json={"question": "x" * 501}).status_code == 422


class BrokenLLM(FakeLLM):
    def __init__(self, exc: Exception):
        super().__init__()
        self.exc = exc

    def extract_query(self, question: str):
        raise self.exc


@pytest.mark.parametrize(
    "exc, status, detail",
    [
        (anthropic.APITimeoutError(request=None), 504, "upstream timeout"),  # type: ignore[arg-type]
        (anthropic.APIConnectionError(request=None), 502, "upstream model error"),  # type: ignore[arg-type]
        (RuntimeError("boom"), 500, "internal error"),
    ],
)
def test_upstream_failures_map_to_status_codes(exc, status, detail):
    client = TestClient(
        create_app(Pipeline(BrokenLLM(exc), BM25Retriever(CORPUS), CORPUS)),
        raise_server_exceptions=False,
    ).__enter__()
    r = client.post("/ask", json={"question": EGGS})
    assert r.status_code == status
    assert r.json()["detail"] == detail
    assert r.json()["trace_id"]
