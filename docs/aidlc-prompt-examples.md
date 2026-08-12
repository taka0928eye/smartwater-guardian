# AI-DLC (AI-Driven Lifecycle) プロンプト集

本ドキュメントは、SmartWater Guardian の開発において各担当者（フロントエンド、バックエンド、AI/データ処理）がAIツール（ChatGPT / Claude / GitHub Copilot 等）を活用するための標準プロンプト定義です。

---

## 1. Inceptionフェーズ

/aidlc `.aidlc/v2/workflows/architecture.md` と `@CLAUDE.md` をロードしてください。

「SmartWater Guardian」のMVP開発における最初のInceptionフェーズを開始します。
以下の指示に従い、PRD（添付要件および `CLAUDE.md`）に基づいた全体タスクの分解と、最初のタスクの実装計画を日本語で提案してください。

【実行指示】
1. システム全体のコンポーネント構成と全体タスク（バックエンド・フロントエンド・Orcarouter連携・画面設計）のリストアップ
2. 最初のタスク「バックエンド: センサテレメトリ受取API (POST /api/v1/telemetry) の型定義 (Pydantic v2) とダミーエンドポイントの実装」についての詳細計画（変更予定ファイル、修正内容、検証方法）の提示
3. gh issue list を実行して重複がないか確認の上、最初のタスク用の GitHub Issue を gh issue create で作成してください。
   (Issue本文には「目的」「作業内容 (- [ ])」「受け入れ条件」を含めること)

※プラン提示後、私の承認を得てからコード作成および Issue 作成へ進んでください。


## 2. Constructionフェーズ
/aidlc GitHub内のISUUESを確認し、ISSUE#18「BE-8: KPI「推定削減コスト」の算定ロジックとサマリAPIの実装」を実装してください。短期開発で時間が限られているので、Constructionフェーズにジャンプし、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。

