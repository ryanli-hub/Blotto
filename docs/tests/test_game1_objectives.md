# Exact Game 1 search checks

## English

Run `python -m unittest discover -s tests -p 'test_game1_objectives.py' -v`.

A small-budget game is independently enumerated using literal pairwise scoring. Its population optima and all five decision rules are compared with the production search, including fractional tail weights, zero-weight scenarios, and several guard tolerances. The weighted-mean winner is also checked against DP on the weighted mixture.

A two-soldier example verifies a real tradeoff: the mean winner scores 8.2 on average with tail mean 7, while a 0.25 tail guard chooses an allocation averaging 7.6 with tail mean 7.5. Relaxing the guard to 0.50 restores the mean winner. Other checks cover exclusion of zero-weight scenarios, the one legal allocation at budget zero, enumeration counts, and invalid inputs.

## 中文

运行 `python -m unittest discover -s tests -p 'test_game1_objectives.py' -v`。

测试独立枚举一个小预算博弈，逐对按规则计算得分。再将人群最优值和五种决策规则与正式搜索比较，覆盖部分尾部权重、零权重场景和不同尾部容忍度。加权平均最优值还与混合人群上的 DP 结果比较。

一个两名士兵的例子验证真实取舍：均值最优方案平均得 8.2 分，尾部均值为 7；0.25 分尾部限制改选平均 7.6、尾部 7.5 的配兵。将限制放宽至 0.50，又恢复均值最优方案。其他检查覆盖零权重场景的排除、零预算下唯一配兵、枚举总数，以及错误输入。
