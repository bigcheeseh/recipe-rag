"""The two model calls. Everything else in the pipeline is pure Python."""

import hashlib
from pathlib import Path
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from app.models import Draft, Query, Recipe

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
# USD per 1M tokens (input, output). SPEC section 7.
PRICES = {"claude-sonnet-5": (2.00, 10.00)}

T = TypeVar("T", bound=BaseModel)


class UnparseableOutput(RuntimeError):
    """The model returned no object matching the schema, twice. Surfaces as 502."""


class TokenUsage(BaseModel):
    tokens_in: int = 0
    tokens_out: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            tokens_in=self.tokens_in + other.tokens_in,
            tokens_out=self.tokens_out + other.tokens_out,
        )


def cost_usd(model: str, usage: TokenUsage) -> float:
    p_in, p_out = PRICES[model]
    return usage.tokens_in * p_in / 1e6 + usage.tokens_out * p_out / 1e6


def render_context(r: Recipe) -> str:
    box = "".join(f"{k}: {v}\n" for k, v in r.infobox.items())
    return (
        f"id: {r.id}\nTitle: {r.title}\n{box}Ingredients:\n"
        + "\n".join(f"- {i}" for i in r.ingredients)
        + "\nSteps:\n"
        + "\n".join(f"{n}. {s}" for n, s in enumerate(r.steps, 1))
    )


class LLM:
    def __init__(self, client: anthropic.Anthropic, model: str):
        self.client, self.model = client, model
        blob = b"".join(p.read_bytes() for p in sorted(PROMPTS.glob("*.md")))
        self.prompt_hash = hashlib.sha256(blob).hexdigest()[:12]

    def _parse(self, prompt: str, output: type[T], max_tokens: int) -> tuple[T, TokenUsage]:
        """One structured-output call; retried once if the model returns no parseable object."""
        for _ in range(2):
            resp = self.client.messages.parse(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                output_format=output,
            )
            usage = TokenUsage(
                tokens_in=resp.usage.input_tokens, tokens_out=resp.usage.output_tokens
            )
            if resp.parsed_output is not None:
                return resp.parsed_output, usage
        raise UnparseableOutput(f"{output.__name__}: stop_reason={resp.stop_reason}")

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]:
        prompt = (PROMPTS / "extract_query.md").read_text(encoding="utf-8")
        return self._parse(prompt.replace("{question}", question), Query, max_tokens=512)

    def generate(self, question: str, recipes: list[Recipe]) -> tuple[Draft, TokenUsage]:
        prompt = (PROMPTS / "generate.md").read_text(encoding="utf-8")
        prompt = prompt.replace("{question}", question)
        prompt = prompt.replace("{recipes}", "\n\n".join(render_context(r) for r in recipes))
        return self._parse(prompt, Draft, max_tokens=1024)
