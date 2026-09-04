# Eval run 20260904T195201Z — full-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 23/23. Regressions vs last committed run: none.

Mean cost per question: 0.0148 USD (x1000 = 14.83 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2027 | 2349 |
| retrieve | 0 | 0 |
| generate | 3090 | 11623 |
| total | 5197 | 13235 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 22 responses: clarity 3.00, care 2.95, language 3.00. Judge cost USD 0.1280.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27564 | 153 | 0.0698 | 4213 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 27548 | 271 | 0.0104 | 5197 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 27558 | 178 | 0.0094 | 4424 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 27552 | 311 | 0.0108 | 6707 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27552 | 306 | 0.0107 | 5925 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7533 | 344 | 0.0217 | 6554 | 3/3/3 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12562 | 641 | 0.0372 | 7978 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 20 | 0.0025 | 2154 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 2027 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27560 | 713 | 0.0148 | 8537 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27540 | 314 | 0.0108 | 5762 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 27546 | 159 | 0.0092 | 4387 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 27566 | 202 | 0.0097 | 4345 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 27546 | 351 | 0.0112 | 6041 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 27550 | 1131 | 0.0190 | 13235 | 3/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4632 | 1358 | 0.0246 | 15933 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 27544 | 272 | 0.0104 | 5783 | 3/2/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 27546 | 150 | 0.0091 | 4278 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 27564 | 191 | 0.0096 | 5112 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1481 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 27572 | 197 | 0.0097 | 4839 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 7537 | 708 | 0.0107 | 11493 | 3/3/3 |
