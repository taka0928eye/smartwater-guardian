# Decision Log — BE-5: services/orcarouter.py によるLLM自動起票の実装

イデエーション段階（intent-capture・feasibility・scope-definition・team-formation・rough-mockups・approval-handoff）で記録された決定の一覧。各決定は質問ファイルのソースレジスタ（[Q1]〜[Q8]）・ステージ成果物・一次ソース（Issue #13）に対応する。

## 1. 対象ファイルと配線範囲（intent-capture Q1・scope-definition Q1）

- 変更対象は Issue #13 記載の4ファイル（`backend/app/services/orcarouter.py` 新規・`backend/app/routers/alerts.py` 修正・`backend/.env.example` 修正・`backend/tests/test_orcarouter.py` 新規）に限定し、フロントエンドは変更しない。 [scope-doc]
- 受入条件（`source == "fallback"` 等）を満たすため、不足成果物 `backend/app/data/repair_parts.json`（フォールバック用部材マスタ）を対象に追加して BE-5 内包とする（`feasibility:c1` 学習）。 [constraint]
- 出典: `ideation/scope-definition/scope-document.md`・`ideation/feasibility/constraint-register.md`（TC-1）

## 2. 実装方針（intent-capture Q2）

- `httpx.AsyncClient` + `HttpClientDep`（OR-1 再利用）・API キーは環境変数・タイムアウト30秒・5xx/ネットワークのみ1回リトライ・4xx/パース失敗は即フォールバック。 [intent]
- 出典: `ideation/intent-capture/intent-statement.md`（Initial Scope Signal）

## 3. 開発プロセス（intent-capture Q3・memory:M2）

- TDD（Red → Green → Refactor）を厳格に順守する。 [memory:M2]
- 対象ファイル・配線範囲はユーザー確認で確定する（`intent-capture:c1` 学習）。 [memory:M1]

## 4. ステークホルダー（intent-capture Q4・Q7）

- 主たる受益者は水道事業者の運用スタッフ。決定権者は PRD / GitHub Issue（要件は決定済み）。デモ評価者（8/15）が最終確認。 [stakeholder]
- 出典: `ideation/intent-capture/stakeholder-map.md`

## 5. 検証方針（feasibility Q1）

- モック中心検証（`httpx.MockTransport`）で TDD・CI を完結させる。実キーはデモ直前に環境変数（`ORCAROUTER_API_KEY`）で注入。未入手時はフォールバックでデモ成立。 [feasibility]
- 出典: `ideation/feasibility/feasibility-assessment.md`（R-1）

## 6. 上流依存の取り扱い（feasibility Q2）

- OR-1 / OR-2 / OR-4 は実装済みのため再利用。OR-3（#14）フォールバックは未実装のため、BE-5 内包で最小実装し、後続 OR-3 マージ時に委譲・強化へ切替可能な境界を保つ。 [feasibility] [constraint]
- 出典: `ideation/feasibility/feasibility-assessment.md`（R-2）・`constraint-register.md`（TC-9）

## 7. 実装完了タイムライン（feasibility Q3）

- 8/13 実装完了は成立見込み。8/15 デモ（P1）までにバッファを確保し、フェイルオーバーとしてフォールバック動作でもデモ成立。 [feasibility]
- 出典: `ideation/feasibility/feasibility-assessment.md`（タイムライン評価）

## 8. スコープ優先度（scope-definition Q2）

- 単一 Issue（BE-5）完結のため、バックログ優先度はすべて Must-have（`scope-definition:c5` 学習）。 [scope-doc]
- 出典: `ideation/scope-definition/scope-document.md`・`intent-backlog.md`

## 9. 実装順序（scope-definition Q3）

- 依存先順（`repair_parts.json` → `orcarouter.py` → `alerts.py` → テスト → `.env.example`）で進める（`scope-definition:c2` 学習）。 [scope-doc]
- 出典: `ideation/scope-definition/scope-document.md`（実装順序）

## 10. チーム編成（team-formation Q1）

- 単独開発者（人間1名）+ AI-DLC エージェント群。従来モブ編成は不成立のため省略。 [team]
- 出典: `ideation/team-formation/team-assessment.md`

## 11. ラフモックの扱い（rough-mockups Q1）

- BE-5 は非UI（API バックエンドのみ）のため、ラフモックは非UIパス（システムコンテキスト図 + API 相互作用フロー）で作成。UI ワイヤーフレーム・アクセシビリティ注記は生成しない。 [wireframes]
- 出典: `ideation/rough-mockups/wireframes.md`・`user-flow.md`

## 12. イニシアティブ承認（approval-handoff Q1）

- **Go 承認**。受入条件は一次ソース（Issue #13）の13件に統一し、上流成果物の「11件」表記から欠落2件 — (a) `backend/.env` がコミットされていない（`.gitignore` 済みの再確認）、(b) LLM呼び出しロジックが `services/orcarouter.py` 以外に散らばっていない（CLAUDE.md §5.3）— を DoD / テスト対象に明記して引き継ぐ（rough-mockups レビュー Major 指摘の解消・`approval-handoff:c6` 学習）。 [issue] [memory:M2]
- 出典: `ideation/approval-handoff/approval-handoff-questions.md` Q1（`[Answer]: A. 確定する`）
