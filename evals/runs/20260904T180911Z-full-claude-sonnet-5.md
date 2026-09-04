# Eval run 20260904T180911Z — full-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 23/23. Regressions vs last committed run: none.

Mean cost per question: 0.0148 USD (x1000 = 14.83 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2023 | 2230 |
| retrieve | 0 | 0 |
| generate | 2902 | 10523 |
| total | 4905 | 12601 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27431 | 158 | 0.0696 | 4313 |
| g02 | factual | PASS |  |  | 3 | 0 | 27415 | 319 | 0.0108 | 4854 |
| g03 | factual | PASS |  |  | 1 | 0 | 27425 | 180 | 0.0094 | 4489 |
| g04 | factual | PASS |  |  | 3 | 0 | 27419 | 320 | 0.0108 | 6071 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27419 | 376 | 0.0114 | 7106 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7400 | 349 | 0.0214 | 5789 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12429 | 561 | 0.0361 | 8006 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 20 | 0.0025 | 2054 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 1964 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27427 | 778 | 0.0154 | 9701 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27407 | 511 | 0.0127 | 7063 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 27413 | 165 | 0.0093 | 4526 |
| g14 | comparison | PASS |  |  | 2 | 0 | 27433 | 199 | 0.0096 | 4809 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 27413 | 342 | 0.0110 | 5535 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 27417 | 581 | 0.0134 | 7869 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4499 | 1028 | 0.0209 | 12601 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 27411 | 216 | 0.0098 | 4905 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 27413 | 151 | 0.0091 | 4067 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 27431 | 190 | 0.0095 | 5025 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1321 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 27439 | 194 | 0.0096 | 4890 |
| g23 | constraint_ru | PASS |  |  | 10 | 0 | 7404 | 1508 | 0.0187 | 20773 |
