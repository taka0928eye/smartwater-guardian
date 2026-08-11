# SmartWater Guardian - Reverse Engineering Timestamp & Scope

## Reverse Engineering Session Metadata

**Session ID**: 260811-fe7-kpi-summary  
**Intent**: FE-7 KPI サマリ実データ配線（フロントエンド限定・6ファイル変更）  
**Scope Type**: feature (standard depth)  
**Performed**: 2026-08-11  
**Performed By**: aidlc-developer-agent (code scan) + aidlc-architect-agent (synthesis)  
**Repository**: smartwater-guardian (primary)  
**Base Branch**: main  
**Commit Context**: git HEAD = 7830301（BE-8: KPIサマリ推定削減コスト算定ロジック実装）

---

## Scope Summary

この逆リバースエンジニアリングスキャンは、アクティブインテント FE-7（KPI サマリ実データ配線）
のために実施した**リポジトリ全体の部分スキャン**。バックエンドの主要ルーター・サービス・スキーマ
（BE-8 の KPI 算定含む）と、フロントエンドの配線対象（`page.tsx` / `DashboardClient` /
`KpiSummary` / `lib/api.ts`）を深く解析し、スナップショットとして固定する。対象は
**frontend 6 ファイル**の変更（FE-7）だが、配線先の契約（`GET /api/v1/kpi/summary`）と
表示元（`KpiSummary.tsx`）を正確に記録するため、バックエンド KPI 層も深く解析した。

### What Was Analyzed Deeply

1. **Backend API 一式**
   - `backend/main.py` — CORS・ルーター登録・ヘルスチェック
   - `backend/app/routers/{telemetry,alerts,sensors,kpi}.py` — 4 ルーター全実装
   - `backend/app/store.py` — スレッドセーフなインメモリストア（`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`、モジュールレベルシングルトン、`get_hydrants` の `@lru_cache` ローダー）
   - `backend/app/services/{ledger,kpi}.py` — 疑似GIS配管台帳照合・KPI 算定
   - `backend/app/schemas/{telemetry,alert,pipe,kpi}.py` — Pydantic v2 スキーマ一式
   - `backend/app/data/{hydrants.json,pipes.json}` — 実マスタデータ（10件/10路線）
   - `backend/scripts/simulate_sensor.py` — 疑似センサー CLI

2. **Backend テスト・環境**
   - `backend/tests/conftest.py`・`tests/test_kpi.py`（全文）＋ `test_alerts.py` / `test_store.py` / `test_ledger.py` の先頭部
   - `backend/requirements.txt`・`backend/README.md`・`backend/.env.example`

3. **Frontend 配線対象**
   - `frontend/src/app/page.tsx`（Server Component・`force-dynamic`・`MOCK_KPI_DATA` / `FALLBACK_SENSOR_FEATURES` 保持中）
   - `frontend/src/components/dashboard/DashboardClient.tsx`（アラート 5 秒ポーリング + 地図/一覧/ドロワー連動）
   - `frontend/src/components/dashboard/KpiSummary.tsx`（5 枚カード・`formatManYen`）
   - `frontend/src/components/dashboard/Header.tsx`・`components/alert/*`・`components/common/SeverityBadge.tsx`
   - `frontend/src/components/map/SensorMap.tsx`・`SensorMapInner.tsx`（Leaflet）
   - `frontend/src/hooks/useAlertPolling.ts`
   - `frontend/src/lib/api.ts`（axios クライアント・snake_case→camelCase 変換・`ApiError`）・`lib/severity.ts`（`SEVERITY_META` 単一ソース）・`lib/alertSort.ts`
   - `frontend/src/types/api.ts`・`types/sensor.ts` — TS 契約型（camelCase）
   - `frontend/package.json`・`tsconfig.json`・`eslint.config.mjs`・`vitest.config.mts`・`next.config.ts`・`src/test/setup.ts`・`.env.local.example`
   - `frontend/src/lib/__tests__/api.test.ts`・`src/app/__tests__/page.test.tsx`（全文）＋ `KpiSummary` / `DashboardClient` / `alertSort` テスト先頭部

4. **CI・ドキュメント**
   - `.github/workflows/ci.yml`・`.gitignore`・ルート `CLAUDE.md`
   - `docs/PRD.md`・`docs/business-model.md`・`docs/ui-wireframe.md`・`docs/issues-summary.md` の先頭部

### What Was Skimmed (Not Deep Coverage)

- `backend/tests/test_telemetry.py` / `test_pipes.py` / `test_simulate_sensor.py` / `test_dependencies.py` / `test_hydrants.py`
- `backend/scripts/check_alerts.py` / `check_ledger.py` / `check_telemetry.py`
- `frontend` 残りのコンポーネントテスト（`AlertList` / `AlertDetailDrawer` / `SeverityBadge` / `Header` / `SensorMap`）
- `frontend/public/`・`next-env.d.ts`・`postcss.config.mjs`
- `docs/llm-cost.md` / `docs/code-review-closed-issues.md` / `docs/aidlc-prompt-examples.md`
- `frontend/coverage/`（生成物・git 未追跡）
- `.claude/`・`.codex/`・`aidlc/`（フレームワーク内部・対象外）

---

## Technical Findings

### Identified Technical Debt

1. **FE-7 未配線（KPI がモックのまま）** ⚠️ **CRITICAL（アクティブインテントの対象）**
   - `page.tsx` が `MOCK_KPI_DATA`（`totalSensors: 1240` 等の固定値）を `KpiSummary` へ渡している
   - `lib/api.ts` に `fetchKpiSummary` が**未実装**。`KpiSummary.tsx` の `KpiData` 型もバックエンド
     `KpiSummary`（7 フィールド）と非整合（`todayDetections` を含み `level1Count` を欠く）
   - FE-7 では `DashboardClient` で `fetchKpiSummary` をポーリングし `KpiSummary` を配下に描画する

2. **`KpiData` 型とバックエンド契約の乖離** ⚠️ **HIGH（FE-7 で解消予定）**
   - バックエンド `KpiSummary` は `total_sensors / level1_count / level2_count / level3_count / estimated_cost_saved_yen / is_estimate / assumption_doc` の 7 項目
   - フロント `KpiData` は `totalSensors / level3Count / level2Count / todayDetections / estimatedCostSavedYen` の 5 項目。`level1_count` が無く `today_detections`（D-3 で対象外）を含む

3. **`SeverityLevel` の二重定義** ⚠️ **MEDIUM（解消方針は確定済み）**
   - `types/api.ts` と `lib/severity.ts` の両方に `SeverityLevel` が存在
   - 単一ソース化は表示メタ（`SEVERITY_META` 等）と同居する `lib/severity.ts` を本拠とし、`types/api.ts` から re-export する方針（feasibility 学習済み）

4. **`SensorInfo.status` / `SensorProperties.status` が `string`** ⚠️ **LOW**
   - バックエンドは `Literal["normal","watch","warning","critical","unknown"]` を強制するが、フロントは `string` で Literal なし

5. **BE-3 `services/audio.py` 未実装** ⚠️ **MEDIUM**
   - docstring 参照が残る。`telemetry.py` の `_analyze_audio_mock` が仮実装として代行。SciPy は現状未使用

6. **`WorkOrder` 等の将来契約の先取り** ⚠️ **LOW**
   - フロント `types/api.ts` に `WorkOrder / RepairPart / Urgency / WorkOrderSource` が定義済みだが、バックエンドは `POST .../work-order` を 501 で返すだけ

7. **その他** ⚠️ **LOW**
   - `HttpClientDep`（`dependencies.py`）未使用（BE-5/Orcarouter 用の先取り）
   - CORS `allow_origins` が `["http://localhost:3000"]` に硬コード
   - `backend/README.md` のスコープ記載が BE-6 までで古い
   - `frontend/coverage/`・`tsconfig.tsbuildinfo` 等の生成物がリポジトリに混在

### Code Quality Assessment

- **Type Safety**: 75%（`SensorInfo.status` の Literal 欠如・`KpiData` 契約乖離・`SeverityLevel` 二重定義）
- **Test Coverage**: 80%+（CI ゲート。backend `--cov-fail-under=80` / frontend 80% thresholds）
- **Linting**: ESLint 9 flat config で CI ゲート。Python 側は ruff/mypy 未導入
- **Performance**: 良好（`@lru_cache` ローダー・`threading.Lock` 保護・FFT は同期 def + スレッドプール）
- **Documentation**: 80%（docstring 日本語丁寧・Issue トレーサビリティあり。`backend/README.md` は陳腐化）

---

## Related Code Knowledge

The following knowledge base artifacts were synthesized from this scan and depend on the scope's accuracy:

| Artifact | Depends On | Freshness Impact |
|----------|-----------|------------------|
| business-overview.md | Core mission（安定） | Low |
| architecture.md | ルーター構成・KPI 配線フロー ← **page.tsx, DashboardClient, kpi.py** | **HIGH** |
| code-structure.md | モジュール構成 ← 全解析ファイル | **HIGH** |
| api-documentation.md | エンドポイント契約 ← routers/*・lib/api.ts | **HIGH** |
| component-inventory.md | 責務分担 ← services/*・routers/*・components/* | **HIGH** |
| technology-stack.md | フレームワークバージョン（安定） | Low |
| dependencies.md | import グラフ ← 全解析ファイル | **HIGH** |
| code-quality-assessment.md | テスト・デット信号 ← **page.tsx, kpi.py, api.ts** | **HIGH** |

**Rerun Risk**: `page.tsx`・`DashboardClient.tsx`・`KpiSummary.tsx`・`lib/api.ts`・`types/api.ts` は
FE-7 の変更対象。実装後は KPI 配線の状態（モック残存・`fetchKpiSummary` 実装有無）を再検証すること。

---

## Future Extension Points

### Known Out-of-Scope Items

1. **FE-7（本インテント）**: `DashboardClient` での `fetchKpiSummary` ポーリングと `KpiSummary` 配下描画。
   `today_detections` はバックエンドスキーマ上 FE-7 以降の対応と明記されているため対象外。

2. **BE-3（FFT 音響解析）**: `audio.py` はスタブ。`_analyze_audio_mock` を置き換える。SciPy 導入予定。

3. **BE-5（工事発注書自動起票）**: `POST /alerts/{id}/work-order` は 501 スタブ。Orcarouter API 連携。

4. **永続 DB**: 現状 JSON マスタ + インメモリストア。将来は PostgreSQL + PostGIS（CLAUDE.md §3 で本番用大型 GIS DB はスコープ外）。

5. **認証・権限**: CLAUDE.md §3 でスコープ外。

---

## Scan Methodology

**Developer Phase (Step 2)**
- ファイル単位のコード精読（AST 自動解析は不使用）
- import チェーン追跡: `kpi.py → services/kpi.py → store.py → schemas/kpi.py`
- Pydantic モデルシグネチャ・型ヒントの検証
- カバレッジゲート（CI `--cov-fail-under=80`・frontend 80% thresholds）の確認
- 手動精査による契約乖離の特定

**Architect Phase (Step 3)**
- 9 知識ベース成果物を合成
- 依存グラフ作成（dependencies.md）
- KPI 配線の現状と FE-7 ギャップを記録（api-documentation.md / code-quality-assessment.md）
- Mermaid 図の構文検証とテキスト代替の併記

**Quality Checks**
- 全 9 成果物の内部整合を検証
- Mermaid ダイアグラム構文チェック（✓）
- コード例が実ソースと一致（spot-check ✓）

---

## Access to Knowledge

This knowledge base (all 9 artifacts) was written for the FE-7 intent on 2026-08-11.
It accurately represents the codebase **at that date**（git HEAD = 7830301）、focused on:

- **What Changed (recent)**: BE-8（`GET /api/v1/kpi/summary`・推定削減コスト算定）実装
- **What Will Change (FE-7)**: page.tsx の `MOCK_KPI_DATA` 撤去・`fetchKpiSummary` 実装・`DashboardClient` での KPI ポーリング・`KpiData` 型の契約整合
- **What Stays Stable**: バックエンド API・ストア・配管台帳照合・Pydantic strict 検証

For **future intents** that touch these modules, rerun reverse-engineering to:
1. Validate the KPI wiring state (mock removal, `fetchKpiSummary` presence)
2. Check if `KpiData`/`KpiSummary` type contract has been unified
3. Verify test coverage remains >= 80%
4. Update architecture.md if the KPI polling flow changes

---

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: 260811-fe7-kpi-summary
fingerprint: 84be679dcff76ce096e7db318870e3b561beaca2
analyzed:
  paths:
    - backend/
    - frontend/src/
    - frontend/package.json
    - frontend/tsconfig.json
    - frontend/eslint.config.mjs
    - frontend/vitest.config.mts
    - frontend/next.config.ts
    - .github/
    - docs/
    - CLAUDE.md
    - .gitignore
  components:
    - FastAPI App (main.py)
    - Router: telemetry.py
    - Router: alerts.py
    - Router: sensors.py
    - Router: kpi.py
    - Store (store.py)
    - Service: ledger.py
    - Service: kpi.py
    - Schemas (Pydantic v2)
    - Frontend Page (page.tsx)
    - DashboardClient.tsx
    - KpiSummary.tsx
    - Header.tsx
    - AlertList.tsx
    - AlertDetailDrawer.tsx
    - SeverityBadge.tsx
    - SensorMap.tsx / SensorMapInner.tsx
    - useAlertPolling.ts
    - lib/api.ts
    - lib/severity.ts
    - lib/alertSort.ts
shallow:
  paths:
    - backend/tests/test_telemetry.py
    - backend/tests/test_pipes.py
    - backend/tests/test_simulate_sensor.py
    - backend/tests/test_dependencies.py
    - backend/tests/test_hydrants.py
    - backend/scripts/
    - frontend/src/components/__tests__/
    - frontend/public/
    - frontend/next-env.d.ts
    - frontend/postcss.config.mjs
    - docs/llm-cost.md
    - docs/code-review-closed-issues.md
    - docs/aidlc-prompt-examples.md
```
