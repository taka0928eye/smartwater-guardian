# Unit of Work Story Map — FE-7 KPIサマリの実データ連携と「試算値」注記

> 全ストーリー（US-1〜4）を単一ユニット `BU-1` に割り当てる（Q1=A 承認済み）。
> ストーリー実装順は上流 `stories.md` の依存関係（US-1 → US-2 → US-3、US-4 は US-1 と同順）に従う。

## 1. ストーリー → ユニット対応

| ストーリー | ユニット | 備考 |
|---|---|---|
| US-1: `KpiSummary` 型定義と `fetchKpiSummary` API クライアント | `BU-1` | `types/api.ts`・`lib/api.ts`・`api.test.ts` |
| US-2: KPI サマリの実データ表示と「試算値」注記 | `BU-1` | `page.tsx`・`KpiSummary.tsx`・`KpiSummary.test.tsx`・`page.test.tsx` |
| US-3: 取得失敗時のスケルトン表示フォールバック | `BU-1` | `DashboardClient.tsx`・`DashboardClient.test.tsx`・`page.test.tsx` |
| US-4: `SeverityLevel` 型の単一ソース化（内部品質） | `BU-1` | `lib/severity.ts`・`types/api.ts`・`api.test.ts` |

## 2. 複数ユニットにまたがるストーリー（クロスカッティング）

- **なし**。全ストーリーが単一ユニット `BU-1` 内で完結する（`stories.md`「単一 proto-Unit で完結」・
  scope-definition:c1 学習と整合）。
- クロスカッティング要件（NFR-1 カバレッジゲート恒久化）はストーリーに属さない品質ゲートであり、
  US-2 / US-3 の実装対象ファイル（`vitest.config.mts` / `package.json` / `ci.yml`）と併せて BU-1 内で対応する。

## 3. ユニット内のストーリー実装順

`BU-1` 内では上流の依存関係（scope-definition:c2 学習: 型 → APIクライアント → 表示）に従う:

1. **US-1**（`KpiSummary` 型 + `fetchKpiSummary`）— 契約と API クライアントの基盤を構築。
2. **US-4**（`SeverityLevel` 単一ソース化）— 同じ `types/api.ts` を編集するため US-1 と同順で実施。
3. **US-2**（実データ表示 + 試算値注記）— `KpiSummary` / `page` の表示を実データへ置換。
4. **US-3**（スケルトン表示フォールバック）— `DashboardClient` / `useKpiPolling` のポーリングとスケルトン切替を実装。
5. **NFR-1**（カバレッジゲート恒久化）— `vitest.config.mts` / `package.json` / `ci.yml` の設定を整備。

> 注: 上記はユニット**内部**の実装手順であり、Bolt 順序（経済的順序付け）は Delivery Planning（2.8）の責務。

## 4. カバレッジ検証

- **全ストーリーの割当て**: US-1 / US-2 / US-3 / US-4 すべて `BU-1` に割当て済み（未割当なし）。
- **全ユニットへのストーリー割当て**: 唯一のユニット `BU-1` に 4 ストーリーすべてが割当てられている（ストーリー未割当のユニットなし）。
- **ファイル対応**: `stories.md` の対象ファイル一覧 13 件（10 ソース + 3 config/CI）はすべて `BU-1` の境界に含まれる。

## Assumptions & Open Questions

- 単一ユニットのため、ストーリー間の依存は実装順序（内部手順）としてのみ作用し、Bolt 分割・並行開発の根拠にはならない。
- その他の未確定項目はなし（None.）

## Sources

- [components] `inception/application-design/components.md`（コンポーネント・ストーリー対応の根拠）
- [component-methods] `inception/application-design/component-methods.md`（テスト観測点・実装順の根拠）
- [services] `inception/application-design/services.md`（新規サービスなし・ストーリー範囲の確認）
- [component-dependency] `inception/application-design/component-dependency.md`（データフロー・実装依存順）
- [decisions] `inception/application-design/decisions.md`（ADR-001〜005 のストーリーへの影響）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR-1）
- [stories] `inception/user-stories/stories.md`（US-1〜4・依存関係・対象ファイル一覧）
