# SmartWater Guardian - コード品質評価

## 総合評価

| 次元 | 評価 | 所見 |
|------|------|------|
| 型安全性 | 良好 | Pydantic v2 strict / extra=forbid。フロント TS strict。ただし FE-7 の KPI 契約乖離・`SensorInfo.status` の Literal 欠如あり |
| テストカバレッジ | 良好 | CI ゲート（backend 80% / frontend 80% thresholds）。`any` 使用なし |
| リント | 良好（FE）/ 未設定（BE） | ESLint 9 flat config で CI ゲート。Python 側は ruff / mypy 未導入 |
| ドキュメント | 良好 | docstring は日本語で丁寧・Issue トレーサビリティあり。`backend/README.md` のスコープ記載は BE-6 までで陳腐化 |
| エラーハンドリング | 良好 | 入力境界で検証、API エラーは 404 / 422 / 501 に整理（500 にしない設計） |
| 保守性 | 良好 | ルーター/サービス/ストアの3層・責務分離。フロントは表示・ロジック・境界変換を分離 |
| 性能 | 良好 | `@lru_cache` ローダー・`threading.Lock` 保護・FFT はスレッドプール |
| セキュリティ | 部分 | 入力検証は強固。認証・HTTPS はスコープ外（CLAUDE.md §3）。CORS は開発用に硬コード |

## テストカバレッジと CI/CD

### CI ゲート（.github/workflows/ci.yml）
- **backend-test**: `python -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80`
- **frontend-test**: `npm run lint` → `npx vitest run --coverage`（lines / functions / branches / statements 各 80%）→ `npm run build`
- main push / PR で実行。カバレッジ成果物（backend/coverage.xml・frontend/coverage/）をアップロード

### テスト構成（backend）
- 9 ファイル: `test_alerts` / `test_kpi` / `test_store` / `test_ledger` / `test_telemetry` / `test_pipes` / `test_hydrants` / `test_dependencies` / `test_simulate_sensor`
- `conftest.py` が `client` / `store` フィクスチャ + autouse の `_reset_store` で隔離
- `test_kpi.py` は「単価計算 → サマリ集計 → エンドポイント（TestClient 統合境界）→ スキーマ型制約」を 4 クラスで TDD 検証

### テスト構成（frontend）
- `lib/__tests__/api.test.ts`・`app/__tests__/page.test.tsx` 全文＋ `KpiSummary` / `DashboardClient` / `alertSort` 等
- Vitest + jsdom + @testing-library/react

## ドキュメント品質

- **docstring**: 日本語で丁寧。ルーターはスレッドプール実行・エラー設計・座標順序など理由を含む
- **トレーサビリティ**: Issue 参照（BE-1 / BE-4 / BE-6 / BE-8 / FE-2 / FE-3 / FE-5 等）を docstring に明記
- **陳腐化**: `backend/README.md` のスコープ記載が BE-6 まで（BE-8 の KPI 反映済みかを要確認）

## 技術負債シグナル

### FE-7 ギャップ（アクティブインテントの対象）— 本 KB の主眼

1. **`page.tsx` のモック KPI 硬コード**（`MOCK_KPI_DATA`）
   - `totalSensors: 1240` 等の固定値を `KpiSummary` へ渡している。実データ不在のカードは撤去し、
     実データで埋められるカード（BE-8 の `level1_count` 等）へ構成を揃える方針（feasibility 学習済み）
2. **`fetchKpiSummary` 未実装**（lib/api.ts）
   - BE-8 の `GET /api/v1/kpi/summary` は実装済みだが、フロントの API 関数・型が存在しない
3. **`KpiData` 型とバックエンド契約の乖離**
   - `KpiData`（5 項目: totalSensors / level3Count / level2Count / todayDetections / estimatedCostSavedYen）は
     バックエンド `KpiSummary`（7 項目）と非整合。`level1Count` を欠き、`today_detections`（D-3 契約外）を含む

### その他の技術負債

4. **`SeverityLevel` 二重定義**（types/api.ts と lib/severity.ts）
   - 単一ソース化は表示メタ（SEVERITY_META 等）と同居する lib/severity.ts を本拠とし、types/api.ts から re-export する方針（feasibility 学習済み）
5. **`SensorInfo.status` / `SensorProperties.status` が `string`**（フロント）
   - バックエンドは `Literal["normal","watch","warning","critical","unknown"]` を強制するが、フロント型が Literal なし
6. **BE-3 `services/audio.py` 未実装のまま docstring 参照が残る**
   - telemetry.py の `_analyze_audio_mock` が仮実装として代行。SciPy は未使用
7. **将来契約の先取り**（`WorkOrder` / `RepairPart` / `Urgency` / `WorkOrderSource`）
   - フロント types/api.ts に定義済みだが、バックエンドは `POST .../work-order` を 501 で返すだけ
8. **`HttpClientDep` 未使用**（app/dependencies.py）
   - BE-5 / Orcarouter 用の先取り。現状どのルーターも使っていない
9. **CORS `allow_origins` 硬コード**（main.py）
   - `["http://localhost:3000"]` を直書き。環境変数化は未実施
10. **生成物の混在**: `frontend/coverage/`・`tsconfig.tsbuildinfo` 等がリポジトリに残りうる（.gitignore 要確認）

## 改善推奨（優先度順）

1. **FE-7（本インテント）**: `fetchKpiSummary` 実装・`KpiData` の契約整合・`DashboardClient` でのポーリング配線・`MOCK_KPI_DATA` 撤去
2. **型の単一ソース化**: `SeverityLevel` を lib/severity.ts に集約し types/api.ts から re-export
3. **`SensorInfo.status` の Literal 化**: バックエンド契約とフロント型を一致させる
4. **Python リント導入**: ruff（+ 必要なら mypy）を CI に追加
5. **CORS 設定の環境変数化**・**生成物のクリーンアップ**（.gitignore 精査）
6. **BE-3 / BE-5 の実装**: audio.py（SciPy 導入）・work-order の Orcarouter 連携

## 品質スコア（目安）

```
型安全性          75%  (KPI 契約乖離・status Literal 欠如・SeverityLevel 二重定義)
テストカバレッジ  80%+ (CI ゲート達成)
ドキュメント       80%  (docstring 丁寧・README 一部陳腐化)
エラーハンドリング 90%  (境界検証・HTTP 状態整理)
保守性            80%  (3層分離・責務分離)
性能              90%  (lru_cache・Lock・スレッドプール)
```

**注記**: 本 KB は reverse-engineering 時点（2026-08-11）で固定される。FE-7 の実装後は
「モック KPI 撤去・fetchKpiSummary 実装・KpiData 契約整合」の状態を再検証すること
（project.md 学習済み: codekb スナップショットは RE 時点で古くなりうるため、実装前に grep 等で現状確認）。
