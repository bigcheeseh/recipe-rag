Implement a new requirement in the order this project is graded on: spec and evals first, code second. Requirement: $ARGUMENTS

Work through the steps below in order. Stop and show the diff after step 3 and again after step 6; do not continue past a stop without confirmation. One commit per step, no squashing, no attribution trailers.

1. **Read before deciding.** SPEC.md (contract, acceptance criteria, assumptions), the relevant ADR, `evals/golden_set.yaml`, and the modules the change touches. State in two or three sentences what changes and what does not.
2. **Spec.** Edit SPEC.md: add or change the acceptance criterion as a measurable assertion, add an edge case row if the requirement has one, and record any decision made without asking under Assumptions. If an existing ADR's invalidation condition is now met, say so and propose the ADR change; do not silently override it.
   Commit: `spec: <requirement>`.
3. **Golden questions.** Add two to four questions to `evals/golden_set.yaml` with deterministic `expect` fields (cites, contains, refusal, constraint checks). At least one must fail on the current code, and say which. Run `python evals/run_evals.py --judge none` to confirm the failure and quote the failing rows. Do not commit the run file yet.
   Commit: `eval: golden questions for <requirement>`.
   **STOP. Show SPEC diff and the new questions.**
4. **Failing unit test.** For the pure-Python part of the change (filters, ranking, validation, models, contract), write the test first and run it to confirm it fails.
   Commit: `test: <behaviour>`.
5. **Implementation.** Smallest change that makes the test pass; no new dependencies, no "for later" code. Prompt changes go in `prompts/*.md`, never in code. Run `pytest`, `ruff check .`, `mypy src`.
   Commit: `feat: <behaviour>` (or `fix:`).
6. **Evals.** Run `python evals/run_evals.py` (default judge) and commit the run table. Every previously passing question must still pass; the new questions must pass. If one does not, fix and re-run; record each failed attempt with its numbers in DEVLOG.md.
   Commit: `eval: <requirement> N/M`.
   **STOP. Show the eval table and the DEVLOG entry.**
7. **Record.** DEVLOG.md entry with what changed, the measured numbers before and after, and anything rewritten after a failing run. Update README's Cost & Latency if a measured number moved. Update the ADR if step 2 found its condition met.
   Commit: `docs: <requirement>`.

Never invent a latency or cost figure; write `TBD` until a run file has it.
