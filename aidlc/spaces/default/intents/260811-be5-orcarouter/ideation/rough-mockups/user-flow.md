# User Flow (非UI: API 相互作用フロー) — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本ユーザーフローは、前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）・スコープ定義書（`ideation/scope-definition/scope-document.md`）・インテント・バックログ（`ideation/scope-definition/intent-backlog.md`）を入力とし、BE-5 の**主要 API 相互作用フロー（ハッピーパス + フォールバック + キャッシュ）**を記述します。受入条件11件（Issue #13 記載・`intent-backlog.md` Definition of Done）を満たすパスを定義します。 [intent] [scope-doc] [backlog]

## 主要相互作用フロー（Key Interaction Flow）

```mermaid
flowchart TD
  A[POST /api/v1/alerts/{telemetry_id}/work-order] --> B{alerts.py<br/>telemetry_id 存在?}
  B -->|No| ERR[404 NotFound<br/>実在IDのみ受理]
  B -->|Yes| C{orcarouter.py<br/>キャッシュヒット?}
  C -->|Yes| CACHE[キャッシュ済み WorkOrder 返却<br/>LLM 再呼び出しなし・原価二重計上なし]
  C -->|No| D[prompts.py でプロンプト編成<br/>OR-2]
  D --> E[Orcarouter API 呼び出し<br/>httpx.AsyncClient / タイムアウト30秒]
  E -->|成功| OK[WorkOrder source=llm<br/>usage からトークン数・実モデル名・latency_ms 記録]
  E -->|4xx| FALLBACK[フォールバック応答<br/>repair_parts.json 由来 source=fallback]
  E -->|5xx/ネットワーク| R[1回リトライ]
  R -->|成功| OK
  R -->|再失敗| FALLBACK
  E -->|パース失敗| FALLBACK
  OK --> G[llm_cost.py で FR-6 原価記録<br/>OR-4]
  FALLBACK --> G
  G --> H[WorkOrder 返却 + 1行JSON構造化ログ<br/>telemetry_id/model/トークン数/cost_yen/source/latency_ms]
```

（テキスト代替）`POST /alerts/{telemetry_id}/work-order` 受信時、存在しない ID は 404。キャッシュヒットなら LLM を再呼び出しせずキャッシュ済み `WorkOrder` を返却（原価二重計上なし）。キャッシュミス時は `prompts.py` でプロンプト編成し Orcarouter API へ呼び出し（タイムアウト30秒）。成功で `WorkOrder(source="llm")`、4xx はリトライせず即フォールバック、5xx/ネットワークは1回リトライ後に失敗ならフォールバック、パース失敗も即フォールバック（`repair_parts.json` 由来・`source="fallback"`）。いずれも `llm_cost.py` で FR-6 原価5フィールドを記録し、`WorkOrder` と 1 行 JSON 構造化ログを返却する。 [scope-doc] [backlog] [intent]

## 状態・分岐の整理（Decision Points）

| 分岐 | 動作 | 根拠 |
|---|---|---|
| `telemetry_id` 不在 | 404（実在 ID のみ受理） | 受入条件・`scope-document.md` 対象ファイル2 |
| キャッシュヒット | LLM 再呼び出しなし・原価二重計上なし | 受入条件 9・10 |
| Orcarouter API 成功 | `WorkOrder source="llm"`・トークン数/実モデル名/`latency_ms` 記録 | 受入条件 1・3 |
| 4xx | リトライせず即フォールバック | 受入条件 7・`intent-statement.md` 実装方針 |
| 5xx / ネットワーク | 1回リトライ → 失敗ならフォールバック | 受入条件 6 |
| パース失敗 | 即フォールバック | 実装方針 |
| API キー未設定 | 500 でなくフォールバック応答 | 受入条件 5 |

## Assumptions & Open Questions

- 主要相互作用フローはスコープ定義書 D-1〜D-7・インテント・バックログの価値連鎖図と整合しており、本ステージで新たな追加決定はない。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・実装方針）
- [scope-doc] `ideation/scope-definition/scope-document.md`（イン/アウト境界・依存関係 D-1〜D-7・対象ファイル）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・価値連鎖図・受入条件11件・Definition of Done）
