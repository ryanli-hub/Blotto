# Saved experiment results / 已保存的实验结果

## English

These files preserve the existing synthetic-population studies. Their paths remain unchanged because later experiments load earlier populations, equilibrium solutions, and comparisons. JSON files store settings and summaries; compressed NumPy `.npz` files store populations and score arrays. The reports explain each array's meaning. Use `numpy.load` to inspect `.npz` files.

| Location | Experiment stage |
|---|---|
| Files directly in this folder | Original Game 1 equilibrium, diagnostics, comparisons, and summary |
| `revised/` | Revised Game 1 opponent models and robust search |
| `anticipation/` | Further reasoning and counterstrategy checks |
| `structure/` | Castle-2/4/5 cohort and historical populations |
| `game1_final/` | Final Game 1 objectives, fresh validation, stress tests, and reviewed decision |
| `game2/` | First Game 2 study and follow-up |
| `game2_round2/` | Second Game 2 study with controlled population changes |
| `game2_round3/` | Latest Game 2 study with multiple objectives and coverage checks |
| `previous_workflow.zip` | Archived original runner and report |

Start with the [current reports](../docs/README.md) before interpreting older files. Historical metadata and archived code may use former module names. Current entry points live in `experiments/` and run from the project root. Rerunning into a saved folder overwrites that stage's outputs; use a new `--output` path to preserve it.

## 中文

这里保存各轮模拟人群实验。后续实验需要读取早期人群、均衡和比较数据，因此保留原有路径。JSON 保存设定与汇总，压缩的 NumPy `.npz` 保存人群和分数数组，可用 `numpy.load` 读取；各数组的含义见对应报告。

根目录文件属于最初的 Game 1 实验；`revised/`、`anticipation/`、`structure/` 是后续阶段；`game1_final/` 保存最终搜索、检验及审阅判断；`game2/`、`game2_round2/`、`game2_round3/` 分别对应 Game 2 的三轮实验。`previous_workflow.zip` 是最早入口与报告的历史压缩包。

阅读旧结果前，先从[文档索引](../docs/README.md)找到当前报告。历史元数据及归档代码可能保留旧模块名；当前入口位于 `experiments/`，从项目根目录运行。同一目录重跑会覆盖该阶段输出，可用新的 `--output` 路径保留原结果。
