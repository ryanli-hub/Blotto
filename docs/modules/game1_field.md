# Game 1: a coherent field of finite reasoning

## English

`build_field(seed, samples=3000, responses_per_order=8, fresh=False)` builds **80 population scenarios**. `scenarios[name]` is a `5 × 101` marginal table for exact DP scoring. `models` retains legal full allocations and weights for H, C, T, and every S level. Each player spends exactly 100 soldiers.

### Player types and scenario families

H equally mixes the existing three simple templates. C chooses two to four main castles, with small bids elsewhere. T includes the exact original proposals **2/16/1/37/44** and **1/14/1/37/47**, together with their nearby 2/4/5-focused variations. S forms beliefs about these populations and chooses a strong response before submission.

| Family | Training H/C/T/S | Fresh H/C/T/S | Training/fresh castle-5 selection multiplier for C |
|---|---|---|---|
| Concentration | 2/58/10/30% | 2/53/12/33% | 1.50 / 1.35 |
| Calculation | 2/28/10/60% | 2/23/12/63% | 1.00 / 0.90 |
| Original ideas | 2/28/35/35% | 2/28/30/40% | 1.00 / 1.10 |
| T absent | 2/48/0/50% | 2/43/0/55% | 1.00 / 1.00 |
| Fifth-castle avoidance | 2/43/10/45% | 2/38/12/48% | 0.45 / 0.35 |

Each family has low and raised C bid habits, narrow and diverse S responses, two H shares, and two S depth mixtures. Training H shares are **0% and 5%**; fresh shares are **1% and 4%**. Adjust C to offset the change from the table's 2% H. Every family has weight 20%, and each of its four binary factors splits equally. Thus **5 × 2 × 2 × 2 × 2 = 80**, with equal scenario weights summing to one. These scenario weights aggregate different possible populations; the table percentages describe players within one population.

### C and T construction

`considered_population` supplies C using these settings. Probability entries refer to bids beginning at zero, so leading zeros exclude those bids.

| Setting | Training | Fresh |
|---|---|---|
| Main-castle counts 2/3/4 | 25/50/25% | 20/50/30% |
| Low secondary-bid probabilities | 10/45/35/10% on 0/1/2/3 | 5/20/30/25/15/5% on 0/1/2/3/4/5 |
| Raised secondary-bid probabilities | 5/10/20/15/35/15% on 0/1/2/3/5/10 | 3/7/12/15/10/20/10/8/10/5% on 0/1/2/3/4/5/6/8/10/12 |
| Equal initial shares / log-noise / five-soldier rounding / one-two soldier transfer | 35% / 0.25 / 35% / 40% | 50% / 0.35 / 60% / 70% |

Training T assigns 30% to exact proposals and 70% to an equal mixture of the existing `local` and `broad` cohorts. Fresh T assigns 15% to exact proposals and 85% to `shifted` and `overbid` cohorts, equally weighted. Across the five families, the teammate's share of the exact proposals is 50/50/75/50/25% in training and 40/60/25/50/80% fresh. T's total population share remains zero in the T-absent family.

### S: fixed H/T shares and varied response methods

For each bank, generate four levels. Each level mixes three beliefs equally. A belief predicts

\[
Q=hH+tT+(1-h-t)[(1-r)C+rS_{\mathrm{earlier}}].
\]

Level 1 uses `r=0`. Higher levels use an equal mixture of completed earlier levels. **H and T keep their specified shares** when earlier responders enter; the remaining share is divided between C and earlier S.

C's predicted allocation distribution also varies: the first belief uses the family's other bid habit, the second uses the actual habit, and the third mixes both equally. The raised bank includes round-number bids of 5 and 10, with 8 and 12 added in fresh tests, to test whether our small bids still cross opponents' thresholds.

| Belief settings, in corresponding order | Training | Fresh |
|---|---|---|
| H share | 0/2/5% | 1/3/5% |
| Offset from the family's T share | −10/0/+10 percentage points | −8/+3/+12 percentage points |
| Earlier S fraction of the remaining population | 40/60/80% | 45/65/85% |
| Teammate's share of exact T | 25/50/75% | 15/55/85% |

T beliefs are clipped to 0% through 50%. Each belief uses four equally weighted response samples, normally eight allocations per sample:

- **Narrow, training:** score gaps of at most 0.05/0.10/0.05/0.10 points. The first two samples use the original castle order; the other two use random orders.
- **Diverse, training:** gaps of at most 0.30/0.50/0.30/0.50, all with random orders.
- **Fresh:** every sample uses a random order; narrow gaps are at most 0.08, and diverse gaps are at most 0.35/0.60/0.35/0.60.

`near_best_responses` samples during DP backtracking, so castle order affects which strong allocations it selects. `response_sample(marginal, rng, count_per_order=8, slack=0.10, orders=None)` permutes **both marginal rows and castle values**, samples, and restores the original columns. It returns allocations and diagnostics. `orders=None` draws four random orders. Every restored allocation is checked against the original game's exact DP optimum; its total score gap must stay within `slack`. These are bounded score-loss models with different tie-selection habits.

Training's three-level mixture uses 15/45/40/0%; its four-level mixture uses 5/20/35/40%. Fresh weights are 10/40/50/0% and 0/15/35/50%. S is generated once per bank and reused when H shares or depth mixtures change.

### Outputs and interpretation

The return value contains `scenarios`, `weights`, `metadata`, `models`, and `parameters`. Metadata records each world's family, bank, actual shares, response style, depth weights, and evaluation weight. Models retain C parameters, sampling seeds and orders, legal response allocations, and verified score gaps. `distribution` and `mix_distributions` preserve both joint supports and their marginals.

Expected scores and best responses are exact for the specified marginal tables. Different seeds change the generated populations. The original Game 1 equilibrium E remains a separate mathematical benchmark for the experiment runner.

## 中文

`build_field(seed, samples=3000, responses_per_order=8, fresh=False)` 建立 **80 个人群场景**。`scenarios[name]` 是用于精确 DP 计分的 `5 × 101` 边际概率表。`models` 保留 H、C、T 和每层 S 的完整合法配兵及权重。每个玩家都恰好使用 100 名士兵。

### 玩家类型与场景组合

H 等比例使用已有的三个简单模板。C 集中争夺两到四城，其他城小额出价。T 包含原始方案 **2/16/1/37/44**、**1/14/1/37/47**，以及相近的第 2/4/5 城集中方案。S 在提交前预测这些人群，并选择强回应。

| 组合 | 训练 H/C/T/S | 新检验 H/C/T/S | C 选择第五城的训练/新检验权重乘数 |
|---|---|---|---|
| 集中型较多 | 2/58/10/30% | 2/53/12/33% | 1.50 / 1.35 |
| 计算型较多 | 2/28/10/60% | 2/23/12/63% | 1.00 / 0.90 |
| 原始想法热门 | 2/28/35/35% | 2/28/30/40% | 1.00 / 1.10 |
| 没有 T | 2/48/0/50% | 2/43/0/55% | 1.00 / 1.00 |
| 回避第五城 | 2/43/10/45% | 2/38/12/48% | 0.45 / 0.35 |

每个组合交叉两种 C 出价习惯、两种 S 回应方式、两个 H 比例和两种 S 深度。训练 H 为 **0% 或 5%**；新检验为 **1% 或 4%**。通过调整 C，抵消相对表中 2% H 的变化。每组合权重为 20%，四个二元因素各占一半，所以 **5 × 2 × 2 × 2 × 2 = 80**，场景等权且总和为一。场景权重用于汇总不同可能人群；表内百分比表示一个人群内部的玩家构成。

### C 与 T 怎样生成？

`considered_population` 按下表生成 C。概率数组从出价零开始，前置零概率用于排除对应出价。

| 设置 | 训练 | 新检验 |
|---|---|---|
| 主攻城数 2/3/4 | 25/50/25% | 20/50/30% |
| 较低小额出价 | 0/1/2/3，概率 10/45/35/10% | 0/1/2/3/4/5，概率 5/20/30/25/15/5% |
| 较高小额出价 | 0/1/2/3/5/10，概率 5/10/20/15/35/15% | 0/1/2/3/4/5/6/8/10/12，概率 3/7/12/15/10/20/10/8/10/5% |
| 初始均分概率 / 对数扰动 / 五人取整概率 / 调动一两人概率 | 35% / 0.25 / 35% / 40% | 50% / 0.35 / 60% / 70% |

训练 T 中 30% 使用精确原始方案，70% 来自等比例的 `local`、`broad` 人群。新检验改为 15% 精确原方案、85% 等比例的 `shifted`、`overbid` 人群。按五个组合的顺序，队友方案占精确原方案的比例在训练中为 50/50/75/50/25%，新检验为 40/60/25/50/80%。在“没有 T”组合中，T 的实际人数始终为零。

### S：保留 H/T 比例，改变回应方式

每个基础人群生成四层，每层的三种信念等权。预测公式为

\[
Q=hH+tT+(1-h-t)[(1-r)C+rS_{\mathrm{earlier}}].
\]

第一层令 `r=0`；更高层将此前各层等权混合。**加入此前的反制者时，H、T 的预测人数比例保持不变**，只将剩余人数在 C 和此前 S 之间分配。

对 C 配兵方式的预测也有差异：第一种信念采用同一组合的另一种出价习惯，第二种采用实际习惯，第三种将两者等权混合。较高出价包含 5 和 10 这些整数门槛，新检验还加入 8 和 12，用来检查我们的小额出价能否继续跨过对手。

| 三种信念的对应设置 | 训练 | 新检验 |
|---|---|---|
| H 比例 | 0/2/5% | 1/3/5% |
| 相对该组合 T 比例的变化 | −10/0/+10 个百分点 | −8/+3/+12 个百分点 |
| 此前 S 占剩余人数的比例 | 40/60/80% | 45/65/85% |
| 队友方案占精确 T 的比例 | 25/50/75% | 15/55/85% |

T 的信念比例限制在 0% 至 50%。每种信念都使用四组等权回应样本，默认每组八个配兵：

- **训练时较精确：** 与最优分数的差距分别不超过 0.05/0.10/0.05/0.10。前两组按原城堡顺序抽样，后两组随机打乱顺序。
- **训练时较分散：** 差距分别不超过 0.30/0.50/0.30/0.50，全部使用随机顺序。
- **新检验：** 所有组都使用随机顺序；较精确的差距上限为 0.08，较分散的上限为 0.35/0.60/0.35/0.60。

`near_best_responses` 在 DP 回溯时抽样，因此城堡顺序会影响选出哪些强方案。`response_sample(marginal, rng, count_per_order=8, slack=0.10, orders=None)` 同时重排**边际概率行与城堡价值**，抽样后恢复原列顺序，返回配兵与检查记录。`orders=None` 随机生成四种顺序。每个恢复后的配兵都与原博弈的精确 DP 最优分数核对，总差距必须不超过 `slack`。这表示允许不同程度的决策误差，并改变强方案之间的选择习惯。

训练三层权重为 15/45/40/0%，四层为 5/20/35/40%；新检验改为 10/40/50/0% 和 0/15/35/50%。每个基础人群的 S 只生成一次，改变 H 比例或层级混合时直接复用。

### 输出与含义

返回 `scenarios`、`weights`、`metadata`、`models`、`parameters`。元数据记录组合、基础人群、实际人数比例、回应方式、层级权重和场景权重。模型保留 C 参数、抽样种子和城堡顺序、合法回应配兵，以及核对后的分数差距。`distribution`、`mix_distributions` 同时保留完整支持向量与边际概率。

对于给定的边际表，期望得分和最佳回应均可精确计算。改变种子会改变生成的人群。原始 Game 1 的均衡 E 由实验入口单独作为数学基准。
