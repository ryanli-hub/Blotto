# Tests for Game 1

## English

Run from the project root:

```bash
python -m unittest discover -s tests -v
```

`test_game.py` checks the scoring rule and the optimization results against independent calculations. It uses Python's standard `unittest` runner, NumPy, and SciPy.

1. **Score interpretation.** Every matchup awards exactly 15 points across both players; identical allocations receive 7.5 each. The explicit counter `[1, 1, 1, 1, 96]` scores 10 against `[0, 0, 0, 0, 100]`. A simple loop translates the rule directly and checks the vectorized payoff matrix.
2. **Marginal reduction.** Four correlated opponent allocations, each spending seven soldiers, form a weighted mixture. For every legal response, the test compares its direct average matchup score with the sum of its three marginal expected rewards. Dependence between castles is allowed because the score is additive.
3. **DP correctness.** Small games with zero, five, or seven soldiers are small enough to enumerate completely. For several fixed and randomly weighted opponent populations, exhaustive scoring must agree with the DP's maximum and the score of its reconstructed allocation. This checks both the optimum and the returned legal decision.
4. **Equilibrium certificate.** A six-soldier, three-castle game is solved as a full matrix game by linear programming. The double-oracle result is then evaluated against every legal pure strategy. Its reported exploitability and worst-case score must equal these exhaustive evaluations, and its guaranteed score must agree with the full-game optimum.
5. **Pure-strategy vulnerability and cycles.** Moving four soldiers out of a most populated castle and adding one to each other castle wins at least 10 points. The test checks this construction on sample allocations and extreme cases. It also checks that the reported best-response cycle closes and every transition is optimal. The general proof appears in the project analysis.
6. **Input validity.** Opponent allocations with the wrong total, negative counts, or fractional soldiers must be rejected.
7. **Population construction.** Uniform-allocation marginals must match an independent enumeration of small games. Independent-soldier marginals must sum to one and have the correct expected total. The simulated heuristic and concentrated populations, and their weighted mixture, must preserve the 100-soldier budget and reproduce exactly from the same seed.
8. **Robust pure decision.** The bounded-memory enumerator must list every legal five-castle allocation exactly once. On a four-soldier game, independent direct matchup scores determine each scenario's optimum and every candidate's largest regret. `minimax_regret` must attain the smallest of those regrets and report the correct scenario scores.
9. **Adaptive population.** With a fixed background population, the transformed zero-sum payoff must equal each pure strategy's gain over the adaptive population's current average score. Exhaustive small-game evaluations check this identity, the reported deviation gap, and its convergence tolerance, including the limiting case where the background occupies the whole population. The adaptive strategy's separate worst-case certificate is checked against every pure opponent too.
10. **Considered concentration.** All three profiles must produce reproducible legal allocations whose saved marginal probabilities match direct histograms. When configured to focus on two castles and bid 1, 2, or 3 elsewhere, every allocation must retain exactly three specified small bids.
11. **Near-best replies.** Exhaustive direct matchup scores determine a small game's true optimum. Every sampled reply must fall within the requested total score loss. With zero loss, samples must be optimal; a game with tied optima must produce more than one allocation and reproduce from its seed.
12. **Finite reasoning.** Runs with one, two, and three levels must return legal allocations, normalized empirical marginals, and the correct budget. Their combined distribution must equal the mixture of the saved levels. Direct matchup scoring reconstructs each belief from the fixed background and all earlier levels, then checks the responses and their reported score losses against exhaustive optima.
13. **Pruned exhaustive search.** Independent payoff matrices for zero-, three-, and five-soldier games determine every allocation's maximum regret against nine populations. Starting from different legal incumbents must produce the same optimum and tie choice, all reported scores, and the complete enumeration count.
14. **Mixture endpoint bound.** Direct scores against two fixed populations determine regret at five mixture shares between 0 and 15%. Every candidate's intermediate regret must lie below its largest endpoint regret. Optimizing endpoints alone must agree with optimizing all five shares.
15. **Score floors.** Independent matchup scores define three optimization populations and two additional populations with minimum-score constraints. Exhaustive feasible allocations must give the same constrained optimum, scores, and total count as the pruned search. Missing or infeasible initial allocations must be rejected; scenario benchmarks retain their unrestricted optima.
16. **Focused 2/4/5 cohort.** All four profiles must contain distinct legal integer allocations within their specified bounds, with positive normalized weights. The local and broad profiles must include both supplied strategies. Hand-chosen row pairs check the shifted profile's weighting ratios and equal low-bid weights. Direct weighted matchup scores against every saved row must agree with marginal scoring for five candidate allocations, including ties.

Fixed random seeds make every check reproducible.

## 中文

在项目根目录运行：

```bash
python -m unittest discover -s tests -v
```

`test_game.py` 用独立计算检查计分规则和优化结果。依赖 Python 标准库的 `unittest`，以及 NumPy 和 SciPy。

1. **核对计分含义。** 每场双方得分之和必须为 15，相同分配各得 7.5 分。具体地，`[1, 1, 1, 1, 96]` 对 `[0, 0, 0, 0, 100]` 得 10 分。测试用直接逐城比较的循环核对向量化的收益矩阵。
2. **核对边际分布化简。** 构造四个相互加权的对手分配，每个分配共用七名士兵，各城兵力明显相关。对每个合法应对，分别计算逐个对手的加权平均得分，以及三个城堡的边际期望得分之和，两者必须一致。这里允许城堡间相关，因为总得分可加。
3. **核对 DP。** 零名、五名或七名士兵的小规模问题可以穷举全部合法分配。对若干固定和随机加权的对手群体，穷举最大值必须等于 DP 最大值，且 DP 返回的分配必须合法并实际达到该分数。这同时检验最优值与回溯结果。
4. **核对均衡证书。** 对六名士兵、三座城堡的游戏，先建立完整收益矩阵并用 linear programming 求解，再用全部合法纯策略评价 double oracle 返回的混合策略。程序报告的 exploitability 和最坏情形得分必须与穷举结果一致，保证得分还必须与完整游戏的最优值一致。
5. **核对纯策略漏洞和循环。** 从兵力最多的城堡撤出四人，给另外四座城堡各加一人，可以得到至少 10 分。测试在一些样本和极端分配上核对该构造，并检查 best-response 循环是否闭合、每次转移是否最优。项目分析给出普遍结论的证明。
6. **核对输入。** 总兵力不符、兵力为负或士兵数量不是整数时，程序必须拒绝输入。
7. **核对对手群体的构造。** 均匀合法分配的边际公式必须与独立的小规模穷举一致。每名士兵独立选择城堡的边际概率必须归一化，并给出正确的期望总兵力。启发式群体、集中型群体及其加权混合必须保持 100 人预算，且相同随机种子必须产生完全相同的结果。
8. **核对稳健纯策略。** 分块枚举必须恰好一次列出所有合法五城分配。在总兵力为四的小问题上，测试独立计算每次对局得分，从而得到各情景最优值，以及每个候选分配的最大 regret。`minimax_regret` 必须达到其中最小的最大 regret，并报告正确的各情景得分。
9. **核对适应性群体。** 存在固定背景群体时，转换后的零和收益必须等于某个纯策略相对于适应性群体当前平均得分的改善。测试用小规模穷举核对该恒等式、程序报告的偏离获益及收敛容差，也覆盖背景占比为 100% 的边界情况。适应性策略单独面对任意对手时的最坏情形证书也会逐一核对。
10. **核对改进后的集中型。** 三种设置都必须生成可复现的合法配兵，保存的边际概率必须等于逐城直接统计的频率。指定重点争夺两座城、其余各放 1、2 或 3 人时，每个配兵必须恰好保留三个指定的小额投入。
11. **核对近似最佳回应。** 先用小规模逐场穷举得到真实最优分数，再检查每个抽样配兵的总得分损失是否在指定范围内。损失上限为零时，每个样本都必须最优；存在并列最优解时，应生成多个配兵，并能由种子复现。
12. **核对有限层推理。** 分别运行一、二、三层推理，检查配兵合法性、边际概率归一化及总预算。最终群体必须等于保存的各层分布的等权混合。再从固定背景和所有较低层配兵重建各人的预期对手，逐场计分、穷举最优解，核对回应质量及程序报告的得分损失。
13. **核对剪枝穷举。** 对零、三、五人预算的小博弈，独立收益矩阵给出每个配兵面对九个人群的最大 regret。从不同合法初始配兵出发，都必须得到相同最优结果与并列选择、正确的各人群得分和完整枚举数量。
14. **核对混合比例端点界。** 对两个固定人群，直接计分得到 0 至 15% 之间五个混合比例的 regret。每个配兵的中间 regret 均不得超过其最大端点 regret；只优化端点应与优化五个比例得到相同结果。
15. **核对得分下限。** 独立逐场得分构造三个优化人群和另外两个带最低得分要求的人群。穷举全部可行配兵必须与剪枝搜索得到相同的受约束最优解、各人群得分和总枚举数。缺少或不满足约束的初始配兵必须被拒绝；计算 regret 的场景基准仍为无约束最优分。
16. **核对集中于第 2、4、5 城的人群。** 四种设置都必须产生范围内不重复的合法整数配兵，权重为正且归一化。附近与较宽设置均应包含两个给定策略。手工挑选的配兵对核对偏移设置的权重比，以及小额投入变化时的等权关系。对五个候选逐个计算面对全部配兵的加权得分，必须与边际计分一致，并覆盖并列情况。

固定随机种子使每项检查都可以复现。
