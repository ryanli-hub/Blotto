# 在 VS Code 中上传与同步 Blotto

下面从当前项目文件夹开始，完成首次上传，再说明日常同步。Git 在本机保存版本历史，GitHub 托管远程仓库，VS Code 提供操作 Git 的界面。**保存文件、Commit、Push 是三个步骤**：保存写入本地文件，Commit 记录本地版本，Push 才把提交上传。[概念说明](https://code.visualstudio.com/docs/sourcecontrol/overview)

## 1. 打开整个项目，检查 Git

在 VS Code 中选择 **File → Open Folder…**，打开 `/Users/ryanli/Temp/Blotto`。左侧应能看到 `README.md`、`blotto/`、`experiments/`、`docs/`、`results/` 和 `tests/`。不要只打开其中一个子目录。

选择 **Terminal → New Terminal**，执行：

```bash
git --version
```

出现版本号即可继续。如果未安装 Git，macOS 可执行 `xcode-select --install`，按提示安装 Command Line Tools，然后重新打开 VS Code。[Git 安装说明](https://git-scm.com/install/mac)

## 2. 初始化本地仓库并提交

1. 点击左侧 **Source Control（源代码管理）** 图标，选择 **Initialize Repository（初始化仓库）**。找不到按钮时，按 `⌘⇧P`，运行 **Git: Initialize Repository**，选择项目根目录。
2. 在终端设置本项目提交的作者信息。替换以下文字；若已有正确配置，可跳过。这是提交署名，不是 GitHub 登录信息。

   ```bash
   git config user.name "你的名字"
   git config user.email "你的提交邮箱"
   ```

3. 在 **Changes** 中检查文件列表。现有 `.gitignore` 会排除缓存、虚拟环境等本地文件；源代码、文档、测试和 `results/` 中的实验结果都应纳入仓库。“整个项目”指这些需要版本管理的文件。
4. 在 **Changes** 标题旁点击 **+（Stage All Changes）**，把全部待提交文件放入 **Staged Changes**。检查后输入提交说明，例如 `Organize project structure`，点击 **Commit（提交）**。
5. 在终端执行 `git branch -M main`，将当前分支统一命名为 `main`。

此时已建立本地版本，尚未上传。[VS Code 初始化、暂存与提交说明](https://code.visualstudio.com/docs/sourcecontrol/quickstart)

## 3. 首次发布到 GitHub

按 `⌘⇧P`，搜索并运行 **Publish to GitHub**。根据提示在浏览器登录 GitHub 并授权，然后回到 VS Code，输入仓库名，例如 `blotto`。

选择 **Private** 或 **Public**。推荐个人仓库先选 Private，仅你及你明确授权的人可访问；确认需要公开展示时再调整可见性。[可见性说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)

如果出现文件选择界面，保留全部需要纳入的项目文件。VS Code 会创建 GitHub 仓库、配置远程地址并上传提交，无须先去网页创建同名仓库。[发布说明](https://code.visualstudio.com/docs/sourcecontrol/repos-remotes)

上传结束后点击 **Open on GitHub**。核对仓库能看到 `README.md`、主要目录、`results/` 内文件以及刚才的提交记录。若源代码管理中没有待提交修改、没有待推送提交，且网页显示对应提交，本轮同步即完成。

### 当前结果文件的体积

整理前本项目约 **374 MiB**，主要来自已保存实验结果；最大文件 `results/structure/comparison.json` 约 **84.63 MiB**。当前没有超过 100 MiB 的单个文件，因此本次可用普通 Git 完整上传。该大文件可能触发警告：GitHub 对超过 **50 MiB** 的文件警告，对超过 **100 MiB** 的普通 Git 文件拒绝接收。首次传输时间取决于压缩后大小和网络。[GitHub 大文件限制](https://docs.github.com/en/enterprise-cloud@latest/repositories/working-with-files/managing-large-files/about-large-files-on-github)

如果之后会频繁重新生成这些大型结果，建议在首次提交前评估 Git LFS，减少普通 Git 历史中的大文件负担。Git LFS 需要单独安装，并把跟踪规则写入 `.gitattributes`；本项目目前没有启用它。按当前快照上传，可以直接采用上面的普通 Git 流程。[安装 Git LFS](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage)、[配置跟踪规则](https://docs.github.com/en/repositories/working-with-files/managing-large-files/configuring-git-large-file-storage)

## 4. 以后如何同步

每次修改后按以下顺序操作：

1. **Save All**，把编辑器内容保存到文件。
2. 在 **Source Control** 中逐项查看改动，点击 **+** 暂存要上传的文件。
3. 输入具体提交说明，点击 **Commit**。
4. 点击 **Sync Changes（同步更改）**，再到 GitHub 核对新提交。

**Sync Changes 会先 Pull，再 Push**：先整合远程提交，再上传本地提交。若只要上传，源代码管理的 **… → Push** 只执行推送；自动保存或 Commit 本身不会上传。[同步说明](https://code.visualstudio.com/docs/sourcecontrol/repos-remotes)

如果还在其他电脑上修改，或在 GitHub 网页编辑文件，每次开始工作前先在干净工作区执行 **… → Pull**。新电脑首次使用时，运行命令面板里的 **Git: Clone**，粘贴该仓库地址，再选择打开克隆的文件夹；之后使用同一套提交与同步流程。[克隆与拉取说明](https://code.visualstudio.com/docs/sourcecontrol/repos-remotes)

若 Pull 提示 conflict，在 **Merge Changes** 中打开冲突文件，比较两边内容并编辑出需要保留的结果，保存、暂存，然后按 VS Code 提示完成当前合并或 rebase。确认代码与文档正确后再 Push。三方编辑器中的 **Complete Merge** 只完成该文件的处理，还需完成整个仓库的合并操作。[冲突处理说明](https://code.visualstudio.com/docs/sourcecontrol/merge-conflicts)
