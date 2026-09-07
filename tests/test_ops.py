"""Container-level visibility for reviewers without a Fly organisation seat:
one token-protected endpoint serving recent log lines and machine status."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.pipeline import Pipeline
from tests.conftest import CORPUS, FakeLLM, answer, backends

TOKEN = "s3cret"


def make_client(monkeypatch, token: str | None = TOKEN) -> TestClient:
    if token is None:
        monkeypatch.delenv("OPS_TOKEN", raising=False)
    else:
        monkeypatch.setenv("OPS_TOKEN", token)
    llm = FakeLLM(drafts=[answer("5 egg yolks", ["carbonara"])])
    app = create_app(Pipeline(backends(llm), CORPUS))
    return TestClient(app).__enter__()


def test_ops_is_absent_when_no_token_is_configured(monkeypatch):
    assert make_client(monkeypatch, token=None).get("/ops").status_code == 404


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}])
def test_ops_requires_the_token(monkeypatch, headers):
    assert make_client(monkeypatch).get("/ops", headers=headers).status_code == 401


def test_ops_accepts_bearer_header_and_query_token(monkeypatch):
    c = make_client(monkeypatch)
    assert c.get("/ops", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert c.get("/ops", params={"token": TOKEN}).status_code == 200


def test_ops_reports_machine_status(monkeypatch):
    c = make_client(monkeypatch)
    monkeypatch.setenv("FLY_MACHINE_ID", "48ed9345a94068")
    monkeypatch.setenv("FLY_REGION", "ams")
    body = c.get("/ops", params={"token": TOKEN}).json()
    assert body["status"] == "ok"
    assert body["recipes"] == len(CORPUS)
    assert body["machine"] == {"id": "48ed9345a94068", "region": "ams", "release": "unknown"}
    assert isinstance(body["uptime_s"], int)


def test_ops_reports_the_render_instance_and_deployed_commit(monkeypatch):
    """Render names its own variables; without this the status reads "local" in production."""
    c = make_client(monkeypatch)
    monkeypatch.setenv("RENDER_INSTANCE_ID", "srv-d3abc-xyz")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "946e09b")
    monkeypatch.setenv("REGION", "frankfurt")
    body = c.get("/ops", params={"token": TOKEN}).json()
    assert body["machine"] == {
        "id": "srv-d3abc-xyz",
        "region": "frankfurt",
        "release": "946e09b",
    }


def test_ops_serves_the_request_log_newest_last(monkeypatch):
    c = make_client(monkeypatch)
    c.post("/ask", json={"question": "How many eggs in the carbonara?"})
    lines = c.get("/ops", params={"token": TOKEN, "limit": 5}).json()["log"]
    assert any("How many eggs in the carbonara?" in ln for ln in lines)
    assert len(lines) <= 5


def test_ops_never_serves_the_token_back_in_the_log(monkeypatch):
    """An access log records the query string, so the buffer must redact it."""
    c = make_client(monkeypatch)
    logging.getLogger("app.request").info("GET /ops?token=%s&limit=5 200", TOKEN)
    body = c.get("/ops", params={"token": TOKEN}).json()
    assert TOKEN not in " ".join(body["log"])
    assert any("token=***" in ln for ln in body["log"])
