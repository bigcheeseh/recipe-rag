import json
import logging

import anthropic
import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.models import Answer, Query
from app.pipeline import Pipeline
from tests.conftest import CORPUS, FakeLLM, answer, backends, refusal

OUT_OF_DOMAIN = "How do I fix a flat tyre?"
EGGS = "How many eggs in the carbonara?"


def make_client(llm: FakeLLM) -> TestClient:
    app = create_app(Pipeline(backends(llm), CORPUS))
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


def test_one_structured_log_record_per_request(caplog):
    llm = FakeLLM(drafts=[answer("x", ["beef-wellington"]), answer("y", ["carbonara"])])
    with caplog.at_level(logging.INFO, logger="app.request"):
        r = make_client(llm).post("/ask", json={"question": EGGS})
    records = [json.loads(m) for m in caplog.messages]
    assert len(records) == 1
    rec = records[0]
    assert rec["trace_id"] == r.headers["X-Trace-Id"]
    assert rec["question"] == EGGS
    assert rec["query"]["search_terms"] == EGGS
    assert rec["retrieved"][0]["id"] == "carbonara" and rec["retrieved"][0]["score"] > 0
    assert rec["cited"] == ["carbonara"]
    assert rec["grounding"] == "repaired"
    assert rec["prompt_hash"] == "fake" and rec["model"] == "claude-sonnet-5"
    assert rec["tokens_in"] == 300  # extract + generate + repair
    assert set(rec["latency_ms"]) == {"extract", "retrieve", "generate", "total"}


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
        create_app(Pipeline(backends(BrokenLLM(exc)), CORPUS)),
        raise_server_exceptions=False,
    ).__enter__()
    r = client.post("/ask", json={"question": EGGS})
    assert r.status_code == status
    assert r.json()["detail"] == detail
    assert r.json()["trace_id"] == r.headers["X-Trace-Id"]


def test_defaults_are_full_context_and_sonnet_when_env_is_unset(monkeypatch, tmp_path):
    """ADR-002, 2026-09-05: RETRIEVER unset means every filtered recipe goes to the model."""
    from app.api import build_pipeline, build_retrievers

    for var in ("RETRIEVER", "MODEL", "VOYAGE_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    assert list(build_retrievers(CORPUS)) == ["full", "bm25"]  # hybrid needs a Voyage key

    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([r.model_dump() for r in CORPUS]), encoding="utf-8")
    monkeypatch.setenv("CORPUS_PATH", str(corpus))
    monkeypatch.setenv("EMBEDDINGS_PATH", str(tmp_path / "none.npz"))  # .env may hold a Voyage key
    monkeypatch.setattr(anthropic, "Anthropic", lambda: object())  # no key, no network
    d = build_pipeline().backends.describe()
    assert d["defaults"] == {"model": "claude-sonnet-5", "retriever": "full"}
    assert [m["id"] for m in d["models"]] == ["claude-sonnet-5", "claude-haiku-4-5"]  # no Opus


def test_ui_is_served_at_root_when_built(tmp_path, monkeypatch):
    """The TypeScript page is static files; the API mounts them at / when UI_DIR exists."""
    (tmp_path / "index.html").write_text("<title>Recipe Q&A</title>", encoding="utf-8")
    monkeypatch.setenv("UI_DIR", str(tmp_path))
    c = make_client(FakeLLM())
    r = c.get("/")
    assert r.status_code == 200 and "Recipe Q&A" in r.text
    assert c.get("/healthz").status_code == 200  # API routes win over the static mount


def test_missing_ui_dir_does_not_break_the_api(tmp_path, monkeypatch):
    monkeypatch.setenv("UI_DIR", str(tmp_path / "nope"))
    c = make_client(FakeLLM())
    assert c.get("/").status_code == 404
    assert c.get("/healthz").status_code == 200


# per-request backend switch (SPEC 1, assumption 14)


def test_config_lists_backends_with_notes_and_defaults():
    body = make_client(FakeLLM()).get("/config").json()
    assert [m["id"] for m in body["models"]] == ["claude-sonnet-5"]
    assert [r["id"] for r in body["retrievers"]] == ["bm25", "full"]
    assert all(m["note"] for m in body["models"]) and all(r["note"] for r in body["retrievers"])
    assert body["defaults"] == {"model": "claude-sonnet-5", "retriever": "bm25"}


def test_request_can_pick_model_and_retriever_and_the_response_says_so():
    sonnet = FakeLLM(drafts=[answer("s", ["carbonara"])])
    haiku = FakeLLM(drafts=[answer("h", ["carbonara"])], model="claude-haiku-4-5")
    app = create_app(Pipeline(backends(sonnet, haiku), CORPUS))
    c = TestClient(app).__enter__()
    body = {"question": EGGS, "model": "claude-haiku-4-5", "retriever": "full"}
    a = Answer.model_validate(c.post("/ask", json=body).json())
    assert a.answer == "h" and a.usage.model == "claude-haiku-4-5" and a.usage.retriever == "full"
    assert haiku.cache_flags == [True]  # full context is cacheable, whatever the model
    assert sonnet.calls == []
    a = Answer.model_validate(c.post("/ask", json={"question": EGGS}).json())
    assert a.answer == "s" and a.usage.retriever == "bm25" and sonnet.cache_flags == [False]


@pytest.mark.parametrize("field, value", [("model", "gpt-9"), ("retriever", "magic")])
def test_unknown_backend_is_422_before_any_model_call(field, value):
    llm = FakeLLM()
    r = make_client(llm).post("/ask", json={"question": EGGS, field: value})
    assert r.status_code == 422 and value in r.text
    assert llm.calls == []
