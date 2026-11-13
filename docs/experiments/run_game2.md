# Game 2: reproduce the first experiment

## English

Source: [run_game2.py](../../experiments/run_game2.py). Run commands from the project root.

Run from the project root:

```bash
python -m experiments.run_game2
python -m unittest discover -s tests -v
```

To reuse the saved first run and run only the six follow-up scenarios:

```bash
python -m experiments.run_game2 --followup-only
```

The experiment follows the Game 1 workflow: define populations, search for a low-regret fixed allocation, freeze candidates, and evaluate fresh populations. Game 2 scores complete four-player matches, including castle ties and ranking ties.

### Population and sequence

1. Generate H, concentrated C, and neighborhoods TA/TB of `0/1/36/0/63` and `0/0/49/51/0`. Build S from one to three reasoning levels, each using three beliefs and several strong responses. See [population construction](../modules/game2_population.md).
2. Construct **54 training scenarios**: three C profiles × H shares 0/5/15% × S shares 35/65% of the remainder after H and T × T shares 0/20/40%. TA and TB split T equally. C profiles use normal, crowded, or avoided castle 5.
3. Search a five-soldier grid, every integer two-castle split, random allocations, anchors, and modeled responses. Screen with 2,048 games per scenario. Add local transfers, rescore with 8,192, and calibrate finalists with 20,000. Select the smallest maximum searched regret.
4. Freeze our candidates. Generate fresh C/T samples and retrain S with separate random streams. The new small-bid profile uses 2 to 6 soldiers on secondary castles and four reasoning levels.
5. Build **100 fresh population scenarios**: four profiles × H shares 0/10% × S shares 50/80% of the remainder × T shares 10/30/60% × TA's share within T 20/80%, plus one T-free scenario per profile.
6. Add **nine stress scenarios**: for each original profile, test 15% adopting our recommendation, 15% anticipating that adoption, and half of S adopting one shared recommendation.
7. For each of these **109 scenarios**, select a reference through a separate search and calibration draw. Then evaluate every fixed candidate and that reference on the same **200,000 fresh triples**. Pure H/C/S/T and the central mixture are separate explanatory benchmarks.
8. After inspecting those results, add **six follow-up scenarios** for `0/0/0/0/100`, which had the lowest maximum estimated regret. For each original profile, test 15% copying this allocation and 15% anticipating that copying. Keep all eight candidates fixed and run another 200,000 fresh triples per scenario. Retain the original 109 results and combine all **115 scenarios**.

If H has share (h), T has share (t), and S has fraction (s) of the remainder, actual shares are:

\[
H=h,\quad T=t,\quad C=(1-h-t)(1-s),\quad S=(1-h-t)s.
\]

The central mixture is **5% H + 26.25% C + 48.75% S + 20% T**. Each opponent independently draws from this mixture. S's levels 1/2/3 use weights 70/25/5% when its remainder share is 35%, 35/45/20% at 50%, and 15/35/50% at 65% or 80%. Four-level stress weights are 5/15/30/50%.

Because a match draws three opponents, expected payout varies cubically with population shares. Interior mixture proportions therefore need their own tests. Game 1's two-player equilibrium is not used as a Game 2 population. Equal expected self-play payout is (15/4=3.75), a symmetry check.

### Saved evidence

`results/game2/` contains:

| File | Content |
|---|---|
| `selection.json` | Candidate counts, training choice, frozen allocations |
| `training_scores.npz` | Finalist allocations and training score matrix |
| `design.json` | All population settings, mixtures, reasoning diagnostics, seeds |
| `populations.npz`, `population_index.json` | Full joint allocation distributions for every scenario |
| `comparison.json` | All 109 fresh results, reference allocations, paired standard errors |
| `references.json` | Central and pure-population explanatory comparisons |
| `followup_design.json`, `followup_populations.npz` | Six post-validation stress populations, seeds, and search-pool definition |
| `followup_comparison.json` | Independent results for the six additional scenarios |
| `combined_comparison.json` | All 115 scenarios, preserving the original and follow-up groups |

The reported regret is the fresh average payout gap to a searched reference. The reference is selected before the test games. Scores have sampling error; the search does not enumerate all 4,598,126 legal allocations. The report separates the training choice from its fresh performance.

The follow-up reconstructs each central population from the saved 15%-copy scenario, removing its training-choice point mass. Its reference search uses the initial candidate pool, saved finalists, and saved population supports. Independent random streams generate anticipators, calibrate references, and evaluate final games. The follow-up was introduced after the first validation; allocations remain those frozen before it.

## 中文

源码：[run_game2.py](../../experiments/run_game2.py)。以下命令均在项目根目录运行。

在项目根目录运行上面的两条命令，分别复现实验和检查计分、抽样、搜索等逻辑。

加上 `--followup-only` 可复用已保存的首轮结果，只运行六个追加场景。

沿用 Game 1 的流程：建立人群，寻找最大 regret 较低的固定方案，冻结候选，再检验新人群。Game 2 逐场计算四个人的完整结果，处理城堡并列和名次并列。

### 人群与实验顺序

1. 生成 H、集中型 C，以及 `0/1/36/0/63` 和 `0/0/49/51/0` 附近的 TA/TB。S 包含一到三层推理，每层采用三种信念并保留多个强回应。具体见[人群说明](../modules/game2_population.md)。
2. 建立 **54 个训练场景**：三种 C 出价习惯 × H 占 0/5/15% × 扣除 H、T 后 S 占 35/65% × T 占 0/20/40%。T 内 TA、TB 各一半。C 分别正常争夺、偏好或回避第五城。
3. 搜索五人步长网格、全部整数双城分配、随机配兵、原始方案及生成的回应。每个场景用 2,048 场初筛，再增加局部调兵，用 8,192 场复筛、20,000 场校准，选择最大搜索 regret 最小的方案。
4. 固定候选。换随机种子生成 C/T，并重新训练 S。新增小额出价较高的人群：次要城投 2 至 6 人，S 推理四层。
5. 建立 **100 个新场景**：四种习惯 × H 占 0/10% × 剩余人群中 S 占 50/80% × T 占 10/30/60% × T 内 TA 占 20/80%；另给每种习惯加入一个没有 T 的场景。
6. 增加 **九个压力场景**：对原三种习惯，分别测试 15% 采用我们的推荐、15% 预判别人采用推荐，以及一半 S 采用共同推荐。
7. 对这 **109 个场景**，分别用独立搜索和校准对局选择参考方案。然后让每个固定候选与参考方案面对同一批 **200,000 场新对局**。纯 H/C/S/T 和中心混合单独用于解释。
8. 查看首轮结果后，对最大估计 regret 最低的 `0/0/0/0/100` 增加 **六个场景**：原三种习惯分别加入 15% 模仿者和 15% 预判这种模仿的玩家。八个候选保持不变，每个场景再运行 200,000 场新对局。保留原 109 个结果，合并为 **115 个场景**。

若 H 占 (h)、T 占 (t)、S 占剩余人群的 (s)，实际比例为：H = (h)，T = (t)，C = ((1-h-t)(1-s))，S = ((1-h-t)s)。

中心人群为 **5% H + 26.25% C + 48.75% S + 20% T**。三个对手分别从整个混合中独立抽取。S 占剩余部分 35% 时，一/二/三层按 70/25/5% 混合；占 50% 时为 35/45/20%；占 65% 或 80% 时为 15/35/50%。四层压力测试使用 5/15/30/50%。

每场抽取三个对手，使期望奖励随人群比例呈三次变化，所以中间比例也要测试。Game 1 的双人均衡不作为 Game 2 的对手人群。四个人都从同一分布抽取配兵时，每人平均奖励为 (15/4=3.75)，用于检查对称性。

### 保存的证据

`results/game2/selection.json` 保存训练选择与固定候选；`training_scores.npz` 保存候选得分；`design.json` 保存比例、人群参数和种子；`populations.npz` 与索引文件保存每个场景的完整联合分布；`comparison.json` 保存 109 个新场景的得分、参考策略和配对标准误；`references.json` 保存解释用的单类人群与中心人群结果。

报告中的 regret 是相对于已搜索参考方案的新对局平均得分差。参考方案在检验对局之前选定。得分存在抽样误差；搜索没有遍历全部 4,598,126 种配兵。报告分别展示训练选择及其独立检验结果。

追加实验从已保存的 15% 模仿场景中扣除训练方案对应的点质量，恢复相同的中心人群。参考方案搜索使用初始候选、已保存的决赛候选和人群支持集；预判者生成、参考校准、最终检验采用三个独立随机流。`followup_design.json` 和 `followup_populations.npz` 保存六个场景的设计与人群，`followup_comparison.json` 保存结果，`combined_comparison.json` 合并全部 115 个场景并标明来源。追加实验是在首轮检验后设计的，候选仍使用检验前固定的八个方案。
