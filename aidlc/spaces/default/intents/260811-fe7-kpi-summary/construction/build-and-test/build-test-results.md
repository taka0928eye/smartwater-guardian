# Build Test Results — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> Build and Test ステージ Step 10（Execute Build and Tests）の実測結果。
> 実行日時: 2026-08-11T10:35:06Z（リポジトリルート `C:\workspace\smartwater-guardian`、branch main）。

## 1. ビルド結果

### 1.1 ESLint（`cd frontend && npm run lint`）
```
> frontend@0.1.0 lint
> eslint
```
- 結果: **PASS**（終了コード 0・警告 0）

### 1.2 Next.js ビルド（`cd frontend && npm run build`）
```
▲ Next.js 16.3.0 (Turbopack)
✓ Compiled successfully in 1586ms
  Running TypeScript ...
  Finished TypeScript in 4.1s ...
  Generating static pages using 5 workers (0/3) ...
✓ Generating static pages using 5 workers (3/3) in 956ms

Route (app)
┌ ƒ /
└ ○ /_not-found
```
- 結果: **PASS**（コンパイル成功・TS 型検査成功・静的生成 3/3）

## 2. テスト結果（`cd frontend && npm run test`）

```
Test Files  11 passed (11)
     Tests  91 passed (91)
  Duration  8.03s (transform 1.36s, setup 8.94s, import 2.64s, tests 3.23s, environment 24.44s)
```

### 2.1 サマリ

| 項目 | 値 |
|------|-----|
| テストファイル | 11 |
| 実行テスト | 91 |
| 成功 | 91 |
| 失敗 | 0 |
| スキップ | 0 |
| 状態 | **全 Green** |

### 2.2 失敗詳細

なし（失敗テスト 0 件）。

## 3. カバレッジレポート（V8）

| 指標 | 実測値 | 閾値（NFR-1） | 結果 |
|------|--------|---------------|------|
| Statements | **93.15%**（204/219） | ≥ 80% | ✅ |
| Branches | **84.15%**（85/101） | ≥ 80% | ✅ |
| Functions | **90.12%**（73/81） | ≥ 80% | ✅ |
| Lines | **94.05%**（190/202） | ≥ 80% | ✅ |

### 主要ファイル別（コンソールレポートより抜粋）

| ファイル | % Stmts | % Branch | % Funcs | % Lines |
|----------|---------|----------|---------|---------|
| `components/dashboard/DashboardClient.tsx` | 92.85 | 91.66 | 83.33 | 91.66 |
| `components/dashboard/Header.tsx` | 83.33 | 100 | 62.5 | 86.95 |
| `components/map/SensorMap.tsx` | 60 | 100 | 33.33 | 60 |
| `components/map/SensorMapInner.tsx` | 90.62 | 66.66 | 91.66 | 89.28 |
| `hooks/useAlertPolling.ts` | 91.66 | 50 | 100 | 100 |
| `lib/api.ts` | 100 | 93.33 | 100 | 100 |
| `lib/severity.ts` | 83.33 | 100 | 80 | 83.33 |

> FE-7 の新規・主要対象ファイル（`useKpiPolling.ts` / `KpiSummary.tsx` / `app/page.tsx`）は
> HTML レポート（`frontend/coverage/`）で個別 100% を確認済み。コンソール出力は 10 ファイルまで
> の表示制限があるため、これらは非表示となる（code-generation 時の知見と同様）。

### 3.1 ゲート判定

- `vitest.config.mts` の thresholds（lines / functions / branches / statements 各 80）に対し、
  4 指標すべて超過 → **カバレッジゲート PASS**。
- ローカル実行（`npm run test`）と CI（`.github/workflows/ci.yml` の `npm run test`）で同一ゲート。

## 4. 診断・修正履歴

- ビルド・テストとも初回実行で成功。修正・再実行は不要。
- 既知の許容制約: `useKpiPolling` の out-of-order（`build-and-test-summary.md` §6 参照）。

## 5. 結論

BU-1（FE-7）は **build-ready / test-ready**。ビルド（lint + build）・テスト（91 Green）・カバレッジ
（4 指標 80% 超）をすべて満たし、`ci-pipeline` ステージへ進む準備が整った。
