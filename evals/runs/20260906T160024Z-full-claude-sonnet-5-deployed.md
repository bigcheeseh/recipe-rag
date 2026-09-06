# Eval run 20260906T160024Z — full-claude-sonnet-5-deployed

Model: "claude-sonnet-5". Questions: 29. Passed: 29/29. Regressions vs last committed run: none.

Mean cost per question: 0.0159 USD (x1000 = 15.87 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 2137 | 2653 |
| retrieve | 0 | 0 |
| generate | 4013 | 12939 |
| total | 6305 | 15212 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 30115 | 123 | 0.0759 | 6673 |  |
| g02 | factual | PASS |  |  | 3 | 0 | 30099 | 278 | 0.0109 | 4832 |  |
| g03 | factual | PASS |  |  | 1 | 0 | 30109 | 178 | 0.0100 | 4465 |  |
| g04 | factual | PASS |  |  | 3 | 0 | 30103 | 317 | 0.0113 | 5440 |  |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 30103 | 380 | 0.0120 | 6189 |  |
| g06 | constraint | PASS |  |  | 1 | 0 | 8248 | 342 | 0.0234 | 6305 |  |
| g07 | constraint | PASS |  |  | 16 | 0 | 13847 | 991 | 0.0439 | 10592 |  |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 1158 | 19 | 0.0025 | 1881 |  |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 1160 | 20 | 0.0025 | 1939 |  |
| g10 | conflict | PASS |  |  | 5 | 1 | 30111 | 624 | 0.0144 | 7066 |  |
| g13 | conflict | PASS |  |  | 2 | 1 | 30091 | 426 | 0.0124 | 6397 |  |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 30097 | 132 | 0.0095 | 4133 |  |
| g14 | comparison | PASS |  |  | 2 | 0 | 30117 | 232 | 0.0105 | 4643 |  |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 30097 | 309 | 0.0112 | 5142 |  |
| g16 | described_dish | PASS |  |  | 2 | 0 | 30101 | 862 | 0.0168 | 10583 |  |
| g17 | constraint | PASS |  |  | 5 | 0 | 5015 | 1394 | 0.0259 | 15827 |  |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 30095 | 231 | 0.0105 | 5764 |  |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 30097 | 156 | 0.0097 | 3929 |  |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 30115 | 192 | 0.0101 | 4314 |  |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 1165 | 20 | 0.0025 | 1506 |  |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 30123 | 216 | 0.0104 | 5184 |  |
| g23 | constraint_ru | PASS |  |  | 1 | 0 | 8252 | 580 | 0.0096 | 9849 |  |
| g24 | corpus_wide | PASS |  |  | 1 | 0 | 30105 | 491 | 0.0131 | 6789 |  |
| g25 | corpus_wide | PASS |  |  | 1 | 0 | 30095 | 1585 | 0.0240 | 15212 |  |
| g26 | aggregate | PASS |  |  | 5 | 0 | 30125 | 601 | 0.0142 | 7050 |  |
| g27 | constraint_list | PASS |  |  | 3 | 0 | 4179 | 551 | 0.0154 | 7741 |  |
| g28 | corpus_wide | PASS |  |  | 3 | 0 | 30097 | 459 | 0.0127 | 7285 |  |
| g29 | corpus_wide_ru | PASS |  |  | 1 | 0 | 30101 | 1081 | 0.0190 | 11916 |  |
