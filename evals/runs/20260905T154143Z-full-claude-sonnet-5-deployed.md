# Eval run 20260905T154143Z — full-claude-sonnet-5-deployed

Model: "claude-sonnet-5". Questions: 29. Passed: 28/29. Regressions vs last committed run: ['g27'].

Mean cost per question: 0.0128 USD (x1000 = 12.81 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2093 | 2375 |
| retrieve | 0 | 0 |
| generate | 3702 | 9341 |
| total | 5762 | 11463 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 3.00, care 3.00, language 3.00. Judge cost USD 0.1623.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27564 | 140 | 0.0091 | 5019 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 27548 | 252 | 0.0102 | 5349 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 27558 | 186 | 0.0095 | 4148 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 27552 | 345 | 0.0111 | 5708 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27552 | 333 | 0.0110 | 5530 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7533 | 324 | 0.0215 | 5762 | 3/3/3 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12562 | 866 | 0.0395 | 9062 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 1978 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 1840 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27560 | 860 | 0.0163 | 9605 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27540 | 463 | 0.0123 | 7081 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 27546 | 152 | 0.0092 | 4623 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 27566 | 197 | 0.0097 | 4686 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 27546 | 346 | 0.0111 | 5770 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 27550 | 572 | 0.0134 | 8035 | 3/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4632 | 1730 | 0.0283 | 20138 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 27544 | 238 | 0.0100 | 5148 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 27546 | 149 | 0.0091 | 4342 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 27564 | 186 | 0.0095 | 4874 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1908 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 27572 | 202 | 0.0097 | 4408 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 7537 | 815 | 0.0118 | 11354 | 3/3/3 |
| g24 | corpus_wide | PASS |  |  | 1 | 0 | 27554 | 1011 | 0.0178 | 11463 | 3/3/3 |
| g25 | corpus_wide | PASS |  |  | 1 | 0 | 27544 | 687 | 0.0145 | 8405 | 3/3/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 27574 | 602 | 0.0137 | 7279 | 3/3/3 |
| g27 | constraint_list | FAIL | cites_min 2: got 1 |  | 1 | 0 | 3892 | 484 | 0.0140 | 7958 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 3 | 0 | 27546 | 536 | 0.0130 | 8027 | 3/3/3 |
| g29 | corpus_wide_ru | PASS |  |  | 1 | 0 | 27550 | 848 | 0.0161 | 10453 | 3/3/3 |
