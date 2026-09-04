# Eval run 20260904T194849Z — hybrid-claude-sonnet-5

Model: "claude-sonnet-5". Questions: 23. Passed: 23/23. Regressions vs last committed run: none.

Mean cost per question: 0.0153 USD (x1000 = 15.35 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1945 | 2390 |
| retrieve | 326 | 60897 |
| generate | 2824 | 9273 |
| total | 5546 | 69295 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 22 responses: clarity 2.95, care 3.00, language 3.00. Judge cost USD 0.1260.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 7497 | 146 | 0.0165 | 4353 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 6801 | 303 | 0.0166 | 5495 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 8008 | 178 | 0.0178 | 4463 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 5482 | 298 | 0.0139 | 66785 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 6960 | 280 | 0.0167 | 6028 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 6155 | 454 | 0.0169 | 7027 | 3/3/3 |
| g07 | constraint | PASS |  |  | 3 | 0 | 6039 | 245 | 0.0145 | 66028 | 3/3/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 20 | 0.0025 | 1903 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 1943 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 6774 | 630 | 0.0198 | 7570 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 6815 | 497 | 0.0186 | 7344 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 8237 | 151 | 0.0180 | 65859 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 6969 | 153 | 0.0155 | 5165 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 6333 | 258 | 0.0152 | 5546 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 8071 | 580 | 0.0219 | 69295 | 2/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 4632 | 1443 | 0.0237 | 17984 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 7003 | 187 | 0.0159 | 5204 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 6983 | 152 | 0.0155 | 65184 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 8238 | 173 | 0.0182 | 4875 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1627 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 6810 | 175 | 0.0154 | 5485 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 6177 | 710 | 0.0195 | 72484 | 3/3/3 |
