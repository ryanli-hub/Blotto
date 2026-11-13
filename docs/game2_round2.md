# Game 2: rules, opponent model, and round 2

## English

### What are we trying to maximize?

Submit **one fixed allocation** of 100 integer soldiers to castles worth 1, 2, 3, 4, and 5 points. Each match groups us with three opponents. At each castle, the highest bidders split its points. Add each player's castle points, rank the four players, and award **9, 4, 2, 0**. Tied players share the rewards for their occupied places. Our final score is the average reward over repeated groupings.

For example, consider these four players:

| Players | Allocation, each | Castle points, each | Ranking reward, each |
|---|---|---:|---:|
| A and B | 0 / 0 / 50 / 50 / 0 | 4.25 | 6.50 |
| C and D | 0 / 0 / 0 / 0 / 100 | 3.25 | 1.00 |

Everyone gets $(1+2)/4=0.75$ from the first two abandoned castles. A and B also split castles 3 and 4; C and D split castle 5. A and B tie for first and receive $(9+4)/2=6.5$ each. C and D tie for third and receive $(2+0)/2=1$ each.

### How does our simulation represent thoughtful students?

We model different ways of reaching a decision:

| Type | Thought process | How we represent it |
|---|---|---|
| H | Use a quick allocation rule. | A small share of equal, proportional, and simple concentrated templates. |
| C | Winning against three people requires strong bids on selected castles. | Choose one, two, or three main castles; compare full commitment with retaining small secondary bids. |
| T | Castle 5 may be crowded; another combination could work. | Our actual proposals `0/1/36/0/63` and `0/0/49/51/0`, plus nearby choices. |
| S | Predict these choices and find a strong response. | Score complete matches under several beliefs; model one to four levels of reasoning before submission. |

T has the clearest behavioral evidence: these are strategies we actually considered. C and S follow explicit decisions about competition and counterplay. Students with similar ability can disagree about what others will choose, so we vary both their beliefs and their population shares.

For each C model, we build S using three beliefs about the population. We then vary the actual H/C/S/T mixture shares while retaining those strategy distributions. Three opponents independently draw from the full mixture, and the simulator computes all four players' scores and rewards. Our candidate allocation stays fixed throughout evaluation. For example, if T represents 20% of people, the chance of meeting at least one T opponent is $1-0.8^3=48.8\%$.

We compare strategies using **estimated regret**: the mean reward of a strong searched reference minus ours against the same population. A reference scoring 6 versus our 5.5 gives regret 0.5. Reference selection uses separate calibration games; fresh games measure the gap. We seek a small maximum gap across populations.

### What did this round improve?

The earlier C model rarely produced an exact 100-soldier bid, because even single-main-castle players usually reserved soldiers elsewhere. We now explicitly represent both choices. Within single-main-castle C, half deliberately go all-in during training; fresh tests change that fraction to 20% or 80%.

In a matched central comparison with 15% single-main-castle C, adding this branch raises the share of C putting exactly 100 on castle 5 from **0.52% to 4.55%**. The probability of meeting at least one such opponent rises from **0.41% to 3.54%**.

We independently vary the single-main-castle share, secondary bids, fifth-castle popularity, and reasoning depth. The deeper S mixture keeps the original three-level mixture intact and replaces half of it with level 4. Fresh tests also include players who follow recommendations, anticipate followers, or misjudge fifth-castle popularity.

The search covers **277 development populations**, including the previous 115, and **18,055 initial allocations** plus local refinements. We then freeze nine candidates and test **258 fresh populations**, with **200,000 games each**. These include 72 cases with **43.4% C**, ensuring that concentration behavior matters at substantial population shares. Full settings are in the [experiment guide](experiments/run_game2_round2.md).

### Results and current choice

Training selected **16 / 17 / 54 / 8 / 5**, with maximum estimated regret 2.550. The fresh tests give a different ranking:

| Allocation | Lowest scenario mean reward | Maximum estimated regret |
|---|---:|---:|
| Teammate: 0 / 1 / 36 / 0 / 63 | 1.525 | 6.521 |
| Yours: 0 / 0 / 49 / 51 / 0 | 1.819 | 5.728 |
| Earlier compromise: 6 / 37 / 50 / 7 / 0 | 2.295 | 4.696 |
| Round 1: 0 / 5 / 0 / 5 / 90 | 3.402 | 3.349 |
| **Round 2: 16 / 17 / 54 / 8 / 5** | **3.999** | **3.500** |
| **All fifth: 0 / 0 / 0 / 0 / 100** | **3.681** | **3.074** |

All scores are average ranking rewards out of 9. Each row uses the same 258 populations. **All fifth has the lowest maximum estimated regret among the nine frozen candidates, so keep it as the current benchmark.** The new candidate has a higher lowest mean reward, but misses more attainable reward in its worst-regret population: the searched reference earns 8.074, the new candidate 4.574, and all fifth 4.999.

The new candidate's idea is understandable. Against our two original proposals plus an all-fifth opponent, it wins castles 1, 2, and 3. Castle scores are **6, 0, 4, 5**, so it earns 9. It combines several castles to compete for first place.

Controlled comparisons also show why opponent details matter. Below, change one setting from the balanced central case, rebuilding S when C changes:

| Setting | All fifth | Round 1 | Round 2 |
|---|---:|---:|---:|
| Base: 15% single-main-castle C, low bids, depth 3 | 5.18 | 5.33 | 5.87 |
| Higher secondary bids | 4.98 | 4.89 | 5.18 |
| More fourth-level reasoning | 5.31 | 5.76 | 5.13 |
| Single-main-castle C increases to 30% | 5.29 | 5.49 | 4.72 |
| Single-main-castle C increases to 45% | 5.21 | 5.17 | 6.43 |

These comparisons include S's responses to C, so changing C also changes the counterstrategies. The observed effects vary in direction: higher concentration or deeper reasoning can help one candidate while hurting another. We therefore use the fresh comparison to choose among the candidates.

Our assumptions have explicit decision motives and cover several plausible responses to the same problem. Their numerical prevalence is the remaining behavioral uncertainty. Independent allocations and short explanations from additional students would help identify missing strategies and constrain these proportions.

Sources within the project: [rules](rules.md), [all fresh results](../results/game2_round2/combined_comparison.json), [controlled comparisons](../results/game2_round2/factorial.json). **44 tests pass**, covering both tie layers, joint distributions, population reweighting, and reasoning-depth consistency.

---

## 中文

### 我们到底在优化什么？

提交**一套固定配兵**：把 100 名整数士兵分到价值为 1、2、3、4、5 分的城堡。每场你和另外三人一组。每座城由兵力最多的人平分该城分数；然后累加各人的城堡分，按四个人的名次发 **9、4、2、0** 分。名次并列时，平分所占名次的奖金。最后成绩是反复分组后的平均奖励。

例如，这四个人参赛：

| 玩家 | 每人的配兵 | 每人的城堡分 | 每人的名次奖励 |
|---|---|---:|---:|
| A、B | 0 / 0 / 50 / 50 / 0 | 4.25 | 6.50 |
| C、D | 0 / 0 / 0 / 0 / 100 | 3.25 | 1.00 |

前两城所有人都放 0，因此每人分到 $(1+2)/4=0.75$ 分。A、B 再平分第三、第四城，C、D 平分第五城。A、B 并列第一，各拿 $(9+4)/2=6.5$；C、D 并列第三，各拿 $(2+0)/2=1$。

### 我们怎样模拟认真思考的同学？

按做决定的过程来建模：

| 类型 | 思考过程 | 代码怎样表示 |
|---|---|---|
| H | 用一个快捷规则配兵。 | 少量平均分配、按价值分配和简单集中模板。 |
| C | 要同时赢三个人，重点城必须有足够强的兵力。 | 选择一、二、三座重点城，并比较全力投入与保留小额出价。 |
| T | 第五城可能太拥挤，其他组合也许更好。 | 我们实际提出的 `0/1/36/0/63`、`0/0/49/51/0` 及附近变体。 |
| S | 预测这些选择，再找强回应。 | 根据几种信念计算完整对局，模拟提交前一至四层推理。 |

T 的行为依据最直接：这些就是我们认真考虑过的方案。C、S 也有明确的竞争与反制逻辑。能力相近的同学，对别人会怎么选可能判断不同，所以我们同时改变信念和人数比例。

每改变一个 C 模型，先根据三种人群预期生成 S；再保留这些策略分布，改变实际 H/C/S/T 混合比例。每场分别从整个人群抽取三个对手，计算四人的城堡分和奖金。我们的候选配兵在检验期间始终固定。例如 T 占人数的 20%，一场遇到至少一个 T 的概率是 $1-0.8^3=48.8\%$。

比较标准是**估计 regret**：同一人群下，搜索到的强参考方案平均奖励减去我们的平均奖励。它得 6 分、我们得 5.5 分，regret 就是 0.5。参考方案用另外的校准对局选择，再用新对局测差距。目标是让跨人群的最大差距较小。

### 本轮改进了什么？

上一版 C 很少恰好出价 100，因为只重点争夺一座城的人也通常在其他地方留兵。本轮明确加入两种选择：训练时，一半单城型直接全押；新检验改为 20% 或 80%。

在同样“C 中 15% 为单城型”的中心对照中，加入这一分支后，C 中恰好全投第五城的比例从 **0.52% 升至 4.55%**；一场遇到至少一个这种对手的概率从 **0.41% 升至 3.54%**。

我们分别改变单城型比例、小额出价、第五城热门程度和推理深度。加深推理时，保留原三层混合的内部比例，只把其中一半替换为第四层。新检验还包括采用共同推荐、预判跟随者，以及猜错第五城热门程度的玩家。

搜索使用 **277 个开发人群**，包含上一轮的 115 个；初始比较 **18,055 个配兵**，再做局部调整。之后固定九个候选，在 **258 个新场景中各检验 200,000 场**。其中 72 个场景的 **C 占比为 43.4%**，用来检验较多人选择集中配兵时的表现。完整设置见[实验说明](experiments/run_game2_round2.md)。

### 结果与当前选择

训练选出 **16 / 17 / 54 / 8 / 5**，最大估计 regret 为 2.550。新检验的排序发生了变化：

| 配兵 | 最低场景平均奖励 | 最大估计 regret |
|---|---:|---:|
| 队友：0 / 1 / 36 / 0 / 63 | 1.525 | 6.521 |
| 你的：0 / 0 / 49 / 51 / 0 | 1.819 | 5.728 |
| 之前折中：6 / 37 / 50 / 7 / 0 | 2.295 | 4.696 |
| 第一轮：0 / 5 / 0 / 5 / 90 | 3.402 | 3.349 |
| **第二轮：16 / 17 / 54 / 8 / 5** | **3.999** | **3.500** |
| **全投第五城：0 / 0 / 0 / 0 / 100** | **3.681** | **3.074** |

得分都是满分 9 分的平均名次奖励，每行使用同样的 258 个人群。**在本轮九个固定候选中，全投第五城的最大估计 regret 最低，暂时保留为基准。** 新候选的最低均分更高，但在它损失机会最多的人群中，参考策略得 8.074，新候选得 4.574，全投第五城得 4.999，所以它的 regret 更大。

新候选的思路也很清楚：若三个对手分别采用我们的两个原始方案和全投第五城，它能拿下第一、第二、第三城。四人的城堡分为 **6、0、4、5**，它因此拿到 9 分。它通过组合几座城来争取第一名。

控制变量比较说明了对手细节的重要性。下表从偏好正常的中心人群出发，每次改变一个设置；C 改变时，同时重新生成 S：

| 设置 | 全投第五城 | 第一轮方案 | 第二轮方案 |
|---|---:|---:|---:|
| 基础：C 中单城型 15%，低小额出价，三层推理 | 5.18 | 5.33 | 5.87 |
| 提高小额出价 | 4.98 | 4.89 | 5.18 |
| 增加第四层推理 | 5.31 | 5.76 | 5.13 |
| C 中单城型提高到 30% | 5.29 | 5.49 | 4.72 |
| C 中单城型提高到 45% | 5.21 | 5.17 | 6.43 |

这些比较包含 S 对 C 的回应，所以改变 C 也会改变反制配兵。实际结果中，影响的方向会变化：更集中或多想一层，可能帮助一个候选、同时伤害另一个。因此，我们根据新场景中的综合表现做选择。

这些假设有明确的决策动机，也覆盖了对同一问题的多种合理回应；实际有多少人采用每种方式，仍是主要的行为不确定性。接下来可以收集其他同学独立写出的配兵及简短理由，检查遗漏的策略，并约束这些比例。

项目依据：[规则](rules.md)、[全部新检验结果](../results/game2_round2/combined_comparison.json)、[控制变量比较](../results/game2_round2/factorial.json)。**44 项测试通过**，覆盖两层并列、联合分布、人群重加权，以及推理深度对照的一致性。
