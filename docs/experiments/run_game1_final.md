# Game 1: final population and objective revision

## English

Source: [run_game1_final.py](../../experiments/run_game1_final.py). Run commands from the project root.

Run from the project root:

```bash
python -m experiments.run_game1_final
python -m unittest discover -s tests -v
```

The experiment asks whether `8/9/10/11/62` remains a good submission after changing our objective and how thoughtful opponents are generated. Results go to `results/game1_final/`; previous results remain in their existing folders.

### What transfers from Game 2?

We use weighted average reward as the main objective, protect performance in unfavorable populations, include the possibility that a familiar strategy group is absent, and vary the reasoning model. Game 1's reward remains the sum of castle points in a two-player match.

For Game 1, expected reward is linear in the opponent population. Averaging scores across population scenarios gives exactly the same result as scoring against their weighted mixture. Thus the highest weighted mean can be found by DP. Each scenario's regret reference is also an exact DP optimum. The tail constraint depends on several scenarios together, so the search enumerates all **4,598,126** legal allocations.

### Computation in order

1. `build_field` creates 80 training populations. The five families emphasize concentration, calculation, our initial 2/4/5 ideas, absence of that group, or avoidance of castle 5. Each family crosses two small-bid habits, two response-quality settings, two H shares, and two reasoning-depth mixtures. [game1_field.md](../modules/game1_field.md) specifies all shares and mechanisms.
2. `priors` gives each family 20% weight. Five alternatives put 50% on one family and 12.5% on each other family. These weights describe possible populations; H/C/T/S percentages describe players inside a population.
3. `search_objectives` enumerates every legal allocation. It finds the global best mean, worst-20% mean, minimum, maximum-regret solution, and mean subject to tail tolerances 0/0.10/0.25/0.50 under every prior. The primary choice uses equal family weights and tolerance 0.25 castle points. See [game1_objectives.md](../modules/game1_objectives.md).
4. `freeze_candidates` retains each distinct objective/prior winner and five previous allocations. Selection is saved before generating fresh populations.
5. Generate two independent suites of 80 populations using seeds `seed+10000` and `seed+20000`. Change C/T bids, response quality, beliefs, and sampling orders. `evaluate_panel` computes the fixed candidates' scores and exact regret; no random match simulation is needed. The combined comparison gives each suite half the weight.
6. On a representative weighted mixture within each fresh family, test 5% and 15% copies, responders anticipating those copies, and direct counters. Target each of the 17 frozen candidates in turn and score every candidate on the same resulting populations, giving 510 tests. This expanded the initial 90-case audit after the main validation so the final contenders received the same treatment.
7. Reevaluate the 5,624 saved historical populations from `results/structure/` and check the original game's equilibrium separately. Stress and equilibrium results do not enter the training objective.

### Reading the outputs

Each score is expected **castle points out of 15**. The worst-20% mean averages the least favorable 20% of scenario weight. The minimum is the lowest scenario mean. Maximum regret is the largest gap to that scenario's exact optimum. The scores are exact conditional on generated population distributions; changing those distributions tests uncertainty about behavior.

The selection file identifies the preselected primary: `3/3/13/13/68` in this run. Validation also reports which frozen candidate leads under each objective. The final reviewed recommendation, `3/8/13/11/65`, weighs fresh performance and older model coverage; `decision.json` records that judgment separately. The runner regenerates all numerical evidence and `diagnostics.json`; it leaves the reviewed decision unchanged. After rerunning with changed parameters, reassess the decision against the new outputs.

| File in `results/game1_final/` | Purpose |
|---|---|
| `training_design.json`, `training_populations.npz` | Population mechanisms, beliefs, and marginal distributions |
| `search.json`, `selection.json` | Exhaustive optima, objective/prior choices, frozen candidate list |
| `training.json`, `validation1.json`, `validation2.json`, `validation.json` | Metrics and comparisons under each prior |
| Matching `*_scores.npz` | Candidate-by-population scores, exact optima, and reference allocations |
| `validation*_design.json`, `validation*_populations.npz` | Independently regenerated populations and parameters |
| `stress_design.json`, `stress.json`, `historical.json` | Targeted and previous-population audits |
| `diagnostics.json`, `decision.json` | Reproducible behavior/score breakdown and the separately recorded final review |
| `equilibrium.json`, `run.json` | Equilibrium check, counts, arguments, and runtime |

Every new candidate is a fixed legal integer allocation totaling 100. The runner reuses the general weighted metrics in `game2_metrics.py`; that module operates on score matrices and has no four-player scoring assumptions.

## 中文

源码：[run_game1_final.py](../../experiments/run_game1_final.py)。以下命令均在项目根目录运行。

在项目根目录运行上面的命令。本轮检验：改变评价目标和聪明对手的生成方式后，`8/9/10/11/62` 是否仍适合提交。输出写入 `results/game1_final/`，此前结果保留。

### 从 Game 2 借鉴什么？

以加权平均得分为主目标，保护不利人群中的表现，允许我们熟悉的某类玩家缺席，并改变推理模型。Game 1 仍按两人对局的城堡分之和计分。

Game 1 的期望得分对人群分布是线性的：按权重平均不同人群下的得分，等于面对这些人群加权混合后的得分。因此，最高加权平均分可以由 DP 精确求出。每个场景的 regret 参考也是精确 DP 最优值。尾部限制同时涉及多个场景，所以枚举全部 **4,598,126** 种合法配兵进行优化。

### 计算顺序

1. `build_field` 建立 80 个训练人群。五种环境分别强调集中配兵、计算回应、我们的第 2/4/5 城初步思路、该类玩家缺席，以及避开第五城。每种环境交叉两种小额出价、两种回应质量、两个 H 比例、两种推理深度。[game1_field.md](../modules/game1_field.md) 给出全部比例和生成方法。
2. `priors` 默认给五种环境各 20% 权重。五套替代权重把一种提高到 50%，其余各为 12.5%。这些权重描述哪种人群可能出现；H/C/T/S 则描述一个人群内部的玩家构成。
3. `search_objectives` 枚举所有合法配兵，对每套权重分别找到均值、最差 20% 均值、最低分、最大 regret 的全局最优解，并计算尾部容忍度为 0/0.10/0.25/0.50 时的最优均值。主选使用五类等权、容忍度 0.25 城堡分。具体见 [game1_objectives.md](../modules/game1_objectives.md)。
4. `freeze_candidates` 保留各目标与权重产生的不同配兵，加上五个旧候选。在生成新人群前保存固定选择。
5. 分别使用 `seed+10000`、`seed+20000` 生成两组独立的 80 个人群，改变 C/T 出价、回应质量、信念和抽样顺序。`evaluate_panel` 精确计算固定候选的得分与 regret，无需随机模拟对局。合并比较时两组各占一半权重。
6. 对每类新环境的加权代表人群，加入 5% 或 15% 跟随者、预判这些跟随者的回应者，以及直接反制者。依次针对 17 个固定候选生成检验人群，所有候选面对同样的这些人群，共 510 项。在主检验后，将最初 90 项审查扩展到这一范围，使最终比较的候选接受相同检验。
7. 重新评价 `results/structure/` 保存的 5,624 个旧人群，并单独检查原博弈均衡。压力与均衡结果不进入训练目标。

### 怎样读输出？

得分是期望**城堡分，满分 15**。最差 20% 均值取表现最差的 20% 场景权重进行平均；最低分是最低的场景均值；最大 regret 是相对于该场景精确最优得分的最大差距。给定生成的人群分布，得分可以精确计算；改变分布用于检验行为假设的不确定性。

`selection.json` 记录事先选定的主选，本次为 `3/3/13/13/68`。检验还报告固定候选中各指标的领先者。综合新检验表现和旧模型覆盖后，最终建议为 `3/8/13/11/65`，单独写入 `decision.json`。入口重新生成全部数值证据和 `diagnostics.json`，保留这份最终判断；改变参数重新运行后，需要根据新输出重新评估选择。

`training_design.json` 和 `training_populations.npz` 保存人群机制、信念与边际分布；`search.json`、`selection.json` 保存穷举结果和固定候选；`training.json`、`validation1.json`、`validation2.json`、`validation.json` 保存各套权重下的指标；同名 `*_scores.npz` 保存完整得分矩阵、精确最优值和参考配兵。

`validation*_design.json`、`validation*_populations.npz` 保存新人群；`stress_design.json`、`stress.json`、`historical.json` 保存压力检验；`equilibrium.json`、`run.json` 保存均衡检查、数量、参数和耗时。

每个新候选都是总和为 100 的合法整数配兵。入口复用 `game2_metrics.py` 中的通用加权指标；该模块只处理得分矩阵，不依赖四人计分规则。
