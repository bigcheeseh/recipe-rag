import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.llm import LLM, UnparseableOutput
from app.models import Answer, AskRequest, Recipe
from app.pipeline import Pipeline
from app.retrieval import BM25Retriever


def load_corpus(path: Path) -> list[Recipe]:
    return [Recipe.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def build_pipeline() -> Pipeline:
    """Production wiring from the environment. Tests inject a Pipeline instead."""
    load_dotenv()
    recipes = load_corpus(Path(os.environ.get("CORPUS_PATH", "data/corpus.json")))
    llm = LLM(anthropic.Anthropic(), os.environ.get("MODEL", "claude-sonnet-5"))
    return Pipeline(llm, BM25Retriever(recipes), recipes)


def create_app(pipeline: Pipeline | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.pipeline = pipeline or build_pipeline()
        yield

    app = FastAPI(title="Recipe RAG", lifespan=lifespan)

    @app.get("/healthz")
    def healthz(request: Request) -> dict:
        return {"status": "ok", "recipes": len(request.app.state.pipeline.by_id)}

    @app.post("/ask")
    def ask(req: AskRequest, request: Request) -> Answer:
        return request.app.state.pipeline.ask(req.question)

    @app.exception_handler(Exception)
    async def upstream_errors(request: Request, exc: Exception) -> JSONResponse:
        trace_id = uuid.uuid4().hex
        if isinstance(exc, anthropic.APITimeoutError):
            status, detail = 504, "upstream timeout"
        elif isinstance(exc, anthropic.APIError | UnparseableOutput):
            status, detail = 502, "upstream model error"
        else:
            status, detail = 500, "internal error"
        return JSONResponse({"detail": detail, "trace_id": trace_id}, status_code=status)

    return app


app = create_app()
