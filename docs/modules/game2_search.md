# Game 2: search and finite reasoning

## English

The input is a distribution of **complete legal opponent allocations**. The objective is average ranking payout, from 0 to 9.

1. `sampled_scores` draws three opponents per match and compares candidates on the same matches. Shared draws make score differences less noisy.
2. `response_search` screens a broad candidate pool, adds transfers of 1, 2, 5, or 10 soldiers around six promising allocations, and scores the shortlist on new matches. It retains up to 12 choices within 0.12 estimated payout of the best, separated by at least four soldiers in total absolute difference.
3. `finite_reasoning` builds three levels of opponents. Level 1 responds to C, H, and the team-inspired T population. Higher levels also anticipate earlier levels. Three beliefs vary H, T, and the relative popularity of the two team ideas. Each player chooses before submitting.
4. `maximum_regrets` compares a candidate with the best searched candidate in each scenario. `shortlist_indices` keeps both low-regret candidates and scenario specialists. `neighbors` preserves the 100-soldier budget when refining them.
5. `independent_evaluation` freezes a reference selected on calibration games, then evaluates it and our candidates on fresh common games. It returns means, standard errors, and paired score gaps.

For example, if the reference earns 5.2 and our allocation earns 4.8 against the same population, its estimated regret is 0.4. The search is approximate, so this is a gap to a searched reference. A negative test gap means our allocation beat that reference on the fresh games.

The three base beliefs use `(H share, T share, TA share within T)` = `(5%, 10%, 50%)`, `(0%, 30%, 80%)`, and `(10%, 30%, 20%)`. From level 2 onward, earlier levels replace 35%, 50%, or 65% of the corresponding base. For example, replacing 35% of the first base leaves 3.25% H and 6.5% T. Completed earlier levels receive equal weight.

For (A) candidates and (G) games, scoring takes (O(5AG)) operations. Candidate and game batches limit working memory. Standard errors describe sampling uncertainty conditional on the specified population; changing the population is tested separately.

## 中文

输入是**完整、合法配兵向量**组成的对手分布。目标是最大化 0 到 9 分的平均名次奖励。

1. `sampled_scores` 每场抽取三个对手，让所有候选面对同一批对局，减少得分差中的随机噪声。
2. `response_search` 先筛选大范围候选，再对六个有希望的方案移动 1、2、5 或 10 名士兵，用新对局重新评分。保留最多 12 个距最高估计奖励不超过 0.12 分、相互配兵绝对差之和至少为 4 的方案。
3. `finite_reasoning` 建立三层对手。第一层针对 C、H 和类似我们初步想法的 T；更高层还会预判前面各层。三种信念改变 H、T 及两种初始方案的比例。每位玩家都在提交前做出选择。
4. `maximum_regrets` 将候选与每个场景中搜索到的最佳方案比较。`shortlist_indices` 同时保留最大 regret 较低的候选和擅长特定场景的候选。`neighbors` 在保持总兵力为 100 的条件下调整方案。
5. `independent_evaluation` 固定校准对局选出的参考方案，再让它和我们的候选面对同一批新对局，输出平均分、标准误和配对得分差。

例如，同一人群下参考方案得 5.2 分，我们得 4.8 分，估计 regret 为 0.4。搜索使用近似方法，因此这里衡量与已搜索参考方案的差距。新对局中的差距若为负，表示我们的方案超过了参考方案。

三种基础信念的 `(H 比例，T 比例，T 内 TA 比例)` 分别为 `(5%, 10%, 50%)`、`(0%, 30%, 80%)`、`(10%, 30%, 20%)`。从第二层开始，更早各层替换相应基础人群的 35%、50% 或 65%。例如第一种基础人群被替换 35% 后，H 剩 3.25%，T 剩 6.5%。已经完成的各层等权混合。

比较 (A) 个候选、每个 (G) 场对局，计分需要 (O(5AG)) 次操作。分批处理候选和对局控制内存。标准误衡量给定人群后的抽样误差；人群变化通过另外的场景检验。
