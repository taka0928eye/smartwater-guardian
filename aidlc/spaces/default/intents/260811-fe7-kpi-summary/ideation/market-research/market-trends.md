# Market Trends — FE-7 KPIサマリ実データ連携

## 市場規模と成長見通し

日本のスマート水管理市場は 2024 年に約 12 億米ドル規模で、2025〜2033 年にかけて CAGR 約 6% で成長し、2033 年に約 20 億米ドルに達する見込みです（IMARC Group 調べ）。 [web-1]

世界の水道網向け音響漏水検知市場は 2025 年に約 12.5 億米ドル、2034 年に約 27.4 億米ドル（CAGR 約 9.2%）と予測されています。 [web-3]

漏水騒音ロガー（固定設置型の知能音響センサー）市場は 2025 年に約 4.1〜4.3 億米ドル、2032 年に約 6.4〜6.6 億米ドル（CAGR 6.2〜6.6%）とされています。 [web-2]

## 技術トレンド

- **IoT 音響センサーの常時監視化** — 固定網（Fixed Network）による常時モニタリングが最速の成長セグメント。手動パトロールから常時監視への移行が進む。 [web-2]
- **エッジコンピューティング** — センサー側でのデジタルフィルタ・解析処理（音響データを送信前に前処理）と、クラウド側の AI モデルによる「漏水ヒートマップ」生成が進行。 [web-2]
- **デジタルツイン / ネットワークモデリング** — 配水網全体のモデル化による予防的な漏水対策が注目される。 [web-2]
- **ビジネスモデル多様化** — Leak Management-as-a-Service（LMaaS）や Technology-as-a-Service（TaaS）のようなサービス型提供が登場。 [web-2]

## 規制・社会的要因（日本）

- **水道事業体の人員不足** — 高齢化・少子化により自動検針・遠隔監視・AI 分析など自動化技術の導入ニーズが強い。 [web-1]
- **防災・災害耐性への関心** — 洪水管理と連携した早期警報システムの整備が進む。 [web-1]
- **非収益水（NRW）損失の低減** — 漏水による無収水量の削減が導入の主要ドライバー。 [web-2]
- **規制圧力** — 海外では Ofwat の漏水削減目標（英国）等が導入を後押し。日本でも水道事業体の経営・維持管理計画（アセットマネジメント）が投資判断の背景となる。 [web-2]

## 本イニシアティブへの示唆

FE-7（KPI サマリの実データ連携と「試算値」注記）は、これらの市場トレンドのうち「IoT 常時監視」と「アセットマネジメントの自動化」に整合する機能です。ただし本イニシアティブはデモ評価者向けの内部機能実装であり、市場開拓や販路の設計は本ワークフローのスコープ外です。 [intent] [Q1]

## Assumptions & Open Questions

- 市場規模の数値は公開市場レポートの要約であり、レポート間で集計範囲が異なるため概算値として扱う。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [web-1] Japan Smart Water Management Market Report（2025-2033, IMARC/6Wresearch 系）: https://www.giiresearch.com/report/imarc1956294-japan-smart-water-management-market-size-share.html
- [web-2] Global Leak Noise Logger Market（2026-2032, GlobalInfoResearch）: https://www.marketresearch.com/GlobalInfoResearch-v4117/Global-Leak-Noise-Logger-Supply-44520431/
- [web-3] Acoustic Leak Detection For Water Networks Market（Dataintelo）: https://dataintelo.com/report/acoustic-leak-detection-for-water-networks-market
