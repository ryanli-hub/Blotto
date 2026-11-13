# Game 2: what should we optimize?

## English

The strongest finding is that **population coverage changes the recommendation more than small changes to the objective**. Third-castle strategies lead in the new core model, but their advantage shrinks or reverses when dedicated first-three opponents are scarce. We therefore compare several objectives and explicitly test that missing case.

### 1. Our objective

The competition averages our **ranking reward** over many four-player matches. A castle goes to its highest bidder, with ties sharing its value. Total castle points determine ranks; rewards are **9, 4, 2, 0**, with tied ranks sharing the occupied prizes. We submit one fixed allocation throughout.

I recommend **maximizing average reward across plausible populations, with a limit on performance loss in unfavorable populations**. Minimum reward and maximum regret help diagnose weaknesses.

| Metric | What it answers | Role |
|---|---|---|
| Weighted mean reward | How well do we perform across the populations we expect? | Main objective |
| Worst-20% mean | How well do we perform in the unfavorable part of those possibilities? | Protection against mistaken population assumptions |
| Minimum scenario mean | What is our lowest average in any included population? | Check the single weakest population |
| Maximum estimated regret | Where do we lose the most compared with a strong strategy tailored to that population? | Identify missed opportunities |

The “worst 20%” uses scenario weights. A population with weight 10% occupies half of this tail if it lies entirely within the worst 20%. Each score is already an average over matches; the minimum is not a guaranteed single-match payout.

**Why maximum regret should not decide everything:** suppose two possible populations have weights 90% and 10%. A scores 6 and 3; B scores 5.5 and 4. Their weighted means are **5.70 and 5.35**. If the population-specific best scores are 6 and 8, their maximum regrets are **5 and 4**. Maximizing the minimum and minimizing maximum regret both prefer B, sacrificing 0.35 expected reward to improve the less likely situation. That tradeoff needs a reason.

Our predeclared rule allows the worst-20% mean to fall at most **0.25 points below its best searched value**, then maximizes mean reward. We also test tolerances **0, 0.10, and 0.50**. The tolerance expresses our preference. Weighted average regret adds no separate objective: with fixed reference scores, it equals a constant minus weighted mean reward.

### 2. How we model thoughtful opponents

The model follows plausible decisions students might make:

| Group | Reasoning and example |
|---|---|
| H: simple templates | A small residual group, such as `20/20/20/20/20`; training share 0-5% |
| C: considered concentration | Mostly choose two or three main castles, keep small bids elsewhere, and vary which castles and thresholds to target |
| Z: all fifth | `0/0/0/0/100`; secure or share the most valuable castle, hoping other points are divided |
| F: first three | Try to collect six points from cheaper castles; examples `33/33/34/0/0` and `15/30/55/0/0`, plus unequal bids and small bids elsewhere |
| T: our original ideas | Neighborhoods of `0/1/36/0/63` and `0/0/49/51/0` |
| S: calculated responses | Predict a complete opponent population, search strong allocations, and consider that others may have done the same |

S uses four finite reasoning levels and three beliefs at each level. Most S weight lies on levels 2-4. The computations represent analysis before submission. Different beliefs produce different choices even among equally capable students.

The 90 fresh core populations combine five families, two secondary-bid habits, three H shares, and three S depth mixtures. At the central **H=3%** setting, type percentages are:

| Population family | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| Concentration common | 3 | 32 | 12 | 12 | 15 | 26 |
| Calculation common | 3 | 15 | 12 | 12 | 8 | 50 |
| Fifth-castle all-in common | 3 | 26 | 18 | 8 | 10 | 35 |
| First-three focus common | 3 | 24 | 8 | 22 | 10 | 33 |
| Our original ideas common | 3 | 21 | 8 | 12 | 28 | 28 |

H also takes 1% and 5%, with C absorbing the difference. Secondary bids range from 0-4 or 1-5. Each family receives 20% of the scenario weight. Five additional priors raise one family to 50% and lower each other family to 12.5%. Player shares and scenario weights serve different purposes: simulate each population separately, then average its reward.

This design reflects low reliance on simple templates, concentration with threshold adjustments, and several levels of anticipation. The most consequential assumptions are the popularity of Z/F and the beliefs used to generate S. We test those assumptions separately below.

### 3. Does winning the first three castles guarantee victory?

Winning them gives **6 castle points**. Another player can win castles 4 and 5 for **9**, leaving us second. For example, these four submissions produce castle scores **6, 9, 0, 0** and rewards **4, 9, 1, 1**:

```text
Us:       33 / 33 / 34 /  0 /  0
Opponent:  0 /  0 /  0 / 49 / 51
Opponent: 30 / 30 / 30 / 10 /  0
Opponent: 30 / 30 / 30 /  0 / 10
```

**Actually earning six points guarantees at least second place:** the other three players share nine points, so two of them cannot each reach six. However, allocating all soldiers to castles 1-3 does not guarantee winning them. At least one of those bids is at most 33, which an opponent can exceed.

We screened all **5,151** legal first-three-only allocations. The training mean winner was **8/36/56/0/0**. It scores **5.177** in fresh core validation, compared with **3.241** for equal splitting `33/33/34/0/0`. The idea is useful; the internal allocation matters greatly.

### 4. Search and fresh results

We screened **24,402** candidates, refined **619**, calibrated **182**, and froze **19** for comparison. Training used 90 populations; validation rebuilt 90 populations with new seeds, changed shares and bidding habits, and new S responses. Each fresh population used **200,000 new matches**.

The training mean-and-tail rule selected **10/14/60/5/11**. The table shows fresh validation. Higher is better in the first three numerical columns; lower is better for regret.

| Allocation | Weighted mean | Worst-20% mean | Minimum mean | Maximum estimated regret |
|---|---:|---:|---:|---:|
| Teammate: `0/1/36/0/63` | 3.734 | 3.020 | 2.845 | 3.435 |
| Original: `0/0/49/51/0` | 2.790 | 2.311 | 2.240 | 4.643 |
| All fifth: `0/0/0/0/100` | 4.347 | 3.787 | 3.711 | 2.642 |
| Round 2: `16/17/54/8/5` | 4.977 | 4.188 | 3.874 | 2.312 |
| First-three search: `8/36/56/0/0` | 5.177 | 4.418 | 4.180 | 1.964 |
| Training primary: `10/14/60/5/11` | 5.686 | **4.921** | 4.537 | 1.402 |
| Nearby candidate: `10/15/59/5/11` | **5.707** | 4.902 | 4.515 | 1.423 |
| Training tail choice: `10/14/60/6/10` | 5.594 | 4.801 | **4.587** | **1.351** |

For example, **1.402 regret** means that, in the primary candidate's worst comparison, the independently searched reference earns about 1.402 more ranking points per match. Regret depends on how strong that searched reference is.

The nearby candidate wins fresh mean reward under all six tested priors and also satisfies the 0.25 tail constraint. The training primary has a **0.019** advantage in worst-20% mean; the nearby candidate has a **0.020** advantage in overall mean. The comparison supports a close pair of candidates. The training primary is not the fresh winner under the same mean-and-tail rule.

The common structure is roughly 60 soldiers on castle 3, with meaningful bids on the other four castles. It can take the third castle while collecting points where opponents concentrated elsewhere. Those additional points help outrank players who collect five points from castle 5. The exact small bids remain sensitive to opponent thresholds.

### 5. Broader checks

Eighteen targeted tests replace part of a population with more Z/F players, copies of leading strategies, or players anticipating those copies. The primary candidate's maximum estimated regret is **2.232**, compared with **4.907** for all fifth. The 40% cohort replacement adds to the cohort already present; final prevalence can exceed 40%.

We also replayed **258 earlier populations** on 50,000 new matches each. Here the primary candidate's maximum regret is **3.936**, versus **3.086** for all fifth. These populations include plausible alternatives to the new core assumptions. Thus the new core results improve our choice under a specific behavioral model; the earlier weakness remains relevant when judging that model.

Regret references come from broad searches rather than exhaustive optimization of all legal allocations. The principal uncertainty concerns actual player proportions, beliefs, and bidding habits. For scale, the core weighted-mean sampling standard error is about **0.0009** for the two close candidates; increasing simulation size alone will not resolve those behavioral assumptions.

### 6. What if very few people choose those two ideas?

The fresh core always has 8-18% exact all-fifth players and 8-22% dedicated F players. “Some students will choose this” also allows much smaller shares. We therefore added **36 populations**: Z=1/5/15%, F=0/10/20%, two bid habits and two reasoning mixtures. H=2%, T=15%, S=40%, with C taking the remainder. S is rebuilt for each Z/F/bid combination. Each population uses 50,000 new matches; all 19 candidates stay fixed.

| Z share | F share | Primary `10/14/60/5/11` | All fifth |
|---|---|---:|---:|
| 1% | 0% | 4.207 | **5.134** |
| 5% | 0% | 4.148 | **4.780** |
| 15% | 10% | **6.527** | 4.036 |
| 15% | 20% | **6.386** | 4.092 |

Each entry averages the two bid habits and two reasoning mixtures. F=0 removes the dedicated cohort; C/S can still choose similar allocations. In the low-bid Z=1%, F=0 case, only about 0.5-0.7% of all opponents allocate solely to castles 1-3.

The primary candidate's weakest case is **low bids, Z=15%, F=0, deep S**: **3.325**, versus a searched reference's **7.464**. The same type shares with raised bids give **6.523-6.757**. Both prevalence and opponents' responses to bidding habits matter.

The mechanism is visible in the generated allocations: with deep S, **24.7%** of opponents bid above 60 on castle 3 in the low-bid environment, versus **1.2%** in the raised-bid environment. Later S responses shift toward castle 4. This changes the competition faced by our 60 soldiers and helps explain the score reversal.

These absent-F populations belong in our plausible set. To show the decision consequence, we reweighted the existing results, giving them different total weights. The remaining weight stays on the original core. The 0.25 tail constraint selects the following among the 19 frozen candidates:

| Weight on absent-F populations | Selected allocation | Weighted mean | Worst-20% mean |
|---|---|---:|---:|
| 0% | `10/15/59/5/11` | 5.707 | 4.902 |
| 25% | `10/15/59/6/10` | 5.345 | 4.086 |
| 50% | `8/15/62/5/10` | 5.100 | 4.130 |
| 75% | `8/15/62/5/10` | 4.881 | 4.051 |

This is sensitivity to which population may occur, not the fraction of F players inside a match. These comparisons reuse existing evaluations; they do not establish an optimum over all allocations.

**My working recommendation:** use weighted mean with the tail constraint, include low-Z and absent-F populations in the main search, and carry **8/15/62/5/10** forward as the broader-coverage candidate alongside **10/15/59/5/11**. The former wins the 50/50 coverage comparison; the latter wins the original core. The next useful validation should also vary how S searches and how narrowly it clusters around exact integer bids. That uncertainty matters more than another tiny improvement under one fixed model.

For example, in one calculation-heavy validation population, **14.6%** of opponents put exactly **10** on castle 5. Moving from 10 to 11 can therefore be valuable. Varying the response generator will test whether this threshold advantage survives a different model of thoughtful players.

### Reproduction

Run `python -m experiments.run_game2_round3`. The [runner guide](experiments/run_game2_round3.md) explains each stage. [Population construction](modules/game2_field.md) gives the complete shares and beliefs; [metric definitions](modules/game2_metrics.md) give a worked tail calculation. Saved [selection](../results/game2_round3/selection.json), [fresh metrics](../results/game2_round3/metrics.json), [cohort tests](../results/game2_round3/cohort_sensitivity.json), and [coverage weights](../results/game2_round3/coverage_weights.json) contain the underlying numbers. All **57 tests** pass.

## 中文

本轮最重要的发现是：**人群覆盖范围对推荐的影响，大于微调优化指标。** 新核心模型中重兵第三城的方案领先，但集中前三城的专门人群较少时，优势会缩小或反转。因此，我们比较多个指标，并明确检验了此前缺少的情况。

### 1. 我们要优化什么？

比赛反复随机组成四人局，最后平均的是**名次奖励**。每座城由最高出价者获得，出价并列则平分城堡分；五座城总分决定名次，奖励为 **9、4、2、0**，名次并列则平分所占名次的奖励。我们始终提交同一个配兵。

建议以**合理人群下的平均奖励为主目标，同时限制不利人群中的损失**。最低分和最大 regret 用来检查薄弱处。

| 指标 | 回答什么问题 | 用途 |
|---|---|---|
| 加权平均奖励 | 在我们预期的各种人群中，整体表现如何？ | 主目标 |
| 最差 20% 均值 | 在这些可能性中较不利的一部分，表现如何？ | 防范人群判断失误 |
| 最低场景均值 | 哪个人群下的平均表现最差？ | 检查单个薄弱场景 |
| 最大估计 regret | 相比专门针对该人群的强策略，最多落后多少？ | 找出错失的机会 |

“最差 20%”按场景权重计算。例如某个人群权重为 10%，且完全落在最差 20% 内，就占这个尾部的一半。每项成绩已经是很多场比赛的平均；最低场景均值不保证每一场都能得到那么多分。

**为什么最大 regret 不应独自决定推荐？** 假设两种人群的权重为 90%、10%。A 的得分为 6、3，B 为 5.5、4，加权平均分别是 **5.70、5.35**。若两个场景的最佳成绩为 6、8，A 的最大 regret 为 **5**，B 为 **4**。最大化最低分、最小化最大 regret 都会选择 B，为改善较少出现的环境牺牲 0.35 平均奖励。是否值得，需要明确取舍。

本轮预先确定的规则是：最差 20% 均值距离搜索到的最佳值不超过 **0.25 分**，再最大化平均奖励。另比较容忍度 **0、0.10、0.50**。这个参数表达我们的偏好。平均 regret 无须再独立优化：固定参考成绩后，它等于一个常数减去加权平均奖励。

### 2. 怎样模拟聪明的对手？

按同学可能采取的思考方式建立人群：

| 类型 | 思路与例子 |
|---|---|
| H：简单模板 | 保留少量，例如 `20/20/20/20/20`；训练时占 0-5% |
| C：经过考虑的集中配兵 | 大部分重点争夺两三座城，其他城保留小额出价；选城和出价门槛有变化 |
| Z：全押第五城 | `0/0/0/0/100`，取得或平分最高价值城堡，希望其他分数分散 |
| F：集中前三城 | 尝试从低价值城堡取得六分，例如 `33/33/34/0/0`、`15/30/55/0/0`，并加入不均等出价和小额补充 |
| T：我们原来的思路 | `0/1/36/0/63`、`0/0/49/51/0` 及附近变化 |
| S：计算回应 | 预测完整对手人群，搜索强配兵，再考虑别人也可能做了相似分析 |

S 使用四层有限推理，每层三种信念，大部分权重放在第二至第四层。计算模拟提交前的分析。能力相近的学生，对其他人行为的判断仍可能不同，因此会选择不同配兵。

90 个新核心检验人群由五种环境、两种小额出价、三个 H 比例、三种 S 深度组合而成。在中心 **H=3%** 时，人数百分比如下：

| 人群环境 | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| 集中型较多 | 3 | 32 | 12 | 12 | 15 | 26 |
| 计算型较多 | 3 | 15 | 12 | 12 | 8 | 50 |
| 全押第五城较多 | 3 | 26 | 18 | 8 | 10 | 35 |
| 集中前三城较多 | 3 | 24 | 8 | 22 | 10 | 33 |
| 原始想法较多 | 3 | 21 | 8 | 12 | 28 | 28 |

H 还取 1%、5%，差额从 C 调整。小额出价范围为 0-4 或 1-5。五种环境各占 20% 场景权重，再分别将其中一种提高到 50%、其余各为 12.5%，检验五套替代权重。人数比例和场景权重作用不同：先分别模拟每个人群，再平均成绩。

这个设计体现了简单模板少、集中配兵会调整门槛、对手会进一步预判。影响最大的假设是 Z/F 有多常见，以及 S 怎样预测别人，下面另外检验这些假设。

### 3. 拿下前三城能否保证获胜？

拿下前三城得到 **6 分**；另一个人拿下第四、第五城得到 **9 分**，我们就是第二名。例如：

```text
我们：33 / 33 / 34 /  0 /  0
对手： 0 /  0 /  0 / 49 / 51
对手：30 / 30 / 30 / 10 /  0
对手：30 / 30 / 30 /  0 / 10
```

四人的城堡分为 **6、9、0、0**，奖励为 **4、9、1、1**。

**确实拿到六分，可以保证至少第二名：** 其他三个人总共只有九分，不可能有两个人都达到六分。但把 100 人全放前三城，不能保证拿下它们。前三城至少一座出价不超过 33，对手能够超过它。

我们初筛了全部 **5,151** 种只投前三城的合法配兵。训练平均分最好的候选是 **8/36/56/0/0**，新核心检验得到 **5.177 分**；平均分配的 `33/33/34/0/0` 只有 **3.241 分**。这个方向有价值，内部怎么分兵影响很大。

### 4. 搜索过程与新结果

初筛 **24,402** 个候选，细化比较 **619** 个，校准 **182** 个，最终固定 **19** 个比较。训练使用 90 个人群；检验重新生成 90 个人群，改变种子、人数比例、出价习惯并重新计算 S。每个检验人群使用 **200,000 场新对局**。

训练时，“平均分加尾部限制”选出 **10/14/60/5/11**。下表为新检验结果，前三项分数越高越好，regret 越低越好。

| 配兵 | 加权平均 | 最差 20% 均值 | 最低均值 | 最大估计 regret |
|---|---:|---:|---:|---:|
| 同学：`0/1/36/0/63` | 3.734 | 3.020 | 2.845 | 3.435 |
| 你的原方案：`0/0/49/51/0` | 2.790 | 2.311 | 2.240 | 4.643 |
| 全押第五城：`0/0/0/0/100` | 4.347 | 3.787 | 3.711 | 2.642 |
| 第二轮：`16/17/54/8/5` | 4.977 | 4.188 | 3.874 | 2.312 |
| 前三城搜索：`8/36/56/0/0` | 5.177 | 4.418 | 4.180 | 1.964 |
| 训练主选：`10/14/60/5/11` | 5.686 | **4.921** | 4.537 | 1.402 |
| 相邻候选：`10/15/59/5/11` | **5.707** | 4.902 | 4.515 | 1.423 |
| 训练尾部优选：`10/14/60/6/10` | 5.594 | 4.801 | **4.587** | **1.351** |

例如 **1.402 regret** 表示：主选最不利的那次比较中，独立搜索的参考策略平均每场多拿约 1.402 名次奖励。这个差距也取决于参考策略有多强。

相邻候选在六套场景权重下都取得最高的新检验均值，也满足 0.25 分尾部限制。训练主选的最差 20% 均值高 **0.019**，相邻候选的整体均值高 **0.020**。结果支持两个接近的候选；按同一套“均值加尾部限制”规则，新检验的领先者是相邻候选。

共同结构是第三城投入约 60 人，其他四城保留有竞争力的出价。它尝试拿第三城，再从对手集中到别处的城堡获得额外分数，以超过只拿第五城五分的玩家。具体小额出价仍取决于对手门槛。

### 5. 扩大检验范围后怎样？

18 个定向检验加入更多 Z/F、领先策略的跟随者、预判这些跟随者的对手。主选最大估计 regret 为 **2.232**，全押第五城为 **4.907**。其中“替换 40% 人群”的检验还包含原人群已有的该类玩家，最终总比例可能超过 40%。

另外对 **258 个旧人群** 各重新抽取 50,000 场比赛。这里主选最大 regret 为 **3.936**，全押第五城为 **3.086**。旧人群包含新核心模型之外仍合理的可能性。因此，新核心结果支持特定行为模型下的改进，旧检验暴露的薄弱处仍需用于判断模型。

Regret 的参考策略来自大范围搜索，尚未穷举全部合法配兵。主要不确定性来自真实人数比例、信念和出价习惯。作为量级参考，两个接近候选的核心加权平均抽样标准误约为 **0.0009**；单纯增加模拟场数无法解决行为假设问题。

### 6. 如果选择这两种思路的人很少呢？

新核心模型始终包含 8-18% 全押第五城、8-22% 专门集中前三城的玩家。“会有人这样做”也允许比例更小。因此补充 **36 个人群**：Z=1/5/15%、F=0/10/20%、两种小额出价、两种推理混合。H=2%、T=15%、S=40%，C 占剩余比例。每个 Z/F/出价组合重新生成 S；每个人群抽取 50,000 场新对局，19 个候选保持不变。

| Z 比例 | F 比例 | 主选 `10/14/60/5/11` | 全押第五城 |
|---|---|---:|---:|
| 1% | 0% | 4.207 | **5.134** |
| 5% | 0% | 4.148 | **4.780** |
| 15% | 10% | **6.527** | 4.036 |
| 15% | 20% | **6.386** | 4.092 |

每格平均两种出价与两种推理混合。F=0 表示没有单独的 F 人群，C/S 仍可能选出相似配兵。低额出价、Z=1%、F=0 时，实际只投前三城的玩家约占 0.5-0.7%。

主选最弱的场景是**低额出价、Z=15%、F=0、深层 S**：得到 **3.325**，参考策略得到 **7.464**。同样人数比例改成较高小额出价，主选可得 **6.523-6.757**。人数比例，以及对手对出价习惯的进一步回应，都会影响结论。

具体原因可以从配兵中看到：深层 S 下，低额出价环境中 **24.7%** 的对手在第三城投超过 60 人，较高出价环境中只有 **1.2%**。后几层 S 转向争夺第四城，改变了我们这 60 人面对的竞争，解释了得分反转的重要原因。

这些 F 缺席人群应纳入合理范围。为了看清决策如何变化，我们重新加权已有结果：给 F 缺席人群不同的总权重，剩余权重保留原核心模型。按 0.25 分尾部限制，19 个固定候选中选出：

| F 缺席人群的场景权重 | 选出的配兵 | 加权平均 | 最差 20% 均值 |
|---|---|---:|---:|
| 0% | `10/15/59/5/11` | 5.707 | 4.902 |
| 25% | `10/15/59/6/10` | 5.345 | 4.086 |
| 50% | `8/15/62/5/10` | 5.100 | 4.130 |
| 75% | `8/15/62/5/10` | 4.881 | 4.051 |

这里改变的是“会遇到哪种人群”的判断权重，不能读成一场比赛中 F 玩家占多少。这次比较复用已有检验，结论范围是 19 个固定候选。

**我的阶段性建议：** 使用加权平均加尾部限制，把低 Z、F 缺席人群纳入主要搜索，将 **8/15/62/5/10** 作为更广覆盖下的主候选，与 **10/15/59/5/11** 继续对照。前者在两类人群各占一半权重时领先，后者在原核心模型领先。接下来有价值的检验还包括改变 S 的搜索方式，以及它是否过度聚集在某几个整数出价。这比固定一个模型继续抠很小的得分提升更重要。

例如，一个计算型较多的检验场景中，**14.6%** 的对手恰好在第五城放 **10** 人，因此从 10 加到 11 可能很有价值。改变回应生成方式，可以检验换一种聪明玩家模型后，这个门槛优势是否仍然存在。

### 复现

运行 `python -m experiments.run_game2_round3`。[入口说明](experiments/run_game2_round3.md) 逐步解释流程；[人群构造](modules/game2_field.md) 给出完整比例与信念；[指标说明](modules/game2_metrics.md) 给出尾部均值的手算例子。[固定候选](../results/game2_round3/selection.json)、[新检验指标](../results/game2_round3/metrics.json)、[人群比例检验](../results/game2_round3/cohort_sensitivity.json)、[覆盖权重比较](../results/game2_round3/coverage_weights.json) 保存全部数字。**57 项测试通过。**
