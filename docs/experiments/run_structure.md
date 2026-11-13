# `run_structure.py`

## English

Source: [run_structure.py](../../experiments/run_structure.py). Run commands from the project root.

This experiment adds a population **T** focused on castles 2, 4, and 5, starting from `(2,16,1,37,44)` and `(1,14,1,37,47)`. It tests whether the current `(8,9,10,11,62)` remains a strong fixed submission when this group is common.

```bash
python -m experiments.run_structure
```

Defaults: `--output results/structure --seed 20650619 --samples 4000`. The seed controls new response sampling; `--samples` controls each fresh C profile. The runner reads the existing files in `results/anticipation/` and the equilibrium benchmarks in `results/revised/`. On another machine, install `requirements.txt` and use `python`.

### 1. Define the new cohort

Training uses four versions of T. Validation changes their weights or allocation ranges:

| Training cohort | Definition | Validation cohort | Definition |
|---|---|---|---|
| `exact_A` | All use `(2,16,1,37,44)` | `A_heavy` | 80% A, 20% B |
| `exact_B` | All use `(1,14,1,37,47)` | `B_heavy` | 20% A, 80% B |
| `local` | Uniform legal allocations near both examples | `shifted` | Higher main bids, weighted toward 18 on castle 2 and 40 on castle 4 |
| `broad` | Wider ranges with small bids on castles 1 and 3 | `overbid` | Castles 1 and 3 use 2–5 soldiers; main bids also vary |

[opponents.md](../modules/opponents.md) specifies every bound and weight. Every allocation is an integer vector totaling 100. T retains its own allocation distribution throughout each scenario.

### 2. Keep the cohort's share distinct from the responding share

Let **Q** be an earlier complete opponent population, **α** the actual T share, and **R** the distribution of new responders. The two scenarios are

\[
P_{\rm fixed}=(1-\alpha)Q+\alpha T,
\qquad
P_{\rm responsive}=\alpha T+(1-\alpha)(0.85Q+0.15R).
\]

Responders replace 15% of the players outside T. For example, at `α=40%`, the responsive population is **40% T + 51% Q + 9% R**. T stays at 40%.

To generate R, players form beliefs `(1−β)Q+βT`. Training uses `β = α−10%, α, α+10%`, clipped to `[0,1]` and deduplicated. Each belief contributes 24 sampled allocations within 0.10 points of its own optimal score. Those samples receive equal weights. [dynamics.md](../modules/dynamics.md) explains the near-best response algorithm.

### 3. Search four share ranges

All **296 previously observed base populations** become development data: the first 74, the next two suites containing 148, and the final earlier suite containing 74. Retain another **3,034 earlier anticipation and direct-counter scenarios**, using their original 15% cap. Training adds T shares **10%, 25%, 40%, and 60%**, each with four cohorts and both fixed and responsive cases. The full search therefore contains **12,802 scenarios**.

First run a **baseline control** on the 296 bases and 3,034 retained scenarios before adding T. Then, for each cap of 10%, 25%, 40%, or 60%, [robust.py](../modules/robust.md) searches all **4,598,126** legal allocations over the T scenarios up to that cap, always keeping the bases and earlier threats. It minimizes maximum regret, using each scenario's unrestricted DP optimum as the benchmark. The earlier 0.10-point score-preservation constraint is removed in every search. Comparing the baseline control with the T searches separates the effect of adding T from removing that constraint.

The selected recommendation is the **60% cap** result, chosen by this objective before examining final validation scores. A separate fixed-only diagnostic removes the new responses to T while preserving the earlier threats, measuring how reaction to T changes the choice.

For fixed Q and T, regret is convex in α, so endpoint bounds cover intermediate shares. R is rebuilt for each share, so the responsive search covers its specified share grid. The denser validation grid checks additional shares. At a fixed α and fixed R, the fixed and responsive endpoints also bound intermediate response fractions from 0 to 15% of the remainder.

### 4. Validate on fresh bases and changed behavior

Before selecting candidates, generate **74 fresh base populations** with seed **20891413**. Use the four validation cohorts above, shares **5%, 10%, 15%, 25%, 35%, 40%, 55%, and 60%**, and both response cases. Including the bases, this gives **4,810 cohort-validation scenarios**.

Validation beliefs use `β = α−15%, α+5%, α+15%`, clipped and deduplicated. Their response tolerance is 0.05 points; response sampling uses seed `20891413+500`. This changes the base samples, the cohort structure, the beliefs, and the response quality.

Keep all selected candidates fixed. Then rebuild the earlier peer, anticipation, further-response, and direct-counter checks on the fresh bases, with added shares up to 15%. Further responders face a common pool of the distinct current and selected allocations, and every candidate faces the same counter distributions. This adds **814 non-base scenarios when the two allocations differ**, or 666 if they coincide. Seeds add 700 for peers, 1000 for feedback, and 2000 plus the candidate index for direct counters to the fresh base seed.

Report cohort results, fresh earlier-threat results, and their combined maximum regret separately. Also compare fixed and responsive cases, share caps, pure T populations, and the saved equilibrium benchmarks. Original candidates, both user examples, and the previous defensive candidate remain in the comparisons. The earlier base-only probe is archived as `base_only_comparison.json` and `base_only_design.json`; final validation uses the new seed above.

### Outputs

- `design.json`: shares, seeds, beliefs, response settings, and objective.
- `cohorts.json`: complete weighted allocation supports and parameters for training and validation T.
- `scenario_metadata.json`: each scenario's actual cohort share, response fraction, and beliefs.
- `populations.npz`: named training and validation marginal arrays; each population is `5 × 101`.
- `fresh_legacy.json`: fresh peer, anticipation, feedback, and direct-counter populations.
- `comparison.json`: the baseline control, all T searches, selected allocation, scores, regrets, separate and combined validation, cap comparisons, and benchmarks.

The historical files remain available. Use a different `--output` directory to preserve a separate run.

## 中文

源码：[run_structure.py](../../experiments/run_structure.py)。以下命令均在项目根目录运行。

本实验加入重点争夺第 2、4、5 城的人群 **T**，以 `(2,16,1,37,44)` 和 `(1,14,1,37,47)` 为起点，检验这类玩家较多时，当前 `(8,9,10,11,62)` 是否仍适合作为固定提交。

```bash
python -m experiments.run_structure
```

默认参数：`--output results/structure --seed 20650619 --samples 4000`。种子控制新反制的抽样；`--samples` 控制每种新 C 人群的样本数。程序读取 `results/anticipation/` 中的已有文件，以及 `results/revised/` 中的均衡基准。其他机器安装 `requirements.txt` 后使用 `python`。

### 1. 定义新人群

训练使用四种 T，验证时改变其权重或配兵范围：

| 训练人群 | 定义 | 验证人群 | 定义 |
|---|---|---|---|
| `exact_A` | 全部使用 `(2,16,1,37,44)` | `A_heavy` | 80% A、20% B |
| `exact_B` | 全部使用 `(1,14,1,37,47)` | `B_heavy` | 20% A、80% B |
| `local` | 两个例子附近的合法配兵等权分布 | `shifted` | 主攻城投入更高，第 2 城偏向 18 人，第 4 城偏向 40 人 |
| `broad` | 更宽的范围，第 1、3 城仍小额投入 | `overbid` | 第 1、3 城各放 2–5 人，主攻城投入也变化 |

所有范围与权重见 [opponents.md](../modules/opponents.md)。每个配兵都是总和为 100 的整数向量。每个场景中的 T 保持自身配兵分布不变。

### 2. 区分新人群比例与反制者比例

用 **Q** 表示一个完整的旧对手人群，**α** 表示 T 的实际比例，**R** 表示新反制者的配兵分布。两个场景分别为

\[
P_{\rm fixed}=(1-\alpha)Q+\alpha T,
\qquad
P_{\rm responsive}=\alpha T+(1-\alpha)(0.85Q+0.15R).
\]

反制者替换 T 以外玩家中的 15%。例如 `α=40%` 时，允许反制的人群为 **40% T + 51% Q + 9% R**，T 仍占 40%。

生成 R 时，玩家对人群的判断为 `(1−β)Q+βT`。训练使用 `β = α−10%、α、α+10%`，限制在 `[0,1]` 内并去重。每种判断抽取 24 个配兵，其得分距离该判断下的最优分数至多 0.10 分，然后将这些样本等权混合。近似最佳回应算法见 [dynamics.md](../modules/dynamics.md)。

### 3. 搜索四种比例上限

全部 **296 个已观察基础人群**转为开发数据：最初 74 个、随后两批共 148 个，以及此前最后一批 74 个。再保留 **3,034 个此前的预判与直接反制场景**，沿用原来的 15% 上限。训练加入 T 的比例为 **10%、25%、40%、60%**，每个比例搭配四种 T，以及固定和允许反制两种情况。完整搜索共 **12,802 个场景**。

先在 296 个基础人群和 3,034 个保留场景上，进行**尚未加入 T 的基准对照搜索**。随后对 10%、25%、40%、60% 各个上限，[robust.py](../modules/robust.md) 在该上限以内的 T 场景上搜索全部 **4,598,126** 种合法配兵，同时始终保留基础人群和此前的威胁。目标是最小化最大 regret，各场景基准为无约束 DP 最优得分。每次搜索都取消此前“基础得分最多损失 0.10 分”的保护条件。比较基准对照与加入 T 后的结果，可以区分新人群和取消保护条件各自的影响。

推荐方案按最终验证前确定的目标，选择 **60% 上限**的搜索结果。另外做固定场景诊断：只去掉针对新 T 的反制，保留此前的威胁，检查其他玩家回应 T 会怎样改变选择。

固定 Q、T 时，regret 随 α 为凸函数，端点界可覆盖中间比例。R 会在不同占比下重新生成，因此允许反制的搜索覆盖设定的比例网格，再用更密的验证网格检查额外比例。在固定 α、R 时，固定场景和允许反制场景两端，也能约束反制者占其余玩家 0 至 15% 的中间比例。

### 4. 用新人群与改变后的行为检验

选择候选前，以种子 **20891413** 生成 **74 个新基础人群**。搭配上表四种验证 T，使用 **5%、10%、15%、25%、35%、40%、55%、60%** 八个比例，以及两种反制情况。连同基础人群，共 **4,810 个新人群验证场景**。

验证判断改为 `β = α−15%、α+5%、α+15%`，同样限制范围并去重。反制容差收紧为 0.05 分，抽样种子为 `20891413+500`。这些检验同时改变基础样本、新人群结构、判断和反制质量。

保持选出的候选固定，再在新基础人群上重建此前的同层、预判、进一步反制和直接针对检验，新增比例上限为 15%。进一步反制者面对当前与选定配兵去重后的共同人群；每个候选面对相同的反制分布。若两个配兵不同，增加 **814 个非基础场景**；若相同，则增加 666 个。相对新基础种子，同层抽样加 700，反馈抽样加 1000，直接反制加 2000 与候选序号。

分别报告 T 场景、重新生成的旧威胁，以及两者合并后的最大 regret。另比较固定与允许反制情况、各比例上限、纯 T 人群和保存的均衡基准。比较对象保留原始候选、两个用户配兵，以及此前的防守备选。较早仅保留基础人群的试算存档为 `base_only_comparison.json` 和 `base_only_design.json`；最终验证使用上述新种子。

### 输出

- `design.json`：比例、种子、判断、反制设置和优化目标。
- `cohorts.json`：训练与验证 T 的完整加权配兵及参数。
- `scenario_metadata.json`：每个场景的实际 T 比例、反制比例和判断。
- `populations.npz`：训练与验证的名称和边际概率数组，每个人群为 `5 × 101`。
- `fresh_legacy.json`：重新生成的同层、预判、反馈与直接反制人群。
- `comparison.json`：基准对照、全部 T 搜索、选定配兵、得分、regret、分别与合并的验证结果、比例上限比较和基准。

旧文件继续保留。使用不同的 `--output` 目录可单独保留另一轮结果。
