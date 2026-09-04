# Eval run 20260904T193510Z — full-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 22/23. Regressions vs last committed run: ['g12'].

Mean cost per question: 0.0147 USD (x1000 = 14.68 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1938 | 2508 |
| retrieve | 0 | 0 |
| generate | 3218 | 9134 |
| total | 5238 | 11278 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 22 responses: clarity 3.00, care 3.00, language 3.00. Judge cost USD 0.1269.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27486 | 153 | 0.0696 | 4154 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 27470 | 264 | 0.0103 | 5283 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 27480 | 170 | 0.0093 | 4412 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 27474 | 349 | 0.0111 | 5712 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27474 | 297 | 0.0106 | 6065 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7455 | 319 | 0.0212 | 5852 | 3/3/3 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12484 | 637 | 0.0370 | 8398 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 1938 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 1757 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27482 | 697 | 0.0146 | 8669 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27462 | 409 | 0.0117 | 6264 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | FAIL | refusal insufficient_context: got out_of_domain | out_of_domain | 0 | 0 | 27468 | 155 | 0.0092 | 5215 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 27488 | 222 | 0.0099 | 4770 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 27468 | 264 | 0.0103 | 5238 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 27472 | 516 | 0.0128 | 7067 | 3/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4554 | 1744 | 0.0282 | 18737 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 27466 | 300 | 0.0106 | 6061 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 27468 | 146 | 0.0091 | 4526 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 27486 | 188 | 0.0095 | 5031 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1519 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 27494 | 197 | 0.0096 | 5087 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 7459 | 707 | 0.0107 | 11278 | 3/3/3 |
