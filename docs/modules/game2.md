# Game 2 scoring

## English

The goal is average **ranking reward**: first to fourth receive 9, 4, 2, and 0. Each input allocation contains five nonnegative integers totaling 100.

1. `score_groups(groups)` reads a `(groups, 4, 5)` array. In each castle, split its value among the highest bidders. Add each player's castle points, then split the rewards for tied positions. It returns two `(groups, 4)` arrays: castle points and ranking rewards.
2. Castle points are stored in twelfths. Splitting among one, two, three, or four winners is therefore exact. This keeps total-score ties exact too.
3. `prepare_triples(opponents)` reads `(groups, 3, 5)` complete opponent allocations. For every castle and possible bid, it stores our castle points minus each opponent's points. Its integer table has shape `(5, 101, 3, groups)`.
4. `evaluate_candidates(candidates, prepared)` sums five table entries for each candidate. Negative differences count opponents above us; zero differences count tied opponents. A small lookup gives the appropriate rank reward. It returns one sample mean per candidate. With `return_samples=True`, it returns all rewards as `(candidates, groups)`.

All candidates use the same triples, which makes their differences easier to estimate. Preparing the table costs `O(5 × 101 × groups)` time and storage. Evaluating `N` candidates costs `O(5 × N × groups)` time; `chunk_size` limits temporary storage. The prepared table uses about 3 KB per triple, so large final samples should be evaluated in batches.

## 中文

目标是平均**名次奖励**：第一到第四名分别得 9、4、2、0 分。每个配兵输入包含五个非负整数，总和为 100。

1. `score_groups(groups)` 读取形状为 `(对局数, 4, 5)` 的数组。每城由最高出价者平分该城价值，再累计各人的城堡分，并对总分并列者平分所占名次的奖励。返回两个 `(对局数, 4)` 数组：城堡分和名次奖励。
2. 城堡分以十二分之一分为单位保存。由一、二、三、四人平分时均可用整数精确表示，总分并列也能准确判断。
3. `prepare_triples(opponents)` 读取 `(对局数, 3, 5)` 的完整对手配兵。对每座城和每个可能出价，预先记录我方城堡分减去三位对手各自城堡分。整数表形状为 `(5, 101, 3, 对局数)`。
4. `evaluate_candidates(candidates, prepared)` 对每个候选累加五座城的差值。负值表示对手领先，零表示并列，再查表得到名次奖励。默认返回各候选的样本平均奖励；设置 `return_samples=True` 则返回 `(候选数, 对局数)` 的全部奖励。

所有候选使用同一批三人组合，便于估计候选之间的差距。准备表的时间与空间复杂度均为 `O(5 × 101 × 对局数)`。评估 `N` 个候选的时间复杂度为 `O(5 × N × 对局数)`；`chunk_size` 控制临时内存。准备表每组三名对手约占 3 KB，因此最终大样本应分批评估。
