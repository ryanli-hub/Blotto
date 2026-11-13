# Documentation / 文档索引

## English

Read the current reports first, then follow the experiment or module guide for the implementation details. All commands run from the project root. Existing technical guides place English before Chinese.

### Reports and references

- [Rules](rules.md).
- [Game 1 final report](team_update.md).
- [Game 2 latest report](game2_round3.md).
- [Game 2 second-round report](game2_round2.md) and [team summary](game2_team_update.md).
- [Earlier Game 1 analysis](analysis.md).
- [Historical Game 1 report](reference/game1.md) and [original PDF](reference/game1.pdf), documenting the earlier 8/9/10/11/62 choice.
- [Saved results index](../results/README.md).
- [VS Code and GitHub upload/sync guide, Chinese](github-vscode.md).

### Experiment guides

Use `python -m experiments.<module>` to run a study, replacing `<module>` with a name below. `--help` shows options without running the study. Each guide describes inputs and outputs. Older stages remain available because later studies reuse their saved populations.

| Module | Code | Guide | Default outputs |
|---|---|---|---|
| `run_experiments` | [Python](../experiments/run_experiments.py) | [English / 中文](experiments/run_experiments.md) | [`results/revised/`](../results/revised/) |
| `run_anticipation` | [Python](../experiments/run_anticipation.py) | [English / 中文](experiments/run_anticipation.md) | [`results/anticipation/`](../results/anticipation/) |
| `run_structure` | [Python](../experiments/run_structure.py) | [English / 中文](experiments/run_structure.md) | [`results/structure/`](../results/structure/) |
| `run_game1_final` | [Python](../experiments/run_game1_final.py) | [English / 中文](experiments/run_game1_final.md) | [`results/game1_final/`](../results/game1_final/) |
| `run_game2` | [Python](../experiments/run_game2.py) | [English / 中文](experiments/run_game2.md) | [`results/game2/`](../results/game2/) |
| `run_game2_round2` | [Python](../experiments/run_game2_round2.py) | [English / 中文](experiments/run_game2_round2.md) | [`results/game2_round2/`](../results/game2_round2/) |
| `run_game2_round3` | [Python](../experiments/run_game2_round3.py) | [English / 中文](experiments/run_game2_round3.md) | [`results/game2_round3/`](../results/game2_round3/) |

### Module guides

The core library stays in `blotto/`; its explanations live in `docs/modules/`.

| Module | Code | Explanation |
|---|---|---|
| `dynamics` | [Python](../blotto/dynamics.py) | [English / 中文](modules/dynamics.md) |
| `game` | [Python](../blotto/game.py) | [English / 中文](modules/game.md) |
| `game1_field` | [Python](../blotto/game1_field.py) | [English / 中文](modules/game1_field.md) |
| `game1_objectives` | [Python](../blotto/game1_objectives.py) | [English / 中文](modules/game1_objectives.md) |
| `game2` | [Python](../blotto/game2.py) | [English / 中文](modules/game2.md) |
| `game2_field` | [Python](../blotto/game2_field.py) | [English / 中文](modules/game2_field.md) |
| `game2_metrics` | [Python](../blotto/game2_metrics.py) | [English / 中文](modules/game2_metrics.md) |
| `game2_population` | [Python](../blotto/game2_population.py) | [English / 中文](modules/game2_population.md) |
| `game2_search` | [Python](../blotto/game2_search.py) | [English / 中文](modules/game2_search.md) |
| `opponents` | [Python](../blotto/opponents.py) | [English / 中文](modules/opponents.md) |
| `robust` | [Python](../blotto/robust.py) | [English / 中文](modules/robust.md) |

### Test guides

Run `python -m unittest discover -s tests -v` for the complete suite. These guides explain the independent checks behind each test module.

| Test module | Code | Explanation |
|---|---|---|
| `test_game` | [Python](../tests/test_game.py) | [English / 中文](tests/test_game.md) |
| `test_game1_field` | [Python](../tests/test_game1_field.py) | [English / 中文](tests/test_game1_field.md) |
| `test_game1_objectives` | [Python](../tests/test_game1_objectives.py) | [English / 中文](tests/test_game1_objectives.md) |
| `test_game2` | [Python](../tests/test_game2.py) | [English / 中文](tests/test_game2.md) |
| `test_game2_metrics` | [Python](../tests/test_game2_metrics.py) | [English / 中文](tests/test_game2_metrics.md) |

## 中文

先读当前的 [Game 1 最终报告](team_update.md)及 [Game 2 最新报告](game2_round3.md)，再查对应实验入口与模块说明。上面的表格分别列出实验、核心模块和测试，均提供代码及英中双语说明链接。

实验入口集中在 `experiments/`，从项目根目录使用 `python -m experiments.模块名`；附加 `--help` 可以查看参数而不运行实验。完整测试命令为 `python -m unittest discover -s tests -v`。

规则见 [rules.md](rules.md)，旧版 Game 1 报告及 PDF 放在 `reference/`。旧报告中的建议保留为历史记录，当前审阅判断以最终报告为准。原有结果路径保留，目录含义见[结果索引](../results/README.md)。首次上传和后续同步，按 [VS Code 与 GitHub 教程](github-vscode.md)操作。
