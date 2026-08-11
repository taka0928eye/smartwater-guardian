# Scope Definition Questions — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Sources

- [desc] Initial description: "GitHub内のISUUESを確認し、ISSUE#13「BE-5: services/orcarouter.py によるLLM自動起票の実装」を実装してください。短期開発で時間が限られているので、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。手が離せないので自動承認でOKです。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #13 記載の4ファイル、実装方針: httpx.AsyncClient + HttpClientDep、成功指標: Issue 受入条件11件）。
- [feasibility] 前段フィージビリティ評価 `ideation/feasibility/feasibility-assessment.md`（技術的実現性・リスク・タイムライン）・`feasibility-questions.md`（Q1〜Q3 回答済み: モック中心 / BE-5 内包 / 8/13 成立）。
- [constraint] 制約レジスタ `ideation/feasibility/constraint-register.md`（TC-1〜TC-9 / OC-1〜OC-6 / RC-1）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections`: "相互依存する複数ファイルの変更（1 Issue 完結）は、分割せず単一 proto-Unit として扱う。スコープ管理・受入条件検証が容易になる。 (learned 2026-08-11) <!-- cid:scope-definition:c1 -->"
- [memory:M3] `aidlc/spaces/default/memory/project.md#Corrections`: "実装順序は依存先順（型 → APIクライアント → 表示）で進める。TDD（Red→Green）と整合し、テストも同順に追加できる。 (learned 2026-08-11) <!-- cid:scope-definition:c2 -->"
- [memory:M4] `aidlc/spaces/default/memory/project.md#Corrections`: "単一 Issue 完結のスコープでは、バックログの優先度をすべて Must-have として扱う（Should-have 分離は不要）。 (learned 2026-08-11) <!-- cid:scope-definition:c5 -->"

## Q1. スコープ境界（イン / アウト）の確定

Issue #13 の記載対象は4ファイル（`services/orcarouter.py` 新規・`routers/alerts.py` 修正・`.env.example` 修正・`tests/test_orcarouter.py` 新規）です。feasibility Q2 で、未実装の OR-3 フォールバックを BE-5 内で内包するため、フォールバック用部材マスタ `data/repair_parts.json` を追加対象として確定済みです。このスコープ境界（BE-5 実装対象 = 5ファイル + フロントエンド変更なし + OR-2/OR-4 再利用）を確認しますか？ [intent] [feasibility] [constraint]

- A. 確定する — Issue 記載の4ファイルに `data/repair_parts.json`（フォールバック用・材質×口径の最小版）を追加し、フロントエンドは変更しない。OR-2（`schemas/work_order.py` / `services/prompts.py`）・OR-4（`services/llm_cost.py`）は再利用、OR-3 フォールバック応答は `orcarouter.py` 内で最小実装
- B. 調整する — スコープ境界に追加・削除がある（Other で指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. バックログ表現（proto-Unit の粒度）

BE-5 は相互依存する複数ファイルの変更を伴う1 Issue 完結のスコープです。バックログ（intent-backlog）の proto-Unit はどう表現しますか？ [memory:M2]

- A. 単一 proto-Unit として扱う — 受入条件11件を1つの proto-Unit（BE-5）に集約する。スコープ管理・受入条件検証が容易（`scope-definition:c1` 学習に整合）
- B. 機能別に複数 proto-Unit へ分割する — 例: サービス本体 / ルーター差し替え / テスト・マスタ作成 を別ユニットに分ける
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. 実装順序（依存先順 vs リスク先優先）

BE-5 の実装順序はどの方針にしますか？ [memory:M3]

- A. 依存先順（型 → サービス → ルーター）で進める — テスト（Red）も同順に追加し TDD と整合する。`repair_parts.json` → `orcarouter.py`（サービス）→ `alerts.py`（ルーター差し替え）→ テストの順で実装
- B. リスク先優先 — 未検証リスクの高い Orcarouter API 呼び出し部（モックテスト）から着手する
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープ境界は、Issue 記載の4ファイルに `data/repair_parts.json`（フォールバック用・材質×口径の最小版）を追加した5ファイル + テストを実装対象とし、フロントエンドは変更しない。OR-2 / OR-4 は再利用し、OR-3 フォールバック応答は `orcarouter.py` 内で最小実装する。 [Q1]
- バックログは単一 proto-Unit（BE-5）として表現し、受入条件11件を集約する（`scope-definition:c1` 学習に整合）。 [Q2]
- 実装順序は依存先順（`repair_parts.json` → `orcarouter.py` → `alerts.py` → テスト）で進め、TDD（Red→Green）と整合させる（`scope-definition:c2` 学習に整合）。 [Q3]
- バックログの優先度はすべて Must-have として扱う（`scope-definition:c5` 学習に整合）。 [memory:M4]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- 単一 Issue（BE-5）完結スコープのため、バックログの優先度はすべて Must-have として扱い Should-have 分離は行わない。 [assumption]
- 実装順序は依存先順で進め、テストも同順に追加する。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
