# Game 2: team update

## English

We are looking for **one fixed allocation that earns a high average reward against thoughtful opponents**. Our main task is to model how other students might choose, compare allocations, and check whether the result survives changes to those assumptions.

### 1. What are we trying to win?

Split 100 soldiers across five castles worth 1, 2, 3, 4, and 5 points. Each match has four players. The highest bid wins each castle; tied bids share its points. Total castle points determine the ranking, which pays **9, 4, 2, 0**. Tied ranks share the prizes for those places. The competition averages this reward across many regroupings.

For example, winning castles 1, 2, and 3 gives six castle points. Someone winning castles 4 and 5 gets nine, so we finish second and receive **4 reward points**. We therefore simulate all four players' complete allocations and final rankings.

### 2. Which opponents do we assume?

A **population** is one possible crowd of entrants. Each simulated match draws three opponents from that crowd.

| Type | How they choose |
|---|---|
| **H: simple templates** | Equal or proportional spending, such as `20/20/20/20/20`. We give this group a small share. |
| **C: considered concentration** | Mostly focus on two or three castles, with small bids elsewhere. They vary their targets and adjust bids to beat likely thresholds. |
| **Z: all fifth** | `0/0/0/0/100`. Take or share the five-point castle and hope the other points are divided. |
| **F: first-three focus** | Seek six points from castles 1, 2, and 3, for example `15/30/55/0/0`, with variations in the split and small bids elsewhere. |
| **T: our original ideas** | `0/1/36/0/63`, `0/0/49/51/0`, and nearby variations. |
| **S: calculated responses** | Predict the crowd, search for strong allocations, then consider that others may also have reasoned further. |

S represents analysis **before submission**. We model four reasoning levels and several beliefs about the crowd; most S weight is on levels 2 to 4. Each player ultimately submits one fixed allocation.

Our **core model** tests five possible crowds. At the central H setting, player percentages are:

| Crowd | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| Concentration common | 3 | 32 | 12 | 12 | 15 | 26 |
| Calculation common | 3 | 15 | 12 | 12 | 8 | 50 |
| All fifth common | 3 | 26 | 18 | 8 | 10 | 35 |
| First-three focus common | 3 | 24 | 8 | 22 | 10 | 33 |
| Our original ideas common | 3 | 21 | 8 | 12 | 28 | 28 |

Each row sums to 100%. We also vary H to 1% or 5%, adjusting C, and change small bids and reasoning depth. This produces **90 core test populations**. The five crowds initially receive equal weight when averaging results.

### 3. How do we judge a strategy?

Each population gives us an estimated **average ranking reward**, on the 0 to 9 scale. We compare four quantities:

- **Weighted mean:** average performance across possible populations. This is our main objective.
- **Worst-20% mean:** average performance in the unfavorable 20% of population weight. This protects against mistaken expectations about opponents.
- **Minimum mean:** the lowest population average, identifying the weakest situation.
- **Maximum estimated regret:** the largest gap to a strong strategy searched specifically for each population. If that reference earns 6 and ours earns 5.5, regret is 0.5.

Our rule is: **retain candidates whose worst-20% mean is within 0.25 points of the best candidate on that metric, then maximize weighted mean**. The minimum and maximum regret help reveal weaknesses; a single unusual population can dominate either measure.

The worst 20% refers to possible **populations**, each already averaged over many matches. It does not mean the worst 20% of individual matches.

### 4. What have we run, and what did we find?

1. **Search:** compare 24,402 allocations across 90 training populations, including all 5,151 allocations confined to castles 1 to 3. Retain 19 candidates for further comparison.
2. **Fresh core tests:** regenerate 90 populations with changed shares, bids, and calculated responses. Run **200,000 new matches per population**.
3. **Broader checks:** add 36 populations with fewer Z/F players, including no dedicated F group; add 18 cohort/copy/counterstrategy tests; revisit 258 earlier populations. Each uses 50,000 new matches.

The broader checks vary Z across **1/5/15%** and F across **0/10/20%**, with two bid habits and two reasoning mixtures. S is recalculated for each Z/F/bid combination. F=0 removes the dedicated F group; C and S can still choose similar allocations.

The table compares two ways of weighting the results: **core** uses the 90 core populations; **expanded** gives half the weight to that core and half to the 12 F-absent populations. Higher is better in every score column.

| Allocation | Core mean | Core worst-20% | Expanded mean | Expanded worst-20% |
|---|---:|---:|---:|---:|
| Teammate: `0/1/36/0/63` | 3.734 | 3.020 | 3.309 | 2.374 |
| Original: `0/0/49/51/0` | 2.790 | 2.311 | 2.859 | 2.439 |
| All fifth: `0/0/0/0/100` | 4.347 | 3.787 | 4.491 | 3.872 |
| Round 2: `16/17/54/8/5` | 4.977 | 4.188 | 4.659 | 3.604 |
| First-three candidate: `8/36/56/0/0` | 5.177 | 4.418 | 4.686 | 3.215 |
| **Core candidate: `10/15/59/5/11`** | **5.707** | **4.902** | 5.067 | 3.612 |
| **Broader-coverage candidate: `8/15/62/5/10`** | 5.539 | 4.686 | **5.100** | **4.130** |

Read the last two rows together: widening coverage changes which candidate leads. Within the core, `10/15/59/5/11` also has a minimum population mean of **4.515** and maximum estimated regret of **1.423**.

Both leading candidates put about 60 soldiers on castle 3 and use smaller bids to collect extra points elsewhere. Those extra points can move them above opponents who win only the five-point castle.

### 5. What is our current choice?

**Keep `8/15/62/5/10` as the working candidate for broader coverage, alongside `10/15/59/5/11` for the original core model.** In the expanded comparison, the former improves mean reward from **5.067 to 5.100** and worst-20% performance from **3.612 to 4.130**.

The extra coverage matters: with Z=1% and F=0%, the core candidate averages **4.155**, while all fifth averages **5.134**, across two bid habits and two reasoning mixtures. A strategy's advantage can change when these groups are rare.

The two leading allocations are selected from our 19 candidates using the same rule under different population weights. These weights describe which crowd might occur; the percentages in Section 2 describe players inside a crowd.

The next useful check is to vary how calculated opponents form beliefs and adjust bids, because those choices determine which castles become crowded.

The results compare searched candidates through simulation; regret uses searched reference strategies. Full settings and results: [detailed report](game2_round3.md), [core scores](../results/game2_round3/metrics.json), [coverage comparison](../results/game2_round3/coverage_weights.json).

---

## 中文

我们要寻找**一个固定配兵，在面对经过思考的对手时取得较高平均奖励**。主要工作是模拟其他同学可能怎样选择，比较配兵，再改变这些假设，检查结果是否稳定。

### 1. 比赛究竟比什么？

将 100 名士兵分到五座城，城堡分别值 1、2、3、4、5 分。每场四个人，出价最高者取得城堡，出价并列则平分城堡分。总城堡分决定名次，第一至第四名分别获得 **9、4、2、0** 奖励；名次并列则平分所占名次的奖励。比赛反复重新分组，最后计算平均奖励。

例如，拿下前三城得到六分，但另一人拿下第四、第五城得到九分，我们就是第二名，获得 **4 分奖励**。因此，模拟需要保留四个人的完整配兵，再计算最终排名。

### 2. 我们假设哪些对手？

一个**人群**就是一种可能的参赛者构成。每场从该人群抽取三个对手。

| 类型 | 怎样选择配兵 |
|---|---|
| **H：简单模板** | 平均或按价值分配，例如 `20/20/20/20/20`。这类玩家占比较小。 |
| **C：经过考虑的集中配兵** | 大部分重点争夺两三座城，其他城保留小额出价；改变目标城堡，并加价跨过预期门槛。 |
| **Z：全押第五城** | `0/0/0/0/100`，取得或平分五分城，希望其余分数分散。 |
| **F：集中前三城** | 尝试从前三城取得六分，例如 `15/30/55/0/0`，并改变内部比例、在其他城放少量士兵。 |
| **T：我们的初步思路** | `0/1/36/0/63`、`0/0/49/51/0` 及附近变体。 |
| **S：计算回应** | 预测整个人群，搜索强配兵，再考虑别人也可能进一步思考。 |

S 模拟的是**提交前的分析**。我们设置四层推理和几种人群判断，大部分 S 权重放在第二至第四层。每个人最终仍提交一个固定配兵。

**核心模型**包含五种可能的人群。在 H 的中心设置下，玩家百分比如下：

| 人群 | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| 集中型较多 | 3 | 32 | 12 | 12 | 15 | 26 |
| 计算型较多 | 3 | 15 | 12 | 12 | 8 | 50 |
| 全押第五城较多 | 3 | 26 | 18 | 8 | 10 | 35 |
| 集中前三城较多 | 3 | 24 | 8 | 22 | 10 | 33 |
| 原始思路较多 | 3 | 21 | 8 | 12 | 28 | 28 |

每行合计 100%。另将 H 改为 1% 或 5%，从 C 调整差额，同时改变小额出价与推理深度，形成 **90 个核心检验人群**。汇总成绩时，最初给五种人群相同权重。

### 3. 怎么判断策略好坏？

每个人群得到一个估计的**平均名次奖励**，范围为 0 至 9 分。我们比较四项指标：

- **加权平均奖励：** 综合各种可能人群的表现，是主要目标。
- **最差 20% 均值：** 表现最差的 20% 场景权重所对应的平均奖励，用来防范对人群判断失误。
- **最低均值：** 单个人群中的最低平均奖励，定位最弱情况。
- **最大估计 regret：** 相比专门针对该人群搜索的强参考策略，最大的得分差。例如参考策略得 6 分，我们得 5.5 分，regret 就是 0.5。

选择规则是：**保留最差 20% 均值距离该指标最佳候选不超过 0.25 分的方案，再从中选择加权平均奖励最高的。** 最低均值和最大 regret 用于检查薄弱处；单个特殊人群就可能决定其中任何一个指标。

这里的最差 20% 指可能出现的**人群**，每个人群已经平均了很多场比赛，不能读成单场比赛中最差的 20%。

### 4. 做了哪些实验？结果如何？

1. **搜索：** 在 90 个训练人群中比较 24,402 个配兵，包括全部 5,151 种只投前三城的方案，保留 19 个候选继续比较。
2. **新核心检验：** 重新生成 90 个人群，改变比例、出价习惯和计算回应；每个人群运行 **200,000 场新对局**。
3. **扩大检查范围：** 增加 36 个 Z/F 较少、包含 F 缺席的人群，18 个人群聚集、跟随与反制场景，并复查 258 个旧人群，各运行 50,000 场新对局。

补充人群中，Z 取 **1/5/15%**，F 取 **0/10/20%**，交叉两种出价习惯和两种推理混合。每个 Z/F/出价组合重新计算 S。F=0 表示没有专门的 F 人群，C、S 仍可能选择相似配兵。

下表比较两套权重：**核心**使用 90 个核心人群；**扩大**给核心人群一半权重，给 12 个 F 缺席人群另一半权重。所有得分列都越高越好。

| 配兵 | 核心平均 | 核心最差 20% | 扩大后平均 | 扩大后最差 20% |
|---|---:|---:|---:|---:|
| 队友：`0/1/36/0/63` | 3.734 | 3.020 | 3.309 | 2.374 |
| 原方案：`0/0/49/51/0` | 2.790 | 2.311 | 2.859 | 2.439 |
| 全押第五城：`0/0/0/0/100` | 4.347 | 3.787 | 4.491 | 3.872 |
| 第二轮：`16/17/54/8/5` | 4.977 | 4.188 | 4.659 | 3.604 |
| 前三城候选：`8/36/56/0/0` | 5.177 | 4.418 | 4.686 | 3.215 |
| **核心模型候选：`10/15/59/5/11`** | **5.707** | **4.902** | 5.067 | 3.612 |
| **扩大覆盖后的候选：`8/15/62/5/10`** | 5.539 | 4.686 | **5.100** | **4.130** |

重点对比最后两行：扩大人群覆盖后，领先候选改变。在核心人群中，`10/15/59/5/11` 的最低人群均值为 **4.515**，最大估计 regret 为 **1.423**。

两个主要候选都在第三城放约 60 人，并用较小出价从其他城补分。这些额外分数有机会让我们超过只拿第五城五分的对手。

### 5. 目前选哪个？

**目前保留 `8/15/62/5/10` 作为扩大覆盖后的主候选，同时保留原核心模型领先的 `10/15/59/5/11`。** 在扩大后的同一套比较中，前者将平均奖励从 **5.067 提高到 5.100**，最差 20% 均值从 **3.612 提高到 4.130**。

扩大覆盖有实际意义：Z=1%、F=0% 时，平均两种出价习惯和两种推理混合，核心模型候选得到 **4.155**，全押第五城得到 **5.134**。这些类型较少时，策略优势可能改变。

两个主要候选来自同一批 19 个方案，使用同一选择规则，只改变人群权重。这些权重描述哪种人群可能出现；第二节的百分比描述一个人群内部的玩家构成。

下一项有价值的检验是改变计算型对手怎样预测别人、怎样调整出价，因为这些选择决定哪些城堡会变得拥挤。

这些结果通过模拟比较搜索过的候选，regret 相对搜索得到的参考策略计算。完整设置与数据：[详细报告](game2_round3.md)、[核心成绩](../results/game2_round3/metrics.json)、[覆盖范围比较](../results/game2_round3/coverage_weights.json)。
