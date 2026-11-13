# Game 2 checks

## English

Run `python -m unittest discover -s tests -p 'test_game2.py' -v`.

The tests read the scoring rules independently using exact fractions, then compare them with the production evaluator. They check identical allocations, abandoned castles, three-way castle ties, tied rankings, total castle points and prizes of 15, player-order invariance, and the fast lookup against direct four-player scoring. A separate example holds every castle's marginal distribution fixed while changing complete allocations; the ranking reward changes, confirming that Game 2 needs joint allocations. Invalid budgets, fractional soldiers, and input shapes are rejected.

For the original ideas A = `0 / 1 / 36 / 0 / 63` and B = `0 / 0 / 49 / 51 / 0`, enumerating all eight opponent triples gives a checkable mixture example: with 50% A and 50% B, either earns 3.75; with 80% A and 20% B, A earns 3.12 and B earns 6.27.

Population checks verify that duplicate vectors combine their probabilities correctly and that each of the three opponents independently draws a type. Search checks verify legal budget-preserving neighbor moves, retention of both robust candidates and scenario specialists, and independent evaluation against a deterministic population. The last check uses several batches and confirms exact scores, paired gaps, and zero standard errors.

Concentration tests separate opponents focusing on one, two, and three castles. A small example verifies every allocation's mixture probability and expected soldier counts. Changing the one-castle share preserves each component's full joint distribution; shares of zero and one remove the correct components. Further checks vary the all-in fraction inside the one-castle group, confirm legal generated allocations and profile-specific all-in weights, and verify reproducibility. Extending reasoning from three to four levels under the same seed preserves the first three levels exactly.

A hand-calculated game checks both tie layers: two players use `0 / 0 / 50 / 50 / 0`, and two use `0 / 0 / 0 / 0 / 100`. Castle totals are `4.25, 4.25, 3.25, 3.25`; ranking rewards are `6.5, 6.5, 1, 1`.

Two further games check the first-three-castle idea. `33 / 33 / 34 / 0 / 0` can win those castles for 6 points while another player wins castles 4 and 5 for 9, finishing second. It can also lose all three castles to different opponents. Scoring 6 does guarantee at least second place: two opponents each above 6 would force total castle points above 18, whereas only 15 exist. The population test checks the four original first-three templates, positive bids on those castles, and exact zero-secondary shares of 100%, 50%, and 20% in the three variants.

Field tests distinguish uncertainty about a whole population from mixing types within one population. For strategy A, equal weights on an all-A world and an all-B world give `(3.75 + 9) / 2 = 6.375`; independently drawing opponents from a 50/50 mixture gives 3.75. Further tests inspect the actual allocation probabilities passed to reasoning search: H/Z/F/T retain their assigned masses while C and earlier responders share the remainder. A small 90-scenario field verifies each family's 20% prior weight and includes strategic players when measuring actual first-three and all-in shapes.

## 中文

运行 `python -m unittest discover -s tests -p 'test_game2.py' -v`。

测试用精确分数独立实现计分规则，再与正式计算比较。覆盖所有人配兵相同、无人投入的城、三人并列赢城、总分并列、城堡分与奖金总和均为 15、玩家顺序不影响结果，以及快速查表与直接四人计分的一致性。另一个例子保持每城边际分布相同，但改变完整配兵组合；名次奖励随之改变，验证 Game 2 必须保留联合配兵。错误预算、非整数兵力和错误输入形状会被拒绝。

对原始方案 A = `0 / 1 / 36 / 0 / 63` 和 B = `0 / 0 / 49 / 51 / 0`，枚举全部八种三人组合可得到一个能直接核对的混合例子：A、B 各占 50% 时，两者均得 3.75；A 占 80%、B 占 20% 时，A 得 3.12，B 得 6.27。

人群测试检查重复配兵的概率能正确合并，并确认三位对手分别独立抽取类型。搜索测试检查兵力转移后仍合法、候选筛选同时保留稳健方案与各场景的强者，以及对固定人群进行独立评估。最后一项跨多个批次计算，核对精确得分、配对差值和为零的标准误。

集中程度测试分别构造重点争夺一、二、三座城的人群。一个小例子核对每个完整配兵的混合概率及各城平均兵力。改变单城人群比例时，各组内部的联合分布保持不变；比例为零或一时，正确移除对应成分。还检查单城人群内部的全押比例、生成配兵的合法性、不同第五城偏好下的全押权重及复现性。使用同一随机种子把推理从三层扩展到四层，前三层保持完全相同。

一个手算对局检查两层并列：两人使用 `0 / 0 / 50 / 50 / 0`，两人使用 `0 / 0 / 0 / 0 / 100`。四人的城堡总分是 `4.25、4.25、3.25、3.25`，名次奖励是 `6.5、6.5、1、1`。

另两个对局检验前三城方案。`33 / 33 / 34 / 0 / 0` 可以赢下前三城获得 6 分，同时另一人赢下第四、第五城获得 9 分，因此只排第二；也可能前三城分别被不同对手夺走。实际获得 6 分确实保证至少第二名：若两位对手均超过 6 分，总城堡分就会超过 18，与总分只有 15 矛盾。人群测试核对四个原始前三城模板、前三城正出价，以及三种变体中后两城均为零的概率分别为 100%、50%、20%。

整体人群测试区分“整个参赛人群未知”和“同一人群内部混合类型”。使用方案 A 时，对全 A 人群和全 B 人群各赋 50% 权重，平均得分为 `(3.75 + 9) / 2 = 6.375`；三位对手分别从 A/B 各半的人群抽取时，得分为 3.75。其他测试直接检查传入推理搜索的配兵概率：H/Z/F/T 保留各自指定份额，C 和前层反制者分配剩余部分。一个小型 90 场景实验验证每个人群家族占 20% 权重，并在统计实际前三城和全押结构时计入策略反制者。
