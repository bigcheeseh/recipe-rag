"""The two model calls. Everything else in the pipeline is pure Python."""

import hashlib
from pathlib import Path
from typing import TypeVar

import anthropic
from anthropic.types import TextBlockParam
from pydantic import BaseModel, ValidationError

from app.models import Draft, Query, Recipe

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
# USD per 1M tokens (input, output). SPEC section 7; Anthropic list prices.
PRICES = {
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (5.00, 25.00),
}
CACHE_WRITE, CACHE_READ = 1.25, 0.10  # multipliers on the input price

T = TypeVar("T", bound=BaseModel)


class UnparseableOutput(RuntimeError):
    """The model returned no object matching the schema, twice. Surfaces as 502."""


class TokenUsage(BaseModel):
    tokens_in: int = 0  # uncached input tokens
    tokens_out: int = 0
    cache_write: int = 0
    cache_read: int = 0

    @property
    def total_in(self) -> int:
        return self.tokens_in + self.cache_write + self.cache_read

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            tokens_in=self.tokens_in + other.tokens_in,
            tokens_out=self.tokens_out + other.tokens_out,
            cache_write=self.cache_write + other.cache_write,
            cache_read=self.cache_read + other.cache_read,
        )


def cost_usd(model: str, u: TokenUsage) -> float:
    p_in, p_out = PRICES[model]
    inputs = u.tokens_in + u.cache_write * CACHE_WRITE + u.cache_read * CACHE_READ
    return inputs * p_in / 1e6 + u.tokens_out * p_out / 1e6


def render_context(r: Recipe) -> str:
    """The recipe as the generator sees it. Metadata comes first so diet, allergen and
    time facts the filters relied on are stated, not left for the model to infer from
    a title (g27: it once judged only "Pancakes (Vegan)" vegan out of three)."""
    m = r.meta
    meta = (
        f"Diet: {', '.join(m.diet_tags) or 'none'}\n"
        f"Allergens: {', '.join(m.allergens) or 'none'}\n"
        f"Estimated total time: {m.total_minutes} minutes\nCuisine: {m.cuisine}\n"
        if m
        else "Diet: unknown\nAllergens: unknown\nEstimated total time: unknown\n"
    )
    box = "".join(f"{k}: {v}\n" for k, v in r.infobox.items())
    return (
        f"id: {r.id}\nTitle: {r.title}\n{meta}{box}Ingredients:\n"
        + "\n".join(f"- {i}" for i in r.ingredients)
        + "\nSteps:\n"
        + "\n".join(f"{n}. {s}" for n, s in enumerate(r.steps, 1))
    )


class LLM:
    def __init__(self, client: anthropic.Anthropic, model: str):
        self.client, self.model = client, model
        blob = b"".join(p.read_bytes() for p in sorted(PROMPTS.glob("*.md")))
        self.prompt_hash = hashlib.sha256(blob).hexdigest()[:12]

    def _parse(
        self, output: type[T], max_tokens: int, user: str, system: list[TextBlockParam] | None
    ) -> tuple[T, TokenUsage]:
        """One structured-output call; retried once if the model returns no parseable object."""
        last_error = "no parsed output"
        for _ in range(2):
            try:
                resp = self.client.messages.parse(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system if system else anthropic.omit,
                    messages=[{"role": "user", "content": user}],
                    output_format=output,
                )
            except ValidationError as e:
                # Typically JSON cut off by max_tokens; the SDK raises before we see usage.
                last_error = str(e).splitlines()[-1]
                continue
            u = resp.usage
            usage = TokenUsage(
                tokens_in=u.input_tokens,
                tokens_out=u.output_tokens,
                cache_write=u.cache_creation_input_tokens or 0,
                cache_read=u.cache_read_input_tokens or 0,
            )
            if resp.parsed_output is not None:
                return resp.parsed_output, usage
            last_error = f"stop_reason={resp.stop_reason}"
        raise UnparseableOutput(f"{output.__name__}: {last_error}")

    def extract_query(self, question: str) -> tuple[Query, TokenUsage]:
        prompt = (PROMPTS / "extract_query.md").read_text(encoding="utf-8")
        return self._parse(Query, 512, prompt.replace("{question}", question), None)

    def generate(
        self, question: str, recipes: list[Recipe], cache: bool = False
    ) -> tuple[Draft, TokenUsage]:
        """cache: mark the recipe block for prompt caching. Only pays off when the same
        recipes are sent on every request, which the retriever knows (Retriever.cacheable)."""
        rules = (PROMPTS / "generate.md").read_text(encoding="utf-8")
        context: TextBlockParam = {
            "type": "text",
            "text": "Recipes:\n\n" + "\n\n".join(render_context(r) for r in recipes),
        }
        if cache:
            context["cache_control"] = {"type": "ephemeral"}
        system: list[TextBlockParam] = [{"type": "text", "text": rules}, context]
        return self._parse(Draft, 4096, f"Question:\n{question}", system)
