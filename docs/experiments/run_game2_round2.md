# Game 2, round 2: controlled population changes

## English

Source: [run_game2_round2.py](../../experiments/run_game2_round2.py). Run commands from the project root.

Run from the project root:

```bash
python -m experiments.run_game2_round2
python -m unittest discover -s tests -v
```

This experiment asks which opponent behaviors drive the first round's recommendations. It reuses the four-player scorer and evaluates complete legal allocations. Earlier results remain in `results/game2/`; new results go to `results/game2_round2/`.

### Inputs and population construction

1. `load_previous` loads the 115 previous population distributions and their reference allocations. Those populations now become development data. Every candidate is rescored on common new games.
2. `build_models` generates C separately conditional on choosing one, two, or three main castles. Reweight these distributions to set the one-castle share α exactly; the remaining two groups keep their 13:4 ratio. This preserves their internal choices when α changes.
3. Within the one-castle group, fraction z explicitly puts all 100 soldiers on castle 3, 4, or 5. Others use secondary bids and place the remainder on their main castle. Castle weights are 1:2:4, adjusted by the profile's fifth-castle preference. Exact all-in bids also occasionally occur naturally in the secondary-bid branch.
4. Hold H and the two T neighborhoods fixed within each phase. Generate S anew against each C model, using three beliefs and four reasoning levels. Use the same first three levels for both depth comparisons.

For example, α=30% and z=50% means 15% of C explicitly chooses an all-in allocation, 15% uses the other single-main-castle rule, and 70% chooses two or three main castles. These are shares **within C**.

### Development design

The main factorial design crosses:

| Factor | Settings |
|---|---|
| One-main-castle share α within C | 5%, 15%, 30%, 45% |
| Secondary bids | Low: 0/1/2/3; high: 2/3/4/5/6 |
| Fifth-castle preference | Normal, selection weight ×3, selection weight ×0.25 |
| Reasoning mixture | Three levels; or half of that mixture replaced by level 4 |

The explicit all-in fraction z is 50%. This gives **48 central factorial scenarios**. Add six matched controls with α=15%, low bids, and z=0%, giving 54. Compare fixed allocations on 200,000 new games in each central scenario to explain the effects.

Each factorial scenario also receives three population mixtures:

| Mixture | H | C | S | T |
|---|---:|---:|---:|---:|
| Central | 5% | 26.25% | 48.75% | 20% |
| T heavy | 0% | 12% | 48% | 40% |
| C heavy | 10% | 45% | 45% | 0% |

T splits equally between the two team ideas. This gives **162 new development scenarios**, plus the previous 115, for **277 total**.

Three-level S uses weights 15/35/50%. The deeper comparison is $S_{deep}=0.5S_3+0.5L_4$, giving level weights 7.5/17.5/25/50%. H/C/S/T shares stay fixed when depth changes.

### Search and fresh evaluation

`select` screens the broad allocation pool with 1,024 games per scenario, adds local integer transfers, rescores with 8,192 games, and calibrates finalists with 20,000. It chooses the smallest maximum searched regret and freezes the candidate list.

Fresh models use new population and response seeds, α=10/25/40%, z=20/80%, both bid habits, and all three fifth-castle preferences. Cross both reasoning depths with two new mixtures:

| Mixture | H | C | S | TA | TB |
|---|---:|---:|---:|---:|---:|
| TA popular | 0% | 14% | 56% | 24% | 6% |
| TB popular | 10% | 15% | 15% | 12% | 48% |

This gives **144 fresh base scenarios**. Additional tests give each distinct leading candidate the same treatment: 5% or 15% followers, or responders anticipating those followers, across three population profiles. Six further scenarios let 50% or 100% of S misjudge the popularity of castle 5.

Add **72 fresh C-heavy scenarios** to test concentration behavior at a higher population share. For each TA-popular population $Q$, use $0.60Q+0.35C+0.05H$: **5% H + 43.4% C + 33.6% S + 18% T**, with TA/TB at 14.4/3.6%. Reuse the same fresh C and S distributions, then draw new calibration and test games. This addition was planned during the development search to improve coverage. All candidates remain frozen for evaluation. With three distinct leading candidates, the complete fresh test has **258 scenarios**.

The full command includes this addition. To add it to an already completed main run, use `python -m experiments.run_game2_round2 --concentration-holdout-only`.

For each evaluation scenario, independently search and calibrate a strong reference, then compare it with all frozen candidates on **200,000 fresh games**. Estimated regret is the mean payout gap to that reference. Standard errors measure game sampling noise conditional on the generated populations. Factorial comparisons include the responses of S to the changed C population.

### Saved outputs

| File in `results/game2_round2/` | Purpose |
|---|---|
| `training_design.json`, `design.json` | Parameters, beliefs, seeds, and all mixture weights |
| `training_populations.npz`, `validation_populations.npz`, index files | Complete joint distributions |
| `selection.json`, `training_scores.npz` | Frozen candidates, search counts, calibration scores |
| `factorial.json` | Fixed-candidate scores and standard errors for 54 central comparisons |
| `comparison.json`, `grouped_summary.json` | Fresh scores and regret, with base, following, and mistaken-belief groups |
| `concentration_holdout_*`, `combined_comparison.json` | The 72 C-heavy cases and the complete 258-scenario comparison |

## 中文

源码：[run_game2_round2.py](../../experiments/run_game2_round2.py)。以下命令均在项目根目录运行。

在项目根目录执行上面的命令，分别复现实验和运行测试。

本轮研究哪些对手行为决定上一轮推荐。复用四人计分器，保留完整合法配兵。前一轮结果保存在 `results/game2/`，本轮写入 `results/game2_round2/`。

### 输入与人群构造

1. `load_previous` 读取此前 115 个人群及其参考配兵。它们现在作为开发数据，所有候选都用同一批新对局重新评分。
2. `build_models` 分别生成 C 中重点争夺一、二、三座城的人群，再通过权重精确设置单城型比例 α。其余两类保持 13:4，改变 α 时保留各类内部的配兵分布。
3. 单城型中比例 z 明确选择将 100 人全部放在第三、第四或第五城，其他人保留小额出价，再将剩余兵力放入重点城。选城权重为 1:2:4，并根据第五城偏好调整。小额出价分支偶尔也会自然产生全押配兵。
4. 每个阶段保持 H 和两种 T 变体不变。每改变一个 C 模型，就根据三种信念重新生成四层 S。深度对照共用完全相同的前三层策略。

例如 α=30%、z=50% 表示 C 中 15% 明确全押一城，15% 采用另一种单城集中规则，剩余 70% 争夺两三座城。这些都是 **C 内部比例**。

### 开发场景

主要实验完整交叉四个因素：C 中单城型占 **5/15/30/45%**；小额出价为 **0 至 3 人或 2 至 6 人**；第五城选择权重为 **正常、乘 3、乘 0.25**；S 使用 **前三层混合，或将其中一半替换为第四层**。

明确全押比例 z 固定为 50%，得到 **48 个中心对照场景**。另加六个 α=15%、低出价、z=0% 的匹配对照，共 54 个。每个中心场景用 200,000 场新对局比较固定配兵，解释因素变化的影响。

每个对照场景再测试三种人群比例：

| 混合 | H | C | S | T |
|---|---:|---:|---:|---:|
| 中心 | 5% | 26.25% | 48.75% | 20% |
| T 较多 | 0% | 12% | 48% | 40% |
| C 较多 | 10% | 45% | 45% | 0% |

T 内两个原始想法各占一半。这样得到 **162 个新开发场景**，加上此前 115 个，共 **277 个**。

前三层 S 按 15/35/50% 混合。加深推理时使用 $S_{deep}=0.5S_3+0.5L_4$，四层权重成为 7.5/17.5/25/50%。改变深度时，H/C/S/T 的人数比例保持不变。

### 搜索与新场景检验

`select` 每个场景用 1,024 场初筛大候选池，加入整数调兵方案，用 8,192 场复筛，再用 20,000 场校准。选择最大搜索 regret 最低的方案后，固定候选。

新检验使用新的配兵和推理种子，将 α 改为 **10/25/40%**，z 改为 **20/80%**，交叉两种小额出价、三种第五城偏好、两种推理深度，以及下列两个人群：

| 混合 | H | C | S | TA | TB |
|---|---:|---:|---:|---:|---:|
| TA 热门 | 0% | 14% | 56% | 24% | 6% |
| TB 热门 | 10% | 15% | 15% | 12% | 48% |

共 **144 个新基础场景**。对每个不同的主要候选，另外加入 5% 或 15% 跟随者，以及预判这些跟随者的反制者，在三种偏好下进行相同检验。还有六个场景让 50% 或 100% 的 S 猜错第五城的热门程度。

再加入 **72 个 C 较多的新场景**，检验较多人选择集中配兵的环境。对每个 TA 热门人群 $Q$，使用 $0.60Q+0.35C+0.05H$，得到 **5% H + 43.4% C + 33.6% S + 18% T**，其中 TA/TB 为 14.4/3.6%。保留同一批新 C、S 分布，重新抽取校准和检验对局。这个补充在开发搜索期间确定，用于完善覆盖范围；检验时所有候选保持固定。主要候选有三个不同配兵时，最终共 **258 个新场景**。

完整运行会自动执行这一步；若主实验已经完成，可运行 `python -m experiments.run_game2_round2 --concentration-holdout-only` 单独补充。

每个检验场景先独立搜索、校准一个强参考策略，再让它与所有固定候选面对 **200,000 场新对局**。估计 regret 是与该参考策略的平均奖励差。标准误衡量生成的人群固定后，对局抽样带来的误差。因素对照包含 S 对 C 变化作出的回应。

### 输出

`training_design.json`、`design.json` 保存参数、信念、种子和比例；两份 `populations.npz` 及索引保存完整联合分布；`selection.json`、`training_scores.npz` 保存搜索数量、固定候选和校准分数；`factorial.json` 保存 54 个中心对照的得分与标准误；`comparison.json`、`grouped_summary.json` 保存新人群结果及基础、跟随反制、错误信念三组汇总。

`concentration_holdout_*` 保存 C 较多的 72 个补充场景；`combined_comparison.json` 合并全部 258 个新场景。
