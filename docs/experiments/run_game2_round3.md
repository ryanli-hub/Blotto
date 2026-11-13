# Game 2, round 3: choosing the objective

## English

Source: [run_game2_round3.py](../../experiments/run_game2_round3.py). Run commands from the project root.

Run from the project root:

```bash
python -m experiments.run_game2_round3
python -m unittest discover -s tests -v
```

The runner compares average reward, protection against unfavorable populations, and regret. It adds opponents who target castles 1-3 and an explicit group that puts 100 soldiers on castle 5. Results go to `results/game2_round3/`; the runner reads round 2's saved populations and reference allocations.

### Data flow

1. **Generate opponents.** `build_field` creates 90 training populations: five behavioral families × two secondary-bid habits × three H shares × three reasoning mixtures. Each family has 20% of the total scenario weight. [game2_field.md](../modules/game2_field.md) specifies the distributions, beliefs, and all weights.
2. **Build candidates.** Start with the existing broad pool, earlier reference strategies, and baseline candidates. Add all 5,151 legal allocations confined to castles 1-3, then the generated reasoning strategies and first-three examples.
3. **Search several objectives.** Screen with 1,024 games per population. Preserve strong candidates for mean reward, worst-20% mean, minimum reward, and maximum regret under six scenario priors. Add nearby integer transfers, rescore with 8,192 games, then calibrate finalists with 20,000. Every stage compares candidates on common opponent triples.
4. **Freeze the decision.** The primary rule maximizes weighted mean reward among candidates whose worst-20% mean is within 0.25 points of the best searched value. Also freeze winners for the other objectives, tail tolerances 0/0.10/0.25/0.50, five alternative priors, and the first-three-only restriction.
5. **Validate on new populations.** Rebuild the 90 populations with new random seeds, altered type shares and bid habits, and new reasoning responses. Search a reference independently for each population. Evaluate all frozen candidates and the reference on 200,000 new games per population. Record reward, paired reference gaps, and sampling standard errors.
6. **Audit broader assumptions separately.** Evaluate new cohort/copy/anticipation stresses and the 258 saved round-2 populations on 50,000 new games each. Their scores do not enter core selection. Some old populations remain plausible alternatives to the new core model.
7. **Test low or absent cohorts.** The exploratory supplement crosses Z=1/5/15%, F=0/10/20%, two bid habits, and two S mixtures, giving 36 populations. H=2%, T=15%, S=40%, and C receives the remainder. Rebuild S in each of 18 banks, allowing beliefs with zero F/Z. Within each bid habit, keep H/C/F/T distributions and the response RNG seed matched across shares. Independently search references and evaluate the 19 frozen candidates on 50,000 games per population. Run only this stage with `--cohort-sensitivity-only`.
8. **Explain coverage weights.** `coverage_weight_sensitivity` gives the 12 absent-F populations 0/25/50/75/100% total weight, split equally; the rest keeps the original core weights. It compares existing candidates without another strategy search. These exploratory preference comparisons use saved evaluations. F=0 removes the dedicated F cohort; C and S may still produce first-three allocations.

### What the objectives mean

The score matrix has one row per candidate and one column per population. Each entry is an average **ranking reward**, on the 0-9 scale.

- `weighted_mean`: average across possible populations using their scenario weights.
- `lower_tail_mean`: weighted average of the worst 20% of population mean rewards, including a fractional boundary weight when needed.
- `minimum`: lowest population mean reward.
- `maximum_regret`: largest gap to the searched reference across populations.
- `mean_regret`: weighted reference gap. With fixed references, minimizing this gives the same ordering as maximizing weighted mean reward.

The 0.25 tail tolerance expresses a willingness to trade some protection for higher average reward. It is fixed before validation. The lower tail concerns uncertainty about the opponent population; it is not a subset of individual matches. [game2_metrics.md](../modules/game2_metrics.md) gives a worked example.

`priors` tests equal family weights and five alternatives in which one family has 50% weight and each other family has 12.5%. These weights describe which population might occur. The H/C/Z/F/T/S shares describe players **inside** a population. Simulate each population separately before averaging its score.

### Stress interpretation

For three families, the cohort test replaces 40% of a base population with F or Z: `0.60 Q + 0.40 F/Z`. The resulting total cohort share also includes members already in Q. The base is the first saved population of each family: low secondary bids, H=1%, and the shallow reasoning mixture.

Copy tests replace 15% with a frozen leading strategy. Anticipation tests instead replace 15% with responses computed against the population containing those copies. These model beliefs during pre-submission analysis. Each entrant still submits one fixed allocation.

### Saved files

| File in `results/game2_round3/` | Content |
|---|---|
| `training_design.json`, `training_populations*` | Training parameters and complete joint distributions |
| `selection.json`, `training_scores.npz` | Search sizes, frozen choices, calibration scores |
| `core_design.json`, `core_validation_populations*` | New population parameters, weights, seeds, distributions |
| `core_comparison.json`, `metrics.json` | New scores, regret estimates, objective and prior comparisons |
| `stress_design.json`, `stress_populations*`, `targeted_stress.json` | Cohort and strategy-response stresses |
| `historical_stress.json` | New games against the 258 previously generated populations |
| `cohort_sensitivity*` | The 36 low-Z/absent-F cases, beliefs, populations, and scores |
| `coverage_weights.json` | Reweighting core versus absent-F populations among frozen candidates |

The search covers a broad candidate pool and local refinements. Regret is measured against searched reference strategies; a stronger reference can increase the reported gap. Sampling errors quantify random games conditional on the generated populations.

## 中文

源码：[run_game2_round3.py](../../experiments/run_game2_round3.py)。以下命令均在项目根目录运行。

在项目根目录运行上面的命令。本轮比较平均奖励、不利人群中的表现和 regret，加入集中前三城的对手，以及明确将 100 人全押第五城的对手。结果写入 `results/game2_round3/`；需要第二轮保存的人群和参考配兵。

### 计算流程

1. **生成对手。** `build_field` 生成 90 个训练人群：五种行为环境 × 两种小额出价习惯 × 三种 H 比例 × 三种推理深度混合。五种环境各占 20% 场景权重。[game2_field.md](../modules/game2_field.md) 给出全部分布、信念和比例。
2. **建立候选池。** 保留已有大候选池、旧参考策略和基准方案，加入全部 5,151 种只投前三城的合法配兵，再加入生成的推理策略和前三城变体。
3. **同时搜索多个目标。** 每个人群用 1,024 场初筛，保留在六套场景权重下，均值、最差 20% 均值、最低分和最大 regret 表现好的方案。加入附近整数调兵，用 8,192 场复筛，再用 20,000 场校准。每一步各候选面对相同的对手组合。
4. **固定选择。** 主规则是：最差 20% 均值距离搜索到的最佳值不超过 0.25 分，在此条件下最大化加权平均奖励。同时固定其他目标、0/0.10/0.25/0.50 容忍度、五套替代权重，以及只投前三城的候选。
5. **新人群检验。** 使用新种子、改变人数比例和出价习惯、重新计算推理回应，生成 90 个检验人群。每个人群独立搜索参考策略，再用 200,000 场新对局比较固定候选，记录奖励、与参考策略的配对得分差及抽样标准误。
6. **另外检查更广的假设。** 新增人群聚集、跟随和预判反制场景，并复查第二轮的 258 个已有人群，各用 50,000 场新对局。其得分不参与核心候选选择。部分旧人群仍是新核心模型之外的合理可能。
7. **检验某类玩家很少或缺席。** 探索性补充交叉 Z=1/5/15%、F=0/10/20%、两种出价和两种 S 深度，共 36 个人群。H=2%、T=15%、S=40%，C 分配剩余比例。18 个基础组合分别重新生成 S，允许信念中的 F/Z 为零。同一种出价下，改变人数比例时共用 H/C/F/T 分布与回应随机种子。独立搜索参考策略，每个人群用 50,000 场比较原先固定的 19 个候选。可用 `--cohort-sensitivity-only` 单独执行。
8. **解释覆盖权重的影响。** `coverage_weight_sensitivity` 读取已有得分，给 12 个 F 缺席人群合计 0/25/50/75/100% 的权重，内部等分，其余保留原核心权重。比较已有候选，不再搜索新配兵。F=0 表示没有单独的 F 人群，C、S 仍可能选择前三城配兵。

### 指标含义

得分矩阵每行是一种候选，每列是一种人群。每个数字都是 0-9 分范围内的平均**名次奖励**。

- `weighted_mean`：按场景权重计算的平均奖励。
- `lower_tail_mean`：表现最差的 20% 场景权重对应的平均奖励，边界场景按所需部分计入。
- `minimum`：最低的场景平均奖励。
- `maximum_regret`：所有场景中，与搜索参考策略之间最大的差距。
- `mean_regret`：参考差距的加权平均。参考策略固定时，最小化它与最大化加权平均奖励得到相同排序。

0.25 分容忍度表达愿意牺牲多少不利环境中的表现来换取更高均值，在检验前固定。最差 20% 指对手人群的不确定性，并非单场比赛的最差 20%。[game2_metrics.md](../modules/game2_metrics.md) 提供手算示例。

`priors` 比较五类环境各占 20%，以及某一类占 50%、其余各占 12.5% 的五套替代权重。这是“哪种人群可能出现”的权重。H/C/Z/F/T/S 是一个人群内部的玩家比例。先分别模拟每个人群，再按场景权重平均。

### 压力检验的解释

对三种环境，将基础人群的 40% 替换成 F 或 Z，即 `0.60 Q + 0.40 F/Z`。最后的该类总比例还包括 Q 中原有成员。基础人群取该环境保存的第一项：低额出价、H=1%、浅层推理混合。

跟随检验让 15% 玩家使用某个已固定的领先候选。预判检验则让 15% 玩家针对含有这些跟随者的人群计算回应。这模拟提交前的思考；每位玩家仍提交一个固定配兵。

### 输出与精度

`training_design.json` 和 `training_populations*` 保存训练设定与完整联合分布；`selection.json` 和 `training_scores.npz` 保存搜索规模、固定候选和校准得分；`core_design.json`、`core_validation_populations*` 保存新人群、比例和种子；`core_comparison.json`、`metrics.json` 保存得分及目标、权重比较。

`stress_design.json`、`stress_populations*`、`targeted_stress.json` 保存新增压力检验，`historical_stress.json` 保存对旧 258 个人群的新对局评估。

`cohort_sensitivity*` 保存低 Z、F 缺席等 36 个人群的参数、信念、完整分布与得分；`coverage_weights.json` 保存核心人群与 F 缺席人群之间的权重比较。

搜索使用较大的候选池与局部改进。Regret 相对搜索到的参考策略计算，更强的参考策略可能扩大差距。抽样误差衡量人群固定后随机对局造成的误差。
