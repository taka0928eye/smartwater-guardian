# Competitive Analysis — FE-7 KPIサマリ実データ連携

## 目的と方法

本分析は、前段のイニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）で確定した FE-7（KPI サマリの実データ連携と「試算値」注記）の市場コンテキストを、既存ドキュメント（`docs/business-model.md`・PRD）と軽量な外部調査に基づき整理するものです。 [intent] [Q1]

対象は**水道インフラ DX・漏水検知 IoT** 市場の競合です。粒度は「概要のみ（軽量版）」に留め、詳細な機能比較マトリクス・大規模調査は行いません。 [Q3]

## 競合の分類

| 分類 | 定義 | 主な対象 |
|---|---|---|
| 直接競合 | 同じ漏水検知・監視課題を IoT 音響センサーで解決するソリューション | 富士テコム、HWM、Xylem、Mueller (Echologics)、SebaKMT、Sewerin など |
| 間接競合 | 漏水課題を別方式（スマートメーター・水圧管理・モデリング）で解決 | スマートメーター/AMI ベンダー、水圧管理（PRV）ソリューション、ネットワークモデリング/デジタルツイン事業者 |
| 潜在競合 | スマート水管理分野で AI 漏水検知へ参入可能な大手・海外勢 | 日立、パナソニック、NEC、富士通などの国内大手と海外ベンダーの日本進出 |

[web-1] [web-2] [web-3]

## 主要競合の概要（軽量版）

- **富士テコム**（日本）— 漏水音聴調査・相関式漏水探知の老舗。国内水道事業体への導入実績が最も深い。固定網の漏水騒音ロガーも展開。 [web-2]
- **HWM**（英国）— 漏水騒音ロガー・固定網モニタリング（PAL、FALCON 等）の代表プレイヤー。 [web-2]
- **Xylem / Pure Technologies**（米国）— 買収により音響センサー群を保有し、水道ユーティリティ向けに展開。 [web-2]
- **Mueller / Echologics**（米国）— 音響センサー・相関式漏水検知で実績。 [web-2]
- **SebaKMT / Sewerin**（ドイツ）— 漏水探知機材・ロガーの欧州系主要プレイヤー。 [web-2]
- **国内大手（日立・パナソニック等）** — スマート水管理市場に参入済みで、AI 漏水検知・予測保全を強化中（潜在競合）。 [web-1]

## 差別化の要点

- **消火栓貼付型** — 既設消火栓に貼付するため配管掘削・開削が不要で、導入コストと設置工事を抑えつつ網羅的な展開が可能。 [desc] [Q1]
- **ハイブリッド AI 解析** — FFT 等の音響解析と需要データを組み合わせ、微小漏水を早期検知する。 [desc]
- **自動アセットマネジメント** — 補修部材選定・見積自動起票までつなぎ、検知後の運用を自動化する。 [desc]
- **「試算値」注記の透明性** — 根拠のない金額を断定的に見せず、前提を明示する（`docs/business-model.md` §3.5 準拠）。 [intent]

## ポジショニング（簡略・2軸）

| 検知網密度 | 低コスト（点検・スポット型） | 常時監視（固定網） |
|---|---|---|
| **導入コストが低い** | — | **SMG（消火栓貼付・既設活用）**、富士テコムの軽量ロガー |
| **導入コストが高い** | 音聴調査・スポット調査（SebaKMT/Sewerin 機材） | HWM・Xylem・Echologics の固定網 |

SMG は「低導入コスト × 常時監視」の象限を狙い、既設インフラ活用による差別化を図ります。 [Q1] [Q3]

## Assumptions & Open Questions

- 直接競合の網羅性は、英語市場レポートの主要プレイヤー列挙と日本語市場調査のプレイヤー群から整理した推測に基づく（網羅的ではない）。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [intent] `ideation/intent-capture/intent-statement.md`（Issue #19 要件・配線方式・成功指標）
- [web-1] Japan Smart Water Management Market Report（2025-2033, IMARC/6Wresearch 系）: https://www.giiresearch.com/report/imarc1956294-japan-smart-water-management-market-size-share.html
- [web-2] Global Leak Noise Logger Market（2026-2032, GlobalInfoResearch）: https://www.marketresearch.com/GlobalInfoResearch-v4117/Global-Leak-Noise-Logger-Supply-44520431/
- [web-3] Acoustic Leak Detection For Water Networks Market（Dataintelo）: https://dataintelo.com/report/acoustic-leak-detection-for-water-networks-market
