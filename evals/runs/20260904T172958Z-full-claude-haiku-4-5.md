# Eval run 20260904T172958Z — full-claude-haiku-4-5

Model: "claude-haiku-4-5". Questions: 13. Passed: 13/13. Regressions vs last committed run: none.

Mean cost per question: 0.0063 USD (x1000 = 6.25 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1502 | 2230 |
| retrieve | 0 | 0 |
| generate | 2887 | 5554 |
| total | 4428 | 7551 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 20593 | 82 | 0.0259 | 7551 |
| g02 | factual | PASS |  |  | 3 | 0 | 20579 | 173 | 0.0037 | 3462 |
| g03 | factual | PASS |  |  | 1 | 0 | 20587 | 78 | 0.0032 | 4428 |
| g04 | factual | PASS |  |  | 3 | 0 | 20581 | 187 | 0.0038 | 3158 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 20581 | 166 | 0.0037 | 6338 |
| g06 | constraint | PASS |  |  | 1 | 0 | 5584 | 195 | 0.0077 | 6184 |
| g07 | constraint | PASS |  |  | 10 | 0 | 9226 | 480 | 0.0137 | 14280 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 851 | 17 | 0.0009 | 1502 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 853 | 17 | 0.0009 | 1453 |
| g10 | conflict | PASS |  |  | 5 | 1 | 20585 | 275 | 0.0042 | 5031 |
| g13 | conflict | PASS |  |  | 2 | 1 | 20571 | 190 | 0.0038 | 3719 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 20573 | 106 | 0.0034 | 4128 |
