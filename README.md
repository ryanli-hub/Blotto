# Colonel Blotto: Games 1 and 2

## English

Strategy analysis for allocating 100 soldiers across five castles worth 1, 2, 3, 4, and 5 points. Game 1 optimizes expected head-to-head castle points. Game 2 simulates four-player matches and optimizes ranking rewards. The project includes opponent models, search algorithms, tests, bilingual reports, and saved experimental results.

### Start here

- [Rules](docs/rules.md).
- [Game 1 final report](docs/team_update.md): reviewed allocation **3 / 8 / 13 / 11 / 65**, with its assumptions and tradeoffs. The reviewed choice is saved in [decision.json](results/game1_final/decision.json).
- [Game 2 latest report](docs/game2_round3.md): objectives, opponent coverage, and candidate comparisons.
- [Documentation index](docs/README.md): experiment guides, module explanations, tests, and historical reports.
- [Upload and sync with GitHub in VS Code, Chinese guide](docs/github-vscode.md).

### Project layout

```text
Blotto/
├── blotto/             # Scoring, population models, and optimization
├── experiments/        # Runnable experiment modules
├── tests/              # Unit tests
├── docs/               # Rules, reports, and guides
│   ├── experiments/    # Experiment instructions
│   ├── modules/        # Explanations of blotto modules
│   ├── tests/          # Test explanations
│   └── reference/      # Historical source report and PDF
├── results/            # Saved results and populations by experiment stage
├── requirements.txt    # Runtime dependencies
└── README.md
```

### Setup and run

Use Python 3.12, the version used to validate this project. From the project root, create an environment and install the dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

If you already have a suitable Python environment, activate it and use the last two commands. In VS Code, select that environment with **Python: Select Interpreter**. The virtual environment is excluded from Git; recreate it after cloning.

Run experiments as modules from the project root:

```bash
python -m experiments.run_game1_final --help
python -m experiments.run_game1_final
python -m experiments.run_game2_round3
```

Full runs can take substantial time and overwrite outputs in their default result folders. To preserve the saved studies, pass a different output folder, for example `--output results/game1_new_run`. Some stages read saved inputs from earlier stages; see the [experiment guides](docs/README.md#experiment-guides) before rerunning. The reviewed Game 1 decision is recorded separately from the training optimizer and is not regenerated automatically.

All saved results are retained for reproducibility. See the [results index](results/README.md) for stage names and file types. Results describe the specified synthetic opponent models; they are not observed tournament outcomes.

## 中文

本项目研究如何把 100 名士兵分配到价值为 1、2、3、4、5 分的五座城堡。Game 1 优化双人对局的平均城堡得分；Game 2 模拟四人对局，优化排名奖励。项目保留了对手模型、搜索算法、测试、英中双语报告和实验结果。

先读[规则](docs/rules.md)、[Game 1 最终报告](docs/team_update.md)和[Game 2 最新报告](docs/game2_round3.md)。Game 1 最终审阅建议为 **3 / 8 / 13 / 11 / 65**，其假设、取舍及与其他候选的比较见报告；[decision.json](results/game1_final/decision.json) 保存最终判断。完整导航见[文档索引](docs/README.md)，上传流程见 [VS Code 与 GitHub 教程](docs/github-vscode.md)。

`blotto/` 放核心代码，`experiments/` 放实验入口，`tests/` 放测试，`docs/` 放说明，`results/` 按实验阶段保存结果。已有说明仍保留英文在前、中文在后的形式。`docs/reference/` 中的 Game 1 报告和 PDF 是旧版历史材料。

上面的安装命令使用已验证的 Python 3.12。已有可用环境时，直接激活环境、安装 `requirements.txt` 并执行测试；在 VS Code 中用 **Python: Select Interpreter** 选中该环境。运行实验时，终端必须位于项目根目录，统一使用 `python -m experiments.模块名`。完整实验耗时较长，同一路径重跑会覆盖原输出；需要保留已有结果时，用 `--output` 指定新目录。部分阶段依赖以前保存的结果，先查[实验说明](docs/README.md#experiment-guides)。Game 1 的最终审阅判断与训练选择分开保存，不会由实验自动生成。

全部已有结果均保留，便于复现。它们反映给定模拟对手模型下的表现，不能视为真实赛事成绩。结果目录说明见 [results/README.md](results/README.md)。
