# opponents.py

## English

This module generates legal opponent allocations and converts them into a `5 × 101` probability table. Row `i` describes castle `i + 1`; column `t` gives the fraction placing `t` soldiers there. For example, `[3, 1] = 0.2` means 20% place one soldier on the 4-point castle. Every generated allocation uses exactly 100 soldiers.

`shallow_population()` defines **H** as an equal mixture of three unadjusted templates: `(20,20,20,20,20)`, `(7,13,20,27,33)`, and `(0,0,0,50,50)`. The experiment runner controls H's share of the full field.

`considered_population(...)` generates **C**, players who concentrate their main force while making small bids elsewhere:

1. Choose 2, 3, or 4 main castles with probabilities 25%, 50%, and 25%. Prefer subsets with higher total point value. The `avoid_high` profile multiplies the selection weight of every subset containing the 5-point castle by 0.45.
2. Put 0, 1, 2, or 3 soldiers on each secondary castle, using the probabilities below. Subtract these bids from the 100-soldier budget.
3. Divide the remaining soldiers among the main castles. Choose equal or value-proportional shares, then multiply each share by an independent lognormal factor. Its parameter `noise_sigma` controls variation around those shares.
4. Round to integers. Some players first allocate in five-soldier lots; leftover soldiers go to randomly selected main castles. Exact rounding ties are randomized.
5. Some players transfer one or two soldiers between main castles. This creates bids just above and below the initial thresholds while preserving the total.

| Parameter | `base` | `overbid` | `avoid_high` |
|---|---:|---:|---:|
| Secondary bids: probabilities of 0 / 1 / 2 / 3 | 10 / 45 / 35 / 10% | 5 / 15 / 45 / 35% | 10 / 45 / 35 / 10% |
| Probability of initially equal main shares | 35% | 55% | 35% |
| `noise_sigma` | 0.25 | 0.25 | 0.30 |
| Probability of five-soldier rounding | 35% | 60% | 35% |
| Probability of a one/two-soldier transfer | 40% | 80% | 40% |
| Selection multiplier for subsets containing castle 5 | 1 | 1 | 0.45 |

The result contains `allocations` (`samples × 5`), `marginals` (`5 × 101`), and `parameters`. A fixed seed reproduces the same population. `overrides` changes individual parameters for sensitivity checks; a longer `small_bid_probabilities` list permits larger secondary bids. Allocation generation grows linearly with the number of samples.

```python
from blotto.opponents import considered_population, mixture, shallow_population

c = considered_population(samples=4000, seed=20261103, profile="base")
population = mixture([shallow_population(), c["marginals"]], [0.05, 0.95])
```

`mixture` takes a weighted average of probability tables. These marginal probabilities suffice to calculate expected Game 1 scores because the five castle scores add. `round_allocation` implements proportional integer allocation using largest remainders. The earlier `heuristic_population` and `concentrated_population` remain available to reproduce earlier experiments. Two exact random baselines also remain: `uniform_allocations` weights all legal vectors equally; `independent_soldiers` lets each soldier independently choose a castle.

### Players focused on castles 2, 4, and 5

`focused_245_population(profile="local")` represents the structure shared by `(2,16,1,37,44)` and `(1,14,1,37,47)`: small bids on castles 1 and 3, a moderate bid on castle 2, and large bids on castles 4 and 5.

| Profile | Castle 1 | Castle 2 | Castle 3 | Castle 4 | Castle 5 | Row weights |
|---|---|---|---|---|---|---|
| `local` | 1–3 | 12–19 | 1–3 | 34–40 | 38–51 | Equal |
| `broad` | 0–4 | 10–22 | 0–4 | 30–43 | 35–55 | Equal |
| `shifted` | 1–4 | 16–22 | 1–4 | 38–43 | 32–48 | Prefer castle 2 near 18 and castle 4 near 40 |
| `overbid` | 2–5 | 12–21 | 2–5 | 34–42 | 33–52 | Equal |

1. Enumerate every integer combination for the first four castles within its bounds.
2. Set castle 5 to `100 - sum(first_four)` and keep the row if its fifth bid is within bounds. This produces complete legal allocations, including both input examples in `local` and `broad`.
3. Normalize the row weights and convert the weighted allocations to marginals. For `shifted`, a row x has weight proportional to

\[
\exp\!\left[-\frac12\left(\frac{x_2-18}{2}\right)^2
-\frac12\left(\frac{x_4-40}{1.5}\right)^2\right].
\]

Legal rows with the same castle-2 and castle-4 bids have equal weight. The return value contains `allocations`, normalized `weights`, `marginals`, and `parameters` recording bounds and weighting. Enumeration is deterministic and costs the product of the first four range widths. The experiment runner sets this group's population share and uses the changed profiles to check sensitivity to higher thresholds.

## 中文

本模块先生成合法对手配兵，再转换成 `5 × 101` 的概率表。第 `i` 行代表第 `i+1` 座城，第 `t` 列表示在那里放 `t` 人的比例。例如 `[3,1]=0.2` 表示20%的人在4分城放1人。每个生成的配兵都恰好使用100人。

`shallow_population()` 将 **H** 定义为三个未经调整的模板的等权混合：`(20,20,20,20,20)`、`(7,13,20,27,33)` 和 `(0,0,0,50,50)`。实验入口负责设定 H 在全体对手中的比例。

`considered_population(...)` 生成 **C**：集中主力，同时在其他城保留小额投入的对手。

1. 以25%、50%、25%的概率选择2、3、4座主攻城。总分值更高的组合更容易入选。`avoid_high` 将包含5分城的组合的抽取权重乘以0.45。
2. 每座次要城按下表概率放0、1、2或3人，并从100人的预算中扣除这些投入。
3. 在主攻城之间分配剩余兵力。先选择等额分配或按分值比例分配，再给各城权重乘以独立的对数正态随机数；`noise_sigma` 控制偏离初始比例的幅度。
4. 将人数取整。部分对手先按5人的单位分配，再把余下士兵随机放入主攻城。取整时相同的小数部分随机打破并列。
5. 部分对手在主攻城之间转移1或2人，使人数略高于或低于初始门槛，同时保持总数不变。

| 参数 | `base` | `overbid` | `avoid_high` |
|---|---:|---:|---:|
| 次要城放0 / 1 / 2 / 3人的概率 | 10 / 45 / 35 / 10% | 5 / 15 / 45 / 35% | 10 / 45 / 35 / 10% |
| 主攻城初始等额分配的概率 | 35% | 55% | 35% |
| `noise_sigma` | 0.25 | 0.25 | 0.30 |
| 按5人单位取整的概率 | 35% | 60% | 35% |
| 转移1或2人的概率 | 40% | 80% | 40% |
| 包含5分城的组合的抽取权重乘数 | 1 | 1 | 0.45 |

返回结果包含 `allocations`（`samples × 5`）、`marginals`（`5 × 101`）和 `parameters`。固定随机种子可以复现相同人群。`overrides` 用于修改个别参数，做敏感性检查；延长 `small_bid_probabilities` 列表可以允许次要城放更多人。生成时间随样本数线性增长。上面的例子建立了5% H、95% C的人群。

`mixture` 对概率表进行加权平均。第一局逐城分数可以相加，因此这些边际概率足以计算期望总分。`round_allocation` 用最大小数余数法完成比例配兵的整数化。原有 `heuristic_population` 和 `concentrated_population` 保留用于复现早期实验。两个精确随机基准也保留：`uniform_allocations` 对所有合法向量等权；`independent_soldiers` 让每名士兵独立选择一座城。

### 重点争夺第 2、4、5 城的玩家

`focused_245_population(profile="local")` 表示 `(2,16,1,37,44)` 和 `(1,14,1,37,47)` 的共同结构：第 1、3 城小额投入，第 2 城投入适中，第 4、5 城投入较大。

| 设置 | 第 1 城 | 第 2 城 | 第 3 城 | 第 4 城 | 第 5 城 | 配兵权重 |
|---|---|---|---|---|---|---|
| `local` | 1–3 | 12–19 | 1–3 | 34–40 | 38–51 | 等权 |
| `broad` | 0–4 | 10–22 | 0–4 | 30–43 | 35–55 | 等权 |
| `shifted` | 1–4 | 16–22 | 1–4 | 38–43 | 32–48 | 第 2 城偏向 18 人，第 4 城偏向 40 人 |
| `overbid` | 2–5 | 12–21 | 2–5 | 34–42 | 33–52 | 等权 |

1. 枚举前四座城范围内的每个整数组合。
2. 第五城设为 `100 - sum(first_four)`，仅保留第五城也满足范围的配兵。因此每个向量都合法，`local` 和 `broad` 均包含两个输入例子。
3. 将配兵权重归一化，再转为加权边际概率。`shifted` 中，配兵 x 的权重正比于

\[
\exp\!\left[-\frac12\left(\frac{x_2-18}{2}\right)^2
-\frac12\left(\frac{x_4-40}{1.5}\right)^2\right].
\]

第 2、4 城投入相同的合法配兵具有相同权重。返回 `allocations`、归一化的 `weights`、`marginals`，以及记录范围与权重规则的 `parameters`。枚举过程确定，计算量为前四个范围宽度的乘积。实验入口决定这类玩家的占比，并用改变后的设置检验更高出价门槛的影响。
