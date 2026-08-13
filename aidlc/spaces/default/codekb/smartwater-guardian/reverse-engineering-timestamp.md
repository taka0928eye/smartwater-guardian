# SmartWater Guardian - Reverse Engineering Timestamp & Scope

## Reverse Engineering Session Metadata

**Session ID**: 260813-codekb-refresh  
**Intent**: codekb リフレッシュ（コードベース全体の最新化スナップショット）  
**Scope Type**: feature (standard depth) / ドキュメント更新  
**Performed**: 2026-08-13  
**Performed By**: 手動調査（ビルド・テスト実行は CI に委譲）  
**Repository**: smartwater-guardian (primary)  
**Base Branch**: main  
**Commit Context**: git HEAD = e7ce3e6（INFRA-1: 運用コストを抑えるインフラ構成に変更）

---

## Scope Summary

この逆リバースエンジニアリングスキャンは、**過去の codekb（2026-08-11・commit 7830301 時点で
固定）がコードベースの大幅な前進（BE-3 / BE-5 / BE-7 / BE-8 / DEMO-1 / FR-6 / INFRA-1 / E2E / FE-7）
を取りこぼしている**ため、リポジトリ全体を再スキャンして現状（commit e7ce3e6）のスナップショットを
固定する。9 知識ベース成果物をすべて書き換える。

### What Was Analyzed Deeply

1. **Backend API 一式**
   - `backend/main.py` — CORS（`ALLOWED_ORIGINS` 環境変数化）・6 ルーター登録・`RuntimeError`→502 / 例外→500 ハンドラ
   - `backend/app/routers/{telemetry,alerts,sensors,kpi,disaster,demo}.py` — 6 ルーター全実装
   - `backend/app/services/{audio,orcarouter,llm_cost,ledger,kpi,prompts}.py` — 音響解析（SVM）/ LLM 起票 / 原価算出 / 台帳照合 / KPI 算定 / プロンプト管理
   - `backend/app/schemas/{telemetry,alert,pipe,kpi,work_order,disaster,demo}.py` — Pydantic v2 スキーマ一式
   - `backend/app/store.py` — スレッドセーフなインメモリストア・マスタローダー
   - `backend/app/data/{hydrants.json,pipes.json,repair_parts.json}`・`app/models/leak_svm_v1.joblib`
   - `backend/app/dependencies.py` — `HttpClientDep`（orcarouter 用・実使用）
   - `backend/requirements.txt`・`backend/pyproject.toml`（ruff / mypy）・`backend/scripts/*`

2. **Backend テスト・環境**
   - `backend/tests/`（conftest・test_telemetry / test_alerts / test_kpi / test_store / test_ledger / test_audio / test_work_order 等）
   - `backend/requirements.txt`・`backend/.env.example`・`backend/README.md`

3. **Frontend 全体**
   - `frontend/src/app/page.tsx`（Server Component・`force-dynamic`・`MOCK_KPI_DATA` 撤去済み / `FALLBACK_SENSOR_FEATURES` 保持）
   - `frontend/src/components/dashboard/DashboardClient.tsx`（アラート 5 秒 + KPI ポーリング + 防災シミュレーション）
   - `frontend/src/components/dashboard/{KpiSummary,BusinessModelDocLink,Header}.tsx`
   - `frontend/src/components/alert/*`・`components/workorder/WorkOrderModal.tsx`・`components/chart/{SpectrumChart,WaveformChart}.tsx`
   - `frontend/src/components/map/{SensorMap,SensorMapInner,DisasterOverlay}.tsx`
   - `frontend/src/hooks/{useAlertPolling,useKpiPolling,useSensorPolling,useDisasterSummary}.ts`
   - `frontend/src/lib/{api,severity,alertSort}.ts`・`frontend/src/types/{api,sensor,disaster}.ts`
   - `frontend/src/app/api/docs/business-model/route.ts`（Next.js Route Handler）
   - `frontend/playwright.config.ts`・`frontend/tests/e2e/*`（Playwright E2E 一式）
   - `frontend/package.json`・`vitest.config.mts`・`eslint.config.mjs`・`next.config.ts`

4. **CI/CD・インフラ・ドキュメント**
   - `.github/workflows/ci.yml`（backend / frontend / **e2e** の 3 ジョブ）・`deploy.yml`（INFRA-1 AWS OIDC）
   - `infra/cloudformation/*`（00-github-oidc 〜 07-monitoring）・`infra/scripts/deploy.ps1`
   - `backend/README.md`・`frontend/README.md`・`infra/README.md`
   - `docs/`（PRD・business-model・ui-wireframe・llm-cost 等）

### What Was Skimmed (Not Deep Coverage)

- `frontend/src/components/**/__tests__/*`（テストファイルの細部）
- `frontend/coverage/`・`playwright-report/`（生成物・git 未追跡）
- `aidlc/`・`.claude/`・`.codex/`（フレームワーク内部・対象外）
- `frontend/node_modules/`・`backend/venv/`

---

## Technical Findings

### 解決済み（前回 KB の技術負債が解消）

1. **FE-7 完了** — `MOCK_KPI_DATA` 撤去・`fetchKpiSummary` 実装・`DashboardClient` での KPI ポーリング配線・
   `KpiSummary` 型の契約整合（`level1Count` 追加・`todayDetections` 除去）がすべて完了
2. **`SeverityLevel` 単一ソース化** — `lib/severity.ts` を本拠とし `types/api.ts` から re-export（FE-7 で解消）
3. **BE-3 実装** — `services/audio.py` が SVM（scikit-learn）+ FFT 解析の本実装に。`_analyze_audio_mock` を廃止
4. **BE-5 実装** — `POST /alerts/{id}/work-order` が `services/orcarouter.py` 経由で実装（LLM / フォールバック 2 モード）
5. **ruff + mypy 導入** — `pyproject.toml` 設定・CI ゲート追加（Q6: C）
6. **CORS 環境変数化** — `_get_allowed_origins()`（`ALLOWED_ORIGINS`・INFRA-1）
7. **`HttpClientDep` 実使用** — orcarouter の httpx クライアント注入に使用
8. **SciPy / scikit-learn / joblib 使用** — audio.py の DSP + SVM で実使用
9. **Recharts 使用** — SpectrumChart / WaveformChart が import・描画に使用

### 残存する技術負債

1. **フロント `SensorInfo.status` / `SensorProperties.status` が `string`** ⚠️ **LOW**
   - バックエンドは `Literal["normal","watch","warning","critical","unknown"]` を強制するが、フロント型が Literal なし
2. **`formatManYen` の丸め** ⚠️ **LOW**
   - 万円表記は `maximumFractionDigits: 1` で丸め（意図的な表示仕様。FR-6 / refined-mockups 確定）
3. **インメモリストアの非永続** ⚠️ **MEDIUM（設計判断）**
   - プロセス再起動でテレメトリ/アラート履歴が消失（デモ1日で再構築するため実害なし・CLAUDE.md §3）
4. **HTTP 暫定運用** ⚠️ **MEDIUM（INFRA-1）**
   - ドメイン未保有のため初期は HTTP のみ。WAF / Secrets Manager はコスト削減で不使用

### Code Quality Assessment

- **Type Safety**: 95%（Pydantic v2 strict・TS strict・`any` 禁止。`SensorInfo.status` の Literal 欠如のみ）
- **Test Coverage**: 80%+（CI ゲート。backend `--cov-branch --cov-fail-under=80` / frontend 4 指標 80%）
- **Linting**: ruff + mypy（BE）・ESLint 9 flat config（FE）で CI ゲート
- **Performance**: 良好（`@lru_cache` ローダー・`threading.Lock` 保護・FFT/SVM は同期 def + スレッドプール・work-order は `asyncio.Lock` + LLM キャッシュ）
- **Documentation**: 90%（docstring 日本語丁寧・Issue トレーサビリティ。README 3 本とも最新）

---

## Related Code Knowledge

The following knowledge base artifacts were synthesized from this scan and depend on the scope's accuracy:

| Artifact | Depends On | Freshness Impact |
|----------|-----------|------------------|
| business-overview.md | Core mission（安定）+ 機能一覧 | Medium |
| architecture.md | ルーター構成・KPI / 防災 / 起票フロー | **HIGH** |
| code-structure.md | モジュール構成 ← 全解析ファイル | **HIGH** |
| api-documentation.md | エンドポイント契約 ← routers/*・lib/api.ts | **HIGH** |
| component-inventory.md | 責務分担 ← services/*・routers/*・components/* | **HIGH** |
| technology-stack.md | フレームワークバージョン（安定） | Low |
| dependencies.md | import グラフ ← 全解析ファイル | **HIGH** |
| code-quality-assessment.md | テスト・デット信号 ← 全解析ファイル | **HIGH** |

**Rerun Risk**: 将来のインテントが services/orcarouter.py（LLM 起票）・services/audio.py（音響解析）・
disaster/demo ルーター・infra/ に触れる場合は再スキャンすること。特に LLM プロンプト・モデル・
コスト算出（FR-6）は要件変更の影響が大きい。

---

## Future Extension Points

### Known Out-of-Scope Items

1. **認証・権限管理**: CLAUDE.md §3 でスコープ外（ALB 配下は認証なしで公開）
2. **物理 IoT 通信プロトコル**: スコープ外（疑似センサー CLI / デモシードで代替）
3. **リアルタイム通知**: スコープ外（5 秒ポーリングで代替）
4. **本番用大型 GIS DB**: スコープ外（インメモリストア + JSON マスタ）
5. **WAF / Secrets Manager / HTTPS**: INFRA-1 ではコスト削減のため不使用（To-Be 構成に設計記録あり）

---

## Scan Methodology

**手動調査（Code Scan）**
- ファイル単位のコード精読（AST 自動解析は不使用）
- import チェーン追跡: `alerts.py → services/orcarouter.py → services/llm_cost.py → schemas/work_order.py` 等
- Pydantic モデルシグネチャ・型ヒントの検証
- カバレッジゲート（CI `--cov-branch --cov-fail-under=80`・frontend 4 指標 80%・e2e）の確認
- git 履歴（7830301 → e7ce3e6 間の差分）を基準に「解決済み負債」と「残存負債」を選別

**Quality Checks**
- 全 9 成果物の内部整合を検証（H2 見出しは component-inventory.md の codekb-scope-diff 照合対象を維持）
- Mermaid ダイアグラム構文チェック（✓）とテキスト代替の併記
- コード例が実ソースと一致（spot-check ✓）

---

## Access to Knowledge

This knowledge base (all 9 artifacts) was refreshed for the codekb 最新化 intent on 2026-08-13.
It accurately represents the codebase **at that date**（git HEAD = e7ce3e6）、covering:

- **What Changed (recent)**: BE-3（SVM 音響解析）・BE-5（Orcarouter LLM 起票）・BE-7（防災モード）・BE-8（KPI）・
  DEMO-1（デモシード）・FR-6（LLM 原価）・FE-7（KPI 配線）・FE-4（チャート）・FE-6（自動起票 UI）・
  E2E（Playwright）・INFRA-1（AWS 本番環境）・ruff+mypy・CORS 環境変数化
- **What Stays Stable**: バックエンド API 契約・インメモリストア・配管台帳照合・Pydantic strict 検証・
  深刻度モデル（Level 0〜3）

For **future intents** that touch these modules, rerun reverse-engineering to:
1. Validate the LLM 起票（orcarouter）・コスト算出（llm_cost）の実装状態
2. Check if frontend `SensorInfo.status` Literal 化が実施されたか
3. Verify test coverage remains >= 80% (backend line+branch / frontend 4 metrics)
4. Update architecture.md if the work-order / disaster flow changes

---

## Scope of Analysis

```yaml
scope_version: 2
kind: full
intent: 260813-codekb-refresh
fingerprint: e7ce3e6502474d23eecd42d3a66e7b876ea0661f
analyzed:
  paths:
    - backend/
    - frontend/src/
    - frontend/package.json
    - frontend/playwright.config.ts
    - frontend/tests/e2e/
    - frontend/tsconfig.json
    - frontend/eslint.config.mjs
    - frontend/vitest.config.mts
    - frontend/next.config.ts
    - infra/
    - .github/workflows/
    - docs/
    - CLAUDE.md
    - .gitignore
  components:
    - FastAPI App (main.py)
    - Router: telemetry.py
    - Router: alerts.py
    - Router: sensors.py
    - Router: kpi.py
    - Router: disaster.py
    - Router: demo.py
    - Store (store.py)
    - Service: ledger.py
    - Service: kpi.py
    - Service: audio.py
    - Service: orcarouter.py
    - Service: llm_cost.py
    - Service: prompts.py
    - Schemas (Pydantic v2)
    - Frontend Page (page.tsx)
    - DashboardClient.tsx
    - KpiSummary.tsx
    - BusinessModelDocLink.tsx
    - Header.tsx
    - AlertList.tsx
    - AlertDetailDrawer.tsx
    - WorkOrderModal.tsx
    - SpectrumChart.tsx / WaveformChart.tsx
    - SeverityBadge.tsx
    - SensorMap.tsx / SensorMapInner.tsx
    - DisasterOverlay.tsx
    - useAlertPolling.ts / useKpiPolling.ts / useSensorPolling.ts / useDisasterSummary.ts
    - lib/api.ts / lib/severity.ts / lib/alertSort.ts
    - app/api/docs/business-model/route.ts
    - infra/cloudformation/*.yaml
    - .github/workflows/ci.yml / deploy.yml
shallow:
  paths:
    - backend/tests/ の一部（test_audio.py / test_work_order.py 等の細部）
    - frontend/src/components/**/__tests__/
    - frontend/public/
    - frontend/coverage/
    - frontend/playwright-report/
    - docs/llm-cost.md
    - docs/code-review-closed-issues.md
```
