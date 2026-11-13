# `run_experiments.py`

## English

Source: [run_experiments.py](../../experiments/run_experiments.py). Run commands from the project root.

The runner compares four fixed Game 1 allocations: the teammate's `(2,16,1,37,44)`, the previous `(1,2,2,40,55)` and `(2,2,3,39,54)`, and a new allocation selected by exhaustive search. Scores are expected castle points out of 15.

Run from the project directory:

```bash
python -m experiments.run_experiments
```

Defaults are `--seed 20261103 --samples 4000 --output results/revised`. On another machine, install `requirements.txt` and use `python` as the interpreter. `--samples` sets the number of generated C allocations per profile.

For a later experiment, import `build_population_suite(samples=4000, seed=20261103)`. It returns the same 40 selection and 34 validation populations, their metadata, and the base C marginal tables. Changing the seed generates a fresh suite without running the allocation search.

### 1. Construct the populations

**H** equally mixes `(20,20,20,20,20)`, `(7,13,20,27,33)`, and `(0,0,0,50,50)`. **C** concentrates on two to four castles and usually places one or two soldiers elsewhere. Its three profiles are `base`, `overbid` (larger small bids and more rounding/adjustments), and `avoid_high` (less frequent focus on castle 5). [opponents.md](../modules/opponents.md) specifies their sampling probabilities.

**S** contains finite-reasoning players. For each C profile and actual H share `h`, construct beliefs with H shares `h−0.05`, `h`, and `h+0.05`, clipped to `[0,0.15]` and deduplicated. Cross these with three C beliefs, each mixing 70% of the actual profile with 30% of one reference profile. Shuffle the beliefs with a seeded generator.

Each belief produces 24 allocations per reasoning level, each within 0.10 points of its own optimum. Level 1 responds to its H/C belief. Higher levels mix that belief with the equal mixture of completed lower levels; the assumed lower-level share ranges from 0.35 to 0.65 across shuffled beliefs. [dynamics.md](../modules/dynamics.md) explains sampling and the score-gap checks.

An actual scenario is

\[
Q=hH+(1-h)[(1-s)C+sS].
\]

Here `s` is S's share among the remaining players. At `h=0.10, s=0.50`, the actual proportions are 10% H, 45% C, and 45% S. The following styles determine `s` and the level mixture within S:

| Style | `s` | Levels 1 / 2 / 3 within S |
| --- | ---: | --- |
| `manual_heavy` | 25% | 70% / 25% / 5% |
| `balanced` | 50% | 35% / 45% / 20% |
| `computation_heavy` | 75% | 15% / 35% / 50% |

S is rebuilt for each H share and C profile; styles combine those same level distributions with different weights.

### 2. Select on 40 training scenarios

The three C profiles × four H shares `{0%,5%,10%,15%}` × three styles give **36 scenarios**. Four more use `base/balanced`, one for each H share, and replace 25% of S with shared advice. Advice consists of three near-best responses to `5% H + 95% base C`, sampled with a 0.05-point tolerance and weighted 60% / 30% / 10%.

For each scenario Q, [game.md](../modules/game.md)'s DP computes its highest achievable score. Regret is that score minus a candidate's score. [robust.md](../modules/robust.md) enumerates all **4,598,126** legal allocations and selects the one with the smallest maximum regret across these 40 scenarios.

### 3. Evaluate fixed candidates on 34 validation scenarios

| Group | Construction | Count |
| --- | --- | ---: |
| `fresh` | Fresh samples of all three C profiles; H at 5% or 15%; all three styles | 18 |
| `shifted` | Two changed C mechanisms; H at 0% or 15%; all three styles | 12 |
| `deep` | Fresh base C; H at 5% or 15%; `s=75%`; four levels weighted 5% / 15% / 30% / 50%; tolerance 0.05 | 2 |
| `crowded` | Fresh base/balanced scenarios at 5% or 15% H; replace 50% of S with freshly generated advice | 2 |

The two changed mechanisms start from `base`. `higher_small_bids` assigns secondary bids 0/1/2/3/4 with probabilities 2%/8%/25%/40%/25%. `rounding_and_avoidance` sets five-soldier rounding probability to 75%, castle-5 subset weight multiplier to 0.25, and lognormal noise sigma to 0.35. Shifted and deep players use the fresh three C profiles as belief references.

The new candidate is selected using training regret, then held fixed for all validation scores. The runner also evaluates every legal one-soldier transfer from that candidate to inspect nearby alternatives.

### 4. Check equilibrium diagnostics

The runner loads `results/equilibrium.json` if present, otherwise computes E, then checks it with a full-game best response. Separately, it fixes 5% H and 47.5% base C and lets the remaining 47.5% jointly adjust using double oracle, with tolerance `1e-6` and at most 1,500 iterations. These two diagnostic populations receive their own candidate scores and regrets after selection.

### Reproducibility and outputs

Let `b` be `--seed`. Profile seeds add their zero-based position to the C seed below. Each belief generator uses its seed for belief permutation and successive response-sampling seeds.

| Population group | C seed | Belief generator seed | Advice seed |
| --- | --- | --- | --- |
| Training | `b` | `b+200` | `b+100` |
| Fresh / crowded | `b+10000` | `b+10200` | `b+10100` |
| Shifted | `b+20000` | `b+20200` | — |
| Deep | Reuse fresh | `b+30000` | — |

Files in `results/revised/`:

- `design.json`: experiment settings and existing candidates.
- `populations.json`: exact scenario marginals, C parameters, advice allocations, and reasoning diagnostics.
- `comparison.json`: exhaustive search, candidate scores/regrets, central H/C/S component scores, validation groups, and equilibrium diagnostics.
- `neighbors.json`: scores and regrets for one-soldier transfers.
- `adaptive_diagnostic.json`: the jointly adjusted distribution and solver residual history.

Rerunning into the same directory replaces these outputs. To preserve a separate run, pass `--output results/revised_seed2 --seed 20261203`.

## 中文

源码：[run_experiments.py](../../experiments/run_experiments.py)。以下命令均在项目根目录运行。

主程序比较四个固定的第一局配兵：队友的 `(2,16,1,37,44)`、之前的 `(1,2,2,40,55)` 和 `(2,2,3,39,54)`，以及穷举搜索得到的新配兵。得分是期望城堡分，满分 15 分。

在项目目录运行：

```bash
python -m experiments.run_experiments
```

默认参数为 `--seed 20261103 --samples 4000 --output results/revised`。其他机器安装 `requirements.txt` 后，可将解释器改为 `python`。`--samples` 指定每种 C 配兵规则生成多少个样本。

后续实验可导入 `build_population_suite(samples=4000, seed=20261103)`。它返回同样的 40 个选策略人群、34 个验证人群、相关设置及 base C 的边际分布。更换种子可以生成一组新人群，调用过程只生成数据。

### 1. 构造对手人群

**H** 将 `(20,20,20,20,20)`、`(7,13,20,27,33)`、`(0,0,0,50,50)` 等权混合。**C** 重点争夺二到四座城，其他城通常放一到两人。三种规则为 `base`、`overbid`（更高的小额投入，更多取整和微调）、`avoid_high`（较少重点争夺第 5 座城）。具体抽样概率见 [opponents.md](../modules/opponents.md)。

**S** 包含有限层推理的玩家。对于每种 C 规则和实际 H 比例 `h`，构造 H 比例为 `h−0.05`、`h`、`h+0.05` 的判断，限制在 `[0,0.15]` 内并去重。再分别搭配三种 C 判断：70% 当前规则，加 30% 某一种参考规则。用固定种子的随机生成器打乱这些判断的顺序。

每种判断在每个推理层级生成 24 个配兵，每个配兵距离其自身判断下的最优得分不超过 0.10 分。第一层针对自己的 H/C 判断；更高层将该判断与已完成的较低层等权混合，再求反制。不同判断假设的较低层人群比例在 0.35 到 0.65 之间。抽样方法和得分差距检查见 [dynamics.md](../modules/dynamics.md)。

实际情景为

\[
Q=hH+(1-h)[(1-s)C+sS].
\]

`s` 表示其余玩家中的 S 比例。例如 `h=0.10, s=0.50` 对应 10% H、45% C、45% S。下表决定 `s` 和 S 内部的层级比例：

| 风格 | `s` | S 内第一 / 二 / 三层比例 |
| --- | ---: | --- |
| `manual_heavy` | 25% | 70% / 25% / 5% |
| `balanced` | 50% | 35% / 45% / 20% |
| `computation_heavy` | 75% | 15% / 35% / 50% |

每个 H 比例与 C 规则组合都会重新生成 S；不同风格将同一组分层结果按不同比例组合。

### 2. 在 40 个训练情景中选配兵

三种 C 规则 × 四个 H 比例 `{0%,5%,10%,15%}` × 三种风格，共 **36 个情景**。另外四个使用 `base/balanced`，分别对应四个 H 比例，并将其中 25% 的 S 换为共享建议。建议来自针对 `5% H + 95% base C` 抽取的三个近似最优配兵，得分容差为 0.05 分，权重为 60% / 30% / 10%。

对每个情景 Q，[game.md](../modules/game.md) 中的 DP 算出最高可得分。Regret 等于这个最高分减去候选配兵的得分。[robust.md](../modules/robust.md) 枚举全部 **4,598,126** 个合法配兵，选出这 40 个情景中最大 regret 最小的一个。

### 3. 在 34 个验证情景中评价固定候选

| 组别 | 构造 | 数量 |
| --- | --- | ---: |
| `fresh` | 重新抽样三种 C；H 为 5% 或 15%；三种风格 | 18 |
| `shifted` | 两种改变后的 C 规则；H 为 0% 或 15%；三种风格 | 12 |
| `deep` | 新抽样的 base C；H 为 5% 或 15%；`s=75%`；四层比例为 5% / 15% / 30% / 50%；容差 0.05 | 2 |
| `crowded` | 新抽样的 base/balanced，H 为 5% 或 15%；将 50% 的 S 换为新生成的共享建议 | 2 |

两种改变后的规则均以 `base` 为基础。`higher_small_bids` 将次要城堡的 0/1/2/3/4 人投入概率设为 2%/8%/25%/40%/25%。`rounding_and_avoidance` 将按五人取整的概率设为 75%，包含第 5 座城的子集选择权重乘以 0.25，对数正态扰动的 sigma 设为 0.35。`shifted` 和 `deep` 玩家使用新抽样的三种 C 作为判断参考。

新候选根据训练 regret 选出，随后保持固定，计算全部验证得分。主程序还评价从新候选任意移动一名士兵得到的所有合法配兵，检查附近的替代选择。

### 4. 检查均衡诊断

若存在 `results/equilibrium.json`，读取其中的 E；否则重新求解。随后用完整博弈的最佳反制检查 E。另一个诊断固定 5% H 和 47.5% base C，让剩余 47.5% 通过 double oracle 共同调整，误差容限为 `1e-6`，最多 1,500 次迭代。完成候选选择后，分别计算候选面对这两个人群的得分与 regret。

### 复现与输出

记 `b` 为 `--seed`。每种 C 规则的种子等于下表 C 种子加其从 0 开始的位置编号。判断生成器使用自己的种子打乱判断顺序，并依次生成反制抽样的种子。

| 人群组别 | C 种子 | 判断生成器种子 | 共享建议种子 |
| --- | --- | --- | --- |
| 训练 | `b` | `b+200` | `b+100` |
| Fresh / crowded | `b+10000` | `b+10200` | `b+10100` |
| Shifted | `b+20000` | `b+20200` | — |
| Deep | 复用 fresh | `b+30000` | — |

`results/revised/` 中保存：

- `design.json`：实验设置和已有候选。
- `populations.json`：实际情景 marginal 表、C 参数、建议配兵和推理诊断。
- `comparison.json`：穷举结果、候选得分与 regret、中央 H/C/S 各部分得分、分组验证及均衡诊断。
- `neighbors.json`：移动一名士兵后的得分与 regret。
- `adaptive_diagnostic.json`：共同调整后的分布及求解残差轨迹。

在相同目录重跑会替换这些输出。若要单独保留另一轮，可传入 `--output results/revised_seed2 --seed 20261203`。
