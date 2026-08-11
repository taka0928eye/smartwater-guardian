# Unit of Work — FE-7 KPIサマリの実データ連携と「試算値」注記

> 単一 proto-Unit（BU-1）として定義する（Q1=A・Q2=A 承認済み）。
> 上流成果物（`stories.md`「全ストーリーが単一 proto-Unit で完結」・`requirements.md` C-1〜C-5・
> `application-design` 5 成果物）の確定事項を反映する。実装順序の経済的決定（Bolt 順序）は
> Delivery Planning（2.8）の責務であり、本成果物はトポロジー（依存 DAG）のみを記述する。

## 1. ユニット一覧

| ユニット | kind | 複雑度 | 説明 |
|---|---|---|---|
| `BU-1` | `ui` | M | FE-7 フロントエンド KPI サマリ機能一式（13 ファイル・単一イテレーション） |

## 2. ユニット定義

### 2.1 `BU-1` — FE-7 KPI サマリの実データ連携と「試算値」注記

| 項目 | 内容 |
|---|---|
| **境界** | `frontend/` 配下の KPI サマリ機能一式。型契約（`types/api.ts`）・API クライアント（`lib/api.ts`）・表示メタ単一ソース（`lib/severity.ts`）・表示コンポーネント（`KpiSummary.tsx`）・状態遷移/ポーリング（`DashboardClient.tsx`・新規 `useKpiPolling`）・ページ（`page.tsx`）・テスト 4 ファイル（`api.test.ts` / `KpiSummary.test.tsx` / `DashboardClient.test.tsx` / `page.test.tsx`）・カバレッジゲート設定（`vitest.config.mts` / `package.json` / `.github/workflows/ci.yml`） |
| **非境界（Out of Scope）** | バックエンド（BE-8）のスキーマ・実装変更（`requirements.md` C-1）。`today_detections` の表示対応。認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB（`requirements.md` Out of Scope・team-practices Forbidden） |
| **責務** | US-1（`KpiSummary` 型 + `fetchKpiSummary`）・US-2（実データ表示 + 試算値注記）・US-3（スケルトン表示フォールバック）・US-4（`SeverityLevel` 単一ソース化）・NFR-1（カバレッジゲート恒久化） |
| **デプロイメントモデル** | monolithic deploy（単一 Next.js アプリへの組み込み。Q3=A） |
| **複雑度見積** | **M** — フロントエンド限定・13 ファイル・相互依存が強いが、既存パターン（`useAlertPolling` / `unwrap<T>` / `SEVERITY_META`）の踏襲で実装可能 |
| **kind** | `ui` — フロントエンド表面。サービス（実行可能プロセス）・パッケージング（配布物）・独立ランタイムは持たない |

### 2.2 実装ノート・制約

- **依存 DAG**: 単一ノード（`depends_on: []`。Q2=A）。ユニット間の依存エッジ・並行開発ユニットは存在しない。
- **内部実装順序**: 型（`types/api.ts`・`lib/severity.ts`）→ API クライアント（`lib/api.ts`）→ 表示（`KpiSummary.tsx`）→
  状態遷移（`DashboardClient.tsx`・`useKpiPolling`）→ 設定（`vitest.config.mts` / `package.json` / `ci.yml`）
  （scope-definition:c2 学習と整合。US-1 + US-4 → US-2 → US-3 の順）。
- **テスト**: TDD（Red → Green → Refactor）を厳格に順守。カバレッジ lines / functions / branches / statements 各 80% 以上
  （NFR-1）。`page.tsx` は **Server Component のまま維持**（`requirements.md` C-2）。
- **変換境界**: snake_case→camelCase 変換は `lib/api.ts` 境界で 1 回だけ（C-3 / team-practices）。
- **モック非残置**: 実データで埋められる KPI カードに `MOCK_KPI_DATA` を残さない（C-4 / project.md Forbidden）。
- **循環依存の解消**: Application Design レビュアー指摘（Major 1）に基づき、`useKpiPolling` は
  `intervalMs: number` を引数化し、`DashboardClient` 側から `ALERT_POLL_INTERVAL_MS`（5000）を渡す
  （既存 `useAlertPolling(intervalMs)` と対称。`DashboardClient ↔ useKpiPolling` のモジュール循環を回避）。
- **テストフィクスチャ**: `totalSensors` は実勢（hydrants.json）に合わせ **10**、counts は Level 1: 8 / Level 2: 3 / Level 3: 1、
  `estimatedCostSavedYen` は **2,048,400**（ADR-003）とし、全 7 フィールドを固定（Application Design レビュアー Minor 2 反映）。
- **カードラベル**: 承認済み表示文言（Level 3 破裂リスク / Level 2 警告 / Level 1 微小漏水（AI検知））を固定値とし、
  `SEVERITY_META.label` と分離（ADR-005）。色・`accentClass` のみ `getSeverityMeta(level)` を利用
  （`getSeverityColor` は KPI カードでは未使用。Leaflet マーカー専用。Application Design レビュアー Minor 3 反映）。
- **試算値注記**: `assumptionDoc` は契約のみで表示未使用。注記は固定リテラル「前提: docs/business-model.md」の 2 段構成
  （Application Design レビュアー Minor 4 反映・ADR-004）。

## 3. デプロイメントモデル

- 全ユニットが単一 Next.js アプリ（`frontend/`）への組み込み（monolithic deploy）。独立デプロイ・パッケージング単位は作らない。
- バックエンド（BE-8）は変更対象外（C-1）で、既存 `GET /api/v1/kpi/summary` をフロントから 5 秒ポーリングで利用する。

## Assumptions & Open Questions

- 単一ユニットのため、本スコープの「依存 DAG の経済的順序付け（Bolt 順序）」は Delivery Planning で単一 Bolt（BU-1）として扱う前提。
- 実装順序（型 → APIクライアント → 表示）は Bolt 内の内部手順であり、DAG 上の順序付けではない（2.8 の決定を侵さない）。
- その他の未確定項目はなし（None.）

## Sources

- [components] `inception/application-design/components.md`（コンポーネント境界・責務・8 コンポーネント）
- [component-methods] `inception/application-design/component-methods.md`（公開インターフェース・テスト観測点）
- [services] `inception/application-design/services.md`（新規サービスなし・BE-8 利用方針）
- [component-dependency] `inception/application-design/component-dependency.md`（依存マトリクス・データフロー・共有リソース）
- [decisions] `inception/application-design/decisions.md`（ADR-001〜005・引き継ぎ表）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR-1〜5 / Constraints C-1〜C-5 / Out of Scope）
- [stories] `inception/user-stories/stories.md`（US-1〜4・対象ファイル一覧 13 件・単一 proto-Unit 宣言）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:15:13Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | unit-of-work.md §1・§2.1 / unit-of-work-story-map.md §4 | 「13 ファイル」は stories.md の一覧（13 件）を踏襲しているが、§2.1 の境界には新規フック `useKpiPolling`（component-methods.md §2.1 で新規 hook・ADR-001 Negative で「ファイルが 1 つ増える」と明記）が含まれており、実ファイル数は **14** になる。10 ソース + 3 config/CI + 新規フック = 14。数のみの齟齬で設計上の欠陥ではないが、スコープ境界確認を重視する本プロジェクト（scope-definition:c1 / intent-capture:c1）では開発者が「新規ファイル作成はスコープ内か」を疑う余地がある | `useKpiPolling` を新規ファイルとして明示的に数え「stories 一覧 13 件 + 新規フック = 計 14 ファイル」と記載するか、13 件は stories 一覧ベースである旨を注記する |
| 2 | Minor | unit-of-work.md §2.2 vs component-methods.md §2.1 | Major 1 の循環依存は `useKpiPolling(intervalMs)` の引数化で正しく解消され本成果物 §2.2・dependency §2 に反映済みだが、上流 component-methods.md §2.1 は未更新のまま `useKpiPolling()`（入力なし・内部で `ALERT_POLL_INTERVAL_MS` 参照）と記載されており、開発者が上流契約をそのまま実装すると循環依存が再発するリスクが残る | 本成果物の §2.2 がフックシグネチャの権威である旨を functional-design への引き継ぎ事項として明記するか、上流 component-methods.md の更新（または陳腐化注記）を承認ゲートの確認事項に上げる |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| YAML edge block パース検証（pyyaml） | PASS | `units: [{name: BU-1, kind: ui, depends_on: []}]`。単一ノード・`kind: ui` は許可列挙値・重複なし・自己依存なし・未解決依存なし・無閉路（DAG） |
| required-sections（相当確認） | PASS | 3 成果物すべて H2 見出し 2 以上・unit-of-work-dependency.md に必須の fenced `yaml` ブロック存在 |
| upstream-coverage（相当確認） | PASS | 3 成果物の Sources が consumed 7 契約（components / component-methods / services / component-dependency / decisions / requirements / stories）をすべて参照 |
| フィクスチャ実勢照合 | PASS | `totalSensors: 10` は実マスタ `backend/app/data/hydrants.json` の 10 件と一致。counts（8/3/1）・`estimatedCostSavedYen`（2,048,400 = 8×121,800 + 3×308,000 + 150,000）も ADR-003・business-model §3.4 と整合 |

### Summary

単一 proto-Unit（BU-1・kind `ui`・`depends_on: []`）の分解は Q1=A / Q2=A / Q3=A、stories.md の単一 proto-Unit 宣言、application-design 5 成果物と完全に整合し、Major 1（循環依存）と Minor 2〜4（フィクスチャ / getSeverityColor / assumptionDoc）の解決策も実装ノートへ正確に引き継がれている。必須の YAML エッジブロックは整形式・無閉路で、全 4 ストーリーが BU-1 に割当て済み・全 7 契約が参照されている。ステージ禁止事項（Bolt 順序・臨界経路の推奨）も「ユニット内部手順」として明確に範囲付けされ侵害していない。残る 2 件はファイル数表記（13 vs 実 14）と上流 component-methods.md のシグネチャ未更新に伴う引継ぎ明示の Minor で、いずれも実装を妨げない。Critical 0・Major 0 → **READY**。
