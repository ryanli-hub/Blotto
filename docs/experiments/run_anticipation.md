# `run_anticipation.py`

## English

Source: [run_anticipation.py](../../experiments/run_anticipation.py). Run commands from the project root.

This experiment asks whether a fixed allocation remains strong when up to 15% of opponents reason beyond the previous population model. It compares the three original candidates, the current `(8,9,10,11,62)`, two initial search candidates, and a final constrained refinement.

```bash
python -m experiments.run_anticipation
```

Defaults: `--source results/revised --output results/anticipation --seed 20261107 --samples 4000`. On another machine, install `requirements.txt` and use `python`. `--samples` controls fresh C samples per profile. `--source` supplies the earlier populations and equilibrium files.

### 1. Build peers and anticipators

Let **Q** be one complete earlier opponent population, including H, C, and finite S. The 40 earlier selection populations and 34 previously inspected validation populations become **74 development populations** in this experiment.

For each Q, build six additional opponent types:

- **Model-based peers:** sample 48 allocations within 0.10 points of the best score against the complete Q.
- **Shared-strategy peers:** use the current `(8,9,10,11,62)`.
- **Four anticipator types:** for each peer distribution R and each assumed share `β = 5% or 15%`, sample 48 near-best replies to `(1−β)Q + βR`.

The first peer group optimizes its particular population model; the second represents entrants converging on the same fixed recommendation. Anticipators account for peers while still competing against the rest of the population. The sampled response distributions are then fixed for the allocation search.

**β describes an anticipator's belief about peers. α describes the actual added share in the scenario we evaluate:**

\[
Q_{\alpha,T}=(1-\alpha)Q+\alpha T.
\]

For example, `β=15%, α=5%` means the anticipators expect 15% peers, while anticipators themselves occupy 5% of our evaluated population. The remaining 95% follows Q.

### 2. Search two objectives

**Main search:** minimize maximum regret across the 74 base populations and their 15% additions of each of the six types: **518 endpoint scenarios**.

**Guarded search:** add direct counters to the current allocation. One type uses an exact DP best response; another mixes 96 sampled exact best responses. This gives **666 endpoint scenarios**. Its purpose is to measure the allocation cost of also protecting against opponents focused entirely on our previous recommendation.

Both searches examine all **4,598,126 legal allocations** through [robust.py](../modules/robust.md). Each scenario's best achievable score comes from [game.py](../modules/game.md)'s DP. Candidate regret is that optimum minus its own score.

### 3. Why the endpoints cover intermediate shares

For a fixed candidate x, base Q, and added type T, write `u(x,Q)` for expected score. Regret is

\[
r_x(Q_{\alpha,T})=\max_z\{(1-\alpha)[u(z,Q)-u(x,Q)]+\alpha[u(z,T)-u(x,T)]\}.
\]

Each expression inside the maximum is affine in α, so regret is convex. For `0≤α≤a`, it is at most the larger endpoint regret at 0 and a. Thus testing **0% and 15%** bounds every intermediate share for these fixed distributions. The same argument covers mixtures of the six added types whose total share is at most 15%. Rebuilding T creates a new distribution, which receives its own checks.

### 4. Validate with fresh populations and changed beliefs

Before either search, [build_population_suite](run_experiments.md) generates two fresh 74-population suites with seeds **20270117** and **20390117**, giving **148 validation bases**. Their 15% endpoint expansions give **1,036 validation scenarios**.

Validation uses tighter response tolerance **0.05**, assumed peer shares **10% and 25%**, and shared peers spread equally across the current allocation and its 20 legal one-soldier transfers. Response sampling uses 48 allocations per belief. Response seeds are the suite seed plus 500. These checks change random samples, beliefs, and the concentration of shared advice.

### 5. Test another response after selection

Keep all candidates fixed. Deduplicate the current, main-search, and guarded-search allocations, then mix the distinct allocations equally. For each fresh Q, generate replies to **85% Q + 15% of this peer mixture**, then evaluate a 15% actual addition of those replies.

Also generate direct counters to each distinct allocation and evaluate every candidate against the same union of those threats. These are feedback checks after selection. The script then shows shares **0%, 5%, 10%, 15%, and 25%**; 25% tests pressure beyond the search's 15% cap. Finally, it evaluates the saved E and fully adjusted-population benchmarks.

### 6. Refine while preserving base performance

After inspecting the first two validation suites, promote all **222 observed base populations**, along with their observed advanced-player and feedback scenarios, into development data. Search again with a score floor: on every known base, the new allocation must score at least **the current allocation's score minus 0.10 points**. Among feasible allocations, minimize maximum regret over the expanded development scenarios.

Before this search, generate a third fresh 74-population suite with seed **20510329**, assumed peer shares **10% and 20%**, and response tolerance **0.075**. Once selected, freeze the refined allocation and use this suite for the final check. Further feedback and direct-counter checks use the same threats for every candidate, built from the distinct current, main-search, and refined allocations. Results include the actual base-score loss on both known and fresh populations, plus primary and combined share curves.

### Outputs

- `design.json`: shares, seeds, tolerances, and search objectives.
- `populations.json`: development and fresh bases, added types, sampled allocations, and counters to the current allocation.
- `comparison.json`: both search results, all candidate scores/regrets, validation by seed, feedback checks, share curves, and equilibrium benchmarks.
- `feedback.json`: replies generated after selection and direct counters to the distinct selected/current allocations.
- `refinement_design.json`, `refinement_populations.json`, `refinement.json`: the score-floor settings, third fresh suite and feedback distributions, and final constrained-search evaluations.

The development response seed is `--seed`; direct-old, feedback, and subsequent direct-counter seeds add 1, 1000, and 2000 plus the candidate index, respectively. A separate `--output` directory preserves another run.

## 中文

源码：[run_anticipation.py](../../experiments/run_anticipation.py)。以下命令均在项目根目录运行。

本实验研究：当至多 15% 的对手比此前人群模型多想一步时，一个固定配兵能否保持良好表现。比较对象为三个原始候选、当前 `(8,9,10,11,62)`、最初两次搜索的候选，以及最后的受约束改进方案。

```bash
python -m experiments.run_anticipation
```

默认参数：`--source results/revised --output results/anticipation --seed 20261107 --samples 4000`。其他机器安装 `requirements.txt` 后使用 `python`。`--samples` 指定每种新 C 人群的样本数；`--source` 提供此前的人群及均衡文件。

### 1. 构造同层玩家和预判者

用 **Q** 表示一个包含 H、C 和有限推理 S 的完整旧人群。此前 40 个选策略人群和已查看的 34 个检验人群，在本次实验中合并为 **74 个开发人群**。

对每个 Q，构造六种新增对手：

- **按模型优化的同层玩家：** 针对完整 Q，抽取 48 个距离最优分数至多 0.10 分的配兵。
- **采用共同策略的同层玩家：** 使用当前 `(8,9,10,11,62)`。
- **四种预判者：** 对每一种同层分布 R，以及每个预想比例 `β = 5% 或 15%`，针对 `(1−β)Q + βR` 抽取 48 个近似最优反制。

第一类同层玩家针对各自人群模型优化；第二类表示不同参赛者得到同一个固定推荐。预判者兼顾同层玩家和其余人群。抽取出的反制分布在搜索配兵时保持固定。

**β 是预判者相信的同层玩家比例。α 是我们评价的场景中，新增对手的实际比例：**

\[
Q_{\alpha,T}=(1-\alpha)Q+\alpha T.
\]

例如 `β=15%, α=5%` 表示预判者预计有 15% 的同层玩家，但预判者自身占我们所评人群的 5%，其余 95% 沿用 Q。

### 2. 搜索两个目标

**主搜索：** 在 74 个基础人群，以及每个人群加入 15% 六种新增对手的情况下，最小化最大 regret，共 **518 个端点场景**。

**加强防守搜索：** 再加入直接针对当前配兵的对手。一种使用 DP 找到的精确最佳反制；另一种混合抽取的 96 个精确最佳反制，共 **666 个端点场景**。它衡量：如果还要防范全力针对旧推荐的玩家，需要怎样调整配兵。

两次搜索都通过 [robust.py](../modules/robust.md) 检查全部 **4,598,126 个合法配兵**。[game.py](../modules/game.md) 的 DP 给出各场景最高可得分，减去候选得分就是 regret。

### 3. 为什么端点覆盖中间比例

固定候选 x、基础人群 Q 和新增类型 T，用 `u(x,Q)` 表示期望得分，则

\[
r_x(Q_{\alpha,T})=\max_z\{(1-\alpha)[u(z,Q)-u(x,Q)]+\alpha[u(z,T)-u(x,T)]\}.
\]

大括号中每个表达式都随 α 线性变化，因此最大值是凸函数。在 `0≤α≤a` 内，regret 不超过 0 和 a 两端较大的 regret。所以检验 **0% 和 15%**，就能约束这些固定分布之间的全部中间比例。同理，六种新增对手可以任意混合，只要总比例不超过 15%。重新生成 T 会得到一个新分布，需要单独检验。

### 4. 用新人群和新判断验证

两次搜索前，调用 [build_population_suite](run_experiments.md)，以 **20270117** 和 **20390117** 为种子，各生成 74 个人群，共 **148 个验证基础人群**。加入 15% 新增对手后，共 **1,036 个验证场景**。

验证时将反制容差收紧到 **0.05 分**，预想同层比例改为 **10% 和 25%**，共同策略则在当前配兵及其 20 个合法“移动一人”配兵之间等权分布。每种判断仍抽取 48 个反制，种子为人群种子加 500。这些检验同时改变样本、人群判断和共同推荐的集中程度。

### 5. 选出策略后再检验一层反制

保持所有候选不变。将当前、主搜索、加强防守搜索的配兵去重，再把不同配兵等权混合。对每个新 Q，针对 **85% Q + 15% 该同层混合分布** 生成反制，再评价实际加入 15% 这些反制者时的表现。

另外，对每个不同配兵生成直接反制，并让每个候选面对同一组威胁。这些都属于选出策略后的反馈检验。程序随后展示新增比例为 **0%、5%、10%、15%、25%** 的结果；25% 用来测试超过搜索上限的压力。最后评价保存的 E 和充分调整人群基准。

### 6. 在保留基础表现的条件下改进

查看前两组验证结果后，将全部 **222 个已观察基础人群**，连同已观察的新增玩家和反馈场景，转为开发数据。重新搜索时设置得分下限：在每个已知基础人群中，新方案的得分至少为**当前方案得分减去 0.10 分**。在满足下限的配兵中，最小化扩展开发场景的最大 regret。

搜索前，以种子 **20510329** 生成第三组全新的 74 个人群，预想同层比例为 **10% 和 20%**，反制容差为 **0.075 分**。选出改进方案后将其固定，用这组人群完成最后检验。后续反馈和直接反制由去重后的当前、主搜索、改进方案共同构造，每个候选面对同一组威胁。结果分别记录已知和新人群上的实际基础得分损失，以及主场景和综合场景的比例变化。

### 输出

- `design.json`：比例、种子、容差和两个搜索目标。
- `populations.json`：开发与新人群、新增类型、抽样配兵，以及针对当前配兵的反制。
- `comparison.json`：两个搜索结果、全部候选得分与 regret、按种子分组的验证、反馈检验、比例变化和均衡基准。
- `feedback.json`：选出策略后生成的反制，以及针对不同当前或新配兵的直接反制。
- `refinement_design.json`、`refinement_populations.json`、`refinement.json`：得分下限设置、第三组新人群及反馈分布、最终受约束搜索的检验结果。

开发阶段反制种子为 `--seed`；针对旧策略、反馈、后续直接反制的种子分别为 `seed+1`、`seed+1000`、`seed+2000+候选序号`。使用不同的 `--output` 目录可单独保留另一轮结果。
