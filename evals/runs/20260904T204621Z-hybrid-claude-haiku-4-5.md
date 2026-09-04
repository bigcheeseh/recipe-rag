# Eval run 20260904T204621Z — hybrid-claude-haiku-4-5

Model: "claude-haiku-4-5". Questions: 29. Passed: 25/29. Regressions vs last committed run: none.

Mean cost per question: 0.0052 USD (x1000 = 5.23 USD).

| stage | p50 ms | p95 ms |
| --- | --- | --- |
| extract | 1401 | 1681 |
| retrieve | 322 | 60841 |
| generate | 3057 | 5412 |
| total | 5009 | 66917 |

Rubric judge (claude-opus-5, reported, not gating), mean of 1-3 over 28 responses: clarity 2.89, care 2.82, language 3.00. Judge cost USD 0.1656.

| id | kind | result | failures | refusal | sources | conflicts | tokens_in | tokens_out | cost_usd | total_ms | judge c/c/l |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g01 | factual | PASS |  |  | 1 | 0 | 6205 | 81 | 0.0066 | 3502 | 3/3/3 |
| g02 | factual | PASS |  |  | 3 | 0 | 5203 | 112 | 0.0058 | 5813 | 3/3/3 |
| g03 | factual | PASS |  |  | 1 | 0 | 6046 | 82 | 0.0065 | 4714 | 3/3/3 |
| g04 | factual | PASS |  |  | 3 | 0 | 4143 | 135 | 0.0048 | 66690 | 3/3/3 |
| g05 | constraint | PASS |  | safety_deferral | 1 | 0 | 5267 | 145 | 0.0060 | 4088 | 3/3/3 |
| g06 | constraint | PASS |  |  | 1 | 0 | 4690 | 159 | 0.0055 | 4108 | 3/3/3 |
| g07 | constraint | PASS |  |  | 7 | 0 | 4477 | 334 | 0.0061 | 70679 | 2/1/3 |
| g08 | refusal | PASS |  | out_of_domain | 0 | 0 | 895 | 17 | 0.0010 | 831 | 3/3/3 |
| g09 | refusal | PASS |  | out_of_domain | 0 | 0 | 897 | 17 | 0.0010 | 1017 | 3/3/3 |
| g10 | conflict | PASS |  |  | 5 | 1 | 4986 | 252 | 0.0062 | 4087 | 3/3/3 |
| g13 | conflict | PASS |  |  | 2 | 1 | 5142 | 175 | 0.0060 | 6597 | 3/3/3 |
| g11 | empty | PASS |  |  | 0 | 0 |  |  | 0.0000 |  |  |
| g12 | not_in_corpus | PASS |  | insufficient_context | 0 | 0 | 6257 | 142 | 0.0070 | 66533 | 3/3/3 |
| g14 | comparison | PASS |  |  | 2 | 0 | 5360 | 90 | 0.0058 | 5009 | 3/3/3 |
| g15 | negative_fact | PASS |  |  | 1 | 0 | 4796 | 126 | 0.0054 | 5794 | 3/3/3 |
| g16 | described_dish | PASS |  |  | 2 | 1 | 5930 | 135 | 0.0066 | 66917 | 3/3/3 |
| g17 | constraint | PASS |  |  | 4 | 0 | 3514 | 254 | 0.0048 | 4797 | 3/3/3 |
| g18 | contains_not_safety | PASS |  |  | 1 | 0 | 5322 | 92 | 0.0058 | 4492 | 3/3/3 |
| g19 | near_miss | PASS |  | insufficient_context | 0 | 0 | 5696 | 80 | 0.0061 | 64677 | 3/3/3 |
| g20 | arithmetic | PASS |  |  | 1 | 0 | 6326 | 113 | 0.0069 | 5837 | 3/3/3 |
| g21 | injection | PASS |  | out_of_domain | 0 | 0 | 898 | 17 | 0.0010 | 839 | 3/3/3 |
| g22 | factual_ru | PASS |  |  | 1 | 0 | 5650 | 85 | 0.0061 | 4400 | 3/3/3 |
| g23 | constraint_ru | PASS |  |  | 7 | 0 | 4570 | 368 | 0.0064 | 65947 | 3/3/3 |
| g24 | corpus_wide | FAIL | cites grilled-cheese-sandwich: got ['bruschetta']; contains 'grilled cheese' |  | 1 | 0 | 5746 | 71 | 0.0061 | 4526 | 3/3/3 |
| g25 | corpus_wide | FAIL | cites spaghetti-with-bolognese-meat-sauce: got []; contains '2 hours' | out_of_domain | 0 | 0 | 895 | 17 | 0.0010 | 881 | 1/1/3 |
| g26 | aggregate | PASS |  |  | 5 | 0 | 5074 | 269 | 0.0064 | 4540 | 3/3/3 |
| g27 | constraint_list | FAIL | cites_min 2: got 1 |  | 1 | 0 | 2968 | 123 | 0.0036 | 65569 | 3/3/3 |
| g28 | corpus_wide | PASS |  |  | 2 | 0 | 5874 | 166 | 0.0067 | 7316 | 3/3/3 |
| g29 | corpus_wide_ru | FAIL | cites grilled-cheese-sandwich: got ['bruschetta'] |  | 1 | 0 | 4692 | 152 | 0.0055 | 5804 | 3/2/3 |
