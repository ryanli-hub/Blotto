# Game 1: our final strategy

## English

**Submit: 8 / 9 / 10 / 11 / 62.** The numbers allocate our 100 soldiers to castles worth 1, 2, 3, 4, and 5 points. Our result is the average castle points won across opponents; ties split points.

### Who did we model?

- **H: simple rules.** Equal spending or spending in proportion to castle value. We tested shares up to 15%.
- **C: concentrated spending.** Focus on two to four castles, with small bids elsewhere. We varied their preferred castles and bid sizes.
- **S: strategic responders.** Predict other players' choices and think one to three steps ahead before submitting. We also tested further counterstrategies.
- **T: players like our initial ideas.** Focus on castles 2, 4, and 5, with small bids on 1 and 3. This includes our two original strategies and nearby variations. We tested shares from 10% to 60%.

We also used **E**, a mathematical equilibrium benchmark that randomizes among allocations and limits the best counterstrategy to 7.5 points.

### How did our candidates perform?

The H/C/S/T columns each face only that reference group and show **average scores out of 15; higher is better**. T uses nearby variations of our original strategies.

The last column tests mixed populations with different proportions, bids, and counterstrategies. **Regret** is the best score against that same population minus our score: if the best choice earns 10 and we earn 9.5, regret is 0.5. **Lower maximum regret is better.**

| Allocation | H | C | S | T | Maximum regret* |
|---|---:|---:|---:|---:|---:|
| 2 / 16 / 1 / 37 / 44 | 8.67 | 8.21 | 4.80 | 6.96 | 5.197 |
| 1 / 14 / 1 / 37 / 47 | 8.67 | 8.21 | 4.89 | 7.59 | 5.456 |
| 2 / 2 / 3 / 39 / 54 | 9.67 | 9.35 | 5.16 | 11.24 | 5.755 |
| 2 / 16 / 10 / 12 / 60 | 7.67 | 8.63 | 9.37 | 9.67 | 3.011 |
| **8 / 9 / 10 / 11 / 62** | **7.33** | **8.72** | **10.62** | **9.00** | **2.647** |

**\* Mixtures used for this column:** the maximum is taken across **5,624 fresh scenarios**, using the same scenarios for every candidate.

Start with these 12 H/C/S mixtures. Each C/S pair gives percentages of the whole base population; together with H, they sum to 100%.

| H | C / S: mix 1 | C / S: mix 2 | C / S: mix 3 |
|---:|---:|---:|---:|
| 0% | 75% / 25% | 50% / 50% | 25% / 75% |
| 5% | 71.25% / 23.75% | 47.5% / 47.5% | 23.75% / 71.25% |
| 10% | 67.5% / 22.5% | 45% / 45% | 22.5% / 67.5% |
| 15% | 63.75% / 21.25% | 42.5% / 42.5% | 21.25% / 63.75% |

- **Add T:** test **0%, 5%, 10%, 15%, 25%, 35%, 40%, 55%, or 60% T**, scaling the base population to fill the remainder.
- **Responses to T:** for each positive T share, either keep the remainder unchanged or replace **15% of it** with new responders. For example, 40% T gives either **40% T + 60% base**, or **40% T + 51% base + 9% responders**.
- **Separate anticipation/counter tests:** **85% base + 15% peers, anticipators, or direct counters**.

We also varied composition within groups: S's levels 1/2/3 used **70/25/5%, 35/45/20%, or 15/35/50%**; four-level tests used **5/15/30/50%**. Selected cases replaced **25% or 50% of S** with shared recommendations. Exact-strategy T cases mixed our two initial strategies **80/20% or 20/80%**.

E is tested separately: all five candidates score **7.50 against E**.

### Why this final choice?

The earlier allocations perform well against some concentrated opponents but lose ground against S. Our final allocation beats many small bids while keeping 62 soldiers for castle 5. Against the tested T variations, it consistently wins castles 1, 3, and 5, totaling **9 points**.

Across the fresh tests, it has the **lowest maximum regret among these candidates**. That makes it our choice for opponents whose strategies and proportions we cannot predict precisely.

---

## 中文

**最终提交：8 / 9 / 10 / 11 / 62。** 五个数字把 100 名士兵分配到价值分别为 1、2、3、4、5 分的城堡。成绩是面对各对手时的平均城堡分，并列时平分该城分数。

### 我们设计了哪些对手？

- **H：简单规则型。** 平均分配，或按城堡价值分配。测试比例最高为 15%。
- **C：集中投入型。** 重点争夺两到四座城，其他城少量投入。我们改变其重点城和出价大小。
- **S：策略反制型。** 提交前预测别人怎么选，并向前推理一到三层。我们也测试了进一步反制的情况。
- **T：类似我们初步想法的玩家。** 重点争夺第 2、4、5 城，在第 1、3 城少量投入。包含我们的两个原始方案及附近变体，测试比例为 10% 到 60%。

另外用 **E** 做数学基准：按均衡分布随机选择配兵，使针对它的最佳反制只能拿到 7.5 分。

### 候选策略表现如何？

H/C/S/T 四列分别只面对该类参考对手，展示**平均得分，满分 15 分，越高越好**。T 使用我们原始方案附近的配兵变体。

最后一列来自混合人群的检验，其中人数比例、出价和反制方式都会变化。**Regret** 等于面对同一个人群时，最高可得分减去我们的得分：如果最优方案得 10 分，我们得 9.5 分，regret 就是 0.5。**最大 regret 越低越好。**

| 配兵 | H | C | S | T | 最大 regret* |
|---|---:|---:|---:|---:|---:|
| 2 / 16 / 1 / 37 / 44 | 8.67 | 8.21 | 4.80 | 6.96 | 5.197 |
| 1 / 14 / 1 / 37 / 47 | 8.67 | 8.21 | 4.89 | 7.59 | 5.456 |
| 2 / 2 / 3 / 39 / 54 | 9.67 | 9.35 | 5.16 | 11.24 | 5.755 |
| 2 / 16 / 10 / 12 / 60 | 7.67 | 8.63 | 9.37 | 9.67 | 3.011 |
| **8 / 9 / 10 / 11 / 62** | **7.33** | **8.72** | **10.62** | **9.00** | **2.647** |

**\* 这一列使用的混合比例：** 对每个候选都使用同一组 **5,624 个新场景**，取其中最大的 regret。

先建立以下 12 种 H/C/S 混合。C/S 两个数字都是占整个基础人群的百分比，与该行 H 相加等于 100%。

| H | C / S：组合 1 | C / S：组合 2 | C / S：组合 3 |
|---:|---:|---:|---:|
| 0% | 75% / 25% | 50% / 50% | 25% / 75% |
| 5% | 71.25% / 23.75% | 47.5% / 47.5% | 23.75% / 71.25% |
| 10% | 67.5% / 22.5% | 45% / 45% | 22.5% / 67.5% |
| 15% | 63.75% / 21.25% | 42.5% / 42.5% | 21.25% / 63.75% |

- **加入 T：** 测试 **0%、5%、10%、15%、25%、35%、40%、55%、60% T**，基础人群按原比例缩小，填满剩余部分。
- **针对 T 的反制：** 每个非零 T 比例都测试剩余部分保持不变，或将其中 **15%** 换为新的反制者。例如，T 占 40% 时，测试 **40% T + 60% 基础人群**，以及 **40% T + 51% 基础人群 + 9% 反制者**。
- **单独的预判与反制检验：** **85% 基础人群 + 15% 同层思考者、预判者或直接反制者**。

组内比例也有变化：S 的第一/二/三层使用 **70/25/5%、35/45/20%、15/35/50%**；四层检验使用 **5/15/30/50%**。部分场景将 **25% 或 50% 的 S** 换成采用共同推荐的玩家。T 使用两个原始配兵时，按 **80/20% 或 20/80%** 混合。

E 单独作为基准，五个候选**面对 E 都得 7.50 分**。

### 为什么最终选它？

之前的配兵擅长应对部分集中型对手，但面对 S 会明显失分。最终方案能跨过许多小额出价，同时保留 62 人争夺第五城。面对测试中的 T 变体，它始终赢第一、第三、第五城，合计 **9 分**。

在新场景检验中，它的**最大 regret 是这些候选中最低的**。因此，当我们无法准确预测对手的配兵和人数比例时，选择这个方案。
