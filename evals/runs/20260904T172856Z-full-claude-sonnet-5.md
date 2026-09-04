# Eval run 20260904T172856Z — full-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 13. Passed: 13/13. Regressions vs last committed run: none.

Mean cost per question: 0.0122 USD (x1000 = 12.24 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1783 | 2156 |
| retrieve | 0 | 0 |
| generate | 4372 | 5510 |
| total | 5870 | 7276 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27334 | 131 | 0.0088 | 4512 |
| g02 | factual | PASS |  |  | 3 | 0 | 27318 | 307 | 0.0106 | 5870 |
| g03 | factual | PASS |  |  | 1 | 0 | 27328 | 137 | 0.0089 | 4424 |
| g04 | factual | PASS |  |  | 3 | 0 | 27322 | 262 | 0.0101 | 5128 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27322 | 330 | 0.0108 | 5989 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7303 | 378 | 0.0215 | 6539 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12332 | 592 | 0.0362 | 7276 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1104 | 45 | 0.0027 | 2035 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1106 | 20 | 0.0024 | 1410 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27330 | 644 | 0.0140 | 7294 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27310 | 428 | 0.0118 | 7054 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 27316 | 172 | 0.0092 | 4298 |
