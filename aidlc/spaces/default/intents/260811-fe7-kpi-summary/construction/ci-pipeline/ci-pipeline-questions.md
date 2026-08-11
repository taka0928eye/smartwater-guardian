# CI Pipeline Questions — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> ステージ: ci-pipeline（Construction）| リード: aidlc-pipeline-deploy-agent | 日時: 2026-08-11
> 会話言語: 日本語。質問ファイルは stage-protocol §3 の質問フローに従う。

## 既知の実態（リード導出で確定済み）

以下は既存リポジトリ実態・確定済みプラクティスから回答が自明なため、質問として提示せずリード導出で確定する
（project.md 学習 `approval-handoff:c2` / `requirements-analysis:c1` / `user-stories:c2` と整合）。

### Q1. 使用する CI ツール
- **[Answer]: GitHub Actions**
- 根拠: `.github/workflows/ci.yml` が既に存在し、main への push / PR で backend・frontend 両ジョブを実行中。
  CodePipeline / CodeBuild / Jenkins は本プロジェクトで未使用。

### Q2. ブランチ戦略
- **[Answer]: main 直コミット中心（trunk-based）**
- 根拠: team.md `## Way of Working`（Q1: A 確定）。短命フィーチャーブランチ + PR は大規模変更・他者レビュー時のみ。
  CI トリガーは main への push / PR の両方を維持する。

### Q3. 成果物リポジトリ
- **[Answer]: なし（不使用）**
- 根拠: team.md `## Deployment`。デモはローカル実行（uvicorn / npm run dev）を主とし、クラウドインフラ・
  本番用 DB・レジストリは導入しない。ECR / CodeArtifact / S3 等は本スコープで対象外。

## 実決定が必要な質問

### Q4. backend 品質ゲートの CI 反映範囲
既存 CI の backend-test ジョブは `python -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80`
（**行カバレッジ 80% のみ**）で、practices-discovery で確定した次の品質ゲートが CI 未反映です。

- **Q4-A（Q4: branch カバレッジ）**: backend は「行 + branch の各 80%」（`--cov=app --cov-branch --cov-fail-under=80`）が確定済み
- **Q4-B（Q6: ruff + mypy）**: 「バックエンドに ruff + mypy を導入し CI ゲートに追加」が確定済みだが、
  backend に pyproject.toml / requirements-dev.txt が無く **ruff/mypy 自体が未導入**

BU-1 はフロントエンドのみのスコープ（backend は変更対象外）のため、この乖離をどう扱うか判断が必要です。

- **[Answer]: C. Q4 + Q6 反映**
- A. 文書化のみ（現状の CI を適切と判断し、backend の ruff/mypy 導入と branch カバレッジは backend 側の別 Issue で対応。quality-gates.md に乖離を明記）
- B. Q4 のみ反映（backend-test の pytest コマンドに `--cov-branch` を追加し、行+branch 各 80% ゲートへ。依存追加なしの軽微変更）
- C. Q4 + Q6 を反映（backend に ruff/mypy を導入し CI ステップも追加。backend の設定ファイル作成・依存追加を伴う）
- X. Other (please specify)

## Assumptions & Open Questions

- **None.**
- 自明な 3 問（Q1〜Q3）はリード導出で確定済み。Q4 のみ人間の決定を要する。

## Assumption Confirmation

- **A. Accept assumptions**
- **B. Convert to follow-up questions**

## Review

（本ステージでは外部レビュアーなし。リード（aidlc-pipeline-deploy-agent）がインラインで実行。）

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
