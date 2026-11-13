# Game 1 population regression checks

## English

Run `python -m unittest discover -s tests -p 'test_game1_field.py' -v`.

1. Sample near-optimal responses under two nontrivial castle permutations, then check the restored allocations. Their budgets must be legal, and their original-game scores must lie within the requested optimality gap. Scores are recomputed against complete weighted opponent vectors through `payoff_matrix`, independently of the response sampler's expected-reward lookup.
2. Give H, C, T, earlier responders, and the alternative C population distinct atomic allocations. Replace response search with a known legal response and inspect the actual belief marginals at all four levels. This verifies that H/T retain their stated probability masses while C and earlier responders divide the remainder, in both training and fresh settings.
3. Build small training and fresh fields with fixed responses. Check all 80 scenario weights, five families with 20% each, legal joint distributions in every population bank, H shares at most 5%, and actual omission of the dedicated T component in T-free scenarios.

## 中文

运行 `python -m unittest discover -s tests -p 'test_game1_field.py' -v`。

1. 使用两种非平凡城堡排列抽取近优回应，再检查恢复原顺序后的配兵。预算必须合法，原博弈中的得分差必须在给定范围内。测试通过 `payoff_matrix`，对完整的加权对手向量重新计算得分，独立于抽样器使用的期望收益查表。
2. 为 H、C、T、前层反制者和另一种 C 设置不同的单一配兵。将回应搜索替换为已知合法回应，检查四层推理实际接收的边际分布。这验证训练和新检验中 H/T 的概率份额保持正确，C 与前层反制者分配剩余部分。
3. 使用固定回应构造小型训练与新检验人群。核对 80 个场景的权重、五类环境各占 20%、所有人群库中的完整配兵合法、H 不超过 5%，以及 T-free 场景实际不加入专门的 T 成分。
