"""Pure-Python glue between the two model calls: grounding check with one repair."""

from collections.abc import Callable

from app.models import Draft, Refusal


def validate_grounding(draft: Draft, retrieved_ids: set[str]) -> bool:
    """Every cited id must have been retrieved, and an answer must cite something."""
    cited = set(draft.source_ids)
    if not cited <= retrieved_ids:
        return False
    return draft.answer is None or bool(cited)


def ground(draft: Draft, retrieved_ids: set[str], retry: Callable[[], Draft]) -> Draft:
    """Accept a grounded draft; otherwise regenerate once; otherwise refuse."""
    if validate_grounding(draft, retrieved_ids):
        return draft
    draft = retry()
    if validate_grounding(draft, retrieved_ids):
        return draft
    return Draft(
        answer=None,
        refusal=Refusal(
            reason="insufficient_context",
            message="The retrieved recipes do not support a grounded answer to this question.",
        ),
        source_ids=[],
    )
