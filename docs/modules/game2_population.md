# Game 2 populations

## English

`game2_population.py` represents each opponent by a complete five-number allocation and its probability. Keeping the numbers together preserves which castles the same player contests, which determines the final rankings.

1. `population` validates that each vector contains 100 integer soldiers and combines repeated vectors. `mix_populations` applies the chosen group percentages.
2. `baseline_populations` builds H, C, TA, and TB. H equally mixes equal spending, proportional spending, and 50/50 on castles 4/5. The experiment runner sets H's population share.
3. C chooses one, two, or three main castles with probabilities **15%, 65%, 20%**. Single-castle players choose castles 3/4/5 with weights **1/2/4**. For two or three castles, a subset's weight is its total castle value squared. Secondary bids are **0/1/2/3**, with probabilities **50/25/15/10%**. Remaining soldiers use equal or value-proportional shares with multiplicative noise. Some players round to multiples of five or move one to three soldiers across their main castles.
4. TA starts from **0/1/36/0/63**; TB starts from **0/0/49/51/0**. A quarter of the generated rows retain the exact proposal. Others make one to six one-soldier transfers, usually toward the proposal's main castles. Transfers can cancel, so the final exact-proposal probability can exceed 25%.
5. `sample_triples` independently samples three complete opponent vectors for every match. Each draw follows the specified population proportions; a match can contain three players of the same type.

The profiles change one feature of C at a time:

| Profile | Change from `balanced` |
|---|---|
| `fifth_crowded` | Multiply the selection weight of every subset containing castle 5 by 3. |
| `fifth_avoided` | Multiply that weight by 0.25. |
| `small_bids` | Use secondary bids 2/3/4/5/6 with probabilities 25/30/25/15/5%. |

`candidate_pool` searches broadly: all **10,626** allocations on the five-soldier grid, every integer split across any two castles, the two team proposals and other comparison strategies, transfers of up to six soldiers around those anchors, 4,000 rounded Dirichlet draws, and 1,000 generated C allocations. Repeated candidates are removed. The random seed reproduces both populations and candidate vectors.

### Varying concentration and secondary bids

`baseline_populations(..., overrides={...})` accepts C's settings listed above, including `active_count_probabilities`, `small_bids`, `small_bid_probabilities`, and `fifth_weight`. It checks probability vectors and valid integer bids. Omitting overrides preserves the original generated populations exactly.

For controlled comparisons, `concentrated_by_count(samples, seed, profile, small_bids)` separately generates C1, C2, and C3, conditional on choosing one, two, or three main castles. `small_bids="low"` uses 0/1/2/3; `"high"` uses 2/3/4/5/6. Each main-castle count receives its own reproducible random stream. Hold H, TA, and TB fixed from one baseline call while varying these C settings.

The result contains `components=[C1, C2, C3]`, `one_castle_all_in`, and `parameters`. The all-in distribution puts 100 soldiers on castle 3, 4, or 5, with weights **1, 2, and 4 × fifth_weight**. This explicitly includes players who choose maximum concentration. Ordinary C1 can also produce an all-in allocation when every secondary bid is zero.

`concentration_mixture(conditional, one_castle_share=alpha, all_in_fraction=z)` combines:

\[
\alpha[(1-z)C_1+zC_{\mathrm{all\text{-}in}}]
+ (1-\alpha)\frac{13}{17}C_2
+ (1-\alpha)\frac{4}{17}C_3.
\]

Thus `alpha` sets the exact share assigned to the one-main-castle group. The remaining groups keep their original **65:20 = 13:4** ratio. `z` defaults to 0.5 and controls the explicit all-in branch within that group. For example, `alpha=0.30, z=0.50` assigns 15% of C to the explicit all-in branch and 15% to ordinary C1. Reusing the conditional distributions changes mixture weights without resampling their allocations. The main-castle count records the choice made when generating a player; it is separate from counting positive entries in the resulting vector.

### Players focusing on the first three castles

`first_three_population(samples=3000, seed=20261104, secondary="zero")` returns a full allocation distribution with generation settings in `parameters`. These players try to combine the first three castles, worth six points, while avoiding expensive competition elsewhere. Six castle points can beat an opponent holding only castle 5; an opponent holding both castles 4 and 5 would have nine, so complete ranking simulation remains necessary.

The four starting allocations are **33/33/34/0/0**, **17/33/50/0/0**, **15/30/55/0/0**, and **20/25/55/0/0**, with equal weights. Within each secondary-bid branch, 25% follow these anchor proportions exactly, scaled to the remaining budget; 75% add multiplicative noise with log standard deviation 0.20. Half of the noisy draws transfer one soldier between two of the first three castles. Every first-three bid remains positive.

| `secondary` | Probability both last bids are zero | Other secondary bids | First-three variation |
|---|---:|---|---|
| `zero` | 100% | None | Four anchors and noise described above |
| `small` | 50% | Uniform over the 15 nonzero pairs with each bid in 0/1/2/3 | Same four anchors and noise |
| `shifted` | 20% | Uniform over the 35 nonzero pairs with each bid in 0/1/2/3/4/5 | Add anchors 35/40/25 and 25/45/30; six anchor weights are 15/15/20/20/15/15%, and noise increases to 0.35 |

The zero-secondary probabilities are exact mixture weights. Each noisy branch uses `samples` generated rows; repeated allocations are merged. Exact anchor allocations may also occur among noisy draws. The metadata lists anchor weights, secondary pairs, noise, and the count of support vectors with positive bids on all first three castles.

```python
import numpy as np
from blotto.game2_population import baseline_populations, mix_populations, sample_triples

groups = baseline_populations(seed=20261104)
opponents = mix_populations([groups["C"], groups["TA"], groups["TB"]], [0.6, 0.2, 0.2])
triples = sample_triples(opponents, 1000, np.random.default_rng(123))
# triples has shape (1000 matches, 3 opponents, 5 castle bids).
```

## 中文

`game2_population.py` 用完整的五个配兵数字及其概率表示对手。保留完整向量，才能知道同一个人同时争夺哪些城堡，并计算最终排名。

1. `population` 检查每个向量恰好使用 100 名整数士兵，合并重复配兵。`mix_populations` 按指定人数比例混合人群。
2. `baseline_populations` 建立 H、C、TA、TB。H 等比例包含平均分配、按城堡价值分配，以及在第 4/5 城各放 50 人。实验入口设置 H 占总人群的比例。
3. C 以 **15%、65%、20%** 的概率重点争夺一、二、三座城。只争一座城时，第 3/4/5 城的选择权重为 **1/2/4**；争两三座城时，每个组合的权重为城堡总价值的平方。其他城出价 **0/1/2/3**，概率为 **50/25/15/10%**。剩余兵力按均分或价值比例分配，并加入扰动；部分玩家取五的倍数，或在重点城之间转移一至三人。
4. TA 从 **0/1/36/0/63** 出发，TB 从 **0/0/49/51/0** 出发。生成时四分之一保留原方案，其他方案进行一至六次单人转移，通常转向原方案重点争夺的城。转移可能相互抵消，所以最终原方案的占比可能超过 25%。
5. `sample_triples` 为每场比赛独立抽取三个完整配兵。每次抽取都遵循人群比例，因此同一场可能出现三个同类玩家。

不同 profile 每次改变 C 的一个特征：

| Profile | 相对 `balanced` 的变化 |
|---|---|
| `fifth_crowded` | 包含第五城的组合，其选择权重乘以 3。 |
| `fifth_avoided` | 该权重乘以 0.25。 |
| `small_bids` | 其他城改为出价 2/3/4/5/6，概率为 25/30/25/15/5%。 |

`candidate_pool` 广泛生成搜索候选：全部 **10,626** 个五人步长配兵、任意两座城之间的全部整数分配、两个团队方案和其他比较方案、这些方案附近最多六人的转移、4,000 个取整的 Dirichlet 随机配兵，以及 1,000 个 C 配兵。最后删除重复候选。固定随机种子可以复现人群和候选向量。

### 分别改变集中程度与小额出价

`baseline_populations(..., overrides={...})` 接受上述 C 设置，包括 `active_count_probabilities`、`small_bids`、`small_bid_probabilities`、`fifth_weight`，并检查概率向量和整数出价是否合法。不传 overrides 时，生成的原始人群完全保持一致。

做控制变量比较时，`concentrated_by_count(samples, seed, profile, small_bids)` 分别生成 C1、C2、C3，条件是玩家已选择一、二、三座重点城。`small_bids="low"` 使用 0/1/2/3，`"high"` 使用 2/3/4/5/6。每一种重点城数量使用独立、可复现的随机流。改变 C 设置时，H、TA、TB 保留同一次 baseline 调用的结果。

返回值包含 `components=[C1, C2, C3]`、`one_castle_all_in` 和 `parameters`。全投人群将 100 人放到第 3、4 或 5 城，选择权重为 **1、2、4 × fifth_weight**，直接覆盖追求最大集中度的玩家。普通 C1 在其他城都出价零时，也会生成全投方案。

`concentration_mixture(conditional, one_castle_share=alpha, all_in_fraction=z)` 按英文部分的公式混合：`alpha` 精确指定单重点城人群的占比，其余两组保持原来的 **65:20 = 13:4** 比例。`z` 默认为 0.5，表示单重点城人群中进入明确全投分支的比例。例如 `alpha=0.30, z=0.50` 表示 C 中 15% 进入全投分支、15% 使用普通 C1。反复使用同一组条件分布，只改变权重，无需重新抽取配兵。重点城数量记录生成玩家时的选择，与最终配兵中非零数字的数量分别记录。

### 集中争夺前三城的人群

`first_three_population(samples=3000, seed=20261104, secondary="zero")` 返回完整配兵分布，并在 `parameters` 中记录生成设置。这些玩家希望组合价值六分的前三城，避开其他地方的高额竞争。六分能超过只拿第五城的对手；同时拿下第四、第五城的对手却有九分，因此仍要模拟完整排名。

四个起点为 **33/33/34/0/0**、**17/33/50/0/0**、**15/30/55/0/0**、**20/25/55/0/0**，权重相等。在每个次要城出价分支内，25% 按这些起点的比例分配剩余预算；75% 加入对数标准差为 0.20 的乘法扰动。带扰动的配兵中，一半会在前三城之间转移一人。前三城的出价始终为正。

| `secondary` | 后两城同时为零的概率 | 其他后两城出价 | 前三城的变化 |
|---|---:|---|---|
| `zero` | 100% | 无 | 上述四个起点及扰动 |
| `small` | 50% | 后两城各为 0/1/2/3，从除去全零的 15 个组合中等概率选择 | 同样四个起点及扰动 |
| `shifted` | 20% | 后两城各为 0/1/2/3/4/5，从除去全零的 35 个组合中等概率选择 | 增加 35/40/25、25/45/30；六个起点权重为 15/15/20/20/15/15%，扰动提高到 0.35 |

后两城全零的概率通过精确混合权重设置。每个带扰动的分支生成 `samples` 行，随后合并重复配兵。带扰动的分支也可能生成精确起点。元数据列出起点权重、后两城组合、扰动参数，以及前三城都为正的支持向量数量。

上面的例子生成 60% C、20% TA、20% TB 的人群，再抽取 1,000 场比赛的对手。输出形状是 **1,000 场 × 3 个对手 × 5 个城堡出价**。
