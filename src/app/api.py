from fastapi import FastAPI

from app.models import Answer, AskRequest, Source, Usage

app = FastAPI(title="Recipe RAG")


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "recipes": 0}


@app.post("/ask")
def ask(req: AskRequest) -> Answer:
    # Stub: static response so the contract can be tested before the pipeline exists.
    return Answer(
        answer=f"stub answer for: {req.question}",
        refusal=None,
        sources=[Source(recipe_id="stub", title="Stub", url="https://example.org/stub")],
        usage=Usage(
            model="stub",
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            latency_ms={"extract": 0, "retrieve": 0, "generate": 0, "total": 0},
        ),
    )
