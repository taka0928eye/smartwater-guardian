# Application Design — Decisions

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の設計判断（ADR）。
> 3 つの実決定事項（Q1〜Q3）は人間承認済み（application-design-questions.md・統合サマリ確認済み）。
> refined-mockups 再レビューからの引き継ぎ（Major 1/2・Minor 3/4/5）の解決方針も本成果物で確定する。

## ADR インデックス

| ADR | タイトル | 状態 | 日付 |
|---|---|---|---|
| 001 | KPI ポーリングを専用フック `useKpiPolling` に実装 | Accepted | 2026-08-11 |
| 002 | KPI セクションのランドマーク所有を `DashboardClient` に一元化 | Accepted | 2026-08-11 |
| 003 | テストフィクスチャを 2,048,400（204.8万円）に統一 | Accepted | 2026-08-11 |
| 004 | 試算値注記のテストアサートはカード内順序検証に変更 | Accepted | 2026-08-11 |
| 005 | KPI カードのラベルは承認済み表示文言を固定値とし `SEVERITY_META` と分離 | Accepted | 2026-08-11 |

---

## ADR-001: KPI ポーリングを専用フック `useKpiPolling` に実装

### Status
Accepted

### Date
2026-08-11

### Context

FE-7 は `fetchKpiSummary()` を 5 秒ポーリングし、KPI サマリを取得する（requirements FR-7）。
既存のアラート取得は `useAlertPolling` カスタムフック（`DashboardClient` から抽出）が担う。
KPI のポーリングをどこに実装するかはコンポーネント境界の設計判断であり、人間に確認した（Q1）。

特に、KPI の失敗時挙動は**再スケルトン**（stale 値を表示しない。FR-8）である一方、
アラートの失敗時挙動は**最終状態据え置き**であり、両者は異なる。このため `useAlertPolling` を
そのまま共用できない。

### Decision

KPI ポーリングは新規カスタムフック **`useKpiPolling`** に実装し、`DashboardClient` は
「データ取得の集約・描画の束ね」に専念させる（Q1=A 承認済み）。`useAlertPolling` は変更しない。

### Consequences

#### Positive
- 既存 `useAlertPolling` の先例と対称で、責務分離が明確。
- スケルトン切替・クリーンアップ・ポーリング周期の責務がフック内に閉じる。
- 失敗時挙動の分岐（再スケルトン vs 据え置き）を含む複雑性をフック側に隔離でき、フック単体でテスト可能。
- テスト分離が容易（`DashboardClient` のテストはフックをモック可能）。

#### Negative
- ファイルが 1 つ増える（新規フック分）。
- アラートと KPI でフックが 2 つに分かれ、共通ロジックの抽象化余地は残る。

#### Neutral
- 将来アラートと KPI の失敗時挙動が統一された場合、共通フックへの統合を検討できる（追従判断）。

### Alternatives Considered

#### Alternative 1: DashboardClient にインライン実装（Q1 の選択肢 B）
- Description: フックを新設せず `DashboardClient` 内で `useEffect` + `setInterval` を実装。
- Pros: ファイル増減なしで最も単純。
- Cons: `DashboardClient` の責務が肥大化（地図/アラート/KPI の状態と描画が混在）。テスト分離が困難。

#### Alternative 2: useAlertPolling を拡張して KPI も取得（Q1 の選択肢 C）
- Description: 既存フックを一般化し KPI とアラートの両方を扱う。
- Pros: フックが 1 つで済む。
- Cons: 失敗時挙動の違い（再スケルトン vs 据え置き）で分岐が複雑化し、単一責任が崩れる。既存テストへの影響が大きい。

### References
- [requirements] `inception/requirements-analysis/requirements.md`（FR-7 / FR-8）
- [stories] `inception/user-stories/stories.md`（US-3）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（`useAlertPolling` 先例）

---

## ADR-002: KPI セクションのランドマーク所有を `DashboardClient` に一元化

### Status
Accepted

### Date
2026-08-11

### Context

refined-mockups 再レビューの **Major 1** として、`section` / `h2` / `aria-labelledby` / `aria-busy` の
所有が上流成果物間で乖離していた:
- `interaction-spec.md`・`accessibility-checklist.md` は KpiSummary 側に h2 を記述。
- `mockups.md` のスケルトン図は h2 が常時表示される構成を示す。
- refined-mockups:c4 学習（承認済み）は「常時描画されるラッパー側が `section`/`h2`/`aria-labelledby`/
  `aria-busy` を一元所有し、配下でスケルトンかカードグリッドを切替える」を定める。

スケルトン中は KpiSummary が描画されないため、KpiSummary 側に h2 を置くとスケルトン表示中に
見出し・ランドマークが消える。Application Design で一元確定が必要（Q2）。

### Decision

KPI セクションの `section`（h2「KPI サマリ」+ `aria-labelledby` + `aria-busy`）は
**常時描画される `DashboardClient` が所有**し、配下でスケルトン（`data-testid="kpi-skeleton"`）か
`KpiSummary` のカードグリッドを切替える（Q2=A 承認済み）。`KpiSummary` はカードグリッドのみ描画する。
US-2 AC4 の「KpiSummary に h2 を追加」は実装上 DashboardClient 側の所有に読み替える。

### Consequences

#### Positive
- refined-mockups:c4 学習と整合し、スケルトン中も h2・ランドマーク・`aria-labelledby` を維持できる。
- `KpiSummary` は表示専用の責務に徹し、状態依存の描画分岐を持たない。
- スクリーンリーダー利用者はスケルトン中もセクションの意味を把握できる（アクセシビリティ維持）。

#### Negative
- `DashboardClient` の JSX 構造が複雑になる（セクションのランドマーク + 切替ロジック）。
- US-2 AC4 の文言（「KpiSummary に h2」）と実装が異なるため、テストの観測点を DashboardClient 側に
  置く旨を機能設計以降に明示する必要がある。

#### Neutral
- `aria-busy` は DashboardClient がスケルトン中 `true`・取得成功で `false` を制御する。

### Alternatives Considered

#### Alternative 1: KpiSummary が `section`/`h2`/`aria` を所有（Q2 の選択肢 B）
- Description: US-2 AC4 の文言通り KpiSummary 側に h2 を置く。
- Pros: 上流文言と字面上は一致。
- Cons: スケルトン中は KpiSummary が描画されないため h2 が消え、ランドマークが不安定になる。
  refined-mockups:c4 学習と矛盾。

### References
- [refined-mockups] `inception/refined-mockups/interaction-spec.md`・`accessibility-checklist.md`・`mockups.md`
- [project] `aidlc/spaces/default/memory/project.md`（refined-mockups:c4 学習）

---

## ADR-003: テストフィクスチャを 2,048,400（204.8万円）に統一

### Status
Accepted

### Date
2026-08-11

### Context

refined-mockups 再レビューの **Major 2** として、表示例とテストフィクスチャの乖離が指摘された:
- refined-mockups のモックアップ表示例は `docs/business-model.md` §3.4 のデモ算出例
  （Level 1×8 / Level 2×3 / Level 3×1 → **204.8万円 = 2,048,400 円**）を参照。
- 一方、Q2（stories 時点）で確定したテストフィクスチャは `estimatedCostSavedYen: 800_000`（80万円）を使用。

両者が一致しないため、functional-design 以降のテスト設計で矛盾のないよう方針を確定する（Q3）。

### Decision

モックアップ・business-model §3.4 のデモ算出例（**2,048,400 円 = 204.8万円**）を単一の参照値として採用し、
**テストフィクスチャも 2,048,400** に揃える（Q3=A 承認済み）。フィクスチャの counts は
`level1: 8 / level2: 3 / level3: 1` とし、カード表示順（L3→L2→L1）と整合させる。

検証ポイント:
- `formatManYen(2_048_400)` = `"204.8万円"`（ja-JP / `maximumFractionDigits: 1`）。
- 旧 MOCK 値（1,420,000 / 1,240）とは異なるため、`queryByText("1,240")` 非存在アサートの偽陰性を回避できる。

### Consequences

#### Positive
- レビューア・デモ評価者がモックアップと実際の表示値を目視照合できる。
- 単一の参照値（204.8万円）が設計・テスト・モックアップの全体で一貫する。

#### Negative
- 旧テストフィクスチャ（800_000 等）の値を更新する必要がある（scope 内ファイルのテスト修正）。
- business-model の算出例が将来変わると、フィクスチャの同期が必要になる。

#### Neutral
- 金額は「試算値」として `isEstimate` フラグ + 注記（前提: docs/business-model.md）で明示されるため、
  実績値と誤認されない（business-model §3.5 と整合）。

### Alternatives Considered

#### Alternative 1: モックアップ表示例を「設計参照専用」と明記しフィクスチャは 800_000 のまま（Q3 の選択肢 B）
- Description: 表示例とテスト値の分離を明文化し、フィクスチャは旧値のまま。
- Pros: 変更範囲が小さい。
- Cons: 目視照合時にモックアップと実際の表示値が乖離し、レビュー・デモ評価の違和感が残る。

#### Alternative 2: functional-design のテスト指示書で確定（Q3 の選択肢 C）
- Description: 本ステージでは decisions.md への引き継ぎ記録のみ行う。
- Pros: 本ステージの作業が最小。
- Cons: 機能設計時まで判断が先送りされ、下流で再調整の余地が残る。

### References
- [business-model] `docs/business-model.md`（§3.4 デモ算出例・§3.5 試算値の扱い）
- [refined-mockups] `inception/refined-mockups/mockups.md`（表示例 204.8万円）

---

## ADR-004: 試算値注記のテストアサートはカード内順序検証に変更

### Status
Accepted

### Date
2026-08-11

### Context

refined-mockups 再レビューの **Minor 4** として、試算値注記のテストアサート方針が指摘された。
上流（`mockups.md`・`stories.md` US-2 AC3・project.md 学習 refined-mockups:c1）は
「2 文字列の完全一致 + 連結文字列『試算値（前提: docs/business-model.md）』の部分一致」を定めるが、
注記は**2 段構成**（見出しラベル「試算値」とカード本文「前提: docs/business-model.md」が別要素）のため、
連結文字列「試算値（前提: docs/business-model.md）」は DOM 上に連続文字列として存在せず、
部分一致アサートが構造と噛み合わない。

### Decision

試算値注記のテストアサートを**カード内スコープの順序検証**に変更する:
- 固定文字列 `試算値` の完全一致（見出しラベル。`getByText` 等）。
- 固定文字列 `前提: docs/business-model.md` の完全一致（カード本文注記）。
- コストカードの textContent に対し、`試算値` が `前提: docs/business-model.md` より**前**に出現する
  ことを正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/` で検証（2 段構成の構造維持）。

これにより FR-6 の文言要件（両文字列が常に画面にあること）を満たしつつ、2 段構成の DOM 構造と整合する。

### Consequences

#### Positive
- テストアサートが実 DOM 構造（2 段構成）と噛み合い、偽陰性・偽陽性を回避できる。
- 順序検証により「見出しラベル → 本文注記」の視覚順序も担保される。

#### Negative
- 上流の「連結文字列の部分一致」という表現と異なるため、functional-design のテスト指示書に
  本 ADR の根拠を引き継ぐ必要がある。

#### Neutral
- 2 つの完全一致アサート（`試算値` と `前提: docs/business-model.md`）は上流方針のまま維持する。

### Alternatives Considered

#### Alternative 1: 完全一致 2 つのみに縮小
- Description: 連結部分一致を撤廃し、2 文字列の完全一致のみで検証。
- Pros: 最も単純。
- Cons: 2 段構成の「見出しが本文より先」という構造（順序）を検証できない。

### References
- [refined-mockups] `inception/refined-mockups/mockups.md`（試算値注記 2 段構成）・`interaction-spec.md`
- [stories] `inception/user-stories/stories.md`（US-2 AC3）
- [project] `aidlc/spaces/default/memory/project.md`（refined-mockups:c1 学習）

---

## ADR-005: KPI カードのラベルは承認済み表示文言を固定値とし `SEVERITY_META` と分離

### Status
Accepted

### Date
2026-08-11

### Context

refined-mockups 再レビューの **Minor 5** として、`SEVERITY_META` の label と KPI カードラベルの
不一致が指摘された:
- `SEVERITY_META` の label: Level 1「Level 1 微小漏水（AI検知）」/ Level 2「Level 2 進行性漏水」/
  Level 3「Level 3 管路破裂」。
- 承認済み KPI カードラベル（`mockups.md`）: Level 1「Level 1 微小漏水（AI検知）」/ Level 2「Level 2 警告」/
  Level 3「Level 3 破裂リスク」。

Level 1 は一致するが、Level 2・Level 3 はカードラベルが `SEVERITY_META.label` と異なる表示文言である。

### Decision

KPI カードのラベルは**承認済みの表示文言（`mockups.md` のカード構成表）を固定値として**利用し、
`SEVERITY_META.label` はカードラベルのソースと**しない**。`SEVERITY_META` は深刻度の**表示メタの単一
ソース**として色（color / accentClass）の提供に徹し、カードラベルは KpiSummary 内の表示仕様（固定文字列）
として定義する。Level 1 のラベルが `getSeverityMeta(1).label` と一致するのは結果であり、依存ではない。

### Consequences

#### Positive
- 承認済みカード表示文言を変更しない（レビュー・デモ評価の整合性を維持）。
- `SEVERITY_META` の意味論（深刻度状態の正規ラベル）と KPI カードの表示文言（ユーザー向け短縮ラベル）の
  分離が明確になり、片方を変えてももう片方へ波及しない。

#### Negative
- カードラベルが `SEVERITY_META.label` から機械的に導出されないため、ラベルの定義箇所が
  KpiSummary（表示仕様）と `lib/severity.ts`（表示メタ）の 2 箇所に分かれる。表示文言の変更時は
  両者の整合を機能設計・テストで担保する。

#### Neutral
- カードの枠線・文字色（accentClass）は引き続き `getSeverityMeta(level).accentClass` を利用
  （色は `SEVERITY_META` が単一ソース）。

### Alternatives Considered

#### Alternative 1: カードラベルを `SEVERITY_META.label` に寄せて統一
- Description: Level 2・Level 3 のカードラベルを「Level 2 進行性漏水」「Level 3 管路破裂」へ変更。
- Pros: ラベルの定義が 1 箇所になる。
- Cons: 承認済みモックアップ・ワイヤーフレームの表示文言（「Level 2 警告」「Level 3 破裂リスク」）を
  無断で変更することになり、レビュー・デモ評価の整合性を損なう（approval-handoff:c6 学習に反する）。

### References
- [refined-mockups] `inception/refined-mockups/mockups.md`（カード構成表）・`design-system-mapping.md`（SEVERITY_META）
- [project] `aidlc/spaces/default/memory/project.md`（refined-mockups:c2・approval-handoff:c6 学習）

---

## 引き継ぎ事項の解決状況（refined-mockups 再レビュー分）

| 指摘 | 内容 | 解決 |
|---|---|---|
| Major 1 | `section`/`h2`/`aria` の所有が上流成果物間で乖離 | ADR-002（Q2=A で確定） |
| Major 2 | モックアップ表示例（204.8万円）とテストフィクスチャ（800_000）の乖離 | ADR-003（Q3=A で確定） |
| Minor 3 | `[interaction-design-patterns]` タグが Sources に未掲載 | refined-mockups 成果物の参照タグは `ideation/rough-mockups/wireframes.md` のインタラクションパターン項を指す。本設計の各成果物では wireframes 参照を明記して解決。refined-mockups 成果物は承認済みのため改変せず、本 ADR で扱いを記録 |
| Minor 4 | 連結文字列の部分一致アサートが 2 段構成と噛み合わない | ADR-004（カード内順序検証へ変更） |
| Minor 5 | `SEVERITY_META.label` とカードラベルの不一致 | ADR-005（カードラベルは固定表示文言・`SEVERITY_META` と分離） |

## Assumptions & Open Questions

- 本スコープはフロントエンドのみの変更で、新規サービス・データ所有の設計判断は発生しない
  （バックエンド BE-8 は実装済み・変更対象外。C-1）。
- ADR-004 / ADR-005 のラベル・アサート方針は functional-design のテスト指示書へ引き継ぐ。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / Constraints / Out of Scope）
- [stories] `inception/user-stories/stories.md`（US-1〜4）
- [refined-mockups] `inception/refined-mockups/mockups.md`・`interaction-spec.md`・`design-system-mapping.md`・`accessibility-checklist.md`（表示仕様・引き継ぎ）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・単一ソース Q9）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`
- [project] `aidlc/spaces/default/memory/project.md`（refined-mockups:c1〜c4・approval-handoff:c6 学習）
- [business-model] `docs/business-model.md`（§3.4 デモ算出例・§3.5 試算値の扱い）
