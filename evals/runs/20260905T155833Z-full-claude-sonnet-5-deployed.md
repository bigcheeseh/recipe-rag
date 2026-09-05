# Eval run 20260905T155833Z — full-claude-sonnet-5-deployed

Model: "claude-sonnet-5". Questions: 29. Passed: 29/29. Regressions vs last committed run: none.

Mean cost per question: 0.0126 USD (x1000 = 12.61 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2060 | 2435 |
| retrieve | 0 | 0 |
| generate | 3380 | 12522 |
| total | 5517 | 14528 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 3.00, care 2.93, language 3.00. Judge cost USD 0.1681.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 30115 | 123 | 0.0094 | 4507 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 30099 | 308 | 0.0112 | 5437 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 30109 | 165 | 0.0098 | 4795 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 30103 | 412 | 0.0123 | 6210 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 30103 | 352 | 0.0117 | 6112 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 8248 | 423 | 0.0243 | 6823 | 3/3/3 |
| g07 | constraint | PASS |  |  | 16 | 0 | 13847 | 1673 | 0.0216 | 14528 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 20 | 0.0025 | 1908 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 1959 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 30111 | 940 | 0.0176 | 9284 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 30091 | 319 | 0.0113 | 5181 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 30097 | 155 | 0.0097 | 4103 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 30117 | 202 | 0.0102 | 4662 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 30097 | 321 | 0.0114 | 4871 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 1 | 30101 | 1034 | 0.0185 | 10894 | 3/3/3 |
| g17 | constraint | PASS |  |  | 5 | 0 | 5015 | 2016 | 0.0321 | 21631 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 30095 | 204 | 0.0102 | 4759 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 30097 | 160 | 0.0098 | 4211 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 30115 | 187 | 0.0101 | 4927 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 19 | 0.0025 | 1921 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 30123 | 176 | 0.0100 | 4760 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 8252 | 506 | 0.0089 | 8692 | 3/3/3 |
| g24 | corpus_wide | PASS |  |  | 1 | 0 | 30105 | 878 | 0.0169 | 9886 | 3/3/3 |
| g25 | corpus_wide | PASS |  |  | 1 | 0 | 30095 | 900 | 0.0171 | 10418 | 3/3/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 30125 | 565 | 0.0139 | 7433 | 3/3/3 |
| g27 | constraint_list | PASS |  |  | 3 | 0 | 4179 | 292 | 0.0128 | 5517 | 3/2/3 |
| g28 | corpus_wide | PASS |  |  | 3 | 0 | 30097 | 421 | 0.0124 | 7065 | 3/3/3 |
| g29 | corpus_wide_ru | PASS |  |  | 1 | 0 | 30101 | 446 | 0.0126 | 7119 | 3/2/3 |
