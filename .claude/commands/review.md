Run the CLAUDE.md final check on the current state of the repo and report each item as PASS or FAIL with evidence. Do not fix anything; report only. Scope: $ARGUMENTS (empty means everything).

Checks, in this order:

1. **Gate.** `pytest`, `ruff check .`, `ruff format --check src tests evals`, `mypy src`, and `cd ui && npx tsc --noEmit`. Quote the last line of each.
2. **Spec first.** `git log --reverse --oneline | head -5`: SPEC.md and the golden set are the first commits.
3. **TDD pairs.** For each `test:` commit, the matching `feat:`/`fix:` commit comes later in `git log --reverse --oneline`. List the five required pairs (schema invariants, HTML parser, chunking, BM25 ranking, filters, groundedness) with both hashes.
4. **ADRs.** Every file in `ADR/` has a number in its title and a section whose heading contains "invalid". Name any that does not.
5. **Numbers.** Every number in README.md's Cost & Latency section traces to a file in `evals/runs/` or a DEVLOG entry. Grep README for digits next to "ms", "USD", "s ", "%" and check each. A number with no source is a FAIL; `TBD` is not a failure.
6. **Latest eval run committed.** The newest file in `evals/runs/` is tracked by git (`git status --short evals/runs` is empty), and its pass count matches the one quoted in README and ADR-002.
7. **Prompts.** `prompts/` holds `extract_query.md`, `generate.md`, `judge.md`, and the enrichment prompt as separate files.
8. **Secrets.** `git ls-files | grep -i env` shows only `.env.example`; `grep -rn "sk-ant" --include=*.py --include=*.md --include=*.toml --include=*.yml .` finds nothing outside `.env`.
9. **Deployed run.** If README names a deployed URL, `python evals/run_evals.py --url <url> --judge none` passes with no regression. Skip with a note if the URL is still TBD.

Output: a table with one row per check, PASS/FAIL/SKIP, and one line of evidence. Then the list of FAILs with the file and line to look at. Nothing else.
