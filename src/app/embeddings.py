"""Optional vector retrieval (Voyage embeddings) fused with BM25 by reciprocal rank fusion.

Off by default. Chunk vectors are computed once by `python -m app.embeddings` and
committed as data/embeddings.npz; only the question is embedded at request time.
"""

import argparse
import json
import os
import time
from collections.abc import Callable
from pathlib import Path

import httpx
import numpy as np

from app.models import Query, Recipe
from app.retrieval import TOP_K, Index, apply_filters, bm25_rank, chunk_recipes, promote_titles

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = "voyage-3.5-lite"

Embedder = Callable[[list[str], str], np.ndarray]


def voyage_embedder(
    api_key: str,
    model: str = DEFAULT_MODEL,
    timeout: float = 30,
    batch: int = 32,
    pause: float = 21,
) -> Embedder:
    client = httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout)

    def post(texts: list[str], input_type: str) -> list[list[float]]:
        body = {"input": texts, "model": model, "input_type": input_type}
        for attempt in range(6):
            resp = client.post(VOYAGE_URL, json=body)
            if resp.status_code != 429:
                resp.raise_for_status()
                return [d["embedding"] for d in resp.json()["data"]]
            time.sleep(20 * (attempt + 1))  # free tier: ~3 requests/min; wait a window
        resp.raise_for_status()
        raise AssertionError("unreachable")

    def embed(texts: list[str], input_type: str) -> np.ndarray:
        rows: list[list[float]] = []
        for i in range(0, len(texts), batch):
            if i:
                time.sleep(pause)  # stay under the per-minute limit on multi-batch builds
            rows += post(texts[i : i + batch], input_type)
        return np.array(rows, dtype=np.float32)

    return embed


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal rank fusion: each list contributes 1/(k+rank) to every id it contains."""
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, rid in enumerate(ranking, 1):
            fused[rid] = fused.get(rid, 0.0) + 1 / (k + rank)
    return fused


def chunk_keys(recipes: list[Recipe]) -> list[str]:
    return [f"{c.recipe_id}:{c.section}" for c in chunk_recipes(recipes)]


class HybridRetriever:
    def __init__(
        self,
        recipes: list[Recipe],
        vectors: np.ndarray,
        keys: list[str],
        embed: Embedder,
        k: int = TOP_K,
    ):
        if keys != chunk_keys(recipes):
            raise ValueError("embeddings do not match the corpus chunks; rebuild them")
        self.recipes, self.k, self.embed = recipes, k, embed
        self.index = Index(recipes)
        self.parents = [key.split(":")[0] for key in keys]
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        self.vectors = vectors / np.where(norms == 0, 1, norms)

    def _vector_rank(self, query: str, allowed: set[str]) -> list[str]:
        q = self.embed([query], "query")[0]
        q = q / (np.linalg.norm(q) or 1)
        sims = self.vectors @ q
        best: dict[str, float] = {}
        for parent, sim in zip(self.parents, sims, strict=True):
            if parent in allowed and sim > 0:
                best[parent] = max(best.get(parent, 0.0), float(sim))
        return sorted(best, key=lambda rid: best[rid], reverse=True)[: self.k]

    def retrieve(self, query: Query) -> list[tuple[Recipe, float]]:
        candidates = apply_filters(self.recipes, query)
        by_id = {r.id: r for r in candidates}
        lexical = [r.id for r, _ in bm25_rank(self.index, query.search_terms, candidates, self.k)]
        semantic = self._vector_rank(query.search_terms, set(by_id))
        fused = rrf([lexical, semantic])
        ranked = sorted(fused, key=lambda rid: fused[rid], reverse=True)[: self.k]
        hits = [(by_id[rid], round(fused[rid], 4)) for rid in ranked]
        hits = promote_titles(query.search_terms, hits, candidates, self.k)
        if hits or not query.constrained:
            return hits
        return [(r, 0.0) for r in candidates[: self.k]]


def load_vectors(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path, allow_pickle=False)
    return data["vectors"], [str(k) for k in data["keys"]]


def main(argv: list[str] | None = None) -> None:
    from dotenv import load_dotenv

    load_dotenv()
    ap = argparse.ArgumentParser(description="Embed corpus chunks with Voyage and save them.")
    ap.add_argument("--corpus", type=Path, default=Path("data/corpus.json"))
    ap.add_argument("--out", type=Path, default=Path("data/embeddings.npz"))
    ap.add_argument("--model", default=os.environ.get("VOYAGE_MODEL", DEFAULT_MODEL))
    args = ap.parse_args(argv)

    recipes = [
        Recipe.model_validate(r) for r in json.loads(args.corpus.read_text(encoding="utf-8"))
    ]
    chunks = chunk_recipes(recipes)
    embed = voyage_embedder(os.environ["VOYAGE_API_KEY"], args.model)
    vectors = embed([c.text for c in chunks], "document")
    np.savez(args.out, vectors=vectors, keys=np.array(chunk_keys(recipes)))
    print(f"{len(chunks)} chunks x {vectors.shape[1]} dims ({args.model}) -> {args.out}")


if __name__ == "__main__":
    main()
