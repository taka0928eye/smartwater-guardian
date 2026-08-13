# SmartWater Guardian - コード品質評価

## 総合評価

| 次元 | 評価 | 所見 |
|------|------|------|
| 型安全性 | 良好 | Pydantic v2 strict / extra=forbid。フロント TS strict。`any` 禁止。`SensorInfo.status` の Literal 欠如のみ残存 |
| テストカバレッジ | 良好 | CI ゲート（backend 行+branch 80% / frontend 4 指標 80%）+ E2E（Playwright） |
| リント | 良好 | ruff + mypy（BE）・ESLint 9 flat config（FE）で CI ゲート |
| ドキュメント | 良好 | docstring は日本語で丁寧・Issue トレーサビリティあり。README 3 本（backend / frontend / infra）とも最新 |
| エラーハンドリング | 良好 | 入力境界で検証、API エラーは 404 / 422 / 501 / 502 に整理。RuntimeError→502・例外→500（構造化）。LLM はフォールバック |
| 保守性 | 良好 | ルーター/サービス/ストアの3層・責務分離。フロントは表示・ロジック・境界変換・フックを分離 |
| 性能 | 良好 | `@lru_cache` ローダー・`threading.Lock` 保護・FFT/SVM はスレッドプール・LLM はキャッシュ + `asyncio.Lock` |
| セキュリティ | 良好 | 入力検証は強固。CORS は環境変数化。Leaflet popup は XSS エスケープ。認証・HTTPS はスコープ外（CLAUDE.md §3） |

## テストカバレッジと CI/CD

### CI ゲート（.github/workflows/ci.yml・3 ジョブ）
- **backend-test**: `ruff check` → `mypy` → `check_telemetry.py` / `check_kpi.py` / `check_disaster.py`
  → `python -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=80`
- **frontend-test**: `npm run lint` → `npm run test`（vitest + coverage thresholds 4 指標 80%）→ `npm run build`
- **e2e-test**（backend / frontend 成功後）: `npx playwright install --with-deps chromium` → `npm run e2e` → playwright-report アップロード
- main push / PR で実行。カバレッジ成果物（backend/coverage.xml・frontend/coverage/）をアップロード

### テスト構成（backend）
- `conftest.py` が `client` / `store` フィクスチャ + autouse の `_reset_store` で隔離
- 主要テスト: `test_telemetry`（SVM 解析経路）・`test_alerts`（一覧/詳細/seed）・`test_work_order`（LLM / フォールバック）・
  `test_audio`（SVM + バリデーション）・`test_kpi`・`test_store`・`test_ledger`・`test_disaster`・`test_demo` 等
- `test_kpi.py` は「単価計算 → サマリ集計 → エンドポイント（TestClient 統合境界）→ スキーマ型制約」を TDD 検証

### テスト構成（frontend）
- Vitest + jsdom + @testing-library/react（component / hook / lib テスト）
- E2E: Playwright（`tests/e2e/`）。`global-setup.ts` がバックエンド起動確認 + `POST /alerts/seed` でシード投入。
  projects は `main`（testIgnore: disaster.spec.ts）→ `disaster`（dependencies）の順。webServer で
  backend（uvicorn・`ORCAROUTER_ENABLED=false`）+ frontend（`next start`）を自動起動

### デプロイ（.github/workflows/deploy.yml・INFRA-1）
- `workflow_dispatch`（environment: dev / staging / prod）。OIDC ロール引き受け → ECR ビルド/プッシュ →
  ECS タスク定義更新 → `services-stable` 待ち

## ドキュメント品質

- **docstring**: 日本語で丁寧。ルーターはスレッドプール実行・エラー設計・座標順序・FR-6 原価など理由を含む
- **トレーサビリティ**: Issue 参照（BE-1〜BE-8 / FE-1〜FE-7 / OR-* / DEMO-1 / INFRA-1 / FR-6）を docstring に明記
- **README**: backend / frontend / infra の 3 本が現状（BE-3〜BE-8・DEMO-1・E2E・INFRA-1・FR-6）を反映

## 技術負債シグナル

### 解決済み（前回 KB 時点の負債が解消）

1. ~~`page.tsx` のモック KPI 硬コード~~ → FE-7 で撤去。`DashboardClient` + `useKpiPolling` が実データ配線
2. ~~`fetchKpiSummary` 未実装~~ → lib/api.ts に実装済み
3. ~~`KpiData` 型とバックエンド契約の乖離~~ → `types/api.ts` の `KpiSummary` が 7 フィールド契約と一致（`level1Count` 追加）
4. ~~`SeverityLevel` 二重定義~~ → `lib/severity.ts` を本拠とし `types/api.ts` から re-export（FE-7 で解消）
5. ~~BE-3 `services/audio.py` 未実装~~ → SVM + FFT の本実装に。`_analyze_audio_mock` を廃止
6. ~~`WorkOrder` 契約の先取り（501 スタブ）~~ → BE-5 で実装。`services/orcarouter.py` が LLM / フォールバック
7. ~~`HttpClientDep` 未使用~~ → orcarouter の httpx クライアント注入に実使用
8. ~~CORS 硬コード~~ → `_get_allowed_origins()`（`ALLOWED_ORIGINS` 環境変数・INFRA-1）
9. ~~ruff / mypy 未導入~~ → `pyproject.toml` 設定 + CI ゲート追加（Q6: C）
10. ~~SciPy 未使用~~ → audio.py の DSP で使用。scikit-learn / joblib も追加

### 残存する技術負債

1. **フロント `SensorInfo.status` / `SensorProperties.status` が `string`** ⚠️ **LOW**
   - バックエンドは `Literal["normal","watch","warning","critical","unknown"]` を強制するが、フロント型が Literal なし
2. **インメモリストアの非永続** ⚠️ **MEDIUM（設計判断）**
   - プロセス再起動でテレメトリ/アラート履歴が消失（デモ1日で再構築するため実害なし。CLAUDE.md §3）
3. **防災シミュレーションのキャッシュ** ⚠️ **LOW**
   - `/tmp/disaster_simulated_items.json` は単一ホスト前提（ローカル/ECS タスク 1 のため実害なし）
4. **HTTP 暫定運用** ⚠️ **MEDIUM（INFRA-1）**
   - ドメイン未保有のため初期は HTTP のみ。WAF / Secrets Manager はコスト削減で不使用（To-Be 構成に記録）
5. **`today_detections` の未採用** ⚠️ **LOW**
   - スキーマ契約外として明記済み。将来 KPI に追加する場合は BE-8 / FE-7 両方の更新が必要

## 改善推奨（優先度順）

1. **`SensorInfo.status` の Literal 化**: バックエンド契約とフロント型を一致させる（契約層 re-export）
2. **防災シミュレーションの冪等性**: `/tmp` キャッシュの寿命・多重投入時の重複クラスタ対策を整理
3. **LLM 原価の可視化強化**: `docs/llm-cost.md` の実測値と WorkOrderModal の表示を定期的に照合
4. **生成物のクリーンアップ**: `frontend/coverage/`・`playwright-report/`・`tsconfig.tsbuildinfo` の .gitignore を精査

## 品質スコア（目安）

```
型安全性          95%  (SensorInfo.status の Literal 欠如のみ)
テストカバレッジ  80%+ (CI ゲート達成・E2E 追加)
ドキュメント       90%  (docstring 丁寧・README 3 本最新)
エラーハンドリング 95%  (境界検証・HTTP 状態整理・LLM フォールバック)
保守性            90%  (3層分離・責務分離・フック分離)
性能              95%  (lru_cache・Lock・スレッドプール・LLM キャッシュ)
```

**注記**: 本 KB は reverse-engineering 時点（2026-08-13・git HEAD = e7ce3e6）で固定される。LLM 起票
（orcarouter）・音響解析（audio）・防災（disaster）・インフラ（infra/）に触れるインテントは実装前に
現状コードを grep 等で再確認すること（project.md 学習: codekb スナップショットは RE 時点で古くなりうる）。
