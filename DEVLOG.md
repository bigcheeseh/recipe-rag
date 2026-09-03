# DEVLOG

Unprompted architectural decisions, measured numbers, and notes on what agent
output was accepted as-is versus rewritten.

## 2026-09-03 — open question: full context on a cheaper model

Raised during Block 1 review: could Haiku 4.5 with the whole corpus in the
prompt beat Sonnet 5 with retrieval on cost and speed?

Back-of-envelope at list prices, token counts unmeasured: Haiku full context
(~40k input tokens at $1/M) is roughly six times the input cost of Sonnet
retrieval (~3.5k tokens at $2/M). With prompt caching of the corpus (cached
reads at ~0.1x) full context on either model becomes competitive with
retrieval. Quality on the conflict and allergy cases is the unknown.

Decision: keep retrieval on Sonnet as the baseline. In Commit 31 the
comparison table gets extra rows: Sonnet full context with caching, Haiku
full context with caching. ADR-002 must state the corpus size at which full
context stops being viable.

## 2026-09-03 — Python 3.11 instead of 3.12

Only 3.11.6 is installed on the dev machine. CLAUDE.md said 3.12; the user
chose to stay on 3.11 rather than install another interpreter.
`requires-python`, the ruff target, and the future Docker base image all
say 3.11. No 3.12-only features are used. The package is installed into the
venv in editable mode (`pip install -e .`) so `app` imports resolve outside
pytest as well.
