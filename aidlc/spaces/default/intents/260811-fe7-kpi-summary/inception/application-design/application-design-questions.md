# Application Design — 明確化質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の Application Design ステージ質問。
> 上流成果物（requirements / stories / refined-mockups / team-practices / RE architecture）で高度に
> 確定済みの項目はリード導出で回答を確定し、実決定が必要な事項のみ人間に確認する
> （approval-handoff:c2 / requirements-analysis:c1 学習と整合）。
>
> 本ステージはフロントエンドのみの変更（バックエンド BE-8 は実装済み・変更対象外）で、新規サービスや
> データ所有の設計判断は発生しない。質問はコンポーネント境界と主要引き継ぎ事項に絞る。

## Q1: KPI ポーリングの実装形状（コンポーネント境界 — 実決定事項）

**背景:** 既存のアラート取得は `useAlertPolling` カスタムフック（`DashboardClient` から抽出）が担う。
FE-7 では `fetchKpiSummary()` を 5 秒ポーリングし、スケルトン切替（成功後失敗は再スケルトン）を行う。
KPI のポーリングをどこに実装するかはコンポーネント境界の設計判断。なお KPI の失敗時挙動（再スケルトン）
はアラート（最終状態据え置き）と異なるため、`useAlertPolling` をそのまま共用できない。

| 選択肢 | 内容 | 得失 |
|---|---|---|
| A | **専用フック `useKpiPolling` を新設**（`useAlertPolling` と対称・責務分離が明確） | 既存パターンと一貫。テスト分離が容易。ファイル 1 つ増える |
| B | `DashboardClient` にインライン実装（フック新設せず最小実装） | ファイル増減なしで最も単純。ただし DashboardClient の責務が肥大化 |
| C | `useAlertPolling` を拡張し KPI も取得 | 共通化。ただし失敗時挙動の違い（再スケルトン vs 据え置き）で分岐が複雑化 |

**リード導出の推奨（A）:** 既存 `useAlertPolling` の先例に合わせ、KPI は専用 `useKpiPolling` フックを
新設する。DashboardClient は「データ取得の集約・描画の束ね」に専念でき、スケルトン切替・クリーンアップ・
ポーリング周期の責務がフック内に閉じる。テストもフック単体で検証できる（MVP 優先でも、失敗時挙動の
分岐を含むため複雑性はフック側に隔離する方がシンプル）。

- [x] A. 専用フック `useKpiPolling` を新設（推奨）
- [ ] B. DashboardClient にインライン実装
- [ ] C. useAlertPolling を拡張して KPI も取得
- [ ] X. Other (please specify)

## Q2: KPI セクションの DOM/ARIA 所有権の確定（refined-mockups Major 1 引き継ぎ — 実決定事項）

**背景:** refined-mockups 再レビューで `section` / `h2` / `aria-labelledby` / `aria-busy` の所有が
`interaction-spec.md`（KpiSummary 側 L70-72）と `accessibility-checklist.md`（KpiSummary に h2 L80）で
KpiSummary 側に記述されている一方、mockups.md のスケルトン図は h2 が常時表示される構成を示し、
refined-mockups:c4 学習（常時描画ラッパー側が一元所有）と不一致。Application Design で一元確定する。

| 選択肢 | 内容 | 得失 |
|---|---|---|
| A | **DashboardClient（常時描画ラッパー）が `section`（h2 + aria-labelledby + aria-busy）を所有**し、配下でスケルトン（`kpi-skeleton`）かカードグリッドを切替え。KpiSummary はカードグリッドのみ描画 | c4 学習と整合。スケルトン中も h2・ランドマーク維持。KpiSummary は表示専用の責務に徹する |
| B | KpiSummary が `section`（h2 + aria-labelledby + aria-busy）を所有 | US-2 AC4 文言の通りだが、スケルトン中は KpiSummary が描画されないため h2 が消える |

**リード導出の推奨（A）:** refined-mockups:c4 学習（承認済み・`section`/`h2`/`aria-labelledby`/`aria-busy`
は常時描画されるラッパー側に一元所有）と再レビュー指摘の解消方針に従い、DashboardClient が KPI セクション
のランドマークを常時描画し、配下でスケルトンとカードグリッドを切替える。US-2 AC4 の「KpiSummary に h2 を
追加」は、実装上 DashboardClient 側での所有に読み替える。

- [x] A. DashboardClient が section/h2/aria を一元所有（推奨・c4 学習と整合）
- [ ] B. KpiSummary が section/h2/aria を所有（US-2 AC4 文言の通り）
- [ ] X. Other (please specify)

## Q3: コスト表示値とテストフィクスチャの整合方針（refined-mockups Major 2 引き継ぎ — 実決定事項）

**背景:** refined-mockups のモックアップ表示例は business-model.md §3.4 のデモ算出例
（Level 1×8 / Level 2×3 / Level 3×1 → **204.8万円 = 2,048,400 円**）を参照値とし、一方 Q2 で確定した
テストフィクスチャは旧 MOCK 値と異なる値（`estimatedCostSavedYen: 800_000` = 80万円）を使用する。
両者が一致しないため、functional-design 以降のテスト設計で矛盾のないよう方針をここで確定する。

| 選択肢 | 内容 | 得失 |
|---|---|---|
| A | **フィクスチャを 2,048,400（204.8万円）に揃える** | モックアップ・business-model §3.4 のデモ算出と一致し、レビューアが目視照合しやすい。フィクスチャの counts も 8/3/1 と整合 |
| B | モックアップ表示例を「設計参照専用」と明記し、フィクスチャは 800_000 のまま | 表示例とテスト値の分離を明文化。ただし目視照合時に違和感が残る |
| C | functional-design のテスト指示書で確定する | 本ステージでは decisions.md への引き継ぎ記録のみ |

**リード導出の推奨（A）:** モックアップ・business-model §3.4 のデモ算出例（2,048,400 円）を単一の
参照値として採用し、テストフィクスチャも 2,048,400 に揃える。カード表示順（L3→L2→L1）と整合した
counts（level3: 1 / level2: 3 / level1: 8）を使うことで、レビューア・評価者がモックアップと実際の
表示値を目視照合できる。`formatManYen(2_048_400)` = "204.8万円" となることと、旧 MOCK 値
（1,420,000 / 1,240）とは異なること（`queryByText("1,240")` 非存在アサートの偽陰性回避）の両立を確認する。

- [x] A. フィクスチャを 2,048,400（204.8万円・counts 8/3/1）に揃える（推奨）
- [ ] B. モック表示例は設計参照専用と明記し 800_000 のまま
- [ ] C. functional-design のテスト指示書で確定（引き継ぎ記録のみ）
- [ ] X. Other (please specify)

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: KPI ポーリングは **専用フック `useKpiPolling` を新設**し、DashboardClient はデータ取得の集約・
  描画の束ねに専念する（既存 `useAlertPolling` の先例と対称）。
- Q2: KPI セクションの `section`/`h2`/`aria-labelledby`/`aria-busy` は **DashboardClient（常時描画
  ラッパー）が一元所有**し、配下でスケルトン（`kpi-skeleton`）かカードグリッドを切替える。KpiSummary は
  カードグリッドのみ描画（refined-mockups:c4 学習と整合）。
- Q3: テストフィクスチャは **2,048,400（204.8万円・counts 8/3/1）** に揃え、モックアップ表示例と
  目視照合可能にする。

上記の内容で Application Design 成果物（components.md / component-methods.md / services.md /
component-dependency.md / decisions.md）を確定してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumptions & Open Questions

- 本スコープはフロントエンドのみの変更で、新規サービス・データ所有の設計判断は発生しない
  （バックエンド BE-8 は実装済み・変更対象外。C-1）。services.md は「新規サービスなし・既存 API を
  フロントから利用」を記録する。
- refined-mockups で確定済みの表示仕様（カード構成・スケルトン・試算値注記 2 段構成・5 秒ポーリング・
  全面幅配置）は Application Design の前提として引き継ぐ。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR / Constraints / Review）
- [stories] `inception/user-stories/stories.md`（US-1〜4・対象ファイル一覧・US-3 での DashboardClient 配線）
- [refined-mockups] `inception/refined-mockups/mockups.md`・`interaction-spec.md`・`design-system-mapping.md`・`accessibility-checklist.md`（表示仕様・コンポーネント責務・Major 1/2 引き継ぎ）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・フォールバック Q10 / 単一ソース Q9 / カバレッジゲート）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`（コンポーネント関係・KPI 配線予定）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（コンポーネント責務・依存グラフ）
- [business-model] `docs/business-model.md`（§3.4 デモ算出例・§3.5 試算値の扱い）
