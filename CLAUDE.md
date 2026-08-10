
# Project Overview: SmartWater Guardian

消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知し、自動アセットマネジメント（補修部材選定・見積自動起票）を実現するインフラDX Webアプリケーション。

---

## 1. Core Principles & AI-DLC Guardrails (開発原則)

* **Language Requirement (言語規定):**
AI-DLC（Claude Code / Cline）が生成するすべてのドキュメント（アーキテクチャ設計書、タスク分解、Issue、コメント、コミットメッセージ）および会話は**必ず日本語で出力**すること。
* **aidlc-workflows (v2) Compliance:**
開発タスクを実行する際は、必ず `.aidlc/v2/` 配下の指定されたフェーズ（`architecture.md`, `implementation.md`, `code-review.md` 等）のワークフローに従って対話・コード生成・検証を進めること。
* **MVP & Scope Control:** ハッカソン（8/10〜8/15）期間内での確実なデモ完成を最優先とし、スコープ外の機能は実装しない。迷ったら「最もシンプルでデモ映えする実装」を選択する。
* **Human-in-the-Loop:** 大規模な変更やライブラリの新規追加を行う前に、必ず人間（ユーザー）に開発プランを提示して承認を得ること。

---

## 2. Tech Stack (技術スタック)

* **Frontend:** Next.js (App Router / TypeScript / Tailwind CSS)
* **Backend:** FastAPI (Python 3.11+)
* **Libraries (Frontend):** Leaflet / React-Leaflet (GISマップ可視化), Recharts (音響波形表示), Lucide React
* **Libraries (Backend):** NumPy / SciPy (FFT周波数解析)
* **LLM:** Orcarouter API (配管台帳データと音響解析結果に基づく補修部材選定および見積・修繕指示書の自動起票)

---

## 3. Strict Out of Scope (絶対に作らないもの)

AIの迷走防止のため、以下の機能は本フェーズでは**一切実装しない**。

* ❌ 複雑なユーザー認証・権限管理機能（デモ用に単一の自治体ダッシュボード画面として構築する）
* ❌ 実際の物理IoTデバイスとの通信プロトコル実装（擬似データ送信スクリプト/Mockデータで代用する）
* ❌ リアルタイム双方向チャット・複雑な通知基盤
* ❌ 本番用大型GISデータベース構築（軽量な疑似GISデータ/JSON管理で代用する）

---

## 4. Operational Commands (コマンド規定)

Windows PowerShell環境のため、バックエンドのコマンド実行には必ず仮想環境パスを使用・検証すること。

* **Backend Validation & Dev:**
* サーバー起動: `backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000`
* スクリプト検証: `backend/venv/Scripts/python.exe <script_name>.py`


* **Frontend Validation & Dev:**
* 開発サーバー起動: `npm run dev` (frontend ディレクトリ内)
* ビルド確認: `npm run build`
* リンター確認: `npm run lint`


* **GitHub Issues:**
* 一覧確認: `gh issue list`
* 作成: `gh issue create`

---

## 5. Coding & Architecture Rules (コード規約)

1. **Security & API Keys:**
* Orcarouter APIキー等の機密情報は必ず FastAPI 側（`backend/.env`）で保持し、Next.js フロントエンドへ露出させないこと。


2. **Type Safety & Data Models:**
* バックエンドのAPIリクエスト/レスポンスには Pydantic v2 モデルを定義すること。
* フロントエンドでは `any` 型の使用を禁止し、API型定義に合致した TypeScript インターフェースを作成すること。


3. **Module Responsibility:**
* 音響データのFFT解析・深刻度（Level 1〜3）判定ロジックは `backend/app/services/audio.py` に集約すること。


* LLM自動起票処理は `backend/app/services/orcarouter.py` にカプセル化すること。

---

## 6. Workflow per Task & Issue Management (開発フロー・タスク管理)

タスクを実行する際は、必ず以下のステップ順で進めること。

1. **ワークフロー参照:** `.aidlc/v2/` 配下の対応するフェーズ（設計・実装・テスト）の指示書を確認する。
2. **プラン提示:** 実装プラン（修正予定ファイルと変更内容）を簡潔にターミナルに出力し、ユーザーの承認を得る。
3. **既存Issueのチェック:** `gh issue list` を実行し、重複するオープンなIssueがないか確認する。
4. **Issueの作成:** `gh issue create` を使用してIssueを作成する。
* **タイトル:** 簡潔で作業内容がわかる名称
* **本文:** 「目的」「作業内容（チェックリスト形式 `- [ ]`）」「受け入れ条件」を含めること。
5. **実装:** コードの作成・修正を実行する。
6. **自走確認:** `npm run build`（フロント）および `backend/venv/Scripts/python.exe`（バック動作検証）を実行し、エラーが発生していないか確認・修正する。