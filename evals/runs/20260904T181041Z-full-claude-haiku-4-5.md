# Eval run 20260904T181041Z — full-claude-haiku-4-5

Model: "claude-haiku-4-5". Questions: 23. Passed: 23/23. Regressions vs last committed run: none.

Mean cost per question: 0.0049 USD (x1000 = 4.90 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 922 | 1717 |
| retrieve | 0 | 0 |
| generate | 2804 | 6007 |
| total | 4032 | 7576 |

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 20668 | 77 | 0.0260 | 2937 |
| g02 | factual | PASS |  |  | 3 | 0 | 20654 | 175 | 0.0038 | 3276 |
| g03 | factual | PASS |  |  | 1 | 0 | 20662 | 104 | 0.0034 | 4288 |
| g04 | factual | PASS |  |  | 3 | 0 | 20656 | 153 | 0.0037 | 5644 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 20656 | 193 | 0.0039 | 4618 |
| g06 | constraint | PASS |  |  | 1 | 0 | 5659 | 153 | 0.0076 | 3673 |
| g07 | constraint | PASS |  |  | 10 | 0 | 9301 | 444 | 0.0136 | 4619 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 895 | 17 | 0.0010 | 840 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 897 | 17 | 0.0010 | 1085 |
| g10 | conflict | PASS |  |  | 5 | 2 | 20660 | 306 | 0.0044 | 3711 |
| g13 | conflict | PASS |  |  | 2 | 1 | 20646 | 168 | 0.0037 | 5845 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 20648 | 104 | 0.0034 | 4627 |
| g14 | comparison | PASS |  |  | 2 | 0 | 20664 | 92 | 0.0034 | 4942 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 20648 | 124 | 0.0035 | 3002 |
| g16 | described_dish | PASS |  |  | 2 | 0 | 20654 | 143 | 0.0036 | 4437 |
| g17 | constraint | PASS |  |  | 4 | 0 | 3421 | 260 | 0.0047 | 7576 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 20648 | 96 | 0.0034 | 4152 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 20656 | 85 | 0.0033 | 2620 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 20668 | 99 | 0.0034 | 3107 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 898 | 17 | 0.0010 | 896 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 20678 | 92 | 0.0034 | 4032 |
| g23 | constraint_ru | PASS |  |  | 2 | 0 | 5671 | 282 | 0.0028 | 8568 |
