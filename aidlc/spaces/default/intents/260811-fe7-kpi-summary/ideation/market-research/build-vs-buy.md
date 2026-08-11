# Build vs Buy — FE-7 KPIサマリ実データ連携

## 結論

**Build（内製）を採用。** 本イニシアティブでは build-vs-buy の判断が必要な要素はなく、既存の内製資産をそのまま活用します。 [Q2]

## 評価対象の整理

KPI 算定機能は前段の BE-8 で実装済みです（バックエンド `GET /api/v1/kpi/summary` が KPI サマリを返却）。本イニシアティブ（FE-7）は、その実データをダッシュボードへ配線し「試算値」注記を付すフロント側の実装です。 [intent] [Q2]

評価対象となる要素を下表に示します。

| 要素 | 状態 | build/buy 判断 |
|---|---|---|
| KPI 算定ロジック（バックエンド） | BE-8 で実装済み | build 確定（買い直し不要） |
| KPI 表示 UI（フロント） | 既存 Next.js + Recharts スタック | build 確定（外部 BI・可視化ツールの導入余地なし） |
| データ取得クライアント | 既存 `lib/api.ts` の `fetchSensors` 等に準ずる | build 確定（`fetchKpiSummary()` を追加実装） |

## build を採用する理由

- **バックエンドは BE-8 で実装済み** — 買い直し・外部サービスへの置き換えの動機がない。 [intent] [Q2]
- **フロントは既存スタックとの一貫性を優先** — ダッシュボードは既に Next.js + Recharts + Leaflet で構成されており、外部 BI・可視化ツール（Power BI 等）を導入するとデータ配線・認証・レイアウトの統合コストが増える。要件（「試算値」注記・スケルトン表示・`'use client'` なし等）は内部実装で十分に満たせる。 [intent] [Q2]
- **対象ファイルは Issue #19 記載の6ファイルのみ** — ライブラリ追加・外部ツール導入はスコープ境界を越える。 [intent]

## buy を検討しない理由

- KPI 算定は製品の競争優位（漏水削減効果の可視化）に直結する機能であるが、**既に内製済み**であり新規の調達判断が発生しない。 [desc] [Q2]
- デモ期限（8/15）が最優先であり、外部ツールの評価・導入・統合はその制約にそぐわない。 [intent] [Q2]

## Assumptions & Open Questions

- 外部 BI・可視化ツールの導入は本イニシアティブでは評価しない（スコープ外）。将来、ダッシュボードの可視化要求が高度化した場合に再評価する。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [Q2] 市場調査質問ファイル `ideation/market-research/market-research-questions.md` の回答 A（build確定）
