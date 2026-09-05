import json
import logging
import os
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.backends import MODEL_NOTES, Backends
from app.embeddings import HybridRetriever, load_vectors, voyage_embedder
from app.llm import LLM, UnparseableOutput
from app.models import Answer, AskRequest, Recipe
from app.pipeline import Pipeline
from app.retrieval import BM25Retriever, FullContextRetriever, Retriever

log = logging.getLogger("app.request")


def load_corpus(path: Path) -> list[Recipe]:
    return [Recipe.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def build_retrievers(recipes: list[Recipe]) -> dict[str, Retriever]:
    """Every retriever the environment allows. full (default, ADR-002) and bm25 always;
    hybrid only with data/embeddings.npz and VOYAGE_API_KEY, since it calls Voyage per request."""
    out: dict[str, Retriever] = {
        "full": FullContextRetriever(recipes),
        "bm25": BM25Retriever(recipes),
    }
    vectors_path = Path(os.environ.get("EMBEDDINGS_PATH", "data/embeddings.npz"))
    if os.environ.get("VOYAGE_API_KEY") and vectors_path.is_file():
        vectors, keys = load_vectors(vectors_path)
        embed = voyage_embedder(
            os.environ["VOYAGE_API_KEY"], os.environ.get("VOYAGE_MODEL", "voyage-3.5-lite")
        )
        out["hybrid"] = HybridRetriever(recipes, vectors, keys, embed)
    return out


def build_pipeline() -> Pipeline:
    """Production wiring from the environment. Tests inject a Pipeline instead.
    MODEL and RETRIEVER set the defaults; a request may name any built pair."""
    load_dotenv()
    recipes = load_corpus(Path(os.environ.get("CORPUS_PATH", "data/corpus.json")))
    client = anthropic.Anthropic()
    backends = Backends(
        models=[LLM(client, m) for m in MODEL_NOTES],
        retrievers=build_retrievers(recipes),
        default_model=os.environ.get("MODEL", "claude-sonnet-5"),
        default_retriever=os.environ.get("RETRIEVER", "full"),
    )
    return Pipeline(backends, recipes)


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

    @app.get("/config")
    def config(request: Request) -> dict:
        return request.app.state.pipeline.backends.describe()

    @app.post("/ask")
    def ask(req: AskRequest, request: Request) -> Answer:
        try:
            return request.app.state.pipeline.ask(
                req.question, request.state.trace_id, req.model, req.retriever
            )
        except KeyError as e:  # unknown model / retriever, raised before any model call
            raise HTTPException(status_code=422, detail=e.args[0]) from e

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

    # The TypeScript page, compiled to ui/dist by `npm run build` (the Dockerfile does it).
    # Mounted last so /ask and /healthz keep precedence; absent in unit tests and dev.
    ui = Path(os.environ.get("UI_DIR", "ui/dist"))
    if ui.is_dir():
        app.mount("/", StaticFiles(directory=ui, html=True), name="ui")

    return app


logging.basicConfig(level=logging.INFO, format="%(message)s")
app = create_app()
