<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="../assets/hero-light.svg">
  <img alt="contextify: an AGENTS.md card with line 6 marked stale, linked to a Makefile card where the test-health target is crossed out, a 0 tokens counter, and the install command" src="../assets/hero.svg" width="100%">
</picture>

[![Validate](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml/badge.svg)](https://github.com/Aboudjem/contextify/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/license-MIT-E879DF)](../LICENSE)

[English](../README.md) | [Français](fr.md) | [Español](es.md) | 日本語 | [简体中文](zh-CN.md)

<!-- may-lag -->

**エージェント用の AGENTS.md を 1 つに。チェックはトークン 0 です。**

contextify は短い指示ファイルを 1 つ書き、古くなった行を知らせます。

| 時間の節約 | コンテキストを小さく | トークンの節約 |
|:--|:--|:--|
| 通知はファイル、行、なくなったコマンドを示します。下の例を見てください。 | リポジトリの大きさに合わせて 20、40、60 行の 1 ファイル。`CLAUDE.md` の参照は 4 行です。 | 古い行のチェックはローカルのスクリプトです。モデルを呼ばないので、トークンは 0 です。 |

**対応:** skill を読むすべてのエージェント。テスト済み: Claude Code、Codex。

特定のモデルに依存しません。チェックは素の Bash と Python です。

`AGENTS.md` は、コーディングエージェントが読む指示のファイルです。リポジトリにそれがないとき、または古いコマンドが書かれているときに使います。

短いファイル 1 つと、行が古くなったときの通知が手に入ります。

```bash
npx skills add Aboudjem/contextify -g
# then, in your agent: contextify init
```

このコマンドですべてのプロジェクトに入ります。エージェントごとのコマンドは [インストール](#インストール) にあります。

### レポートの例

2026-11-17 の実際の実行です。contextify 0.3.0 が小さな Python サービスの `AGENTS.md` を書きました。

その後、`Makefile` から `test-health` ターゲットを削除しました。0.3.3 は次を表示します:

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

最新のリポジトリでは何も表示されません。この実行のファイルとスタンプは例に含まれているので、再生できます:

```bash
sh examples/python-service-0.3.0/replay.sh
```

[実行の全体、ファイル、原因となった変更](../examples/python-service-0.3.0/README.md)。

**制限:** コマンド、ターゲット、ファイルを確認しますが、文章は確認せず、コマンドも実行しません。

## インストール

**おすすめ: Vercel の skills CLI。** 1 つのコマンドで、すべてのプロジェクトに入ります:

```bash
npx skills add Aboudjem/contextify -g
```

70 を超えるエージェントで動きます。メニューで自分のものを選んでください ([対応エージェント](https://github.com/vercel-labs/skills#supported-agents))。`npx skills` は、エージェント skill 用の Vercel のオープンなインストーラーです。 <a href="https://skills.sh/aboudjem/contextify"><img src="https://img.shields.io/badge/skills.sh-000000?style=flat-square&logo=vercel&logoColor=white" alt="skills.sh" height="24"></a> [skills.sh/aboudjem/contextify](https://skills.sh/aboudjem/contextify)

このプロジェクトだけなら `-g` を外します。

ターミナルではエージェントのメニューを表示します。スクリプトではすべてのエージェントのフォルダーに入れるので、`-a <agent>` を付けてください。

**または、1 つのエージェントに直接インストール。** どのコマンドも contextify をすべてのプロジェクトに入れます。

<p align="center">
  <a href="#install-claude-code"><img src="https://img.shields.io/badge/Claude_Code-D97757?style=flat-square&logo=claude&logoColor=white" alt="Claude Code" height="24"></a>
  <a href="#install-codex"><img src="https://img.shields.io/badge/Codex-000000?style=flat-square&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyBmaWxsPSJ3aGl0ZSIgcm9sZT0iaW1nIiB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI%2BPHRpdGxlPk9wZW5BSTwvdGl0bGU%2BPHBhdGggZD0iTTIyLjI4MTkgOS44MjExYTUuOTg0NyA1Ljk4NDcgMCAwIDAtLjUxNTctNC45MTA4IDYuMDQ2MiA2LjA0NjIgMCAwIDAtNi41MDk4LTIuOUE2LjA2NTEgNi4wNjUxIDAgMCAwIDQuOTgwNyA0LjE4MThhNS45ODQ3IDUuOTg0NyAwIDAgMC0zLjk5NzcgMi45IDYuMDQ2MiA2LjA0NjIgMCAwIDAgLjc0MjcgNy4wOTY2IDUuOTggNS45OCAwIDAgMCAuNTExIDQuOTEwNyA2LjA1MSA2LjA1MSAwIDAgMCA2LjUxNDYgMi45MDAxQTUuOTg0NyA1Ljk4NDcgMCAwIDAgMTMuMjU5OSAyNGE2LjA1NTcgNi4wNTU3IDAgMCAwIDUuNzcxOC00LjIwNTggNS45ODk0IDUuOTg5NCAwIDAgMCAzLjk5NzctMi45MDAxIDYuMDU1NyA2LjA1NTcgMCAwIDAtLjc0NzUtNy4wNzI5em0tOS4wMjIgMTIuNjA4MWE0LjQ3NTUgNC40NzU1IDAgMCAxLTIuODc2NC0xLjA0MDhsLjE0MTktLjA4MDQgNC43NzgzLTIuNzU4MmEuNzk0OC43OTQ4IDAgMCAwIC4zOTI3LS42ODEzdi02LjczNjlsMi4wMiAxLjE2ODZhLjA3MS4wNzEgMCAwIDEgLjAzOC4wNTJ2NS41ODI2YTQuNTA0IDQuNTA0IDAgMCAxLTQuNDk0NSA0LjQ5NDR6bS05LjY2MDctNC4xMjU0YTQuNDcwOCA0LjQ3MDggMCAwIDEtLjUzNDYtMy4wMTM3bC4xNDIuMDg1MiA0Ljc4MyAyLjc1ODJhLjc3MTIuNzcxMiAwIDAgMCAuNzgwNiAwbDUuODQyOC0zLjM2ODV2Mi4zMzI0YS4wODA0LjA4MDQgMCAwIDEtLjAzMzIuMDYxNUw5Ljc0IDE5Ljk1MDJhNC40OTkyIDQuNDk5MiAwIDAgMS02LjE0MDgtMS42NDY0ek0yLjM0MDggNy44OTU2YTQuNDg1IDQuNDg1IDAgMCAxIDIuMzY1NS0xLjk3MjhWMTEuNmEuNzY2NC43NjY0IDAgMCAwIC4zODc5LjY3NjVsNS44MTQ0IDMuMzU0My0yLjAyMDEgMS4xNjg1YS4wNzU3LjA3NTcgMCAwIDEtLjA3MSAwbC00LjgzMDMtMi43ODY1QTQuNTA0IDQuNTA0IDAgMCAxIDIuMzQwOCA3Ljg3MnptMTYuNTk2MyAzLjg1NThMMTMuMTAzOCA4LjM2NCAxNS4xMTkyIDcuMmEuMDc1Ny4wNzU3IDAgMCAxIC4wNzEgMGw0LjgzMDMgMi43OTEzYTQuNDk0NCA0LjQ5NDQgMCAwIDEtLjY3NjUgOC4xMDQydi01LjY3NzJhLjc5Ljc5IDAgMCAwLS40MDctLjY2N3ptMi4wMTA3LTMuMDIzMWwtLjE0Mi0uMDg1Mi00Ljc3MzUtMi43ODE4YS43NzU5Ljc3NTkgMCAwIDAtLjc4NTQgMEw5LjQwOSA5LjIyOTdWNi44OTc0YS4wNjYyLjA2NjIgMCAwIDEgLjAyODQtLjA2MTVsNC44MzAzLTIuNzg2NmE0LjQ5OTIgNC40OTkyIDAgMCAxIDYuNjgwMiA0LjY2ek04LjMwNjUgMTIuODYzbC0yLjAyLTEuMTYzOGEuMDgwNC4wODA0IDAgMCAxLS4wMzgtLjA1NjdWNi4wNzQyYTQuNDk5MiA0LjQ5OTIgMCAwIDEgNy4zNzU3LTMuNDUzN2wtLjE0Mi4wODA1TDguNzA0IDUuNDU5YS43OTQ4Ljc5NDggMCAwIDAtLjM5MjcuNjgxM3ptMS4wOTc2LTIuMzY1NGwyLjYwMi0xLjQ5OTggMi42MDY5IDEuNDk5OHYyLjk5OTRsLTIuNTk3NCAxLjQ5OTctMi42MDY3LTEuNDk5N1oiLz48L3N2Zz4%3D" alt="Codex" height="24"></a>
  <a href="#install-cursor"><img src="https://img.shields.io/badge/Cursor-3B3B3B?style=flat-square&logo=cursor&logoColor=white" alt="Cursor" height="24"></a>
  <a href="#install-gemini-cli"><img src="https://img.shields.io/badge/Gemini-1A73E8?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini CLI" height="24"></a>
  <a href="#install-github-copilot"><img src="https://img.shields.io/badge/Copilot-24292F?style=flat-square&logo=githubcopilot&logoColor=white" alt="GitHub Copilot" height="24"></a>
  <a href="#install-opencode"><img src="https://img.shields.io/badge/OpenCode-4A4A4A?style=flat-square&logo=opencode&logoColor=white" alt="OpenCode" height="24"></a>
</p>

<a id="install-claude-code"></a>**Claude Code**、インストールのみテスト済み (完全な実行は下のプラグインで実施):

```bash
npx skills add Aboudjem/contextify -g -a claude-code
```

<a id="install-codex"></a>**Codex**、テスト済み:

```bash
npx skills add Aboudjem/contextify -g -a codex
```

<a id="install-cursor"></a>**Cursor**、インストールのみテスト済み:

```bash
npx skills add Aboudjem/contextify -g -a cursor
```

<a id="install-gemini-cli"></a>**Gemini CLI**、インストールのみテスト済み:

```bash
npx skills add Aboudjem/contextify -g -a gemini-cli
```

<a id="install-github-copilot"></a>**GitHub Copilot**、インストールのみテスト済み:

```bash
npx skills add Aboudjem/contextify -g -a github-copilot
```

<a id="install-opencode"></a>**OpenCode**、インストールのみテスト済み:

```bash
npx skills add Aboudjem/contextify -g -a opencode
```

ほかのエージェントの `-a` コードは [エディターの設定](../docs/editors.md) にあります。

**または Claude Code プラグイン**、テスト済み。同じ skill を `/contextify:contextify` で呼び出します。フックは登録しません。

```bash
claude plugin marketplace add Aboudjem/10x && claude plugin install contextify@10x
```

次に、リポジトリの中で最初の下書きを頼みます:

```text
/contextify:contextify init
```

プラグイン以外では `/contextify:` という接頭辞はありません。言葉で頼んでください: "contextify init"、"contextify update"。

Git、Bash、Python 3.11 以降が必要です。Python パッケージ、MCP サーバー、スクリプトからのネットワーク通信はありません。

## 仕組み

Makefile のターゲットを消す、スクリプトの名前を変える、テストを移す。エージェントは古い指示に従い続けます。失敗するたびに 1 ターンを使います。contextify は古い行を先に見せます:

1. `init` がリポジトリを読み、`AGENTS.md` を下書きします。別のエージェントが各行を元のファイルと照らします。
2. diff を確認します。contextify がファイルとスタンプ (各行が指すものの記録) を書きます。
3. ドリフトチェックがリポジトリとスタンプを比べます。ドリフトとは、行がもうないものを指している状態です。

![根拠、下書き、レビュー、書き込み、チェック](../assets/how-it-works.svg)

| モード   | 何が起きるか                                                                             |
| -------- | ---------------------------------------------------------------------------------------- |
| `init`   | リポジトリを読み、指示を下書きし、根拠を確認し、差分を見せてから書き込み、チェックする。 |
| `update` | 根拠を読み直し、管理ブロックを更新する。ブロック外のあなたの編集は残る。                 |
| `check`  | 根拠をコミット済みのスタンプと比べる。何も書き込まない。                                 |
| `accept` | 指示がまだ正しいときにスタンプを更新する。なくなったものを指す行は拒否する。 |

書き込むファイル:

| ファイル                                    | 読み手                                         | 行数                         |
| ------------------------------------------- | ---------------------------------------------- | ---------------------------- |
| `AGENTS.md`                                 | Codex、Cursor など、この規約を読むエージェント | 目標 20、40、60 行。最大 150 |
| `CLAUDE.md`                                 | Claude Code (`@AGENTS.md` 経由)                | 既定で 4                     |
| `GEMINI.md`                                 | Gemini CLI (`@AGENTS.md` 経由)                 | 3                            |
| `.cursor/rules/contextify.mdc`              | Cursor。Cursor は `AGENTS.md` も読むので任意   | 9                            |
| `.github/copilot-instructions.md`           | GitHub Copilot                                 | 4                            |
| `docs/context/architecture.md`              | 任意。コンポーネントとデータの流れの地図       | 最大 120                     |
| `docs/context/workflows.md`                 | 任意。ビルド、テスト、リリースの手順           | 最大 120                     |
| `.contextify/evidence.json` と `stamp.json` | ドリフトチェック                               | リポジトリによる             |

Codex と Cursor は `AGENTS.md` をそのまま読みます。選んだエージェントだけが参照ファイルを受け取ります。事実を述べる各行は、元のファイルと行に対応しています。

ドリフトチェックは、リポジトリが最新なら何も出力せずに 0 で終了します。ドリフトがあれば上の通知を表示し、それでも 0 で終了します。ファイルを書き換えることはありません。

終了コード (2026-11-17、0.3.3、bash で測定):

| モード                                       | 最新                   | ドリフト         | スタンプなし     | チェック自体の失敗 |
| -------------------------------------------- | ---------------------- | ---------------- | ---------------- | ------------------ |
| 通常、`--strict`、`--json`、`--hook <agent>` | 0、出力なし            | 0、通知          | 3、`init` の通知 | 1                  |
| `--ci`                                       | 0、`contextify: fresh` | 0、通知          | 0、`init` の通知 | 1                  |
| `--git`                                      | 0、出力なし            | 0、stderr に通知 | 0、stderr に通知 | 1                  |
| `--ci --strict`、`--git --strict`            | 0                      | 1                | 1                | 1                  |

通知は最大 12 行、2,048 バイトです。`--json` は通知を 1 行の JSON で出力します。`--strict` だけでは終了コードは変わりません。未検証の記述をドリフトとして数えるだけです。

Git チェックは任意です。`init` の最後に、スキルが `pre-commit` と `pre-push` のチェックのインストールを提案します。このリポジトリのクローンからは次も実行できます。

```bash
bash skills/contextify/scripts/install_hooks.sh --yes --activate /path/to/repo
```

既定では警告だけを出し、既存のフックは置き換えません。`--strict` を付けると、ドリフト時にコミットやプッシュを止めます。

グローバルな `core.hooksPath` が設定されていると、有効化は拒否されます。他のフックが隠れてしまうためです。代わりに、普段使っているフック管理ツールから `ctx-check --git` を呼んでください。

ドリフトで失敗する CI ジョブには、strict モードでワークフローを生成します。そのステップは `ctx-check --ci --strict` を実行します。スタンプがない場合や未検証の記述がある場合も、他にドリフトがなくても失敗します。

```bash
bash skills/contextify/scripts/install_hooks.sh --strict --targets github --yes /path/to/repo
```

[フックと CI](../docs/hooks.md)。

### ドリフトチェックを手動で実行する

リポジトリが最新なら何も表示しません。リポジトリのルートで実行してください。

プラグインとしてインストールした場合:

```bash
sh "$(ls -d ~/.claude/plugins/cache/10x/contextify/*/ | sort -V | tail -1)skills/contextify/scripts/ctx-check"
```

`npx skills add -g` でインストールした場合 (Codex、Cursor、Gemini CLI、Copilot、OpenCode は `~/.agents/skills` を使います):

```bash
sh ~/.agents/skills/contextify/scripts/ctx-check
```

Claude Code の skill インストールでは、フォルダーは `~/.claude/skills/contextify` です。`-g` なしなら、フォルダーはリポジトリ内の `.agents/skills/contextify` です。`--ci --strict` を付けると、ドリフトで終了コード 1 になります。

skill のインストールはドリフトになりません。チェックは、エージェントのフォルダーにある contextify 自身のコピーと `skills-lock.json` を無視します。リポジトリの `.agents/skills` に追加したほかの skill は `tree#depth2` の変更として数えます。無視するには、次の 1 行を追加します:

```bash
echo ".agents/" >> .gitignore
```

## 証拠

1 つのコマンドで、すべてのテストスイート、スキルの契約、このリポジトリ自身のドリフトチェックを実行します。

```bash
make test
```

2026-11-17 の出力です (スイートごとに 1 行の要約、実行順)。

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

CI はプッシュとプルリクエストのたびに同じ `make test` を実行します。このリポジトリの `AGENTS.md` は contextify が書いたものなので、古くなれば最後のステップが失敗します。

## 対応エージェント

| エージェント | インストール | テスト済み (Tested) |
| --- | --- | --- |
| Claude Code | `claude plugin install contextify@10x` | 2026-11-17: プラグインをインストールし、`init` を最後まで実行 ([実行記録](../examples/python-service-0.3.0/README.md)) |
| Codex | `npx skills add Aboudjem/contextify -g -a codex` | 2026-11-17: skill をインストールし、Codex がドリフトチェックを実行 ([実行ログ](../examples/python-service-0.3.0/codex-run-0.3.1.md)) |
| Cursor | `npx skills add Aboudjem/contextify -g -a cursor` | 2026-11-17: インストールのみ、空のホームフォルダーで実施。skill は `~/.agents/skills` に入りました。 |
| Gemini CLI | `npx skills add Aboudjem/contextify -g -a gemini-cli` | 2026-11-17: インストールのみ、空のホームフォルダーで実施。skill は `~/.agents/skills` に入りました。 |
| GitHub Copilot | `npx skills add Aboudjem/contextify -g -a github-copilot` | 2026-11-17: インストールのみ、空のホームフォルダーで実施。skill は `~/.agents/skills` に入りました。 |
| OpenCode | `npx skills add Aboudjem/contextify -g -a opencode` | 2026-11-17: インストールのみ、空のホームフォルダーで実施。skill は `~/.agents/skills` に入りました。 |

「インストールのみ」は、ファイルを確認したが、そのエージェントで skill を実行していないという意味です。文書化済みだが今日はテストしていないもの: skill を実行する Gemini CLI、Cursor、GitHub Copilot、OpenCode と、Windsurf、Zed、Continue.dev、Kimi Code CLI。Gemini CLI と Cursor はテスト用マシンでサインインを拒否しました。インストール用のコードは [エディターの設定](../docs/editors.md) にあります。

## FAQ

### なぜ CLAUDE.md ではなく AGENTS.md が元になるのですか?

Codex、Cursor、Copilot は `AGENTS.md` を直接読みます。Claude Code と Gemini CLI は、それを読み込む短いファイルを受け取ります。だから同じ事実が 1 か所にまとまります。

### ドリフトチェックはモデルを呼びますか?

いいえ。シェルと Python のスクリプトです。Git とスタンプが指すファイルを読み、ハッシュを比べます。トークンは使いません。

### 特定のモデルが必要ですか?

いいえ。チェックはモデルをまったく使いません。`init` での下書きには、エージェントがすでに使っているモデルを使います。

### 手で書いた内容は上書きされますか?

いいえ。contextify が管理するのはマーカーの間のブロックだけです。ブロック外のテキストはどの更新でも残ります。ブロック内を編集すると、失われる代わりに競合として報告されます。

### 検証済みのコマンドは本当に動きますか?

それは証明されていません。検証済みとは、スクリプト、ターゲット、ファイルが存在するという意味です。contextify はコマンドを実行しません。動くかどうかはテストで確かめてください。

### accept は何をしますか?

根拠が変わっても指示がまだ正しいときに、スタンプを更新します。引用したコマンドがなくなっている間は拒否するので、壊れた行は通りません。

その他の回答は [FAQ 全文](../docs/faq.md) にあります。

## 制限

- 解決済みのコマンドは見つかっただけで、実行はされていません。リポジトリの根拠自体が間違っていることもあります。
- リゾルバーはすべてのシェル式やビルドシステムを理解するわけではありません。確認できない行には `unverified` が付きます。
- トークン 0 はチェックそのもののコストです。エージェントがチェックを実行してドリフトを見つけると、通知 (最大 12 行) がエージェントのコンテキストに入ります。
- これらのファイルがエージェントのタスク完了を助けると示した研究はありません。[ETH Zurich の研究](https://arxiv.org/abs/2602.11988) では全般的な向上は見られず、モデルのコストは 20% 以上増えました。実際のミスを防ぐ行だけを残してください。
- contextify と並べて `.agents/skills` や他のエージェントフォルダに入れた他のスキルは、ツリーのドリフトとして表示されます。無視するには `.agents/` (またはそのフォルダ) を `.gitignore` に追加してください。
- 0.3.1 以前で、スキルをインストール済みの状態で書いたスタンプには `.agents/skills/` が含まれます。更新後、チェックは `Changed tree#depth2` を 1 回表示します。`accept` を 1 回実行してください。
- プラグインのリポジトリを書いていますか? `claude plugin validate --strict` はルートの `CLAUDE.md` に警告を出します。このリポジトリのように、`.claude/CLAUDE.md` から `@../AGENTS.md` を手で指してください。ライターはまだこのパスを対象にしていません。
- プライバシー: スクリプトはネットワークに接続しません。下書きには、あなたのコーディングエージェントと普段の接続を使います。

すべての制限と出典: [docs/limits.md](../docs/limits.md)。

## さらに詳しく

[クイックスタート](../docs/quickstart.md) · [実例](../examples/README.md) · [エディター設定](../docs/editors.md) · [比較](../docs/comparison.md) · [設計判断](../docs/design/DECISIONS.md)

[コントリビュート](../CONTRIBUTING.md) · [セキュリティ](../SECURITY.md) · [変更履歴](../CHANGELOG.md) · [MIT ライセンス](../LICENSE) · [10x プラグインハブ](https://github.com/Aboudjem/10x)

この翻訳はモデルの支援を受けて作成しました。[英語版](../README.md)より更新が遅れる場合があるため、英語版を正としてください。リンク先の資料は英語です。
