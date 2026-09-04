import json
import logging
import os
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.embeddings import HybridRetriever, load_vectors, voyage_embedder
from app.llm import LLM, UnparseableOutput
from app.models import Answer, AskRequest, Recipe
from app.pipeline import Pipeline
from app.retrieval import BM25Retriever, Retriever

log = logging.getLogger("app.request")


def load_corpus(path: Path) -> list[Recipe]:
    return [Recipe.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def build_retriever(recipes: list[Recipe]) -> Retriever:
    """RETRIEVER=bm25 (default) | hybrid. Hybrid needs data/embeddings.npz and VOYAGE_API_KEY."""
    mode = os.environ.get("RETRIEVER", "bm25")
    if mode == "bm25":
        return BM25Retriever(recipes)
    if mode == "hybrid":
        vectors, keys = load_vectors(Path(os.environ.get("EMBEDDINGS_PATH", "data/embeddings.npz")))
        embed = voyage_embedder(
            os.environ["VOYAGE_API_KEY"], os.environ.get("VOYAGE_MODEL", "voyage-3.5-lite")
        )
        return HybridRetriever(recipes, vectors, keys, embed)
    raise ValueError(f"unknown RETRIEVER={mode!r}")


def build_pipeline() -> Pipeline:
    """Production wiring from the environment. Tests inject a Pipeline instead."""
    load_dotenv()
    recipes = load_corpus(Path(os.environ.get("CORPUS_PATH", "data/corpus.json")))
    llm = LLM(anthropic.Anthropic(), os.environ.get("MODEL", "claude-sonnet-5"))
    return Pipeline(llm, build_retriever(recipes), recipes)


def create_app(pipeline: Pipeline | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.pipeline = pipeline or build_pipeline()
        yield

    app = FastAPI(title="Recipe RAG", lifespan=lifespan)

    @app.get("/healthz")
    def healthz(request: Request) -> dict:
        return {"status": "ok", "recipes": len(request.app.state.pipeline.by_id)}

    @app.middleware("http")
    async def trace(request: Request, call_next: Callable) -> Response:
        request.state.trace_id = uuid.uuid4().hex
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        return response

    @app.post("/ask")
    def ask(req: AskRequest, request: Request) -> Answer:
        return request.app.state.pipeline.ask(req.question, request.state.trace_id)

    @app.exception_handler(Exception)
    async def upstream_errors(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", "")
        log.error(json.dumps({"trace_id": trace_id, "error": repr(exc)}))
        if isinstance(exc, anthropic.APITimeoutError):
            status, detail = 504, "upstream timeout"
        elif isinstance(exc, anthropic.APIError | UnparseableOutput):
            status, detail = 502, "upstream model error"
        else:
            status, detail = 500, "internal error"
        # The catch-all handler runs outside the http middleware, so set the header here.
        body = {"detail": detail, "trace_id": trace_id}
        return JSONResponse(body, status_code=status, headers={"X-Trace-Id": trace_id})

    return app


logging.basicConfig(level=logging.INFO, format="%(message)s")
app = create_app()
