# Project Overview: SmartWater Guardian

消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知し、自動アセットマネジメントを実現するインフラDX Webアプリ。

---

## 1. Core Principles & AI-DLC Guardrails
* **言語規定:** ドキュメント・会話・コメント等は必ず**日本語**で出力すること。
* **TDD徹底:** **Red（失敗するテスト）→ Green（最小実装）→ Refactor** のサイクルを厳格に順守。コード作成前に必ずテストを書く。
* **AI-DLC v2 Compliance:** `.claude/` または `.codex/` 配下のエージェント指示に従う。
* **MVP & Scope Control:** 8/10〜8/15デモ完成を最優先とし、最もシンプルな実装を選択。
* **Human-in-the-Loop:** 大規模変更・ライブラリ追加前は必ず人間にプランを提示し承認を得る。

---

## 2. Tech Stack
* **Frontend:** Next.js (App Router / TS / Tailwind), Leaflet, Recharts, Lucide React, Vitest
* **Backend:** FastAPI (Python 3.11+), NumPy / SciPy (FFT解析), Pytest
* **LLM:** Orcarouter API (補修部材選定・見積自動起票)

---

## 3. Strict Out of Scope (実装禁止)
* ❌ 認証・権限管理 / ❌ 物理IoT通信プロトコル / ❌ リアルタイム通知 / ❌ 本番用大型GIS DB

---

## 4. Quality & Commands (PowerShell環境)
* **品質基準:** カバレッジ **80%以上** 必須 / `any` 禁止 / Pydantic v2 徹底使用
* **Backend Command:** 
  * 起動: `backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000`
  * テスト・カバレッジ: `backend/venv/Scripts/pytest.exe --cov=app --cov-report=term-missing`
* **Frontend Command:** 起動 `npm run dev` | テスト `npm run test` | ビルド `npm run build`

---

## 5. TDD Development Workflow
1. **プラン提示:** 変更予定ファイル・テストケース方針を出力し人間の承認を得る。
2. **Issue確認・作成:** `gh issue list` 確認後、`gh issue create` で作成。
3. **【Step 1】Red:** モック構造を含め、仕様を満たす失敗テスト（`tests/`）を作成・実行。
4. **【Step 2】Green:** テストをパスさせる最小限のプロダクションコードを実装。
5. **【Step 3】Refactor:** テスト成功（Green）を維持したままコードをリファクタリング。
6. **自走確認:** ビルド・型チェック・カバレッジ80%以上を確認して完了。