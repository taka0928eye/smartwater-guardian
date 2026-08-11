# Build vs Buy — BE-5: Orcarouter による LLM 自動起票

## 結論

**Buy（外部 LLM サービス Orcarouter API を利用）を採用。** LLM 呼び出し基盤は Issue #13・PRD（FR-3 / FR-4）で Orcarouter API の採用が確定済みであり、本イニシアティブではこの確定判断の根拠を整理して文書化します。内製モデルの構築や他 LLM プロバイダーへの乗り換えは、8/15 デモ完了を最優先とする制約の下で選択肢としません。 [Q2]

## 評価対象の整理

| 要素 | 状態 | build/buy 判断 |
|---|---|---|
| LLM 呼び出し基盤（部材選定・見積・作業手順・通知文面の生成） | Orcarouter API を利用（Issue #13 実装方針・PRD FR-3/FR-4 で確定） | **buy 確定** — 外部 LLM サービスの購入 |
| 呼び出しラッパー（`services/orcarouter.py`） | 新規に内製実装 | build 確定（Issue 変更予定ファイル） |
| 失敗分類・リトライ・フォールバック | 内製実装（OR-3 フォールバックと連携） | build 確定 |
| 原価計測（usage / model / latency_ms → cost_yen） | 内製実装（FR-6 / `docs/llm-cost.md` §2） | build 確定 — OR-4 の `llm_cost.py` に委譲 |
| キャッシュ（同一アラート2回目以降） | 内製実装（`docs/llm-cost.md` §4-3） | build 確定 |

[desc] [intent] [Q2]

## buy を採用する理由（Orcarouter API）

- **Issue/PRD で採用確定済み** — Orcarouter 経由の LLM 自動起票は本プロダクトの中核機能（FR-3 / FR-4）として PRD に規定され、Issue #13 の実装方針も Orcarouter API 前提です。再判断の動機がありません。 [desc]
- **LLM の能力獲得はコア差別化ではない** — 製品の差別化は「消火栓貼付型センサー × ハイブリッド AI 解析による微小漏水の早期検知」と「検知後の自動アセットマネジメント（起票まで自動化）」にあります。LLM 呼び出し基盤そのものは汎用外部サービスで代替可能なコモディティであり、市場調査手法の「コア差別化でなければ buy を既定」に合致します。 [Q3]
- **内製モデル構築はデモ期間に不適合** — モデル学習・評価・運用基盤の構築は週単位の作業となり、8/15 デモ完了（P1・想定日 8/13）には間に合いません。外部 API は数日の統合で利用可能です。 [intent]
- **ルーティングによる実モデル追跡が FR-6 に整合** — Orcarouter は複数モデルへルーティングするため、レスポンスから実モデル識別子・usage を取得する設計が `docs/llm-cost.md` §2.2 に規定されています。buy 前提の計測設計が既に確定しています。 [intent]

## build を検討しない理由

- **内製モデルの構築・運用は本プロダクトのコアではない** — LLM そのものの内製（基盤モデル学習・ファインチューニング基盤の構築）は、漏水検知という中核価値から外れた大規模投資であり、デモスコープ（インメモリストア + JSON マスタ）の範囲を大きく逸脱します。 [desc] [Q2]
- **他 LLM プロバイダー（OpenAI 直契約等）への乗り換えは評価対象外** — Orcarouter がルーティング・原価計測・障害時フォールバック（OR-3）を含む統合レイヤーを提供しており、プロバイダー差し替えの比較はデモ期間内に判断価値がありません。将来、原価・品質の実測データが揃った時点で再評価可能です。 [Q2]
- **外部 BI・可視化ツールの導入は既にスコープ外** — `market-research:c3` 学習のとおり、外部ツールの導入は build-vs-buy の評価対象外です（本イニシアティブでも該当する要素はありません）。 [memory:M2]

## Assumptions & Open Questions

- Orcarouter API の採用は Issue/PRD で確定済みであり、本ステージで再判断しない（build-vs-buy は確定判断の根拠整理として文書化する）。 [assumption]
- LLM の実測原価・品質（モデル別）は未計測であり、プロバイダー再評価の判断材料はデモ後の実測データ待ちである。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 目的（FR-3/FR-4 中核・本プロダクトの目玉）・実装方針（Orcarouter API）・FR-6 計測要件
- [intent] `ideation/intent-capture/intent-statement.md`（対象ファイル・実装方針・成功指標）
- [Q2] 市場調査質問ファイル `ideation/market-research/market-research-questions.md` の回答 A（buy 確定）
- [Q3] 同 Q3 の回答 A（競合分析・トレンドは軽量版）
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `market-research:c3`（外部 BI・可視化ツールは build-vs-buy 対象外）
