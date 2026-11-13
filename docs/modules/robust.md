# `robust.py`

## English

**Goal:** choose one legal allocation with the smallest maximum regret across the supplied populations. For population `s`, DP computes its best attainable score `V_s`. An allocation's regret is `V_s - score_s`. If two populations allow scores 10 and 9, while our allocation scores 9.5 and 8.2, its regrets are 0.5 and 0.8; the objective is 0.8 points.

`allocation_blocks` enumerates every legal five-castle allocation once. It fixes the first two counts, enumerates the next two, and assigns the remaining soldiers to the fifth. Blocks share the first count. A budget of 100 gives **4,598,126** allocations.

`minimax_regret` searches these allocations in five steps:

1. Compute each population's optimum and its five expected-reward rows. `score_allocations` sums the five entries indexed by an allocation.
2. Evaluate a legal initial allocation across every population. Its maximum regret is an attainable upper bound on the optimum. Pass `initial_allocation` to use an existing candidate; otherwise use the first population's best response.
3. Check populations in decreasing order of this initial allocation's regret, so restrictive cases tend to appear early.
4. For each block, maintain each remaining allocation's largest regret so far. Discard an allocation as soon as this exceeds the current best bound. Additional populations can only increase that maximum, so a discarded allocation cannot improve the answer.
5. Update the best allocation from the survivors, then continue to the next block. Floating-point ties within `1e-12` favor lexicographically earlier allocations. Finally compute the chosen allocation's score in every population.

The pruning changes the amount of scoring work, while retaining exhaustive coverage. The output contains the chosen allocation, its maximum regret, all scenario scores and optima, scenario names, and the total number of allocations examined.

### Preserve baseline performance

Optional `score_floors` maps names to `(population_marginals, minimum_score)` pairs. For example, set each minimum to an existing candidate's score minus 0.10. The search then minimizes maximum regret among allocations satisfying every floor. Supply an explicit feasible `initial_allocation`; its regret is a valid upper bound within this restricted set. The program checks this feasibility first, then removes floor-violating allocations before the regret comparisons. Scenario optima used to define regret still come from the complete legal strategy set. The enumeration count includes allocations eliminated by either kind of constraint.

For `S` scenarios, `F` score floors, `K=5` castles, budget `B`, `A=C(B+4,4)` allocations, and largest block size `N`, worst-case time is `O(SKB² + (S+F)KA)`. Working memory is `O(NK + (S+F)K(B+1))`: the search retains reward tables and one block, with no allocation-by-scenario score matrix.

### Why mixture endpoints suffice

Fix two populations `Q` and `T`, and vary the added share `a`. For any fixed candidate `x`, its regret against `(1-a)Q+aT` is the maximum over alternative allocations `z` of

\[
(1-a)[u(z,Q)-u(x,Q)] + a[u(z,T)-u(x,T)].
\]

Each expression is linear in `a`; their maximum is convex. Consequently, the largest regret on `0 ≤ a ≤ 0.15` occurs at an endpoint. Including shares 0 and 15% therefore covers every intermediate share of the same two fixed populations. Regenerating `T` creates a different family to evaluate.

```python
from blotto.opponents import uniform_allocations, independent_soldiers
from blotto.robust import minimax_regret

result = minimax_regret({
    "uniform": uniform_allocations(),
    "independent": independent_soldiers(),
}, initial_allocation=[8, 9, 10, 11, 62])
print(result["allocation"], result["max_regret"])
```

## 中文

**目标：** 在给定人群中，选择最大 regret 最小的固定合法配兵。对人群 `s`，DP 先算出最高可得分 `V_s`，某配兵的 regret 为 `V_s - score_s`。例如，两个人群的最优得分是 10 和 9，我们得 9.5 和 8.2，则 regret 是 0.5 和 0.8，目标值为 0.8 分。

`allocation_blocks` 恰好一次枚举所有合法五城配兵：固定前两个人数，枚举第三、第四个人数，剩余兵力放到第五城。每块共用第一个人数。100 人预算对应 **4,598,126** 个配兵。

`minimax_regret` 按五步搜索：

1. 计算各人群的最高可得分和五行期望收益表。`score_allocations` 按配兵索引五个收益，再求和。
2. 在所有人群中评价一个合法初始配兵。它的最大 regret 是已经能够达到的上界。可用 `initial_allocation` 传入已有候选，否则使用第一个人群的最佳回应。
3. 按初始配兵的 regret 从高到低检查各人群，使较严格的条件优先出现。
4. 对每块中尚未淘汰的配兵，记录已经检查过的人群中的最大 regret。一旦超过当前最好上界，就淘汰该配兵。继续加入人群只能提高最大值，因此被淘汰的配兵无法改善答案。
5. 从剩余配兵中更新当前最好方案，再检查下一块。浮点差距在 `1e-12` 内时，优先选择字典序较小的配兵。最后计算选中方案在所有人群中的得分。

剪枝减少了计分工作量，仍覆盖全部合法配兵。返回值包含选中配兵、最大 regret、各场景得分与最优分、场景名称，以及检查的配兵总数。

### 保留原有场景的表现

可选参数 `score_floors` 将名称映射到 `(人群边际分布, 最低得分)`。例如，将每个人群的最低得分设为已有配兵得分减去 0.10。程序在满足全部最低得分要求的配兵中，最小化最大 regret。此时必须明确传入满足要求的 `initial_allocation`，其 regret 才是受约束可行集中的有效上界。程序先检查该初始方案，再在计算 regret 之前淘汰违反得分下限的配兵。定义 regret 所用的各场景最优分仍从全部合法配兵求出。枚举数量包括因得分下限或 regret 上界被淘汰的配兵。

设场景数为 `S`，得分下限数量为 `F`，城堡数 `K=5`，预算为 `B`，合法配兵数 `A=C(B+4,4)`，最大块大小为 `N`。最坏时间复杂度为 `O(SKB² + (S+F)KA)`，工作内存为 `O(NK + (S+F)K(B+1))`。程序保存收益表和一个配兵块，无须构造所有“配兵 × 场景”得分。

### 为什么混合比例只需检查端点？

固定人群 `Q` 和 `T`，改变加入比例 `a`。对固定配兵 `x`，面对 `(1-a)Q+aT` 的 regret，是对所有替代配兵 `z` 取下面表达式的最大值：

\[
(1-a)[u(z,Q)-u(x,Q)] + a[u(z,T)-u(x,T)].
\]

每个表达式都关于 `a` 线性，其最大值为凸函数。因此，`0 ≤ a ≤ 0.15` 内最大的 regret 位于端点。把 0 和 15% 两个端点纳入搜索，就覆盖了这两个固定人群的全部中间比例。重新生成 `T` 会产生另一组需要评价的人群。

上面的示例先构造两个人群，再传入已有配兵作为初始上界，搜索所有合法配兵并输出最优结果。
