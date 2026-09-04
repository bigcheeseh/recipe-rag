from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Allergen = Literal["nuts", "dairy", "eggs", "gluten", "shellfish", "soy"]
DietTag = Literal["vegan", "vegetarian", "pescatarian"]


class AskRequest(BaseModel):
    question: str = Field(max_length=500)

    @field_validator("question")
    @classmethod
    def _strip_and_require_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be empty")
        return v


class Source(BaseModel):
    recipe_id: str
    title: str
    url: str


class Refusal(BaseModel):
    reason: Literal["out_of_domain", "insufficient_context", "safety_deferral"]
    message: str


class Usage(BaseModel):
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: dict[str, int]  # extract, retrieve, generate, total


class Answer(BaseModel):
    answer: str | None
    refusal: Refusal | None
    sources: list[Source]
    conflicts: list[str] = []
    usage: Usage

    @model_validator(mode="after")
    def _invariants(self) -> "Answer":
        if (self.answer is None) == (self.refusal is None):
            raise ValueError("exactly one of answer / refusal must be set")
        if self.answer is not None and not self.sources:
            raise ValueError("an answer must cite at least one source")
        if self.refusal is not None and self.refusal.reason == "out_of_domain" and self.sources:
            raise ValueError("out_of_domain refusal must have no sources")
        return self


class Meta(BaseModel):
    allergens: list[Allergen]
    diet_tags: list[DietTag]
    cuisine: str
    total_minutes: int


class Query(BaseModel):
    in_domain: bool
    search_terms: str
    exclude_allergens: list[Allergen] = []
    diet: list[DietTag] = []
    max_minutes: int | None = None

    @property
    def constrained(self) -> bool:
        return bool(self.exclude_allergens or self.diet or self.max_minutes is not None)


class Recipe(BaseModel):
    id: str
    title: str
    url: str
    revid: int
    ingredients: list[str]
    steps: list[str]
    infobox: dict[str, str] = {}
    meta: Meta | None = None


class GeneratorRefusal(BaseModel):
    """out_of_domain is decided by the extractor before retrieval; the generator, which
    always has recipes in front of it, may only plead missing context or safety."""

    reason: Literal["insufficient_context", "safety_deferral"]
    message: str


class Draft(BaseModel):
    """What the generator returns. The pipeline turns source_ids into Source objects."""

    answer: str | None
    refusal: GeneratorRefusal | None
    source_ids: list[str] = []
    conflicts: list[str] = []
