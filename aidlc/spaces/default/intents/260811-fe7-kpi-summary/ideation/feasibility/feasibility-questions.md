# Feasibility & Constraints Questions — FE-7 KPIサマリの実データ連携と「試算値」注記

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #19 記載の6ファイルのみ、配線方式: DashboardClient ポーリング、8/15 デモ完了優先、`today_detections` はバックエンドスキーマ上 FE-7 以降対応で対象外）。
- [intent] 市場調査成果物 `ideation/market-research/`（build 確定・競合/トレンドは概要のみ）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. KPI サマリの実データと「本日の検知数」カードの整合

BE-8 の `GET /api/v1/kpi/summary` が返すフィールドは `total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` / `is_estimate` / `assumption_doc` であり、現行フロントの KpiSummary が表示する「本日の検知数（`todayDetections`）」に相当するフィールドはありません（バックエンド `schemas/kpi.py` で「FE-7 以降で対応」と明記）。モック廃止後にこのカードをどう扱いますか？ [intent]

- A. 「本日の検知数」カードを削除し、BE-8 が返す実データのみで構成する（センサー総数・レベル1〜3別・推定削減コスト）
- B. カードは残し「—」等のプレースホルダ表示（データ不在を明示）にする
- C. その他（フロント側で別ソースから値を算出する等）
- X. Other (please specify)

[Answer]: A

## Q2. SeverityLevel 型の単一ソース化の方向性

Issue #19 は「`lib/severity.ts` を単一ソースとし、`types/api.ts` から re-export」を指定しています（現状は両ファイルに同一の `0 | 1 | 2 | 3` が重複定義され、`lib/severity.ts` 側のコメントは旧 `1|2|3` の記述が残る陳腐化状態）。`types/api.ts`（API 契約層）が `lib/severity.ts`（UI ユーティリティ層）に依存する方向になりますが、この方向で確定しますか？ [intent]

- A. Issue 記載どおり `lib/severity.ts` を単一ソースにし、`types/api.ts` から re-export する（推奨 — Issue 指定に準拠し `SEVERITY_META` 等の表示メタと同居）
- B. 逆方向 — `types/api.ts` を単一ソースにし、`lib/severity.ts` が import する（API 型の本拠を契約層に置く）
- C. その他
- X. Other (please specify)

[Answer]: X  `0 | 1 | 2 | 3`に統一

## Q3. 規制・コンプライアンス要件の適用有無

本イニシアティブ（FE-7）はデモ評価者向けの内部フロント機能実装で、PII・決済・機微データを扱わず、認証・権限管理は CLAUDE.md でスコープ外、データはモック/算出値です。コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー等）は適用ありますか？ [intent]

- A. N/A — デモ用途・機微データなしで、適用する規制要件はない（推奨）
- B. 一部該当する（具体的に指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]:　A

## Q4. タイムライン・組織制約

デモ期限 8/15（P0・想定完了日 8/12）が最優先です。本件の実装に影響するタイムライン制約や組織ブロッカー（変更凍結・優先度競合等）はありますか？ [intent]

- A. 制約なし — 8/15 デモ完了を最優先で進める
- B. 制約あり（具体的に指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- 「本日の検知数」カードを削除し、KPI サマリは BE-8 実データ（センサー総数・レベル1〜3別・推定削減コスト）のみで構成する。 [Q1]
- SeverityLevel は `0 | 1 | 2 | 3` に統一する。単一ソース化の方向は Issue 指定に従い `lib/severity.ts` を本拠とし、`types/api.ts` から re-export する。 [Q2] [intent]
- 規制・コンプライアンス要件は N/A（デモ用途・機微データなし・認証はスコープ外）。 [Q3]
- タイムライン・組織制約はなし（8/15 デモ完了を最優先）。 [Q4]

- Looks correct
- Request changes

[Answer]: Looks correct
