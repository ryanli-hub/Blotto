# `dynamics.py`

## English

### Five related operations

This module implements five operations for Game 1:

| Function | Opponent at the next step | Question answered |
| --- | --- | --- |
| `near_best_responses` | One fixed marginal table | Which varied allocations score within a chosen tolerance of optimal? |
| `finite_reasoning_population` | Different background beliefs and lower reasoning levels | What do players choose after one to three levels of reasoning? |
| `pure_response_path` | The last pure allocation | Does this deterministic response path settle or cycle? |
| `fictitious_play` | The empirical mixture of all past allocations | Does responding to accumulated experience reduce exploitability? |
| `double_oracle` | A restricted-game equilibrium, checked against every legal response | Can we compute and certify an approximate mixed equilibrium? |

An allocation is one five-integer vector. A mixed strategy is a probability distribution over such vectors. Its mean vector is generally not an equivalent strategy: winning and tying depend nonlinearly on soldier counts. To use a mixed strategy for one submission, draw one legal vector from its support using the returned weights.

### Varied near-best responses

`near_best_responses` takes an opponent marginal table and returns `count` legal allocations. Each scores at least the DP optimum minus `slack`, measured in castle points. For example, an optimum of 8.40 and `slack=0.10` permits scores of 8.30 or higher.

1. Build `prefix[k, b]`: the highest score from the first `k` castles using exactly `b` soldiers. Its recurrence is the best-response DP in `game.py`.
2. Backtrack from the last castle. A possible soldier count is eligible when its reward plus the best remaining completion reaches the required score.
3. Choose uniformly among eligible counts, subtract its soldiers and reward, and continue. If a choice earns 2.00 in the example, the remaining castles must earn at least 6.30. This carries one total score requirement through all castles.

Different samples can select different near-best allocations. Sampling is uniform among eligible counts at each step; complete allocations can have different probabilities. Duplicate samples retain their empirical weight. The cost is \(O(KB^2+NKB)\) time and \(O(B^2+KB+NK)\) space for `N` samples, `K` castles, and budget `B`.

### Finite reasoning with different beliefs

`finite_reasoning_population` receives a list of marginal tables called `backgrounds`. Each table is one player's belief about the mixture of shallow and considered manual allocations. All beliefs receive equal sample counts.

- Level 1 samples near-best responses to each background.
- Level 2 combines each background with the aggregate level-1 distribution.
- Level 3 combines each background with an equal mixture of levels 1 and 2.

At levels 2 and 3, a player's belief is \((1-r)G+rL\), where `G` is their background and `L` mixes completed lower levels. The shares `r` range evenly from 0.35 to 0.65 across beliefs; a single belief uses 0.50. Each level describes reasoning before submission.

The returned `allocations_by_depth` contains the sampled legal vectors; `depth_marginals` gives their castle-by-castle probabilities. `allocations` and `marginals` combine all levels with equal weights. The runner uses the separate depth tables to test other level mixtures. `diagnostics.by_depth` records sample counts, distinct allocations, and actual score gaps against each player's belief. A fresh best-response calculation checks those gaps. The arrays remain NumPy arrays for further computation; `parameters` records the seed and model settings.

### Pure responses and cycles

Starting from \(x_0\), `pure_response_path` repeatedly calls the DP from `game.py`:

\[
x_{t+1}=\operatorname{BR}(\delta_{x_t}),
\]

where \(\delta_x\) means an opponent who always uses \(x\). The deterministic DP tie rule makes this a function on a finite set. If it runs long enough, some state must repeat; after that, the same successors repeat. A one-state cycle is a fixed point. A longer cycle is not convergence to an allocation.

The output `allocations` lists each distinct visited vector, including the starting vector. `scores[t]` is the score of the response to `allocations[t]`, not the score that allocation earned against its predecessor. `cycle_start` is a zero-based index; `cycle_length` is the number of states in the loop. `repeated_allocation` identifies the successor closing the loop. A `None` cycle means the step limit was reached without detecting repetition. `converged` is true only for a one-state cycle. Changing the rule for choosing among equally good responses can change the path.

### Fictitious play

`fictitious_play` initializes the empirical distribution with one copy of `initial`. At each update it best-responds to the current empirical marginals, then adds that response as one further observation. The output weights are occurrence counts divided by the total number of observations. `iterations` counts added responses, so `sample_count = iterations + 1`.

This is simultaneous symmetric fictitious play in the finite two-player zero-sum game obtained by subtracting 7.5 from each score. The finite zero-sum convergence result concerns empirical mixed strategies approaching the equilibrium set, not convergence of the current pure action. See [Julia Robinson (1951), *An Iterative Method of Solving a Game*](https://cs.brown.edu/courses/csci1440/labs/2023/lab01/robinson.pdf). Finite-run error need not decrease at every checkpoint. The code measures the actual error with a fresh full-game best response, rather than inferring convergence from a smooth-looking path. `checkpoints` selects which update counts appear in `history`; the final update is always recorded.

### Equilibrium and the numerical certificate

For ordinary Game 1, \(u(x,y)+u(y,x)=15\), and both players have the same strategy set. The finite minimax theorem and symmetry imply game value \(c=15/2=7.5\), with a symmetric optimal mixed strategy. For a candidate mixture \(H\), define

\[
\epsilon(H)=\max_x u(x,H)-c.
\]

Since \(u(H,H)=c\), this quantity is nonnegative. Constant sum also gives

\[
\min_y u(H,y)=15-\max_y u(y,H)=c-\epsilon(H).
\]

Thus `exploitability` measures the largest gain an opponent can obtain over 7.5, and `worst_case_score` is the corresponding guarantee for the **mixture**. Individual support vectors need not have that guarantee. These values check all legal allocations through the DP, not only the strategies currently stored by the solver. Floating-point calculations make this a numerical certificate.

`double_oracle` starts from `initial_allocations`, or the five all-in allocations by default. For the current \(n\) strategies it builds the \(n\times n\) antisymmetric matrix \(A_{ij}=u(x_i,x_j)-c\). It then solves

\[
\min_{q,z} z\quad\text{subject to }Aq\le z\mathbf1,
\quad q\ge0,\quad\mathbf1^\top q=1.
\]

Here \(q\) is the opponent's mixture and \(z\) bounds every stored strategy's advantage. Antisymmetry ensures the restricted game has value zero, and its solution is also a symmetric equilibrium on that restricted set. The DP then finds a best response over the full legal strategy set. If its improvement is too large, that allocation is added and the process repeats. Each accepted response expands the set; only the new row and column of the payoff matrix need to be computed.

`tolerance` is an additive score threshold. `max_iterations` limits LP solves. `converged` means the full-space residual was at most the requested tolerance, not that floating-point arithmetic proved an exact equilibrium. `status` distinguishes `tolerance_reached`, `iteration_limit`, and `numerical_stall`. The last means numerical residuals asked for an allocation already in the restricted game. A restricted equilibrium alone does not establish full-game convergence.

### Smart players with a fixed background population

Optional `background` is a \(K\times(B+1)\) marginal table for a fixed population \(G\); `background_weight = rho` is its proportion \(\rho\in[0,1]\). Here \(B\) remains the soldier budget. The endogenous smart population uses mixture \(H\). Every smart player faces

\[
Q=\rho G+(1-\rho)H.
\]

Write \(f(x)=u(x,G)\). The smart player's payoff against another smart allocation \(y\) is \((1-\rho)u(x,y)+\rho f(x)\). Subtracting \((1-\rho)c+\rho f(y)\), which is independent of its own choice \(x\), preserves all best responses. Therefore the solver uses the strategically equivalent antisymmetric matrix

\[
M_{ij}=(1-\rho)(u(x_i,x_j)-c)+\rho(f(x_i)-f(x_j)).
\]

The DP best-responds to the full population \(Q\). A smart player drawing from \(H\) earns

\[
s(H,Q)=(1-\rho)c+\rho\,\mathbb E_{x\sim H}f(x).
\]

The stopping residual is `population_exploitability` = \(\max_xu(x,Q)-s(H,Q)\). `population_score` stores \(s(H,Q)\); `best_response` and `best_response_score` refer to \(Q\). `exploitability` and `worst_case_score` still describe \(H\) against arbitrary opponents in the original game. A small population residual does **not** imply a small unrestricted exploitability. With \(\rho=0\), both residuals coincide and all fields reduce to the ordinary equilibrium calculation.

The calculation holds the opponent distribution fixed when evaluating one person's strategy change.

### Usage and outputs

```python
from blotto.dynamics import double_oracle, fictitious_play, pure_response_path

path = pure_response_path([0, 0, 0, 0, 100])
empirical = fictitious_play([0, 0, 0, 0, 100], iterations=2000)
equilibrium = double_oracle(tolerance=0.02, max_iterations=1000)
print(path["cycle_start"], path["cycle_length"])
print(equilibrium["converged"], equilibrium["exploitability"])
```

`fictitious_play` and `double_oracle` store parallel lists `allocations` and `weights`, a full-space best response, and checkpoint `history`. Their outputs use ordinary lists and numbers for JSON serialization. The restricted solver may retain allocations whose final weight is zero. General `values` and `budget` arguments allow exhaustive small-game verification. The DP costs \(O(KB^2)\) per response; the restricted matrix uses \(O(n^2)\) space, while LP runtime depends on the solver and current strategy set.

## 中文

### 五种相关计算

本模块实现 Game 1 的五种计算：

| 函数 | 下一步针对的对手 | 回答的问题 |
| --- | --- | --- |
| `near_best_responses` | 一张固定的 marginal 表 | 哪些不同配兵的得分距离最优值足够近？ |
| `finite_reasoning_population` | 不同背景判断与较低推理层级 | 玩家推理一到三层之后会选择什么？ |
| `pure_response_path` | 上一步的纯策略 | 这条确定性反制路径会停止还是循环？ |
| `fictitious_play` | 所有过去策略的经验混合 | 针对累计经验反制，能否降低可利用程度？ |
| `double_oracle` | 受限博弈均衡，并用完整策略空间检查 | 能否算出并验证一个近似混合均衡？ |

一个 allocation 是一个五维整数向量。一个 mixed strategy 是这些向量上的概率分布。把向量求平均通常得不到等价策略，因为胜负和平局依赖兵力大小关系，不是兵力的线性函数。如果只提交一次，应按照返回的权重抽取一个合法向量。

### 多样的近似最优反制

`near_best_responses` 接收对手的 marginal 表，返回 `count` 个合法配兵。每个配兵的得分至少达到 DP 最优值减去 `slack`，单位是城堡分。例如，最优值为 8.40，`slack=0.10` 时，允许得分不低于 8.30。

1. 建立 `prefix[k, b]`：前 `k` 座城恰好用 `b` 人时的最高得分。递推与 `game.py` 的最佳反制 DP 相同。
2. 从最后一座城向前回溯。一个兵力选项的当前收益加上剩余部分的最高收益，达到所需分数时，才允许选择。
3. 在允许的选项中等概率抽取，扣除对应兵力和收益，再继续。上例中，若当前选择贡献 2.00 分，剩余城堡就必须达到 6.30 分。整个回溯过程始终共用一个总分要求。

不同抽样可以得到不同的近似最优配兵。每一步的可行兵力选项等概率，完整配兵的概率可以不同。重复样本保留对应的经验权重。抽取 `N` 个样本、`K` 座城、兵力预算为 `B` 时，时间复杂度为 \(O(KB^2+NKB)\)，空间复杂度为 \(O(B^2+KB+NK)\)。

### 不同判断下的有限层推理

`finite_reasoning_population` 接收一组 marginal 表 `backgrounds`。每张表描述一位玩家对浅层配兵与经过考虑的手动配兵的混合判断。每种判断抽取相同数量的样本。

- 第一层针对各自背景生成近似最优反制。
- 第二层把各自背景与第一层的总体分布混合，再反制。
- 第三层把各自背景与第一、二层的等权混合分布混合，再反制。

第二、三层中，玩家的判断为 \((1-r)G+rL\)。`G` 是自己的背景判断，`L` 是已经生成的较低层分布的混合。不同判断对应的 `r` 在 0.35 到 0.65 之间均匀排列；只有一种判断时使用 0.50。每一层都描述提交策略之前的推理。

返回的 `allocations_by_depth` 保存每层的合法配兵样本，`depth_marginals` 保存对应的逐城兵力概率。`allocations` 和 `marginals` 将所有层等权合并。实验入口使用分层结果测试其他层级比例。`diagnostics.by_depth` 记录样本数、不同配兵数，以及每个配兵相对其自身判断下最优值的实际差距。这些差距由一次独立调用的最佳反制计算检查。数组保留为 NumPy 格式，方便继续计算；`parameters` 保存随机种子与模型设置。

### 纯策略反制与循环

`pure_response_path` 从 \(x_0\) 开始，反复调用 `game.py` 的 DP：

\[
x_{t+1}=\operatorname{BR}(\delta_{x_t}),
\]

其中 \(\delta_x\) 表示始终使用 \(x\) 的对手。DP 在最优解并列时采用确定规则，因此这是有限集合上的一个函数。只要运行足够久，必定出现重复状态；重复之后，后继状态也会重复。长度为 1 的循环是 fixed point；更长的循环不是收敛到某个分配。

输出 `allocations` 包含各个首次出现的分配，包括初始分配。`scores[t]` 是针对 `allocations[t]` 的最优反制得分，不是这个分配针对前驱的得分。`cycle_start` 是从 0 开始的循环起点索引，`cycle_length` 是循环中的状态数，`repeated_allocation` 是使路径闭合的后继状态。循环字段为 `None` 表示达到步数上限时尚未发现重复。只有长度为 1 的循环才会令 `converged` 为真。改变并列最优解的选取规则，可能改变路径。

### Fictitious play

`fictitious_play` 先把 `initial` 作为第一条观测。每轮针对当前经验 marginals 求最优反制，再把这个反制作为一条新观测加入。输出权重等于各分配出现次数除以总观测数。`iterations` 表示新增反制次数，因此 `sample_count = iterations + 1`。

从每次得分中减去 7.5 后，原问题成为有限双人零和博弈；这里的更新就是对称、同步的 fictitious play。有限零和博弈的收敛结论是经验混合策略趋近均衡集合，不保证当前纯策略收敛，参见 [Julia Robinson (1951), *An Iterative Method of Solving a Game*](https://cs.brown.edu/courses/csci1440/labs/2023/lab01/robinson.pdf)。有限次运行时，误差也不一定在每个检查点下降。代码通过一次新的完整博弈 best response 测量真实误差，不通过轨迹看起来是否平滑来判断收敛。`checkpoints` 指定要保存哪些更新次数的结果，最后一次总会保存。

### 均衡与数值验证

在普通 Game 1 中，\(u(x,y)+u(y,x)=15\)，且双方具有相同的策略集合。有限博弈的 minimax theorem 加上对称性说明博弈值为 \(c=15/2=7.5\)，并存在对称最优混合策略。对候选混合策略 \(H\)，定义

\[
\epsilon(H)=\max_xu(x,H)-c.
\]

由于 \(u(H,H)=c\)，这个数非负。恒和性质还给出

\[
\min_yu(H,y)=15-\max_yu(y,H)=c-\epsilon(H).
\]

因此 `exploitability` 表示对手可以在 7.5 基础上最多多拿多少分，`worst_case_score` 表示我们使用**整个混合策略**时的保底期望分数。混合中的单个向量未必有这个保证。DP 检查的是所有合法分配，并不局限于求解器当前保存的策略。由于使用浮点运算，这是数值验证。

`double_oracle` 从 `initial_allocations` 开始，默认使用五个 all-in 分配。对当前 \(n\) 个策略构造 \(n\times n\) 反对称矩阵 \(A_{ij}=u(x_i,x_j)-c\)，再解线性规划：

\[
\min_{q,z}z\quad\text{满足 }Aq\le z\mathbf1,
\quad q\ge0,\quad\mathbf1^\top q=1.
\]

这里 \(q\) 是对手的混合权重，\(z\) 是所有已存策略得分优势的上界。反对称性保证这个受限博弈的值为零，求得的解也构成受限集合上的对称均衡。随后 DP 在完整合法策略集合中寻找 best response。如果改善幅度过大，就把这个分配加入集合，再重新求解。每个接受的新反制都扩展策略集合；计分矩阵只需新增一行一列。

`tolerance` 是以分数为单位的加法误差阈值。`max_iterations` 限制 LP 求解次数。`converged` 只表示完整策略空间的残差不超过阈值，不表示浮点计算证明了精确均衡。`status` 区分 `tolerance_reached`、`iteration_limit` 和 `numerical_stall`。最后一种情况表示数值残差要求添加一个已经存在的分配。只解出受限博弈均衡，并不足以证明完整博弈已经收敛。

### 聪明玩家与固定背景人群

可选参数 `background` 是固定背景人群 \(G\) 的 \(K\times(B+1)\) marginal 表，`background_weight = rho` 是其比例 \(\rho\in[0,1]\)。这里 \(B\) 仍表示兵力预算。内生的聪明玩家人群使用混合策略 \(H\)。每个聪明玩家面对

\[
Q=\rho G+(1-\rho)H.
\]

记 \(f(x)=u(x,G)\)。聪明玩家面对另一个聪明玩家分配 \(y\) 时，其总体期望收益为 \((1-\rho)u(x,y)+\rho f(x)\)。减去与自身选择 \(x\) 无关的 \((1-\rho)c+\rho f(y)\)，不会改变任何 best response。因此求解器使用策略等价的反对称矩阵

\[
M_{ij}=(1-\rho)(u(x_i,x_j)-c)+\rho(f(x_i)-f(x_j)).
\]

DP 针对整个对手人群 \(Q\) 求反制。按 \(H\) 抽取策略的聪明玩家，期望得分为

\[
s(H,Q)=(1-\rho)c+\rho\,\mathbb E_{x\sim H}f(x).
\]

停止条件使用 `population_exploitability`，即 \(\max_xu(x,Q)-s(H,Q)\)。`population_score` 保存 \(s(H,Q)\)；`best_response` 和 `best_response_score` 针对 \(Q\)。`exploitability` 和 `worst_case_score` 仍描述 \(H\) 在原博弈中面对任意对手的表现。较小的人群均衡残差**不保证**较小的完全对抗 exploitability。当 \(\rho=0\) 时，两种残差相同，所有字段退化为普通均衡计算。

计算一个人改变策略的效果时，固定对手的总体分布。

### 使用与输出

```python
from blotto.dynamics import double_oracle, fictitious_play, pure_response_path

path = pure_response_path([0, 0, 0, 0, 100])
empirical = fictitious_play([0, 0, 0, 0, 100], iterations=2000)
equilibrium = double_oracle(tolerance=0.02, max_iterations=1000)
print(path["cycle_start"], path["cycle_length"])
print(equilibrium["converged"], equilibrium["exploitability"])
```

`fictitious_play` 和 `double_oracle` 输出中的 `allocations` 与 `weights` 一一对应，还包含完整策略空间上的 best response 和检查点 `history`。这两个函数的输出使用普通列表和数字，能够直接保存为 JSON。受限求解器可能保留最终权重为零的分配。`values` 和 `budget` 参数支持小型博弈，便于通过穷举独立验证。每次 DP 的时间为 \(O(KB^2)\)；受限计分矩阵的空间为 \(O(n^2)\)，LP 运行时间取决于求解器和当前策略集合。
