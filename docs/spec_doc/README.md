# docs/codekb/ — コード知識ベース（CodeKB）

本ディレクトリは、リポジトリの最新状態（**git HEAD = e7ce3e6・2026-08-13**）で固定した
コード知識ベース（Code Knowledge Base）のスナップショットです。
AI-DLC ワークフローの reverse-engineering 成果物を、開発者・レビュアー向けに
`docs/` 配下へ格納したものです。

## 背景

- 元となる知識ベースは `aidlc/spaces/default/codekb/smartwater-guardian/` にあり、
  本ディレクトリはそれを最新化したコピーです（2026-08-13・セッション `260813-codekb-refresh`）。
- 前回固定時点（2026-08-11・commit 7830301）から、**BE-3（SVM 音響解析）/ BE-5（Orcarouter LLM 起票）/
  BE-7（防災モード）/ BE-8（KPI）/ DEMO-1（デモシード）/ FR-6（LLM 原価）/ FE-7（KPI 配線）/
  E2E（Playwright）/ INFRA-1（AWS 本番環境）** などが実装され、コードベースが大きく前進しました。

## 収録ファイル（9 件）

| ファイル | 内容 |
|----------|------|
| `reverse-engineering-timestamp.md` | スキャン日時・スコープ・検証方法・更新経緯 |
| `business-overview.md` | 事業ドメイン・価値提案・主要機能・深刻度モデル |
| `architecture.md` | コンポーネント図・シーケンス図・設計判断（ADR 相当） |
| `code-structure.md` | モジュール構成・コードパターン・ルーター/サービス一覧 |
| `api-documentation.md` | バックエンド API 契約・フロント API 層・内部サービス仕様 |
| `component-inventory.md` | コンポーネントの責務・依存・オーナーシップ（Issue 対応） |
| `technology-stack.md` | 技術スタック一覧（バックエンド / フロント / インフラ / CI/CD） |
| `dependencies.md` | 外部依存・内部依存・データ依存・依存監査 |
| `code-quality-assessment.md` | 品質評価・CI ゲート・技術負債（解決済み / 残存） |

> **注意**: `component-inventory.md` の H2 見出しはスコープ検証（codekb-scope-diff）と
> 正規表現で照合されるため、見出し文言を変更しないこと。

## 使い方

- コードベースの全体像・責務分担・設計判断を把握したいときは `architecture.md` / `code-structure.md` / `component-inventory.md` から
- API 契約・フロント↔バックエンド変換境界を知りたいときは `api-documentation.md` / `dependencies.md` から
- 技術選定・バージョンを確認するときは `technology-stack.md` から
- 品質ゲート・技術負債を把握するときは `code-quality-assessment.md` から

## 更新方法

この知識ベースはスナップショットのため、**実装前に必ず現状コードを確認すること**
（特に LLM 起票 `services/orcarouter.py`・音響解析 `services/audio.py`・防災 `routers/disaster.py`・
インフラ `infra/` に触れるインテント）。

更新する場合は、元の `aidlc/spaces/default/codekb/smartwater-guardian/` を
最新化したうえで、本ディレクトリへ同期してください。

```powershell
# 元の知識ベースを最新化した後に、docs/ 配下へコピー
Copy-Item aidlc/spaces/default/codekb/smartwater-guardian/*.md docs/codekb/smartwater-guardian/
```
