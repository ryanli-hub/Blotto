# Exact Game 1 objective search

## English

The goal is to compare several decision rules over **every legal allocation**. For 100 soldiers and five castles, there are 4,598,126 choices. Each opponent population is supplied as five marginal bid distributions. Game 1 expected scores add across castles, so these inputs give exact expected scores without sampling matches.

`search_objectives(scenarios, priors, ...)` takes named populations and named vectors of scenario weights in the same order. It normalizes each prior, excludes zero-weight scenarios, and returns the winners and their five metrics. `tail_mass=0.2` means the worst 20% of scenario weight; `guard_0.25` maximizes weighted mean subject to a tail mean within 0.25 points of the globally best tail mean.

1. Compute each castle's expected reward for every possible bid. DP also finds each population's exact best score, providing the regret references.
2. Enumerate all legal allocations in bounded blocks. Score every allocation against every population by adding five table entries.
3. Sort each row of population scores once. Reuse that order for all priors, taking exactly the requested lower-tail weight, including a partial boundary population.
4. Store only each allocation's mean and tail for each prior. Track the best minimum score and smallest maximum regret as the blocks arrive. Priors with the same positive-weight scenarios share those two searches.
5. Select the mean, tail, maximin, minimax-regret, and requested tail-guard winners. Recompute their reported metrics and return the allocations, normalized priors, exact reference scores, and enumeration count.

As an independent check, the weighted-mean winner must match DP applied to the prior-weighted population. Game 1 is linear in the opponent distribution, so averaging populations before optimizing the mean gives the same objective. Tail and minimum objectives still require keeping populations separate.

All feasible allocations are examined. Numerical operations use float64; tail constraints allow a `1e-12` rounding tolerance. Exact numerical ties keep the first enumerated allocation. A supplied tail tolerance is labeled to two decimal places and labels must be distinct.

For `A` allocations, `S` scenarios, and `P` priors, scoring and sorting cost `O(A × S log S + A × P × S)`, with an additional `O(S × 5 × B²)` for the DP references at budget `B`. Persistent storage is `O(A × (5 + 2P))`; chunk workspace is `O(block_size × S)`. At budget 100 and six priors, retained allocations and float64 mean/tail arrays use about 487 MB. Large search arrays are released when the function returns; output contains only selected candidates and summaries.

## 中文

目标是在**全部合法配兵**中比较几种决策规则。100 人、五座城共有 4,598,126 种选择。每个对手人群用五座城各自的出价边际分布表示。Game 1 的期望得分可逐城相加，因此能够精确计算，无须抽样模拟比赛。

`search_objectives(scenarios, priors, ...)` 接收有名称的人群，以及按相同人群顺序排列的场景权重。程序归一化每套权重、排除零权重场景，返回各目标的最优配兵及五项指标。`tail_mass=0.2` 表示最差 20% 的场景权重；`guard_0.25` 要求尾部均值距离全局最高尾部均值不超过 0.25 分，再最大化加权平均。

1. 预先计算每座城在各种出价下的期望收益。DP 同时求出每个人群的精确最优得分，作为 regret 的参考值。
2. 分块枚举所有合法配兵，每个配兵从收益表中取五个数相加，得到各人群下的得分。
3. 对每行的人群得分只排序一次，供所有场景权重重复使用。计算尾部时精确截取所需权重，边界人群可以只取一部分。
4. 只长期保存各配兵在每套权重下的均值和尾部均值。最低分最大、最大 regret 最小的配兵随分块计算更新。正权重场景集合相同的权重方案共享这两项搜索。
5. 选出均值、尾部、最低分、最大 regret 和各尾部限制对应的最优方案，重新计算所选配兵的指标，返回配兵、归一化权重、精确参考分和枚举总数。

额外用 DP 检查加权平均目标：将对手人群按场景权重混合后，DP 的最优得分必须与枚举一致。Game 1 对对手分布是线性的，因此先混合人群再优化均值，目标不变；尾部和最低分目标仍须保留各个人群。

搜索覆盖全部合法配兵。数值计算使用 float64，尾部限制允许 `1e-12` 的舍入误差；数值完全并列时保留先枚举的配兵。尾部容忍度使用两位小数标签，因此标签必须互不相同。

设配兵数为 `A`、场景数为 `S`、权重方案数为 `P`、预算为 `B`，主要计算复杂度为 `O(A × S log S + A × P × S)`，DP 参考值另需 `O(S × 5 × B²)`。长期存储为 `O(A × (5 + 2P))`，分块临时存储为 `O(block_size × S)`。预算 100、六套权重时，配兵以及 float64 均值、尾部数组约占 487 MB。函数返回后释放这些大数组，结果只保留所选候选与摘要。
