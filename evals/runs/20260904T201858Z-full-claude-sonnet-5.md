# Eval run 20260904T201858Z — full-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 29. Passed: 29/29. Regressions vs last committed run: none.

Mean cost per question: 0.0149 USD (x1000 = 14.94 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2062 | 2356 |
| retrieve | 0 | 0 |
| generate | 4245 | 14855 |
| total | 6284 | 16913 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 3.00, care 2.96, language 3.00. Judge cost USD 0.1631.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 27564 | 159 | 0.0699 | 6005 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 27548 | 249 | 0.0101 | 6284 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 27558 | 141 | 0.0091 | 4203 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 27552 | 288 | 0.0105 | 6042 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 27552 | 335 | 0.0110 | 6339 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 7533 | 366 | 0.0219 | 6353 | 3/3/3 |
| g07 | constraint | PASS |  |  | 8 | 0 | 12562 | 520 | 0.0360 | 7422 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 1995 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 1969 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 27560 | 742 | 0.0151 | 8911 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 27540 | 320 | 0.0108 | 5464 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 27546 | 139 | 0.0090 | 4799 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 27566 | 190 | 0.0096 | 4271 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 27546 | 276 | 0.0104 | 4881 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 27550 | 722 | 0.0149 | 9469 | 3/3/3 |
| g17 | constraint | PASS |  | safety_deferral | 5 | 0 | 4632 | 1345 | 0.0244 | 18918 | 3/2/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 27544 | 211 | 0.0097 | 5173 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 27546 | 157 | 0.0092 | 4312 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 27564 | 191 | 0.0096 | 4891 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1600 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 27572 | 206 | 0.0098 | 5511 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 9 | 0 | 7537 | 1337 | 0.0170 | 16913 | 3/3/3 |
| g24 | corpus_wide | PASS |  |  | 1 | 0 | 27554 | 1160 | 0.0193 | 11518 | 3/3/3 |
| g25 | corpus_wide | PASS |  |  | 1 | 0 | 27544 | 633 | 0.0140 | 6883 | 3/3/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 27574 | 549 | 0.0132 | 6850 | 3/3/3 |
| g27 | constraint_list | PASS |  |  | 3 | 0 | 3892 | 783 | 0.0170 | 10410 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 3 | 0 | 27546 | 505 | 0.0127 | 6786 | 3/3/3 |
| g29 | corpus_wide_ru | PASS |  |  | 1 | 0 | 27550 | 886 | 0.0165 | 12198 | 3/3/3 |
