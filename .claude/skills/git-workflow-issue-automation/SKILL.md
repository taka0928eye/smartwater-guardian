---
name: git-workflow-issue-automation
description: >
  gh issue create / gh pr create を安全に実行し、コミット/PR作成の前に
  npm run build（フロント）・backend/venv 配下のPythonでの動作検証を済ませてから
  実行するワークフロー。CLAUDE.md が規定する GitHub Issues 連動・自走確認フローの
  実務手順。Triggers on: `gh issue create`/`gh pr create` の実行、Issue/PR作成前の
  ビルド・テスト確認、コミット前の自走確認、CLAUDE.mdの開発フロー（プラン提示→
  Issueチェック→Issue作成→実装→自走確認）の実施。
---

# Git / GitHub Issue 自動化ワークフロー（このプロジェクト向け）

このスキルは「いつ・何を確認してから `gh` コマンドを叩くか」の手順書。force-push・
hooksスキップ・無承認pushの禁止などグローバルな git 安全プロトコルは重複させず、
そのまま従う。ここではこのプロジェクト固有の前提と、CLAUDE.md の開発フロー
（§6 Workflow per Task & Issue Management）を実務手順に落とし込む。

## 0. 前提確認（毎回ではなく、環境が変わった疑いがある時）

```powershell
git rev-parse --is-inside-work-tree   # gitリポジトリ内かどうか
git remote -v                         # originが設定されているか
gh auth status                        # ghがログイン済みか
```

このプロジェクトは `.git` 初期化済み・`origin`（`https://github.com/taka0928eye/
smartwater-guardian.git`）設定済みだが、**このリポジトリのコミットはまだ0件**
（`git log` が空でもエラー扱いしない）。`gh issue create`/`gh pr create` は
リモートにIssue/PR機能があれば動くので、コミットが無い段階でも `gh issue create`
自体は実行できる（PRだけはブランチとコミットが必要）。

- `is-inside-work-tree` が失敗する（別プロジェクトを新規に扱う場合など）→ ユーザーに
  `git init` の実行可否を確認してから進める（無断で `git init` しない）。
- `origin` が無い → Issue/PR作成はできないので、先にユーザーへリモートURLを確認する。
- `gh auth status` が失敗する → `gh auth login` が必要である旨をユーザーに伝えて止まる
  （認証はユーザー本人の操作が必要）。

## 1. Issue作成前：重複チェック（CLAUDE.md §6-3）

```powershell
gh issue list
```

似た内容のオープンIssueが無いか確認してから作成する。

## 2. Issue作成（CLAUDE.md §6-4）

```powershell
gh issue create --title "<簡潔で作業内容がわかる名称>" --body "$(Get-Content -Raw issue-body.md)"
```

本文は次の3セクションを必ず含める（HEREDOC/一時ファイル経由で改行を保つ）：

```markdown
## 目的
<なぜこの作業をするか>

## 作業内容
- [ ] <チェックリスト項目1>
- [ ] <チェックリスト項目2>

## 受け入れ条件
<完了とみなす具体的な条件>
```

## 3. 実装後、コミット/PR前の自走確認（CLAUDE.md §6-6）

コミットする**前に**、変更した側のビルド/検証を通す。両方変更した場合は両方走らせる。

### フロントエンドを変更した場合

```powershell
cd frontend
npm run lint
npm run build
```

`npm run build` が失敗した状態でコミットしない。エラーを解消してから再実行する。

### バックエンドを変更した場合

```powershell
backend/venv/Scripts/python.exe <script_name>.py
```

CLAUDE.md の規約により、素の `python`/`pytest` ではなく必ず venv 配下の実行ファイルを
直接指定する。**現状 `backend/venv` に pytest は未インストールで、`requirements.txt`
/ `pyproject.toml` も存在しない。** 自動テストを追加する場合は、先に
`backend/venv/Scripts/python.exe -m pip install pytest` の実行可否をユーザーに確認し
（CLAUDE.md の Human-in-the-Loop 原則：ライブラリの新規追加は事前承認が必要）、
`backend/venv/Scripts/python.exe -m pytest` で実行する。テストが無いモジュールは
最低限、対象スクリプトを直接実行してエラーが出ないことを確認する。

## 4. コミット

- ステージングはファイルを明示指定する（`git add -A`/`git add .` は避け、意図しない
  ファイル—特に `.env` や認証情報—を巻き込まない）。
- 大きめの差分をコミットする前は `git status` で意図しないファイルが混ざっていないか
  再確認する（`backend/venv/` と `frontend/node_modules/` は既に `.gitignore` で除外
  済みだが、新規に追加した生成物・秘密情報ファイルが無いかは別途確認する）。
- コミット・push・PR作成に関するグローバルな安全プロトコル（force-push禁止、
  hooksスキップ禁止、pushは毎回ユーザー確認、コミットメッセージはHEREDOC経由）は
  システムのGit Safety Protocolにそのまま従う。

## 5. PR作成

```powershell
gh pr create --title "<70文字以内>" --body "$(Get-Content -Raw pr-body.md)"
```

Summary（変更点の箇条書き）と Test plan（`npm run build`/バックエンド検証を実施した
旨のチェックリスト）を含める。作成後、URLをユーザーに提示する。
