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

## 6. 評価軸
1. **デモ完成度:** 触れて30秒で異常検知〜自動見積起票の価値が伝わるUI/UX。
2. **課題の実在性:** 水道局の現場取材・統計等（熟練者不足・漏水調査コスト）の一次情報に基づく課題解決。→ §1.1 の出典ステータス表で管理。
3. **ビジネス成立性:** 自治体/水道事業者向けのSaaS/B2Gモデル（導入・月額・削減コスト比較の可視化）。→ §3.1 および `docs/business-model.md`。
4. **LLMコスト:** 1起票あたりの実測原価算出、Prompt圧縮・プロキシキャッシュによる削減策の提示。→ FR-6 および `docs/llm-cost.md`。
5. **AI必然性:** 音響波形解析×Orcarouter API（LLM部材自動選定）による完全自動化。→ **Level 1（人間には検知不能な微小漏水）を主役に据えることで訴求する**（§2）。
6. **技術作りこみ:** FFT解析、FastAPI/Next.js構成、TDD（カバレッジ80%以上）。
7. **セキュリティ:** インフラ位置情報・APIキーの厳格保護（環境変数・プロキシ経由）。→ NFR-4。
8. **次世代性:** 1年前には不可能だった「検知から修繕手配までの即時自動化」。