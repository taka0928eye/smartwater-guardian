# Intent Backlog — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本バックログは、スコープ定義書（`ideation/scope-definition/scope-document.md`）で確定した BE-5 の実装対象を proto-Unit として整理します。単一 Issue（BE-5）完結スコープのため、バックログの優先度はすべて Must-have として扱います（`scope-definition:c5` 学習に整合・Q2: A 確定）。受入条件は Issue #13 記載の11件を一次ソースとします。 [scope] [Q2] [memory:M4]

## プロトユニット一覧（proto-Units）

単一 Issue 完結の相互依存する複数ファイル変更であるため、分割せず単一 proto-Unit として扱います（`scope-definition:c1` 学習に整合・Q2: A 確定）。 [scope] [Q2] [memory:M2]

| ID | proto-Unit | 優先度 | 依存 | 対象ファイル | 受入条件 |
|---|---|---|---|---|---|
| PU-1 | BE-5: Orcarouter による LLM 自動起票 | Must-have | D-1〜D-6（OR-1 / OR-2 / OR-4 実装済み再利用・`repair_parts.json` 新規） | `services/orcarouter.py`（新規）・`routers/alerts.py`（修正）・`tests/test_orcarouter.py`（新規）・`data/repair_parts.json`（新規）・`.env.example`（修正） | 受入条件11件（Issue #13 記載） |

## 価値連鎖（Value Stream Map）

```mermaid
flowchart LR
  A[漏水検知アラート<br/>telemetry_id] --> B[alerts.py<br/>POST /alerts/{id}/work-order]
  B --> C[orcarouter.py<br/>LLM 自動起票サービス]
  C --> D{Orcarouter API<br/>呼び出し}
  D -->|成功| E[WorkOrder<br/>source=llm]
  D -->|4xx/パース失敗| F[フォールバック応答<br/>repair_parts.json]
  D -->|5xx/ネットワーク<br/>1回リトライ後| F
  E --> G[FR-6 原価記録<br/>llm_cost.py]
  F --> G
  G --> H[WorkOrder 返却<br/>+ 1行JSON構造化ログ]
```

（テキスト代替）漏水検知アラート → `alerts.py` が `orcarouter.py` を呼ぶ → Orcarouter API 成功なら `WorkOrder(source=llm)`、4xx/パース失敗・5xx/ネットワークの1回リトライ後はフォールバック応答（`repair_parts.json` 由来・`source=fallback`）→ `llm_cost.py` で FR-6 原価を記録し `WorkOrder` と 1 行 JSON 構造化ログを返却。 [scope] [intent]

## 実装順序（Build Order）

依存先順で実装します（Q3: A 確定・`scope-definition:c2` 学習に整合）。テスト（Red）も同順に追加し TDD サイクルを維持します。 [Q3] [memory:M3]

1. `repair_parts.json` — フォールバック用部材マスタ（材質×口径の最小版）・`@lru_cache` ローダー
2. `services/orcarouter.py` — LLM 呼び出し・リトライ・フォールバック・キャッシュ・原価記録の編成
3. `routers/alerts.py` — 501 スタブを `orcarouter.py` 呼び出しへ差し替え
4. `tests/test_orcarouter.py` — モックテスト（`httpx.MockTransport`）・カバレッジ80%以上（行 + branch 各80%）
5. `.env.example` — `ORCAROUTER_API_KEY` の定義追記

## 完了条件（Definition of Done）

- 受入条件11件（Issue #13 記載）がすべて満たされる（`source == "llm"` / `"fallback"`・`WorkOrder` 型・FR-6 原価5フィールド・タイムアウト30秒・リトライ/フォールバック・API キー非出力 NFR-4）
- カバレッジ80%以上（backend: 行 + branch 各80%・`--cov=app --cov-branch --cov-fail-under=80`） [constraint]
- ruff + mypy 静的チェック通過（TC-4） [constraint]
- 起動スモークテスト（`scripts/check_telemetry.py`）成功 [constraint]
- 実装完了は 8/13 想定・デモ（8/15）完了（OC-1） [constraint]

## Assumptions & Open Questions

- バックログは単一 proto-Unit（PU-1）として扱い、受入条件11件を集約する。 [assumption]
- 実装順序は依存先順で進め、テストも同順に追加する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [scope] `ideation/scope-definition/scope-document.md`（イン/アウト境界・優先順位・依存関係・実装順序）
- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（OR-1/OR-2/OR-4 実装済み・OR-3 未実装を BE-5 内包）
- [constraint] `ideation/feasibility/constraint-register.md`（TC-1〜TC-9 / OC-1〜OC-6 / RC-1）
- [Q2] scope-definition 質問ファイルの回答 A（単一 proto-Unit）
- [Q3] 同 Q3 の回答 A（依存先順の実装順序）
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `scope-definition:c1`（相互依存する1 Issue 完結は単一 proto-Unit）
- [memory:M3] 同学習 `scope-definition:c2`（実装順序は依存先順）
- [memory:M4] 同学習 `scope-definition:c5`（単一 Issue のバックログ優先度は全て Must-have）
