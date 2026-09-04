# Eval run 20260904T203554Z — full-claude-haiku-4-5

Model: "claude-haiku-4-5". Questions: 29. Passed: 26/29. Regressions vs last committed run: none.

Mean cost per question: 0.0046 USD (x1000 = 4.62 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1402 | 1690 |
| retrieve | 0 | 0 |
| generate | 3068 | 5953 |
| total | 4253 | 6942 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 2.86, care 2.71, language 3.00. Judge cost USD 0.1765.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 20761 | 81 | 0.0261 | 4106 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 20747 | 187 | 0.0038 | 3832 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 20755 | 78 | 0.0033 | 3140 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 20749 | 202 | 0.0039 | 4253 | 3/2/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 20749 | 188 | 0.0038 | 6613 | 3/2/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 5752 | 151 | 0.0077 | 3939 | 3/3/3 |
| g07 | constraint | PASS |  |  | 10 | 0 | 9394 | 620 | 0.0146 | 6942 | 3/2/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 895 | 17 | 0.0010 | 797 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 897 | 17 | 0.0010 | 1295 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 20753 | 284 | 0.0043 | 4149 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 20739 | 168 | 0.0037 | 5588 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 20741 | 78 | 0.0033 | 3919 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 20757 | 90 | 0.0034 | 4668 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 20741 | 118 | 0.0035 | 5615 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 1 | 20747 | 162 | 0.0037 | 6254 | 2/2/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 3514 | 336 | 0.0052 | 4807 | 3/2/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 20741 | 96 | 0.0034 | 4281 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 20749 | 86 | 0.0033 | 4718 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 20761 | 104 | 0.0034 | 5127 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 898 | 17 | 0.0010 | 849 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 20771 | 85 | 0.0034 | 3851 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 4 | 0 | 5764 | 379 | 0.0033 | 11247 | 3/3/3 |
| g24 | corpus_wide | FAIL | cites grilled-cheese-sandwich: got ['bruschetta']; contains 'grilled cheese' |  | 1 | 0 | 20747 | 93 | 0.0034 | 3420 | 3/3/3 |
| g25 | corpus_wide | FAIL | cites spaghetti-with-bolognese-meat-sauce: got []; contains '2 hours' | out_of_domain | 0 | 0 | 895 | 17 | 0.0010 | 874 | 1/1/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 20765 | 155 | 0.0037 | 3670 | 3/3/3 |
| g27 | constraint_list | PASS |  |  | 3 | 0 | 2968 | 138 | 0.0037 | 2760 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 4 | 0 | 20739 | 171 | 0.0037 | 4955 | 3/3/3 |
| g29 | corpus_wide_ru | FAIL | cites grilled-cheese-sandwich: got [] | insufficient_context | 0 | 0 | 20757 | 183 | 0.0038 | 4286 | 2/2/3 |
