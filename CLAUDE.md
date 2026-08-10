# Project Overview: SmartWater Guardian
消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知し、自動アセットマネジメントを実現するインフラDX Webアプリ。

---

## 1. Core Principles & AI-DLC Guardrails
* **言語規定:** 生成ドキュメント・会話・コメント等は必ず**日本語**で出力すること。
* **AI-DLC v2 Compliance:** `.claude/` または `.codex/` 配下のエージェント指示に従い開発を進めること。
* **MVP & Scope Control:** 8/10〜8/15のハッカソンでのデモ完成を最優先とし、最もシンプルな実装を選択する。
* **Human-in-the-Loop:** 大規模変更やライブラリ追加前は必ず人間にプランを提示し承認を得ること。

---

## 2. Tech Stack
* **Frontend:** Next.js (App Router / TS / Tailwind CSS), Leaflet, Recharts, Lucide React
* **Backend:** FastAPI (Python 3.11+), NumPy / SciPy (FFT解析)
* **LLM:** Orcarouter API (補修部材選定・見積自動起票)

---

## 3. Strict Out of Scope (実装禁止)
* ❌ 認証・権限管理 / ❌ 物理IoT通信プロトコル (Mockで代用) / ❌ リアルタイムチャット・通知 / ❌ 本番用大型GIS DB

---

## 4. Quality & Testing Standards (品質・テスト規定)
* **テストカバレッジ:** バックエンド・フロントエンドともに**テストカバレッジ80%以上を最低限度**とすること。
* **型安全:** フロントの `any` は禁止。バックエンドは Pydantic v2 モデルを徹底使用すること。

---

## 5. Operational Commands (PowerShell環境)
* **Backend:** 起動 `backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000` | テスト `backend/venv/Scripts/pytest.exe`
* **Frontend:** 起動 `npm run dev` | ビルド `npm run build` | リント `npm run lint` | テスト `npm run test`
* **GitHub Issues:** 一覧 `gh issue list` | 作成 `gh issue create`

---

## 6. Development Workflow
1. **ワークフロー参照:** `.claude/` または `.codex/` 配下のフェーズ別エージェント指示を確認する。
2. **プラン提示:** 修正予定ファイルと変更内容を出力し承認を得る。
3. **Issue確認・作成:** `gh issue list` で重複確認後、`gh issue create` で目的・タスク・受入条件を記述して作成。
4. **実装・テスト:** 実装後に単体/統合テストを作成・実行し、カバレッジ80%以上を確認する。
5. **自走確認:** ビルド・型チェック・バックエンド検証を実行しエラーのないことを確認。