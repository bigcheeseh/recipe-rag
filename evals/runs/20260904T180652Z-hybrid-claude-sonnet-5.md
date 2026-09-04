# Eval run 20260904T180652Z — hybrid-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 23/23. Regressions vs last committed run: none.

Mean cost per question: 0.0129 USD (x1000 = 12.91 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1987 | 2276 |
| retrieve | 315 | 60840 |
| generate | 3121 | 12299 |
| total | 6503 | 67906 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 5210 | 124 | 0.0117 | 4336 |
| g02 | factual | PASS |  |  | 3 | 0 | 5017 | 254 | 0.0126 | 5069 |
| g03 | factual | PASS |  |  | 1 | 0 | 6057 | 139 | 0.0135 | 4287 |
| g04 | factual | PASS |  |  | 3 | 0 | 4493 | 252 | 0.0115 | 65746 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 5405 | 319 | 0.0140 | 6503 |
| g06 | constraint | PASS |  |  | 2 | 0 | 4589 | 408 | 0.0133 | 6963 |
| g07 | constraint | PASS |  |  | 3 | 0 | 4493 | 239 | 0.0114 | 65856 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 20 | 0.0025 | 1939 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 1987 |
| g10 | conflict | PASS |  |  | 5 | 1 | 5000 | 604 | 0.0160 | 7993 |
| g13 | conflict | PASS |  |  | 2 | 1 | 5097 | 386 | 0.0141 | 6632 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 6113 | 190 | 0.0141 | 66257 |
| g14 | comparison | PASS |  |  | 2 | 0 | 5084 | 219 | 0.0124 | 8465 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 5188 | 335 | 0.0137 | 5985 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 5982 | 475 | 0.0167 | 67906 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4499 | 2169 | 0.0307 | 23919 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 5566 | 236 | 0.0135 | 5396 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 5101 | 149 | 0.0117 | 64967 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 6294 | 177 | 0.0144 | 5107 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 19 | 0.0025 | 1421 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 5218 | 128 | 0.0117 | 4946 |
| g23 | constraint_ru | PASS |  |  | 3 | 0 | 4706 | 1030 | 0.0197 | 75248 |
