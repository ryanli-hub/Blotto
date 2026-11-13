# `game.py`

## English

### Goal and inputs

This module implements **Game 1** from `docs/rules.md`. An allocation is a vector of nonnegative integers summing to the budget. Its entries follow castle order, worth `[1, 2, 3, 4, 5]` points. The objective is expected castle points per opponent, not the probability of winning a matchup. Ties split a castle's points.

For allocations \(x,y\), the score is

\[
u(x,y)=\sum_{k=1}^{K}v_k\left(\mathbf 1_{x_k>y_k}+\tfrac12\mathbf 1_{x_k=y_k}\right).
\]

Consequently \(u(x,y)+u(y,x)=\sum_k v_k\), which is 15 in the actual game.

### Data flow

1. `validate_allocations` accepts one allocation or a matrix of allocations and returns an integer matrix. With \(N\) opponents, its shape is \(N\times K\). Every row must spend exactly the budget.
2. `payoff` scores two vectors. `payoff_matrix(rows, cols)` returns an \(N\times M\) matrix; entry `[i, j]` is the score of row strategy `i` against column strategy `j`. These scoring functions infer the common budget, so small examples work too.
3. `marginals(allocations, weights)` converts legal opponent allocations into probabilities. Positive weights are normalized; omitted weights mean equal weights. The output \(p\) has shape \(K\times(B+1)\), or \(5\times101\). Entry \(p_{k,a}\) means the probability that an opponent sends exactly \(a\) soldiers to castle \(k\).
4. `expected_rewards` computes the score from sending \(a\) soldiers to one castle:

\[
r_{k,a}=v_k\left(\sum_{j=0}^{a-1}p_{k,j}+\tfrac12 p_{k,a}\right).
\]

5. `best_response` chooses one legal allocation maximizing \(\sum_k r_{k,x_k}\). It returns `(allocation, expected_score)`.

Linearity of expectation justifies step 4 even when an opponent's castle allocations are dependent. Marginals suffice to evaluate a strategy, but arbitrary marginal tables need not describe a legal joint strategy. `marginals` avoids that problem by starting from legal allocation vectors. The equilibrium solver also maintains a mixture of legal vectors.

### A small calculation before the DP

Use budget \(B=3\), values \([1,2]\), and equally likely opponents \([1,2]\) and \([3,0]\). Then

\[
p=\begin{bmatrix}0&1/2&0&1/2\\1/2&0&1/2&0\end{bmatrix},
\qquad
r=\begin{bmatrix}0&1/4&1/2&3/4\\1/2&1&3/2&2\end{bmatrix}.
\]

Rows identify castles; columns identify soldier counts 0, 1, 2, 3. For example, sending two soldiers to castle 2 wins against zero and ties against two, giving \(2(1/2+1/4)=3/2\) points. Allocation \([0,3]\) scores \(r_{1,0}+r_{2,3}=2\), the optimum.

### DP state, update, and reconstruction

Let \(D_k(b)\) be the largest expected score using the first \(k\) castles and **exactly** \(b\) soldiers. Initialize \(D_0(0)=0\) and \(D_0(b)=-\infty\) for \(b>0\). If the current castle receives \(a\), the earlier castles receive \(b-a\), hence

\[
D_k(b)=\max_{0\le a\le b}\{D_{k-1}(b-a)+r_{k,a}\}.
\]

Every feasible allocation appears in one candidate, classified by its last entry. By induction, the previous state already contains the best prefix for its budget. Therefore the recurrence gives the best complete allocation, and \(D_K(B)\) is the desired optimum.

For the example, the four candidates for \(D_2(3)\), in increasing order of the soldiers on castle 2, are \(3/4+1/2,\ 1/2+1,\ 1/4+3/2,\ 0+2\). The last is largest. Backtracking assigns three soldiers to castle 2 and zero to castle 1.

The code computes a \((B+1)\times(B+1)\) candidate grid for each castle. Its rows are total budgets \(b\), and its columns are current allocations \(a\); cells with \(a>b\) are forbidden. `choices[k, b]` records the maximizing column. Backtracking subtracts each chosen allocation from the remaining budget. On exactly equal computed scores, `argmax` selects the smallest current-castle allocation. This makes response paths reproducible; other optimal tie choices can produce other paths.

Runtime is \(O(KB^2)\). Working memory is \(O(B^2+KB)\), including the candidate grid and reconstruction table. This is an exact search over integer allocations, implemented with floating-point expected scores.

### Run a small example

From the project directory:

```python
from blotto.game import best_response, marginals

p = marginals([[1, 2], [3, 0]], budget=3)
allocation, score = best_response(p, values=[1, 2], budget=3)
print(allocation, score)  # [0 3] 2.0
```

## 中文

### 目标和输入

本模块只实现 `docs/rules.md` 的 **Game 1**。一个 allocation 是非负整数向量，各分量之和等于总兵力；实际题目按价值 `[1, 2, 3, 4, 5]` 排列五座城堡。目标是每位对手带来的平均城堡分数，不是赢下一场对决的概率。兵力相等时平分城堡分数。

对双方分配 \(x,y\)，得分为

\[
u(x,y)=\sum_{k=1}^{K}v_k\left(\mathbf 1_{x_k>y_k}+\tfrac12\mathbf 1_{x_k=y_k}\right).
\]

因此 \(u(x,y)+u(y,x)=\sum_kv_k\)，本题恒等于 15。

### 数据如何进入计算

1. `validate_allocations` 接收一个向量或多个分配组成的矩阵，返回整数矩阵。若有 \(N\) 个对手，矩阵大小为 \(N\times K\)。每一行必须用完全部兵力。
2. `payoff` 计算两个向量之间的得分；`payoff_matrix(rows, cols)` 返回 \(N\times M\) 矩阵，其中 `[i, j]` 表示第 `i` 个行策略对第 `j` 个列策略的得分。计分函数从第一行读取共同预算，也适用于小规模例子。
3. `marginals(allocations, weights)` 把合法的对手分配转换为 marginal distributions，正权重会归一化，不提供权重则等权。输出 \(p\) 的大小为 \(K\times(B+1)\)，本题是 \(5\times101\)。\(p_{k,a}\) 表示对手在第 \(k\) 座城堡恰好放 \(a\) 个兵的概率。
4. `expected_rewards` 计算在某座城堡放 \(a\) 个兵的期望得分：

\[
r_{k,a}=v_k\left(\sum_{j=0}^{a-1}p_{k,j}+\tfrac12p_{k,a}\right).
\]

5. `best_response` 在所有合法整数分配中最大化 \(\sum_k r_{k,x_k}\)，返回 `(allocation, expected_score)`。

第 4 步使用期望的线性性，不要求对手在不同城堡的兵力相互独立。计算期望得分只需要 marginals；但任意拼凑的 marginals 未必能对应一个合法的联合分配。`marginals` 从合法向量出发，因此不会引入这个问题。均衡算法也始终保存合法向量的混合。

### 先算一个小例子

设总兵力 \(B=3\)，两座城堡价值为 \([1,2]\)，对手以相等概率使用 \([1,2]\) 和 \([3,0]\)。于是

\[
p=\begin{bmatrix}0&1/2&0&1/2\\1/2&0&1/2&0\end{bmatrix},
\qquad
r=\begin{bmatrix}0&1/4&1/2&3/4\\1/2&1&3/2&2\end{bmatrix}.
\]

每一行对应一座城堡，每一列对应兵力 0、1、2、3。例如在城堡 2 放两个兵，以一半概率胜过零兵，以一半概率与两个兵打平，期望得分为 \(2(1/2+1/4)=3/2\)。选择 \([0,3]\) 的得分为 \(r_{1,0}+r_{2,3}=2\)，是最优解。

### DP 的状态、更新和还原

定义 \(D_k(b)\)：只使用前 \(k\) 座城堡，且**恰好**分配 \(b\) 个兵时的最高期望分数。初始条件为 \(D_0(0)=0\)，对 \(b>0\) 取 \(D_0(b)=-\infty\)。若当前城堡放 \(a\) 个兵，前面的城堡只能使用 \(b-a\) 个兵，因此

\[
D_k(b)=\max_{0\le a\le b}\{D_{k-1}(b-a)+r_{k,a}\}.
\]

所有合法分配都能按最后一座城堡的兵力归入某个候选项。归纳假设保证上一层已经给出对应预算下的最优前缀，所以当前最大值就是完整分配的最优值。最终答案是 \(D_K(B)\)。

上例中，按城堡 2 的兵力从小到大，\(D_2(3)\) 的四个候选项是 \(3/4+1/2,\ 1/2+1,\ 1/4+3/2,\ 0+2\)。最后一项最大，所以回溯得到城堡 2 放三个兵，城堡 1 放零个兵。

代码为每座城堡计算一个 \((B+1)\times(B+1)\) 候选矩阵：行是总预算 \(b\)，列是当前分配 \(a\)，屏蔽 \(a>b\) 的位置。`choices[k, b]` 保存最大值所在列。回溯时逐座城堡扣除已经选中的兵力。在计算出的得分完全相等时，`argmax` 选择当前城堡兵力最小的一项。这个规则保证反制路径可重复；换一种最优解的选取规则，可能得到另一条路径。

时间复杂度为 \(O(KB^2)\)，空间复杂度为 \(O(B^2+KB)\)，包括候选矩阵和回溯记录。算法穷尽了所有整数分配的可能性，但期望得分使用浮点数计算。

### 运行小例子

在项目目录中执行：

```python
from blotto.game import best_response, marginals

p = marginals([[1, 2], [3, 0]], budget=3)
allocation, score = best_response(p, values=[1, 2], budget=3)
print(allocation, score)  # [0 3] 2.0
```
