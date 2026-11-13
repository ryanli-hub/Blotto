# Weighted objective checks

## English

Run `python -m unittest discover -s tests -p 'test_game2_metrics.py' -v`.

The tests independently calculate a fractional tail boundary, verify that a 100% tail equals the mean, and split one scenario into identical copies whose weights sum to the original. Metrics must remain unchanged. They also verify that zero-weight scenarios are excluded, rescaling weights changes nothing, and mean regret gives the same ordering as mean score with fixed references.

A three-candidate example separates the mean, minimum, tail, and minimax-regret objectives, then checks the tail guard at several tolerances. Pareto tests retain genuine tradeoffs and duplicate pairs while removing dominated choices. Invalid weights, shapes, reference scores, tail masses, and tolerances are rejected.

## 中文

运行 `python -m unittest discover -s tests -p 'test_game2_metrics.py' -v`。

测试独立手算尾部边界只取部分权重的情况，验证 100% 尾部等于平均值，并将一个场景拆为多个相同副本、保持总权重不变。指标应保持一致。还验证零权重场景被排除、权重整体缩放不影响结果，以及参考值固定时平均 regret 与平均得分产生相同排序。

一个三个候选的例子区分平均分、最低分、尾部均值和最小最大 regret 的选择，并检验不同尾部容许差距。Pareto 测试保留真实取舍及相同指标组合，移除被全面超过的方案。错误权重、形状、参考值、尾部比例和容许差距会被拒绝。
