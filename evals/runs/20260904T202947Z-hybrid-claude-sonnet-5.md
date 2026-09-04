# Eval run 20260904T202947Z — hybrid-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 29. Passed: 26/29. Regressions vs last committed run: none.

Mean cost per question: 0.0169 USD (x1000 = 16.86 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2068 | 2386 |
| retrieve | 321 | 60810 |
| generate | 4035 | 8317 |
| total | 8652 | 67378 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 2.96, care 3.00, language 3.00. Judge cost USD 0.1630.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 7497 | 147 | 0.0165 | 4437 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 6801 | 270 | 0.0163 | 5504 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 8008 | 177 | 0.0178 | 4246 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 5482 | 234 | 0.0133 | 65605 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 6960 | 292 | 0.0168 | 7009 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 6155 | 360 | 0.0159 | 6101 | 3/3/3 |
| g07 | constraint | PASS |  |  | 3 | 0 | 6039 | 324 | 0.0153 | 67378 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 2048 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 1887 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 6694 | 644 | 0.0198 | 8652 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 6815 | 348 | 0.0171 | 6424 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 8237 | 139 | 0.0179 | 65616 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 6969 | 202 | 0.0160 | 4964 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 6333 | 261 | 0.0153 | 5543 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 7918 | 623 | 0.0221 | 69568 | 2/3/3 |
| g17 | constraint | PASS |  | safety_deferral | 4 | 0 | 4632 | 3298 | 0.0422 | 33943 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 7003 | 247 | 0.0165 | 5269 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 6983 | 161 | 0.0156 | 25331 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 8238 | 190 | 0.0184 | 5183 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1460 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 6810 | 174 | 0.0154 | 25529 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 6177 | 623 | 0.0186 | 31245 | 3/3/3 |
| g24 | corpus_wide | FAIL | cites grilled-cheese-sandwich: got ['bruschetta', 'chocolate-chip-cookies-i', 'risotto-alla-milanese']; contains 'grilled cheese' |  | 3 | 0 | 7284 | 679 | 0.0214 | 8563 | 3/3/3 |
| g25 | corpus_wide | FAIL | cites spaghetti-with-bolognese-meat-sauce: got ['bolognese-sauce', 'banana-bread-ii', 'risotto-alla-milanese', 'banana-bread-i', 'chocolate-chip-cookies-i']; contains '2 hours' |  | 5 | 0 | 7976 | 442 | 0.0204 | 26980 | 3/3/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 6788 | 618 | 0.0198 | 28118 | 3/3/3 |
| g27 | constraint_list | PASS |  |  | 2 | 0 | 3892 | 770 | 0.0155 | 10342 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 2 | 0 | 7663 | 461 | 0.0199 | 27496 | 3/3/3 |
| g29 | corpus_wide_ru | FAIL | cites grilled-cheese-sandwich: got ['bruschetta', 'chocolate-chip-cookies-i', 'risotto-alla-milanese'] |  | 3 | 0 | 7784 | 539 | 0.0210 | 30041 | 3/3/3 |
