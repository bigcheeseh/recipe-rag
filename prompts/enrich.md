You classify a single recipe for a search index. Read the ingredients, steps
and infobox below and return metadata that must be exactly right, because it
drives hard filters for people with allergies and dietary restrictions.

Rules:
- allergens: list every allergen category present in the ingredients.
  Categories: nuts (including peanuts), dairy (milk, butter, cheese, cream,
  yogurt, ghee), eggs, gluten (wheat flour, bread, pasta, soy sauce, seitan,
  barley, rye), shellfish, soy (tofu, soy sauce, edamame, miso, soy milk).
  Optional or substitute ingredients still count. When in doubt, include it.
- diet_tags: include vegan only if there are no animal products at all;
  vegetarian if there is no meat, poultry, fish or shellfish; pescatarian if
  there is no meat or poultry (fish and shellfish allowed). Vegan implies
  vegetarian implies pescatarian, so list all that apply.
- cuisine: one or two words, e.g. "Italian", "Thai", "American".
- total_minutes: total time from start to finished dish, as an integer.
  Prefer the infobox Time value if present; otherwise estimate from the
  steps. If a range is given, use the upper end.

Recipe:
{recipe}
