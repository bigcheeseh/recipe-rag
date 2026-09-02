import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.models import Answer


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ask_returns_valid_answer(client):
    r = client.post("/ask", json={"question": "How many eggs in the carbonara?"})
    assert r.status_code == 200
    body = r.json()
    Answer.model_validate(body)
    assert set(body["usage"]["latency_ms"]) == {"extract", "retrieve", "generate", "total"}


@pytest.mark.parametrize("q", ["", "   ", "\n"])
def test_empty_question_is_422(client, q):
    r = client.post("/ask", json={"question": q})
    assert r.status_code == 422


def test_missing_question_is_422(client):
    r = client.post("/ask", json={})
    assert r.status_code == 422


def test_overlong_question_is_422(client):
    r = client.post("/ask", json={"question": "x" * 501})
    assert r.status_code == 422
