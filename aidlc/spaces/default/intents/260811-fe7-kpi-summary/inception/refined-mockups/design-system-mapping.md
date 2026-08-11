# Design System Mapping — FE-7 KPIサマリの実データ連携と「試算値」注記

> KPI サマリの UI が既存デザインシステム（`lib/severity.ts` の深刻度メタ / Tailwind v4 トーン /
> 既存コンポーネント構造）にどのように適合するかをマッピングする。既存デザインを崩さない
> ことを最優先とする（requirements NFR-5 と整合）。表示仕様は `mockups.md`、
> インタラクションは `interaction-spec.md`、アクセシビリティは `accessibility-checklist.md` を参照。

## デザイントークン（深刻度カラー）

**単一ソース:** `frontend/src/lib/severity.ts` の `SEVERITY_META` が深刻度カラーの本拠
（team-practices Q9=A — 表示メタは型と同居するユーティリティ層を本拠とし、契約層から re-export）。

| レベル | label | color | accentClass（KPI カード枠線 + 文字） | 用途 |
|---|---|---|---|---|
| 0 | 正常 | `#64748b` | `border-slate-200 text-slate-700` | 一覧表示（本スコープのカードでは未使用） |
| 1 | Level 1 微小漏水（AI検知） | `#84cc16`（lime） | `border-lime-200 text-lime-700` | **Level 1 カード（追加・lime 黄緑）** |
| 2 | Level 2 進行性漏水 | `#f59e0b`（amber） | `border-amber-200 text-amber-700` | Level 2 カード（既存） |
| 3 | Level 3 管路破裂 | `#ef4444`（red） | `border-red-200 text-red-700` | Level 3 カード（既存） |

**Level 1 カードの lime 採用の根拠:** 承認済み Q4=A（lime 黄緑・`getSeverityMeta(1)` 再利用・統合サマリ確認済み）。
`SEVERITY_META[1]` は既に lime 定義済みのため、新規トークン追加なし。 [stories]

## コンポーネントマッピング

### 既存コンポーネントの再利用

| 既存要素 | 再利用箇所 | 変更 |
|---|---|---|
| `KpiCard`（KpiSummary.tsx 内プライベート） | 5 カードすべて | 変更なし（label / value / unit / accentClass / testId を受ける構造のまま） |
| `getSeverityMeta(level)` | Level 3 / Level 2 / Level 1 カードの accentClass | Level 1 への適用を追加 |
| `formatManYen(yen)` | 推定削減コストカードの金額 | 変更なし（ja-JP / `maximumFractionDigits: 1`） |
| `toLocaleString("ja-JP")` | 件数・台数の数値表示 | 変更なし |

### 変更対象コンポーネント

| コンポーネント | 変更内容 | デザインシステム対応 |
|---|---|---|
| `KpiSummary.tsx` | `KpiData` → `KpiSummary` 契約へ置換、カード構成変更（today→Level 1）、h2 見出し、試算値注記 | 表示専用のまま（Client 化しない） |
| `DashboardClient.tsx` | KPI 全面幅セクションの先頭描画、5 秒ポーリング、スケルトン切替 | 既存 3 列グリッドを包む親要素追加（レイアウト構造変更） |
| `page.tsx` | `MOCK_KPI_DATA` 撤去 | Server Component のまま（デザイン変更なし） |

## レイアウトシステム

### KPI サマリのグリッド

- **ベース:** `grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5`（既存 KpiSummary を踏襲）。
- **カード:** `rounded-xl border bg-white p-4 shadow-sm`（既存 KpiCard の外観を維持）。
- **NFR-5:** 既存の Tailwind v4 トーン・リテラルクラス名・`lg:grid-cols-5` グリッドを踏襲し、
  デザインを崩さない。 [requirements]

### DashboardClient のページ構造

```
<main class="mx-auto max-w-7xl space-y-4 p-4 lg:p-6">
  <DashboardClient>
    <KpiSummary …/>                      ← 全面幅（新規）
    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">   ← 既存 3 列グリッド
      <section センサー地図 (lg:col-span-2) />
      <section アラート一覧 />
      {selectedAlert && <AlertDetailDrawer />}
    </div>
  </DashboardClient>
</main>
```

- KPI セクションは地図・アラートの上部に全面幅で配置（俯瞰情報を先に見せる）。 [stories US-2 AC6]
- 既存の `space-y-4` による縦間隔を維持する。

## タイポグラフィ

| 要素 | 既存クラス | 変更 |
|---|---|---|
| カードラベル | `text-xs font-medium text-slate-500`（p） | 変更なし |
| カード値 | `text-2xl font-bold tabular-nums`（p） | 変更なし |
| 単位 | `ml-1 text-sm font-semibold text-slate-500`（span） | 変更なし |
| **KPI サマリ見出し（新規）** | `h2`（デザインガイドラインに従い h1 より小さい見出し） | `aria-labelledby` で紐付け |
| 試算値注記（新規） | ラベル: 見出し内 `text-xs font-medium text-slate-500` と同系 / 本文注記: `text-xs text-slate-500` | 金額と区別しつつ控えめに表示 |

> h1→h2→p の見出し階層は wireframes.md:65 のアクセシビリティ注記に従う。 [wireframes]

## 状態表現（スケルトン）

| 状態 | 表現 | トークン |
|---|---|---|
| loading | カード 5 枚相当のグレーアニメーション | `animate-pulse` + `bg-slate-200`（既存トーン）。`prefers-reduced-motion` では静止 |
| success | 実データカード | 通常のカード外観 |

- スケルトンは数値テキストを一切含まず、stale 値と誤認されない形状（固定 testId `kpi-skeleton`）。 [stories US-3 AC5]

## アイコン・アセット

- 本スコープで新規アイコン・画像アセットは使用しない（カード構成の変更はテキスト + 既存トークンのみ）。

## レスポンシブ

| ブレークポイント | グリッド | 備考 |
|---|---|---|
| mobile（<640px） | `grid-cols-1` | 縦積み（既存どおり・専用レイアウトはスコープ外） |
| sm（640–1023px） | `sm:grid-cols-2` | 2 列 + 1 枚 |
| lg（≥1024px） | `lg:grid-cols-5` | 5 枚 1 行（デモの主表示対象） |

## Assumptions & Open Questions

- なし（None.）— デザイントークン・コンポーネント・レイアウトはすべて既存デザインシステム内で解決可能。

## Sources

- [wireframes] `ideation/rough-mockups/wireframes.md`（カード構成・試算値注記・スケルトン・アクセシビリティ注記）
- [user-flow] `ideation/rough-mockups/user-flow.md`（画面遷移・状態）
- [stories] `inception/user-stories/stories.md`（US-2 カード構成・Level 1 lime Q4=A・試算値 2 段構成 Q1=A）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-5 / FR-6 / NFR-5 / C-2）
- [team-practices] `inception/practices-discovery/team-practices.md`（表示メタの単一ソース Q9 / フォールバック Q10 / UI 一貫性）
