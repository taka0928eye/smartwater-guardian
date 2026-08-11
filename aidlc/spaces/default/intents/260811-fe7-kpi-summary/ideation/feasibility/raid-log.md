# RAID Log — FE-7 KPIサマリの実データ連携と「試算値」注記

## Risks（リスク）

| ID | リスク | 影響度 | 発生可能性 | 対策 |
|---|---|---|---|---|
| R-1 | `types/api.ts` から `lib/severity.ts` への re-export で、依存方向が逆転し将来の設計が混乱する | 低 | 低 | `lib/severity.ts` は `types/api.ts` に依存しないことを確認し、単一ソース方針を本フェーズの成果物（feasibility-assessment）に明記する [intent] [Q2] |
| R-2 | BE-8 の KPI API が返す `level1_count` を現行 UI が表示していないため、KPI カード構成の変更が必要 | 中 | 確定 | センサー総数・レベル1〜3別・推定削減コストの構成に揃える（Q1=A で確定済み） [Q1] |
| R-3 | バックエンド停止時に KPI データが取得できず白画面になる | 中 | 中 | スケルトン表示にフォールバックする（TC-8） [intent] |
| R-4 | `today_detections` を表示し続けると、実データ不在で誤った値（モック残り）を見せる | 高 | 中 | 「本日の検知数」カードを削除し、ハードコードを0件にする（Q1=A） [intent] [Q1] |

## Assumptions（前提）

| ID | 前提 | 根拠 |
|---|---|---|
| A-1 | `lib/severity.ts` を単一ソースとし、`types/api.ts` から re-export する方向でよい | Issue #19 指定・Q2 回答 X（`0 \| 1 \| 2 \| 3` に統一） [intent] [Q2] |
| A-2 | KPI カードの注記「試算値（前提: `docs/business-model.md`）」は常時表示する | Intent Statement 成功指標 [intent] |
| A-3 | バックエンド（BE-8）は変更しない | スコープ境界（Issue #19 の6ファイルのみ） [intent] |
| A-4 | 規制・コンプライアンス要件は N/A | Q3 回答 A [Q3] |

## Issues（課題）

| ID | 課題 | 状態 | 対応 |
|---|---|---|---|
| I-1 | 現行 `lib/severity.ts` の docstring が旧 `1\|2\|3` を参照しており陳腐化 | オープン | 単一ソース化の際に `0 \| 1 \| 2 \| 3` へ更新する [Q2] |
| I-2 | 現行 `KpiSummary.tsx` の `KpiData` に `todayDetections` があるが、BE-8 に相当フィールドがない | オープン | カード削除（Q1=A）に伴い `KpiData` からも除去する [Q1] |

## Dependencies（依存）

| ID | 依存 | 種別 | 状態 |
|---|---|---|---|
| D-1 | BE-8 の `GET /api/v1/kpi/summary` が実装済み | 外部API | 充足済み |
| D-2 | 既存の `lib/api.ts` の `unwrap` / `toCamelCase` ヘルパー | 内部モジュール | 充足済み |
| D-3 | `npm run test` / `npm run lint` / `npm run build`（品質ゲート） | 開発環境 | 充足済み |

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [Q1] Feasibility 質問ファイル `ideation/feasibility/feasibility-questions.md` の回答 A（本日の検知数カード削除）
- [Q2] 同 Q2 回答 X（`0 | 1 | 2 | 3` に統一）
- [Q3] 同 Q3 回答 A（規制・コンプライアンス N/A）
- [competitive-analysis] `ideation/market-research/competitive-analysis.md`
- [market-trends] `ideation/market-research/market-trends.md`
- [build-vs-buy] `ideation/market-research/build-vs-buy.md`
