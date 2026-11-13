# Game 2: a field of related opponent populations

## English

`build_field(candidates, seed, samples=3000, screen=1024, check=8192, fresh=False)` builds **90 scenarios** from ten population banks. Each scenario is a probability distribution over complete legal allocations. The input candidate matrix supplies allocations that strategic opponents can evaluate and refine.

### Player types and population families

H uses simple templates. C concentrates on selected castles with secondary bids. Z submits **0/0/0/0/100**. F focuses on castles 1/2/3. T uses the team's original two Game 2 ideas and nearby choices. S chooses strong responses to predictions of the whole field.

The training families use these percentages:

| Family | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| Concentration | 2 | 38 | 10 | 10 | 15 | 25 |
| Calculation | 2 | 18 | 10 | 10 | 10 | 50 |
| Fifth castle | 2 | 28 | 20 | 5 | 10 | 35 |
| First three | 2 | 23 | 5 | 25 | 10 | 35 |
| Original ideas | 2 | 23 | 10 | 10 | 25 | 30 |

Each family has two C bid habits. Low secondary bids are 0/1/2/3; raised bids are 1/2/3/4. Both use probabilities 25/35/25/15%. C chooses one/two/three main castles with probabilities 5/70/25%, with log-noise standard deviation 0.25. The fifth-castle selection weights are 1, 1, 1.5, 0.8, and 1 across the five families.

H and the two original T neighborhoods are generated once per phase and reused. Within T, the teammate's share is 50%, 50%, 75%, 25%, and 50% across families. F mixes 75% of the zero-secondary first-three population with 25% of its small-secondary variant. C and S may also choose Z-like or F-like allocations; `structural_probabilities` measures these shapes across the complete mixture.

### How S reasons

Each bank builds four levels, with three beliefs at every level:

1. Start from the family's Z and F shares. Belief offsets, in percentage points, are **(Z −5, F +5)**, **unchanged**, and **(Z +5, F −5)**; each resulting share is clipped to 2% through 30%. H is 2%, and T retains its family share.
2. Let the remaining population share be \(R=1-h-z-f-t\). Level 1 assigns all of R to C. Higher levels assign 40%, 60%, or 80% of R to an equal mixture of completed earlier S levels, depending on the belief. The rest of R stays C. The explicit H/Z/F/T shares remain fixed within that belief.
3. `response_search` compares candidates on full four-player ranking rewards, refines promising allocations, and independently rescores them. It retains up to 12 diverse strong choices. The three belief-specific response distributions receive equal weight to form the next level.

The stored diagnostics include each belief's full shares, response seed, and search result. S is built once per bank; scenarios change its level weights without retraining it.

`_reasoning_levels(..., belief_floor=0.02)` sets the lower bound on predicted Z and F shares. Sensitivity tests can pass `belief_floor=0` so a belief may assign no players to either type. This changes predictions used to generate S; actual population shares are supplied separately. The default reproduces the original field.

### From ten banks to 90 scenarios

For each family/bid bank, H takes shares **0/2/5%**, transferring the difference from C. Three S mixtures use level-1/2/3/4 weights:

| Style | Level weights |
|---|---|
| Shallow | 10/50/40/0% |
| Central | 5/30/50/15% |
| Deep | 0/15/40/45% |

Thus five families × two bid habits × three H shares × three S styles produce 90 scenarios. Their evaluation weights are the product of **20% per family**, **50% per bid habit**, **25/50/25% across H settings**, and **25/50/25% across S styles**. These weights sum to one and weight scenarios in evaluation; the H/C/Z/F/T/S percentages instead describe players inside a scenario.

### Fresh populations

`fresh=True` uses the caller's new seed and changes the underlying settings:

| Family | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| Concentration | 2 | 33 | 12 | 12 | 15 | 26 |
| Calculation | 2 | 16 | 12 | 12 | 8 | 50 |
| Fifth castle | 2 | 27 | 18 | 8 | 10 | 35 |
| First three | 2 | 25 | 8 | 22 | 10 | 33 |
| Original ideas | 2 | 22 | 8 | 12 | 28 | 28 |

H settings become 1/3/5%, again adjusting C. Low secondary bids are 0/1/2/3/4 with probabilities 20/25/30/15/10%; raised bids are 1/2/3/4/5 with probabilities 15/25/30/20/10%. C's main-castle counts use 10/60/30%, with noise 0.35. F mixes 50% zero-secondary with 50% of the broader shifted variant. S styles become 5/50/45/0%, 0/25/50/25%, and 0/10/35/55%. Scenario weighting remains unchanged.

### Output

The return dictionary contains `scenarios`, `metadata`, `weights`, `models`, and `parameters`. Each `models[family/bids]` stores its H/C/Z/F/T components, four S levels, baseline shares, seeds, and reasoning diagnostics. Scenario metadata records actual group shares and probabilities of an exact 100 on castle 5, all soldiers within the first three castles, and the stricter first-three pattern with all three bids positive. All allocation probabilities include overlap between behavioral types.

## 中文

`build_field(candidates, seed, samples=3000, screen=1024, check=8192, fresh=False)` 从十个基础人群建立 **90 个场景**。每个场景都保存完整合法配兵的概率分布。输入候选矩阵供策略型对手比较和局部调整。

### 类型与人群组合

H 使用简单模板，C 集中争夺若干城并保留小额出价，Z 提交 **0/0/0/0/100**，F 集中前三城，T 使用我们最初的两种 Game 2 想法及其变体，S 根据对整个人群的预测寻找强回应。

训练时使用以下人数百分比：

| 组合 | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| 集中型较多 | 2 | 38 | 10 | 10 | 15 | 25 |
| 计算型较多 | 2 | 18 | 10 | 10 | 10 | 50 |
| 第五城热门 | 2 | 28 | 20 | 5 | 10 | 35 |
| 前三城热门 | 2 | 23 | 5 | 25 | 10 | 35 |
| 原始想法热门 | 2 | 23 | 10 | 10 | 25 | 30 |

每个组合分别使用两种 C 出价习惯：低出价为 0/1/2/3，较高出价为 1/2/3/4，概率均为 25/35/25/15%。C 以 5/70/25% 的概率选择一/二/三座重点城，对数扰动标准差为 0.25。五个组合对第五城的选择权重依次为 1、1、1.5、0.8、1。

每个阶段只生成一次 H 和两种原始 T 变体，再反复使用。T 内队友方案的比例依次为 50%、50%、75%、25%、50%。F 按 75% 后两城全零、25% 后两城有小额出价的变体混合。C、S 也可能选出类似 Z 或 F 的配兵；`structural_probabilities` 从整个混合人群统计这些形状的实际概率。

### S 怎样推理？

每个基础人群生成四层，每层有三种信念：

1. 从该组合的 Z、F 比例出发，分别调整 **Z 减 5 个百分点、F 加 5 个百分点**，**保持原值**，以及 **Z 加 5 个百分点、F 减 5 个百分点**；每个调整后比例限制在 2% 至 30%。H 固定 2%，T 保持该组合比例。
2. 剩余人数比例是 \(R=1-h-z-f-t\)。第一层将 R 全部分给 C。更高层按三种信念，分别将 R 的 40%、60%、80% 分给此前各层 S 的等权混合，剩余部分保留 C。这种信念中的 H/Z/F/T 比例保持不变。
3. `response_search` 按完整四人排名奖励比较候选，局部调整有希望的方案，再用新对局复评，保留最多 12 个不同的强选择。三种信念各占三分之一，组成下一层。

记录包括每种信念的完整比例、回应随机种子和搜索结果。每个基础人群只生成一次 S；不同场景改变层级权重时直接复用它。

`_reasoning_levels(..., belief_floor=0.02)` 设置预测中的 Z、F 比例下限。敏感性检验可传入 `belief_floor=0`，允许某种信念认为这类玩家不存在。这只改变生成 S 时的预测，实际人群比例另行指定。默认设置保持原有人群构造。

### 十个基础人群怎样变成 90 个场景？

每个“组合/出价习惯”下，H 分别占 **0/2/5%**，差额从 C 调整。S 使用三种一/二/三/四层比例：较浅 **10/50/40/0%**，中心 **5/30/50/15%**，较深 **0/15/40/45%**。

五个组合 × 两种出价 × 三个 H 比例 × 三种 S 深度，共 90 个场景。评估场景的权重按 **每组合 20%**、**每种出价 50%**、**三个 H 设置为 25/50/25%**、**三种 S 深度为 25/50/25%** 相乘，总和为一。这些权重用于汇总不同场景的成绩；H/C/Z/F/T/S 的人数比例描述每个场景内部的对手构成。

### 新人群检验

`fresh=True` 使用调用者提供的新随机种子，并改变基础设置：

| 组合 | H | C | Z | F | T | S |
|---|---:|---:|---:|---:|---:|---:|
| 集中型较多 | 2 | 33 | 12 | 12 | 15 | 26 |
| 计算型较多 | 2 | 16 | 12 | 12 | 8 | 50 |
| 第五城热门 | 2 | 27 | 18 | 8 | 10 | 35 |
| 前三城热门 | 2 | 25 | 8 | 22 | 10 | 33 |
| 原始想法热门 | 2 | 22 | 8 | 12 | 28 | 28 |

H 改为 1/3/5%，仍通过 C 调整差额。低出价改为 0/1/2/3/4，概率 20/25/30/15/10%；较高出价为 1/2/3/4/5，概率 15/25/30/20/10%。C 选择重点城数量的概率改为 10/60/30%，扰动为 0.35。F 按 50% 后两城全零、50% 更分散的 shifted 变体混合。三种 S 深度权重改为 5/50/45/0%、0/25/50/25%、0/10/35/55%。评估场景的权重保持不变。

### 输出

返回 `scenarios`、`metadata`、`weights`、`models`、`parameters`。`models[组合/出价]` 保存 H/C/Z/F/T 分布、四层 S、基础人数比例、种子及推理记录。场景元数据记录实际人数比例，并统计恰好全投第五城、全部兵力位于前三城、以及前三城均为正且后两城全零的概率。这些概率同时计入不同决策类型产生的相同配兵形状。
