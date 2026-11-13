# Game 1: choosing our final allocation

## English

**Recommendation: 3 / 8 / 13 / 11 / 65.** Allocate these soldiers to castles worth 1, 2, 3, 4, and 5 points. Game 1 rewards our average castle points against every other entrant; ties split a castle's points.

### 1. How might our opponents think?

We expect most classmates to concentrate resources, anticipate popular choices, and adjust a few bids. We model four decision styles:

| Type | Thinking and example |
|---|---|
| **H: simple templates** | Equal or proportional spending, such as `20/20/20/20/20`. Its share is 0% or 5% in training and 1% or 4% in fresh tests. |
| **C: considered concentration** | Pick two to four main castles and leave small bids elsewhere. We vary preferred castles, round numbers, and small bids, including 5, 10, and 12. |
| **T: our initial reasoning** | Focus on castles 2, 4, and 5: `2/16/1/37/44`, `1/14/1/37/47`, and nearby variations. These ideas came from our own discussion. |
| **S: further reasoning** | Predict a population and choose a strong response. Some target concentrated spending; others anticipate those responses. We vary their beliefs, reasoning depth, and choice among nearly best allocations. |

For S, all reasoning happens **before submission**. Students can reason carefully while predicting different opponents. We therefore vary both their predictions and how they select an allocation. The revised sampler also changes the castle order used to select strong responses, reducing dependence on one implementation's preferences.

The fresh tests cover five possible environments. Percentages below are **H / C / T / S**:

| Environment | Shares with 1% H | Main question |
|---|---|---|
| More concentration | 1 / 54 / 12 / 33% | Do many students stop at considered concentration? |
| More calculation | 1 / 24 / 12 / 63% | Do many calculate counterstrategies? |
| Our initial ideas are popular | 1 / 29 / 30 / 40% | Do many reach similar 2/4/5 allocations? |
| Our initial group is absent | 1 / 44 / 0 / 55% | Does our choice work without that opportunity? |
| Avoiding castle 5 | 1 / 39 / 12 / 48% | Do students anticipate crowded high-value castles? |

We also use 4% H, subtracting three percentage points from C. Within each environment we vary small bids, response precision, and three- versus four-level reasoning. Each environment receives 20% weight. Five alternative weightings give one environment 50% and each other environment 12.5%.

### 2. What are we optimizing?

Our main target is **average score across plausible populations**. To protect against unfavorable populations, we also measure the **worst-20% mean**: sort the population scores and average the lowest 20% of their weight. With 160 equally weighted populations, this averages the lowest 32 scores.

We retain **regret** as a diagnostic. If the best allocation against one population scores 10 and ours scores 9.5, regret is 0.5. Maximum regret identifies the largest missed opportunity; the minimum score identifies our lowest actual performance. Looking at both helps explain why a candidate is weak.

The training rule maximizes average score while keeping the worst-20% mean within **0.25 castle points** of its best achievable value. We also compare pure mean, tail, minimum-score, and maximum-regret objectives. This borrows Game 2's approach to balancing typical performance and downside protection.

Game 1 lets us calculate expected scores and each population's best response exactly. We use DP for those best responses and enumerate **all 4,598,126 legal allocations** for the combined objectives.

### 3. What did we run, and what improved?

We searched 80 training populations, retained **17 distinct candidates**, then evaluated them on **two independently regenerated suites of 80 populations**. The fresh suites change bidding habits, population shares, and reasoning choices.

Training selected `3/3/13/13/68`. The following table shows the subsequent **160-population comparison**. Scores are castle points out of 15; higher mean and tail are better, lower regret is better.

| Allocation | Average | Worst-20% mean | Maximum regret |
|---|---:|---:|---:|
| Teammate: 2 / 16 / 1 / 37 / 44 | 6.508 | 5.702 | 5.188 |
| Original: 1 / 14 / 1 / 37 / 47 | 6.543 | 5.777 | 5.005 |
| Previous recommendation: 8 / 9 / 10 / 11 / 62 | 8.982 | 7.936 | 1.860 |
| Training selection: 3 / 3 / 13 / 13 / 68 | 9.053 | 8.363 | 1.889 |
| Fresh mean leader: 4 / 3 / 14 / 12 / 67 | **9.122** | **8.407** | 1.770 |
| **Final recommendation: 3 / 8 / 13 / 11 / 65** | **9.114** | **8.339** | **1.430** |

Our recommendation improves on the previous allocation's mean and tail in both fresh suites and under all six environment weightings. Its family-average scores range from **8.905 to 9.436**. The largest improvement comes when T is absent: **8.631 → 8.948**. When T is popular, the previous allocation retains a small advantage: **9.420 versus 9.366**.

### 4. Why choose it over the mean leader?

We checked **510 additional populations** in which 5% or 15% of players copy a candidate, respond to a population containing copies, or counter the candidate itself. Each of the 17 candidates was targeted equally, and every candidate faced all resulting populations. We also replayed the **5,624 populations from our earlier experiments**.

| Additional check | Previous 8/9/10/11/62 | Mean leader 4/3/14/12/67 | Recommended 3/8/13/11/65 |
|---|---:|---:|---:|
| Targeted tests: average | 8.565 | **8.859** | 8.748 |
| Targeted tests: minimum score | 7.487 | 7.668 | **7.869** |
| Targeted tests: maximum regret | 2.252 | **1.799** | 1.931 |
| Historical tests: maximum regret | **2.647** | 3.316 | 2.888 |

The recommendation gives up only **0.007** fresh average points relative to the mean leader and preserves more strength against the earlier population model. The mean leader does better on average in the targeted tests. Our choice reflects the value we place on covering different plausible models of classmates' behavior.

The old allocation still has the lowest historical maximum regret. The reason to switch is the improved mean and unfavorable-population performance under the revised behavioral model. The gain is largest when the S players choose more varied near-optimal allocations; with very precise S players, the old and recommended allocations perform similarly.

The final recommendation is a reviewed choice among the 17 candidates after these comparisons. E is a separately computed equilibrium distribution: even its best counterstrategy scores only 7.5. Against E, the previous allocation, fresh mean leader, and recommendation each score **7.500**.

### 5. What does the allocation do?

From `8/9/10/11/62`, move five soldiers out of castle 1 and one out of castle 2; add three each to castles 3 and 5. In the fresh populations, the lost expected points on castles 1 and 2 total **0.433**, while castles 3 and 5 gain **0.566**. The net gain is **0.133 points**.

We spend less protecting the least valuable castle and cross more useful bidding thresholds on castles 3 and 5. That explains the change to **3 / 8 / 13 / 11 / 65**.

[Run and reproduce the experiment](experiments/run_game1_final.md) · [Exact population settings](modules/game1_field.md) · [Saved decision and comparisons](../results/game1_final/decision.json)

---

## 中文

**建议提交：3 / 8 / 13 / 11 / 65。** 五个数字分别投入价值为 1、2、3、4、5 分的城堡。Game 1 的成绩是面对所有其他参赛者时的平均城堡分；出价并列就平分该城分数。

### 1. 我们的对手会怎样思考？

我们预计大多数同学会集中兵力、预判热门方案，并调整几个关键出价。模型包含四种决策方式：

| 类型 | 思路与例子 |
|---|---|
| **H：简单模板** | 平均或按价值分配，例如 `20/20/20/20/20`。训练占比为 0% 或 5%，新检验为 1% 或 4%。 |
| **C：经过考虑的集中投入** | 主攻两到四城，其他城小额投入。改变主攻城、取整习惯和小额出价，包含 5、10、12 人等门槛。 |
| **T：我们的初步思路** | 主攻第 2、4、5 城，包括 `2/16/1/37/44`、`1/14/1/37/47` 及附近变体。这些方案来自我们自己的讨论。 |
| **S：进一步推理** | 预测人群并选择强回应。有人针对集中型，有人预判这些回应；我们改变他们的预测、推理深度，以及在接近最优的方案中怎样选择。 |

S 的推理都发生在**提交之前**。认真思考的同学也会对对手作出不同预测，所以我们同时改变其预测和选方案的方式。新版抽样还会改变选择强回应时的城堡处理顺序，减少结果对一种程序选择习惯的依赖。

新检验覆盖五类环境。以下比例顺序为 **H / C / T / S**：

| 环境 | H 为 1% 时的比例 | 检查的问题 |
|---|---|---|
| 集中型较多 | 1 / 54 / 12 / 33% | 很多人是否停在经过考虑的集中配兵？ |
| 计算型较多 | 1 / 24 / 12 / 63% | 是否有很多人计算反制方案？ |
| 我们的初步思路热门 | 1 / 29 / 30 / 40% | 很多人是否想到类似的第 2/4/5 城配兵？ |
| 没有我们的初步人群 | 1 / 44 / 0 / 55% | 没有这类机会，我们还能否表现良好？ |
| 回避第五城 | 1 / 39 / 12 / 48% | 同学是否预判高分城拥挤而转向其他城？ |

还测试 H 为 4%，对应将 C 减少三个百分点。每类环境再改变小额出价、回应精确程度，以及三层或四层推理。五类环境各占 20% 权重；另外五套权重分别将某一类提高到 50%，其余各占 12.5%。

### 2. 我们优化什么？

主目标是**在合理人群中的平均得分**。同时保护不利人群下的表现：把各人群得分排序，取最低得分的 20% 场景权重，计算其**最差 20% 均值**。在 160 个等权人群中，就是最低的 32 个得分取平均。

保留 **regret** 帮助判断问题。如果某个人群的最优配兵得 10 分，我们得 9.5 分，regret 就是 0.5。最大 regret 衡量最大的机会损失；最低得分衡量我们实际表现最差的情况。两者结合，可以理解候选为什么失分。

训练时，要求最差 20% 均值距离其可达到的最好值不超过 **0.25 城堡分**，再最大化平均分。同时比较单独优化均值、尾部、最低分和最大 regret 的结果。这借鉴了 Game 2 对通常表现和不利表现的共同考虑。

Game 1 可以精确计算期望得分和每个人群的最佳回应。我们用 DP 求最佳回应，并枚举**全部 4,598,126 种合法配兵**，优化需要综合多个场景的指标。

### 3. 做了哪些实验，结果怎样？

先在 80 个训练人群中搜索，保留 **17 个不同候选**，再用**两组独立重新生成的 80 个人群**检验。新检验改变出价习惯、人数比例和推理选择。

训练选出 `3/3/13/13/68`。下表是随后 **160 个新人群的比较**。单位为城堡分，满分 15；均值和尾部越高越好，regret 越低越好。

| 配兵 | 平均分 | 最差 20% 均值 | 最大 regret |
|---|---:|---:|---:|
| 同学方案：2 / 16 / 1 / 37 / 44 | 6.508 | 5.702 | 5.188 |
| 原始方案：1 / 14 / 1 / 37 / 47 | 6.543 | 5.777 | 5.005 |
| 上轮建议：8 / 9 / 10 / 11 / 62 | 8.982 | 7.936 | 1.860 |
| 本轮训练选择：3 / 3 / 13 / 13 / 68 | 9.053 | 8.363 | 1.889 |
| 新检验均值领先：4 / 3 / 14 / 12 / 67 | **9.122** | **8.407** | 1.770 |
| **最终建议：3 / 8 / 13 / 11 / 65** | **9.114** | **8.339** | **1.430** |

最终建议在两组新人群、六套环境权重下，均值和尾部都优于上轮方案。五类环境的平均分为 **8.905 至 9.436**。提升最大的是没有 T 的环境：**8.631 → 8.948**。T 热门时，上轮方案仍略好：**9.420 对 9.366**。

### 4. 为什么选择它，而不是均值领先的方案？

另外检查了 **510 个人群**，其中 5% 或 15% 的玩家分别照抄候选、针对含有照抄者的人群回应，或直接针对该候选。17 个候选接受同等次数的针对，每个候选都面对全部这些人群。还重新计算了**此前实验的 5,624 个旧人群**。

| 补充检查 | 上轮 8/9/10/11/62 | 均值领先 4/3/14/12/67 | 建议 3/8/13/11/65 |
|---|---:|---:|---:|
| 针对性检验：平均分 | 8.565 | **8.859** | 8.748 |
| 针对性检验：最低分 | 7.487 | 7.668 | **7.869** |
| 针对性检验：最大 regret | 2.252 | **1.799** | 1.931 |
| 旧人群检验：最大 regret | **2.647** | 3.316 | 2.888 |

建议方案比均值领先方案只少 **0.007** 分，同时更好地保留了对旧人群模型的适应能力。均值领先方案在针对性检验中的平均表现更好。我们最终选择前者，是因为我们重视它能适应几种不同的对手假设。

上轮方案在旧人群中的最大 regret 仍最低。更换的理由是，新行为模型下的平均表现和不利人群表现都改善了。当人群中的 S 玩家选择更多样的接近最优配兵时，提升最大；S 玩家回应非常精确时，上轮和建议方案的表现接近。

最终建议是在上述比较后，从 17 个固定候选中作出的综合选择。E 是单独求出的均衡分布，针对它的最佳回应也只能拿到 7.5 分。面对 E 时，上轮方案、新检验均值领先方案和最终建议都得到 **7.500** 分。

### 5. 这个配兵具体改进在哪里？

从 `8/9/10/11/62` 出发，第一城撤出五人，第二城撤出一人；第三、第五城各增加三人。新检验中，前两城合计损失 **0.433** 期望分，第三、第五城合计增加 **0.566** 分，净增加 **0.133 分**。

减少对最低价值城堡的投入，把兵力用于跨过第三、第五城更有价值的出价门槛。这就是调整为 **3 / 8 / 13 / 11 / 65** 的具体依据。

[运行与复现实验](experiments/run_game1_final.md) · [完整人群设置](modules/game1_field.md) · [最终选择与比较数据](../results/game1_final/decision.json)
