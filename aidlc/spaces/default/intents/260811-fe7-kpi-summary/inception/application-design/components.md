# Application Design — Components

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」のコンポーネント設計。
> 表示仕様は refined-mockups（`mockups.md` / `interaction-spec.md` / `design-system-mapping.md` /
> `accessibility-checklist.md`）、要件は `requirements.md`、ユーザーストーリーは `stories.md`、
> 既存構造は RE 成果物（`codekb/architecture.md` / `codekb/component-inventory.md`）を参照。
> 本スコープは **フロントエンドのみの変更**（バックエンド BE-8 は実装済み・変更対象外。C-1）。

## 1. 設計方針（コンポーネント境界）

- **表示専用と状態遷移の分離:** `KpiSummary` は表示専用（props 受領で描画のみ）に徹し、
  **状態遷移・データ取得・スケルトン切替は `DashboardClient` と新規フック `useKpiPolling` が担う**
  （US-2=表示単位・US-3=状態遷移単位の責務分割。mockups.md と整合）。
- **専用フックによる責務閉包:** KPI ポーリングは新規フック `useKpiPolling` に実装し、
  `DashboardClient` は「データ取得の集約・描画の束ね」に専念する（Q1=A 承認済み）。
- **ランドマークの一元所有:** KPI セクションの `section` / `h2` / `aria-labelledby` / `aria-busy` は
  **常時描画されるラッパー `DashboardClient` が所有**し、配下でスケルトンかカードグリッドを切替える
  （Q2=A 承認済み・refined-mockups:c4 学習と整合。スケルトン中も h2・ランドマークを維持）。
- **表示メタの単一ソース:** 深刻度メタは `lib/severity.ts` を本拠とし、契約層 `types/api.ts` から
  re-export する（team-practices Q9=A）。

## 2. コンポーネント一覧

| コンポーネント | 種別 | 責務 | 変更 |
|---|---|---|---|
| `DashboardClient` | 状態遷移・データ取得（Client） | KPI セクションのランドマーク所有・`useKpiPolling` による取得集約・スケルトン切替・地図/アラート一覧/詳細ドロワーの束ね | **変更** |
| `useKpiPolling` | カスタムフック（新規） | `fetchKpiSummary` を 5 秒ポーリングし `KpiSummary` を保持。クリーンアップ・`cancelled` フラグでリーク防止 | **新規** |
| `KpiSummary` | 表示専用（Server 互換・Client 化しない） | 5 カード + 試算値注記を描画（`KpiSummary` 型を受領） | **変更** |
| `fetchKpiSummary` | API クライアント関数 | `GET /api/v1/kpi/summary` を呼び `KpiSummary`（camelCase）を返す | **新規** |
| `lib/severity.ts` | ユーティリティ（表示メタ単一ソース） | `SeverityLevel` / `SEVERITY_META` / `getSeverityMeta` / `getSeverityColor` の本拠 | **変更（権威化）** |
| `types/api.ts` | 契約層 | `KpiSummary` 型追加 + `SeverityLevel` を `lib/severity.ts` から re-export | **変更** |
| `page.tsx` | ページ（Server Component） | `MOCK_KPI_DATA` 撤去・`KpiSummary` import 削除。Server Component のまま維持 | **変更** |
| `lib/api.ts` | API クライアント境界 | `fetchKpiSummary` 追加・snake_case→camelCase 変換の単一境界 | **変更** |

## 3. コンポーネント詳細

### 3.1 `DashboardClient`（ラッパー・状態遷移）

| 項目 | 内容 |
|---|---|
| 分類 | layout + data-fetching（Client Component） |
| 入力 | `sensorFeatures: SensorFeatureCollection`（サーバー側取得済み GeoJSON） |
| 責務 | KPI セクションの `section`（h2「KPI サマリ」+ `aria-labelledby` + `aria-busy`）を常時描画し、`useKpiPolling` の取得状態に応じてスケルトン（`kpi-skeleton`）か `KpiSummary` のカードグリッドを切替える。既存 3 列グリッド（地図/アラート一覧/詳細ドロワー）を包む親要素の先頭に KPI 全面幅セクションを描画 |
| 所有 | KPI セクションのランドマーク（h2 の ID 例: `kpi-summary-heading`）・`aria-busy` を**一元所有**（Q2=A） |
| 状態 | (a) 初回ローディング＝スケルトン (b) 取得成功＝カード値表示 (c) **成功後に失敗＝再スケルトン**（stale 値非表示） |
| 参照 | `requirements.md` FR-7 / FR-8、`stories.md` US-3、`codekb/architecture.md` KPI 配線予定 |

### 3.2 `useKpiPolling`（新規フック）

| 項目 | 内容 |
|---|---|
| 分類 | custom hook（新規・`useAlertPolling` と対称） |
| 責務 | `fetchKpiSummary` を `ALERT_POLL_INTERVAL_MS`（5000ms）でポーリングし、取得成功時のみ `kpiData` を更新。失敗時は `isLoading`（スケルトン状態）へ戻す。`useEffect` クリーンアップで `clearInterval` + `cancelled` フラグ徹底 |
| 戻り値 | `{ kpiData: KpiSummary \| null, isLoading: boolean }` |
| 根拠 | Q1=A 承認済み。失敗時挙動（再スケルトン）が `useAlertPolling`（最終状態据え置き）と異なるため共用しない |
| 参照 | `requirements.md` FR-7 / FR-8、`team-practices.md`（ポーリングクリーンアップ規約）、`codekb/component-inventory.md`（`useAlertPolling` 先例） |

### 3.3 `KpiSummary`（表示専用）

| 項目 | 内容 |
|---|---|
| 分類 | display（Server 互換。Client 化しない） |
| 入力 | `kpiData: KpiSummary`（型エイリアス `KpiSummaryData` で import） |
| 責務 | 5 カード（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト · 試算値）と試算値注記（2 段構成）を降順で描画。**section/h2 は描画しない**（Q2=A: DashboardClient が所有） |
| 非責務 | データ取得・状態遷移・スケルトン描画は行わない |
| 参照 | `requirements.md` FR-5 / FR-6、`stories.md` US-2、`mockups.md`（カード構成・降順）、`interaction-spec.md`（試算値 2 段構成・カード詳細） |

### 3.4 `fetchKpiSummary`（API クライアント関数）

| 項目 | 内容 |
|---|---|
| 分類 | input（データ取得・`lib/api.ts` 内） |
| 入力 | なし |
| 出力 | `Promise<KpiSummary>`（7 フィールド・camelCase） |
| 責務 | `GET /api/v1/kpi/summary` を呼び、snake_case→camelCase 変換を `lib/api.ts` 境界で 1 回だけ行う。4xx/5xx は `unwrap<T>` が `ApiError` へ変換して throw、非 axios エラーは透過 |
| 参照 | `requirements.md` FR-4、`stories.md` US-1 AC1、`team-practices.md`（変換境界・`ApiError` 変換規約）、`codekb/component-inventory.md`（既存 fetch 関数の先例） |

### 3.5 `lib/severity.ts`（表示メタ単一ソース）

| 項目 | 内容 |
|---|---|
| 分類 | ユーティリティ層 |
| 責務 | `SeverityLevel`（0\|1\|2\|3）・`SEVERITY_META`（label / color / accentClass）・`getSeverityMeta` / `getSeverityColor` の**本拠**。Level 1（lime）を含む全レベル定義 |
| 根拠 | team-practices Q9=A。型と表示メタの二重定義（`types/api.ts` と `lib/severity.ts`）を `lib/severity.ts` に集約し、契約層から re-export。`requirements.md` の FR 参照は SeverityLevel の扱いに関する上流指示（C-2）を満たす |
| 参照 | `codekb/component-inventory.md`（現状 `SeverityLevel` の二重定義・単一ソース化の対象）、`design-system-mapping.md`（デザイントークン） |

### 3.6 `types/api.ts`（契約層）

| 項目 | 内容 |
|---|---|
| 分類 | 外部契約境界 |
| 責務 | `KpiSummary` 型（`totalSensors` / `level1Count` / `level2Count` / `level3Count` / `estimatedCostSavedYen` / `isEstimate` / `assumptionDoc`）を追加。`SeverityLevel` は `lib/severity.ts` から re-export |
| 参照 | `interaction-spec.md`（`KpiSummary` 7 フィールド camelCase・型エイリアス）、`stories.md` US-1 |

## 4. 境界と所有権のまとめ

| 領域 | 所有者 | 根拠 |
|---|---|---|
| KPI データ取得・ポーリング周期・クリーンアップ | `useKpiPolling` | Q1=A |
| KPI セクションの `section`/`h2`/`aria-labelledby`/`aria-busy`・スケルトン切替 | `DashboardClient` | Q2=A・refined-mockups:c4 |
| 5 カード + 試算値注記の描画（表示文字列・順序） | `KpiSummary` | mockups / interaction-spec |
| snake_case→camelCase 変換 | `lib/api.ts` 境界のみ | team-practices |
| 深刻度表示メタ（色・ラベル） | `lib/severity.ts`（単一ソース） | team-practices Q9=A |
| API 契約（型・再 export） | `types/api.ts` | interaction-spec |

## 5. スコープ外（本設計で扱わないもの）

- バックエンドの変更（BE-8 実装済み。`GET /api/v1/kpi/summary` は既存エンドポイントを利用）。
- 認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB
  （`requirements.md` Out of Scope・team-practices Forbidden と整合）。
- モバイル専用レイアウト・外部 BI/可視化ツールの導入（`mockups.md`・project.md 学習と整合）。

## Assumptions & Open Questions

- 本スコープはフロントエンドのみの変更で、新規サービス・データ所有の設計判断は発生しない（C-1）。
  `services.md` は「新規サービスなし・既存 API をフロントから利用」を記録する。
- KPI のポーリング周期はアラートと同一（`ALERT_POLL_INTERVAL_MS = 5000`）を共用する
  （requirements FR-7・interaction-spec）。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / NFR / Constraints / Out of Scope）
- [stories] `inception/user-stories/stories.md`（US-1〜4・対象ファイル一覧）
- [refined-mockups] `inception/refined-mockups/mockups.md`・`interaction-spec.md`・`design-system-mapping.md`・`accessibility-checklist.md`（表示仕様・カード構成・試算値 2 段構成）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・エラーハンドリング・フォールバック Q10 / 単一ソース Q9 / カバレッジゲート）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`（コンポーネント関係・KPI 配線予定）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（コンポーネント責務・依存グラフ・useAlertPolling 先例）
- [business-model] `docs/business-model.md`（§3.4 デモ算出例・§3.5 試算値の扱い）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:02:42Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Major | component-methods.md §2.1 / component-dependency.md §4・§6 | **循環依存を見落としている**。`ALERT_POLL_INTERVAL_MS` は既存 `DashboardClient.tsx`（L23 `export const`）から export されている。設計は `useKpiPolling` が「内部で `ALERT_POLL_INTERVAL_MS` を参照」するとし（component-methods §2.1）、`DashboardClient` は `useKpiPolling` を import するため、**`DashboardClient.tsx → useKpiPolling.ts → DashboardClient.tsx` のモジュール循環**が発生する。component-dependency.md §6 の「依存グラフに循環はなし。すべて DAG 構造」の主張・依存マトリクス（`useKpiPolling` の行にこのエッジが欠落）と矛盾する。実行時は const が関数体内で遅延参照されるため通常は動作するが、lint（import/no-cycle）・保守性の観点で実装時に必ず修正が必要になる | `useKpiPolling(intervalMs: number)` と引数化し `DashboardClient` 側で `ALERT_POLL_INTERVAL_MS` を渡す（既存 `useAlertPolling(intervalMs)` のパターンと対称・循環解消）。または定数を `lib/constants.ts` 等の共通モジュールへ抽出する |
| 2 | Minor | decisions.md ADR-003 / component-methods.md §2.6 | **テストフィクスチャに `totalSensors` が未指定**。ADR-003 は counts（8/3/1）と `estimatedCostSavedYen`（2,048,400）のみ固定し、「旧 MOCK 値（1,420,000 / 1,240）とは異なるため `queryByText("1,240")` 非存在アサートの偽陰性を回避できる」と主張するが、`1,240` が画面に出るかは `totalSensors` の値で決まる。現状 `KpiSummary.test.tsx` の `BASE_KPI` は `totalSensors: 1240` のため、開発者がこの値を据え置くと「1,240」がセンサー数カードに出現し、US-2 AC5 / US-3 AC2 の非存在アサートが壊れる（実勢の hydrants.json は 10 件で、フィクスチャの自然値は 1240 ではない） | ADR-003 のフィクスチャ仕様に `totalSensors`（例: 10）を明記し、costs/counts と併せて全 7 フィールドを固定する。機能設計・テスト指示書への引き継ぎ時に必ず含める |
| 3 | Minor | component-methods.md §2.5 | **`getSeverityColor` の用途記述が不正確**。§2.5 は「Level 3 / Level 2 / Level 1 カードの `accentClass`（枠線 + 文字色）を取得」するものとして `getSeverityMeta` / `getSeverityColor` を併記するが、`getSeverityColor`（`lib/severity.ts` L71-73）は hex カラー（Leaflet マーカー用）を返し `accentClass` を返さない。KPI カードが実際に使うのは `getSeverityMeta(level).accentClass`（既存 `KpiSummary.tsx` L94 と整合）。誤って `getSeverityColor` をカード配線するリスクがある | §2.5 から `getSeverityColor` を削除するか、「KPI カードでは未使用（Leaflet マーカー専用）」と明記する |
| 4 | Minor | components.md §3.6 / component-methods.md §2.2 | **`assumptionDoc` が型に定義されるが表示で未使用、かつ表示固定文字列とバックエンド値が乖離する**。`KpiSummary` 型には FR-1（1:1 契約）で `assumptionDoc` を含める一方、注記は固定リテラル「前提: docs/business-model.md」で描画する（FR-6）。バックエンドの `assumption_doc` 実値は「docs/business-model.md §3」（`services/kpi.py` L30）で表示文字列と異なる。開発者がレスポンスの `assumptionDoc` を注記描画に流用すると、ADR-004 の完全一致アサート（`前提: docs/business-model.md`）が壊れる | `assumptionDoc` は「契約のみ・表示未使用」である旨を components.md §3.6 に明記し、注記は固定リテラルと確定させる |

### Validation Tool Results

ステージ定義（application-design.md）に検証ツールの指定はなく、実行対象なし。センサー（required-sections / upstream-coverage）はフレームワーク側で自動実行される。本レビューは成果物 5 ファイル・上流契約（requirements / stories / refined-mockups 4 点 / team-practices / codekb architecture・component-inventory）と既存フロント実装（DashboardClient / KpiSummary / useAlertPolling / lib/api / lib/severity / types/api / page.tsx / 既存テスト / vitest.config.mts / package.json / backend schemas・services/kpi.py / docs/business-model.md）の照合で実施した。主要な照合結果:
- `ALERT_POLL_INTERVAL_MS = 5000` は DashboardClient.tsx L23 に存在（循環の原因、Finding 1）。
- `useAlertPolling` は失敗時最終状態据え置き・`intervalMs` 引数化（設計の「共用しない」判断・対称パターンと整合）。
- BE-8 の `KpiSummary` は 7 フィールド snake_case を返す（設計の FR-1・データフローと一致）。
- ADR-003 の算定（8×121,800 + 3×308,000 + 150,000 = 2,048,400、`formatManYen` = 「204.8万円」）は business-model §3.4 と一致。
- `getSeverityMeta(1).accentClass` = `border-lime-200 text-lime-700`（Level 1 lime）は既存 `SEVERITY_META` に定義済みで新規トークン不要。
- スコープ拡大（Issue 6 ファイル → stories 13 ファイル）は requirements の NOT-READY 指摘（Critical #1/#2）の解消として stories で正当化済み。components.md の C-1 参照は「バックエンド変更なし」の意図で使用され、6 ファイル制限の再主張はなし（矛盾なし）。
- ADR-002 の h2 所有の読み替え（US-2 AC4 vs refined-mockups:c4）は上流の乖離を正しく解消し、テスト観測点の DashboardClient 側移行を機能設計への引き継ぎ事項として明記している。

### Summary

フロントエンド限定の小規模設計で、責務分割（KpiSummary 表示専用 / DashboardClient ランドマーク所有 / useKpiPolling データ取得）・上流表示仕様（5 カード降順・試算値 2 段構成・kpi-skeleton・aria 属性）・BE-8 契約（7 フィールド）との整合は高く、開発者は上流成果物（stories のスコープ一覧）と合わせて余計な質問なしに実装できる。唯一の設計レベルの指摘は、`ALERT_POLL_INTERVAL_MS` の参照箇所に起因する `DashboardClient ↔ useKpiPolling` の循環依存（Major・1 件）で、既存 `useAlertPolling(intervalMs)` の引数化パターンに合わせるか定数を共通モジュール化すれば解消する。これ以外はフィクスチャ・メソッド表・注記の扱いに関する Minor 3 件で非ブロッキング。判定: Critical 0・Major 1（≤2）→ **READY**。
