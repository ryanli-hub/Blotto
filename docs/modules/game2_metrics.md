# Comparing objectives across opponent populations

## English

Input `scores` is a candidate-by-scenario matrix. Each entry is that candidate's expected ranking reward against one opponent population, estimated from simulated games. `weights` assigns importance to the scenarios and is normalized to sum to one. Zero-weight scenarios are excluded.

`summarize_scores` reports five quantities for every candidate:

| Metric | Meaning | Preferred direction |
|---|---|---|
| `weighted_mean` | Average score using the scenario weights | Higher |
| `minimum` | Lowest score across included scenarios | Higher |
| `lower_tail_mean` | Average score in the worst weighted fraction of scenarios | Higher |
| `maximum_regret` | Largest reference score minus candidate score | Lower |
| `mean_regret` | Weighted average of those reference gaps | Lower |

For scores `2, 6, 9` with weights `10%, 30%, 60%`, the worst 25% includes all 10% at score 2 and 15% at score 6. Its tail mean is `(0.10 × 2 + 0.15 × 6) / 0.25 = 4.4`. The code sorts scores and takes exactly the requested probability mass, including a fractional boundary scenario. These metrics describe changes in **expected reward across opponent populations**. A candidate's game-by-game reward variance is a separate quantity.

References default to the highest score among searched candidates in each scenario. Supplied `reference_scores` keep another fixed benchmark. Thus default regret is relative to the searched candidate set. With the same weights and fixed references, mean regret equals the weighted reference score minus the candidate's weighted mean. Minimizing mean regret therefore gives the same ranking as maximizing mean score.

`select_by_objective` returns a candidate index for mean score, minimum score, tail mean, and maximum regret. `mean_with_tail_guard` maximizes mean score subject to a tail mean within `tail_tolerance` of the best tail mean; the default tolerance is 0.25 points. Exact ties retain the first candidate. The minimum and maximum regret depend on which scenarios have positive weight; changing their positive weights affects the mean and tail metrics.

`pareto_indices(means, tails)` retains candidates for which no other candidate is at least as good in both metrics and strictly better in one. Exact duplicate metric pairs are retained. Sorting makes this step `O(N log N)` for `N` candidates. Computing all summaries costs `O(N × S log S)` for `S` scenarios.

## 中文

输入 `scores` 是“候选 × 场景”矩阵。每个元素表示该候选面对某一对手人群时的期望名次奖励，由模拟对局估计。`weights` 指定各场景的权重，代码将其归一化为总和一，并排除权重为零的场景。

`summarize_scores` 为每个候选计算五项指标：

| 指标 | 含义 | 选择方向 |
|---|---|---|
| `weighted_mean` | 按场景权重计算的平均得分 | 越高越好 |
| `minimum` | 所含场景中的最低得分 | 越高越好 |
| `lower_tail_mean` | 最差一定比例场景中的加权平均得分 | 越高越好 |
| `maximum_regret` | 参考得分减去候选得分的最大差距 | 越低越好 |
| `mean_regret` | 上述差距的加权平均 | 越低越好 |

例如得分为 `2、6、9`，权重为 `10%、30%、60%`。最差 25% 包括得 2 分的全部 10%，再取出得 6 分场景中的 15%。尾部均值是 `(0.10 × 2 + 0.15 × 6) / 0.25 = 4.4`。代码排序后精确取出所需概率质量，允许只使用边界场景的一部分。这些指标衡量**对手人群变化时，期望得分的变化**；单场名次奖励的波动是另一个量。

默认参考值是每个场景中搜索过的候选最高分，也可用 `reference_scores` 提供固定基准。因此默认 regret 相对于已搜索的候选集计算。在场景权重与参考值相同时，平均 regret 等于参考值的加权平均减去候选的加权平均得分。所以最小化平均 regret 与最大化平均得分的排序相同。

`select_by_objective` 分别按平均分、最低分、尾部均值和最大 regret 返回一个候选编号。`mean_with_tail_guard` 要求尾部均值与最优尾部均值的差距不超过 `tail_tolerance`，再最大化平均分；默认容许差距为 0.25 分。指标完全并列时保留第一个候选。最低分与最大 regret 取决于哪些场景具有正权重；改变正权重大小会影响平均值和尾部指标。

`pareto_indices(means, tails)` 保留满足以下条件的候选：没有另一个候选在两项指标上都不差、且至少一项更好。两项指标完全相同的候选均保留。排序使该步骤对 `N` 个候选的复杂度为 `O(N log N)`。计算全部摘要对 `S` 个场景的复杂度为 `O(N × S log S)`。
