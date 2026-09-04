# Eval run 20260904T193206Z — hybrid-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 22/23. Regressions vs last committed run: ['g12'].

Mean cost per question: 0.0148 USD (x1000 = 14.83 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1958 | 2284 |
| retrieve | 335 | 60861 |
| generate | 2691 | 7383 |
| total | 5369 | 67210 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 22 responses: clarity 3.00, care 2.95, language 2.95. Judge cost USD 0.1284.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 7419 | 129 | 0.0161 | 4792 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 6723 | 253 | 0.0160 | 5071 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 7930 | 178 | 0.0176 | 4276 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 5404 | 263 | 0.0134 | 66082 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 6882 | 253 | 0.0163 | 5844 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 6077 | 393 | 0.0161 | 6224 | 3/3/3 |
| g07 | constraint | PASS |  |  | 3 | 0 | 5961 | 266 | 0.0146 | 66078 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 2071 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 1887 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 6696 | 657 | 0.0200 | 8210 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 6737 | 330 | 0.0168 | 5896 | 3/3/2 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | FAIL | refusal insufficient_context: got out_of_domain | out_of_domain | 0 | 0 | 8159 | 131 | 0.0176 | 65431 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 6891 | 201 | 0.0158 | 5044 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 6255 | 265 | 0.0152 | 5369 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 8028 | 387 | 0.0199 | 67210 | 3/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4554 | 1203 | 0.0211 | 13644 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 6925 | 151 | 0.0154 | 4982 | 3/2/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 6905 | 150 | 0.0153 | 64895 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 8160 | 178 | 0.0181 | 5010 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1341 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 6732 | 176 | 0.0152 | 4727 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 3 | 0 | 6099 | 597 | 0.0182 | 70249 | 3/3/3 |
