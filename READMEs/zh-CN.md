<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/hero-light.svg">
  <img alt="contextify: one repository, one source of instructions, multiple coding agents" src="../assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](../LICENSE)

[English](../README.md) | [Français](fr.md) | [Español](es.md) | [日本語](ja.md) | 简体中文

<!-- may-lag -->

**当代理指令指向已不存在的东西时，你会知道。所有代理共用一个 AGENTS.md，再加一个不消耗 token 的本地检查。**

contextify 根据你的仓库写出一份简短的 `AGENTS.md`。之后，当它提到的命令、目标或文件消失时，一个本地脚本会告诉你。

## 安装

在 Claude Code 中，从终端运行：

```bash
claude plugin marketplace add Aboudjem/10x
claude plugin install contextify@10x
```

然后在你的仓库里，请求第一份草稿：

```text
/contextify:contextify init
```

对于 Codex、Cursor、Gemini CLI 和其他代理，安装这个技能：

```bash
npx skills add Aboudjem/contextify
```

这些代理没有 `/contextify:` 前缀。直接用文字请求："contextify init"、"contextify update"。

需要 Git、Bash 和 Python 3.11 或更高版本。不需要 Python 包，不需要 MCP 服务器，脚本不发起任何网络请求。

### 示例报告

2026-11-17，contextify 0.3.0 为一个小型 Python 服务写了 `AGENTS.md`。随后，其 `Makefile` 中的 `test-health` 目标被删除。0.3.3 对这个仓库输出如下内容，不消耗任何 token：

```text
contextify: drift
1. Run /contextify:contextify update to fix AGENTS.md:6 (make test-health)
2. Review the diff it shows before it writes
3. Commit the context files with .contextify/
Agents     outside Claude Code, ask for "contextify update"
Scope      .
Stale      AGENTS.md:6 references make test-health
Unverified AGENTS.md:6 python3 -m unittest tests.test_health
Changed    makefile#targets
More       +3 findings
Files      0 written
Accept     unavailable until the stale command is corrected
```

最新状态的仓库什么也不输出。这次运行的文件和印记随示例一起提供，你可以重放：

```bash
sh examples/python-service-0.3.0/replay.sh
```

[完整运行记录、文件以及引发漂移的修改](../examples/python-service-0.3.0/README.md)。

Makefile 目标被删了，脚本改了名，测试挪了位置。你的代理还在照旧指令做事，每次失败都要浪费一轮。contextify 会先指出过时的那一行。

### 为什么用它

- **看到确切的过时行。** 通知给出文件、行号和失效的命令，就像上面的重放示例。
- **只写一次。** 一个 `AGENTS.md`，Codex 和 Cursor 直接读取，无需额外文件。只有你选择的代理才会得到指针文件：`CLAUDE.md`（默认）、`GEMINI.md`、存在 `.github/` 时的 Copilot 文件，以及可选的 Cursor 规则。
- **运行免费。** 本地脚本，不调用模型，也不联网，仓库是最新时不输出任何内容。本仓库自己的 `AGENTS.md` 在 CI 中通过检查：`make test` 最后输出 `29 claims, 0 stale`。

它解析命令、目标和文件，不读散文，也不运行命令。没有研究表明上下文文件能提高任务成功率，所以只保留能防止真实错误的行。

## 工作原理

![证据、草稿、审阅、写入、检查](../assets/how-it-works.svg)

| 模式     | 发生什么                                                  |
| -------- | --------------------------------------------------------- |
| `init`   | 读取仓库，起草说明，审阅证据，展示 diff，然后写入并检查。 |
| `update` | 重新读取证据并修订托管区块。你在区块之外的修改会保留。    |
| `check`  | 将证据与已提交的印记对比。不写入任何内容。                |
| `accept` | 说明仍然正确时刷新印记。失效的声明会被拒绝。              |

它写入的文件：

| 文件                                        | 读者                                         | 行数                        |
| ------------------------------------------- | -------------------------------------------- | --------------------------- |
| `AGENTS.md`                                 | Codex、Cursor 以及其他遵循此约定的代理       | 目标 20、40 或 60；最多 150 |
| `CLAUDE.md`                                 | Claude Code，通过 `@AGENTS.md`               | 默认 4                      |
| `GEMINI.md`                                 | Gemini CLI，通过 `@AGENTS.md`                | 3                           |
| `.cursor/rules/contextify.mdc`              | Cursor；可选，因为 Cursor 也读取 `AGENTS.md` | 9                           |
| `.github/copilot-instructions.md`           | GitHub Copilot                               | 4                           |
| `docs/context/architecture.md`              | 可选的组件和数据流地图                       | 最多 120                    |
| `docs/context/workflows.md`                 | 可选的构建、测试和发布步骤                   | 最多 120                    |
| `.contextify/evidence.json` 和 `stamp.json` | 漂移检查                                     | 取决于仓库                  |

只有你选择的目标才会得到指针文件。每一行事实都对应一个源文件和行号。在 contextify 写入任何内容之前，会有另一个代理审阅草稿。

仓库是最新状态时，漂移检查以 0 退出且不输出任何内容。发生漂移时，它输出上面的通知，仍以 0 退出。它从不重写文件。

退出码，2026-11-17 在 bash 中用 0.3.3 实测：

| 模式                                         | 最新                   | 漂移                 | 尚无印记             | 检查本身出错 |
| -------------------------------------------- | ---------------------- | -------------------- | -------------------- | ------------ |
| 默认、`--strict`、`--json`、`--hook <agent>` | 0，无输出              | 0，输出通知          | 3，输出 `init` 通知  | 1            |
| `--ci`                                       | 0，`contextify: fresh` | 0，输出通知          | 0，输出 `init` 通知  | 1            |
| `--git`                                      | 0，无输出              | 0，通知输出到 stderr | 0，通知输出到 stderr | 1            |
| `--ci --strict`、`--git --strict`            | 0                      | 1                    | 1                    | 1            |

通知最多 12 行、2,048 字节。`--json` 将其输出为一行 JSON。单独使用 `--strict` 从不改变退出码，它只会把未验证的声明算作漂移。

Git 检查是可选的。在 `init` 结束时，技能会提出安装 `pre-commit` 和 `pre-push` 检查。在本仓库的克隆中，你也可以运行：

```bash
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

默认情况下它们只发出警告，并拒绝替换已有的钩子。加上 `--strict` 可在漂移时阻止提交或推送。

如果设置了全局 `core.hooksPath`，激活会被拒绝，因为它会遮住你的其他钩子。请改为在你已有的钩子管理工具中调用 `ctx-check --git`。

如果需要一个在漂移时失败的 CI 任务，请以 strict 模式生成工作流。它的步骤运行 `ctx-check --ci --strict`。缺少印记或存在任何未验证的声明时，它同样会失败，即使仓库没有其他漂移：

```bash
bash skills/contextify/scripts/install_hooks.sh --strict --targets github --yes /path/to/repo
```

[钩子与 CI](../docs/hooks.md)。

### 手动运行漂移检查

仓库是最新状态时，它什么也不输出。请在仓库根目录运行。

作为插件安装时：

```bash
sh "$(ls -d ~/.claude/plugins/cache/10x/contextify/*/ | sort -V | tail -1)skills/contextify/scripts/ctx-check"
```

通过 `npx skills add` 安装时（Codex、Cursor 和大多数其他代理使用 `.agents/skills`）：

```bash
sh .agents/skills/contextify/scripts/ctx-check
```

如果是 Claude Code 的技能安装，目录是 `.claude/skills/contextify`。加上 `--ci --strict`，漂移时退出码为 1。

安装技能本身不算漂移。检查会忽略任何代理目录下 contextify 自己的副本，以及 `skills-lock.json`。你在 `.agents/skills` 中添加的其他技能会被计入，表现为一次 `tree#depth2` 变化。要忽略它们，加上这一行：

```bash
echo ".agents/" >> .gitignore
```

## 证明

一条命令运行所有测试套件、技能契约，以及本仓库对自身的漂移检查：

```bash
make test
```

它在 2026-11-17 的输出如下（每个套件一行摘要，按运行顺序）：

```text
tests/test_ctx_check.py        128/128 checks passed
tests/test_verify_claims.py     30/30 checks passed
tests/test_hooks.py             Ran 22 tests, OK
tests/test_regressions.py       Ran 25 tests, OK
tests/test_supporting_docs.py   Ran 16 tests, OK
tests/test_manifests.py        155/155 checks passed
evals/check_skill.py           114/114 checks passed
make dogfood                   PASS: ctx-check is fresh and silent
                               29 claims, 0 stale, 0 unverified
```

CI 在每次推送和拉取请求时运行同样的 `make test`。本仓库的 `AGENTS.md` 由 contextify 编写，所以一旦过时，最后一步就会失败。

## 兼容的代理

| 代理        | 安装方式                               | 测试                                                                                                               |
| ----------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Claude Code | `claude plugin install contextify@10x` | 2026-11-17：安装插件，然后完整运行一次 `init`（[运行记录](../examples/python-service-0.3.0/README.md)）            |
| Codex       | `npx skills add Aboudjem/contextify`   | 2026-11-17：安装技能，然后由 Codex 运行漂移检查（[运行日志](../examples/python-service-0.3.0/codex-run-0.3.1.md)） |

有文档、今天未测试：Gemini CLI 和 Cursor（两个 CLI 在测试机器上都无法登录）、GitHub Copilot、OpenCode、Windsurf、Zed、Continue.dev 和 Kimi Code CLI。它们的配置见[编辑器设置](../docs/editors.md)。

## FAQ

### 为什么以 AGENTS.md 为源，而不是 CLAUDE.md？

Codex、Cursor 和 Copilot 直接读取 `AGENTS.md`。Claude Code 和 Gemini CLI 得到一个导入它的短文件。这样同样的事实只存在于一个地方。

### 漂移检查会调用模型吗？

不会。它是一个 shell 和 Python 脚本。它读取 Git 和印记指向的文件，然后比较哈希值。它消耗零 token。

### 它会覆盖我手写的内容吗？

不会。contextify 只管理其标记之间的区块。区块之外的文本在每次更新后都会保留。区块内的修改会引发冲突，而不会被丢掉。

### 已验证的命令真的能运行吗？

这一点没有被证明。已验证的命令，指的是其脚本、目标或文件存在。contextify 不会运行它。能否运行仍由你的测试决定。

### accept 做什么？

当证据变了、但说明仍然正确时，它刷新印记。只要被引用的命令已失效，它就拒绝执行，所以一行坏掉的说明不会被放过。

更多回答见[完整 FAQ](../docs/faq.md)。

## 限制

- 已解析的命令只是被找到，并没有被执行。仓库中的证据本身也可能是错的。
- 解析器并不理解所有 shell 表达式或构建系统。它无法检查的行会被标为 `unverified`。
- 一项 [ETH Zurich 研究](https://arxiv.org/abs/2602.11988) 发现，上下文文件没有带来普遍的任务成功率提升，推理成本却上升了 20% 以上。contextify 没有经过测量的任务成功率优势。只保留能防止具体错误的行。
- 与 contextify 一起安装在 `.agents/skills` 或其他代理目录中的其他技能，会显示为目录树漂移。把 `.agents/`（或那个目录）加入 `.gitignore` 即可忽略它们。
- 由 0.3.1 或更早版本、在已安装技能的情况下写出的印记，会列出 `.agents/skills/`。升级后，检查会显示一次 `Changed tree#depth2`。运行一次 `accept` 即可。
- 在写插件仓库？`claude plugin validate --strict` 会对根目录的 `CLAUDE.md` 发出警告。像本仓库一样，手动让 `.claude/CLAUDE.md` 指向 `@../AGENTS.md`。写入器目前还不支持这个路径。
- 隐私：脚本不发起任何网络请求。起草使用你自己的编码代理及其常规连接。

全部限制及来源：[docs/limits.md](../docs/limits.md)。

## 了解更多

[快速开始](../docs/quickstart.md) · [完整示例](../examples/README.md) · [编辑器设置](../docs/editors.md) · [对比](../docs/comparison.md) · [设计决策](../docs/design/DECISIONS.md)

[参与贡献](../CONTRIBUTING.md) · [安全](../SECURITY.md) · [更新日志](../CHANGELOG.md) · [MIT 许可证](../LICENSE) · [10x 插件中心](https://github.com/Aboudjem/10x)

本译文由模型辅助完成，可能落后于[英文版](../README.md)，请以英文版为准。链接指向的文档仍为英文。
