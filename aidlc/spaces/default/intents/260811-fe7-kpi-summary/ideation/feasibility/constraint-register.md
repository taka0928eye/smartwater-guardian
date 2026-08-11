# Constraint Register — FE-7 KPIサマリの実データ連携と「試算値」注記

## 技術的制約（Technical Constraints）

| ID | 制約 | 出典 | 影響 |
|---|---|---|---|
| TC-1 | 対象ファイルは Issue #19 記載の6ファイルのみ（`types/api.ts`・`lib/api.ts`・`page.tsx`・`KpiSummary.tsx`・`api.test.ts`・`KpiSummary.test.tsx`）。バックエンド（BE-8）は変更しない。 | [intent] [Q1] | 変更範囲の境界。配線ロジックは `lib/api.ts` へ、表示は `KpiSummary.tsx` へ集約 |
| TC-2 | BE-8 の `GET /api/v1/kpi/summary` が返すフィールドは `total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` / `is_estimate` / `assumption_doc` のみ。`today_detections` は存在しない（FE-7 以降で対応）。 | [intent] [Q1] | 「本日の検知数」カードは削除し、実データのみで KPI カードを構成する |
| TC-3 | snake_case（バックエンド）→ camelCase（フロント）の変換は `lib/api.ts` 境界で一度だけ行う。 | [intent] | `fetchKpiSummary()` も既存 `unwrap` / `toCamelCase` パターンに従う |
| TC-4 | `SeverityLevel` はリポジトリ内で1箇所のみ（`lib/severity.ts` の `0 \| 1 \| 2 \| 3`）とし、`types/api.ts` から re-export する。バックエンド `Literal[0,1,2,3]` と一致させる。 | [intent] [Q2] | `types/api.ts` と `lib/severity.ts` の重複定義を解消 |
| TC-5 | `page.tsx` は Server Component のまま維持（`'use client'` を付けない）。KPI 取得は DashboardClient 側のポーリングで実施する。 | [intent] | 配線方式（Issue 推奨 A）を踏襲 |
| TC-6 | `any` 型を使用しない。 | [intent] | 型変換は既存ヘルパー流用で対応 |
| TC-7 | KPI カードに「試算値（前提: `docs/business-model.md`）」の注記を常時表示する。 | [intent] | 表示要件（`is_estimate` に依存せず定常表示） |
| TC-8 | バックエンド停止中でも白画面にせずスケルトン表示に留める。 | [intent] | フェイルセーフ動作 |
| TC-9 | フロントの品質ゲート: `npm run build` / `npm run lint` / `npm run test` 成功、カバレッジ80%以上。 | [intent] | 完了条件 |

## 組織的制約（Organizational Constraints）

| ID | 制約 | 出典 | 影響 |
|---|---|---|---|
| OC-1 | 8/15 デモ完了を最優先（P0・想定完了日 8/12）。 | [intent] [Q4] | シンプルな実装を選択し、スコープを拡大しない |
| OC-2 | コミュニケーション要件は「特になし」（個別 Issue ベースで進捗管理）。 | [intent] | 追加の調整プロセスなし |
| OC-3 | 組織ブロッカー（変更凍結・優先度競合）はなし。 | [Q4] | 進行制約なし |

## 規制制約（Regulatory Constraints）

| ID | 制約 | 出典 | 影響 |
|---|---|---|---|
| RC-1 | N/A — デモ評価者向けの内部フロント機能で、PII・決済・機微データを扱わず、適用する規制要件（PCI / HIPAA / SOC2 / データレジデンシー）はない。 | [intent] [Q3] | コンプライアンス上の追加対応なし |

## Assumptions & Open Questions

- 認証・権限管理・リアルタイム通知・本番用大型 GIS DB は CLAUDE.md でスコープ外（本件にも影響しない）。 [intent]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [Q1] Feasibility 質問ファイル `ideation/feasibility/feasibility-questions.md` の回答 A
- [Q2] 同 Q2 回答 X（`0 | 1 | 2 | 3` に統一）
- [Q3] 同 Q3 回答 A（規制・コンプライアンス N/A）
- [Q4] 同 Q4 回答 A（タイムライン・組織制約なし）
- [competitive-analysis] `ideation/market-research/competitive-analysis.md`
- [market-trends] `ideation/market-research/market-trends.md`
- [build-vs-buy] `ideation/market-research/build-vs-buy.md`
