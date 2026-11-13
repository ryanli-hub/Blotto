> Historical report / 历史报告：this report and its PDF preserve an earlier recommendation. For the current reviewed choice, see the [final Game 1 report](../team_update.md). 本文及其 PDF 保留早期建议，当前最终判断见链接中的报告。

**Submit: 8 / 9 / 10 / 11 / 62.** The numbers allocate our 100 soldiers to castles worth 1, 2, 3, 4, and 5 points. Our result is the average castle points won across opponents; ties split points.

### Who did we model?

- **H: simple rules.** Equal spending or spending in proportion to castle value. We tested shares up to 15%.
- **C: concentrated spending.** Focus on two to four castles, with small bids elsewhere. We varied their preferred castles and bid sizes.
- **S: strategic responders.** Predict other players' cho ices and think one to three steps ahead before submitting. We also tested further counterstrategies.
- **T: players like our initial ideas.** Focus on castles 2, 4, and 5, with small bids on 1 and 3. This includes our two original strategies and nearby variations. We tested shares from 10% to 60%.

We also used **E**, a mathematical equilibrium benchmark that randomizes among allocations and limits the best counterstrategy to 7.5 points.

### How did our candidates perform?

The H/C/S/T columns each face only that reference group and show **average scores out of 15; higher is better**. T uses nearby variations of our original strategies.

The last column tests mixed populations with different proportions, bids, and counterstrategies. **Regret** is the best score against that same population minus our score: if the best choice earns 10 and we earn 9.5, regret is 0.5. **Lower maximum regret is better.**

| Allocation               |        H |        C |         S |        T | Maximum regret* |
| ------------------------ | -------: | -------: | --------: | -------: | --------------: |
| 2 / 16 / 1 / 37 / 44     |     8.67 |     8.21 |      4.80 |     6.96 |           5.197 |
| 1 / 14 / 1 / 37 / 47     |     8.67 |     8.21 |      4.89 |     7.59 |           5.456 |
| 2 / 2 / 3 / 39 / 54      |     9.67 |     9.35 |      5.16 |    11.24 |           5.755 |
| 2 / 16 / 10 / 12 / 60    |     7.67 |     8.63 |      9.37 |     9.67 |           3.011 |
| **8 / 9 / 10 / 11 / 62** | **7.33** | **8.72** | **10.62** | **9.00** |       **2.647** |

**\* Mixtures used for this column:** the maximum is taken across **5,624 fresh scenarios**, using the same scenarios for every candidate.

Start with these 12 H/C/S mixtures. Each C/S pair gives percentages of the whole base population; together with H, they sum to 100%.

|    H |    C / S: mix 1 |  C / S: mix 2 |    C / S: mix 3 |
| ---: | --------------: | ------------: | --------------: |
|   0% |       75% / 25% |     50% / 50% |       25% / 75% |
|   5% | 71.25% / 23.75% | 47.5% / 47.5% | 23.75% / 71.25% |
|  10% |   67.5% / 22.5% |     45% / 45% |   22.5% / 67.5% |
|  15% | 63.75% / 21.25% | 42.5% / 42.5% | 21.25% / 63.75% |

- **Add T:** test **0%, 5%, 10%, 15%, 25%, 35%, 40%, 55%, or 60% T**, scaling the base population to fill the remainder.
- **Responses to T:** for each positive T share, either keep the remainder unchanged or replace **15% of it** with new responders. For example, 40% T gives either **40% T + 60% base**, or **40% T + 51% base + 9% responders**.
- **Separate anticipation/counter tests:** **85% base + 15% peers, anticipators, or direct counters**.

We also varied composition within groups: S's levels 1/2/3 used **70/25/5%, 35/45/20%, or 15/35/50%**; four-level tests used **5/15/30/50%**. Selected cases replaced **25% or 50% of S** with shared recommendations. Exact-strategy T cases mixed our two initial strategies **80/20% or 20/80%**.

E is tested separately: all five candidates score **7.50 against E**.

### Why this final choice?

The earlier allocations perform well against some concentrated opponents but lose ground against S. Our final allocation beats many small bids while keeping 62 soldiers for castle 5. Against the tested T variations, it consistently wins castles 1, 3, and 5, totaling **9 points**.

Across the fresh tests, it has the **lowest maximum regret among these candidates**. That makes it our choice for opponents whose strategies and proportions we cannot predict precisely.
