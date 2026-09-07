# Eval run 20260907T170625Z — full-claude-sonnet-5-render

Model: "claude-sonnet-5". Questions: 29. Passed: 29/29. Regressions vs last committed run: none.

Mean cost per question: 0.0163 USD (x1000 = 16.29 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2030 | 2381 |
| retrieve | 0 | 0 |
| generate | 3874 | 13256 |
| total | 5933 | 14769 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 3.00, care 2.89, language 2.96. Judge cost USD 0.1714.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 30115 | 129 | 0.0760 | 4789 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 30099 | 311 | 0.0113 | 5438 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 30109 | 177 | 0.0099 | 5351 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 30103 | 280 | 0.0110 | 5305 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 30103 | 300 | 0.0112 | 6071 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 8248 | 443 | 0.0245 | 6896 | 3/3/3 |
| g07 | constraint | PASS |  |  | 16 | 0 | 13847 | 2240 | 0.0564 | 20417 | 3/2/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 1894 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 19 | 0.0025 | 2000 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 30111 | 739 | 0.0156 | 8213 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 30091 | 404 | 0.0122 | 5933 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 30097 | 147 | 0.0096 | 4637 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 30117 | 239 | 0.0106 | 4881 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 30097 | 284 | 0.0110 | 5498 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 1 | 30101 | 1394 | 0.0221 | 14769 | 3/2/3 |
| g17 | constraint | PASS |  |  | 5 | 0 | 5015 | 1033 | 0.0223 | 11638 | 3/2/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 30095 | 222 | 0.0104 | 5268 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 30097 | 157 | 0.0097 | 4378 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 30115 | 186 | 0.0100 | 4594 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1269 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 30123 | 136 | 0.0096 | 4217 | 3/3/2 |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 8252 | 1011 | 0.0139 | 13064 | 3/3/3 |
| g24 | corpus_wide | PASS |  |  | 1 | 0 | 30105 | 827 | 0.0164 | 10437 | 3/3/3 |
| g25 | corpus_wide | PASS |  |  | 3 | 0 | 30095 | 1075 | 0.0189 | 10702 | 3/3/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 30125 | 608 | 0.0143 | 7897 | 3/3/3 |
| g27 | constraint_list | PASS |  |  | 3 | 0 | 4179 | 519 | 0.0150 | 7206 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 3 | 0 | 30097 | 609 | 0.0142 | 8498 | 3/3/3 |
| g29 | corpus_wide_ru | PASS |  |  | 1 | 0 | 30101 | 433 | 0.0125 | 6707 | 3/3/3 |
