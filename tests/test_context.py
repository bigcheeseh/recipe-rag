"""What the generator sees for each recipe. Metadata must be in the text, or the model
cannot assert diet, allergen, or time facts the filters already relied on (g27)."""

from app.llm import render_context
from app.models import Meta
from tests.conftest import CORPUS


def test_context_carries_metadata_when_present():
    r = CORPUS[2].model_copy()
    r.meta = Meta(
        allergens=["eggs", "gluten"], diet_tags=["vegetarian"], cuisine="American", total_minutes=75
    )
    text = render_context(r)
    assert "Diet: vegetarian" in text
    assert "Allergens: eggs, gluten" in text
    assert "Estimated total time: 75 minutes" in text
    assert "Cuisine: American" in text
    assert text.index("Diet:") < text.index("Ingredients:")


def test_context_without_metadata_says_so():
    text = render_context(CORPUS[0])  # fixture recipes carry no meta
    assert (
        "Diet: unknown" in text
        and "Allergens: unknown" in text
        and "Estimated total time: unknown" in text
    )
