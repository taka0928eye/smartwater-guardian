# Build and Test Summary — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> 本サマリは `code-generation-plan.md` / `code-summary.md` を上流として、Build and Test ステージの
> 実行結果（ビルド・テスト・カバレッジ）を総括する。テスト戦略 **Standard**（aidlc-state §`**Test Strategy**`）。

## 1. ビルド状態

| 項目 | 状態 | 実測値 |
|------|------|--------|
| 依存インストール | ✅ 必要要件確認 | `npm ci` 前提（lockfile あり） |
| ESLint | ✅ PASS | `npm run lint` 終了コード 0 |
| Next.js ビルド | ✅ PASS | `npm run build`（Turbopack）`✓ Compiled successfully in 1586ms` / TS 4.1s / 静的生成 3/3 |
| ルート生成 | ✅ PASS | `/` サーバーコンポーネント生成（page.tsx は Server Component のまま維持、C-2） |

## 2. テスト種別インベントリ（Standard 戦略で生成）

| テスト種別 | 指示書 | 生成 |
|------------|--------|------|
| ユニットテスト | `unit-test-instructions.md` | ✅（11 ファイル / 91 テスト） |
| 統合テスト | `integration-test-instructions.md` | ✅（フロント内部境界: page → DashboardClient → KpiSummary） |
| 性能テスト | `performance-test-instructions.md` | —（Comprehensive 戦略限定。NFR 性能要件は本スコープ外） |
| セキュリティテスト | `security-test-instructions.md` | —（Comprehensive 戦略限定。デモスコープ / 認証なし / PII なし） |

> バックエンド統合境界（TestClient）は既存 `backend/tests/test_alerts.py` が BE-8 で実質カバー済み
> （project.md build-and-test:c4 と整合）。

## 3. テスト実行結果（実測）

| 指標 | 実測値 | 閾値（NFR-1） | 結果 |
|------|--------|---------------|------|
| テスト数 | 11 ファイル / **91 テスト全 Green** | — | ✅ PASS |
| Statements | **93.15%**（204/219） | ≥ 80% | ✅ |
| Branches | **84.15%**（85/101） | ≥ 80% | ✅ |
| Functions | **90.12%**（73/81） | ≥ 80% | ✅ |
| Lines | **94.05%**（190/202） | ≥ 80% | ✅ |

- カバレッジゲートは `vitest.config.mts` の thresholds を単一ソースとし、ローカル `npm run test` と
  CI（`.github/workflows/ci.yml` の `npm run test`）で一致（NFR-1 / team-practices Q3=A）。

## 4. ユニット別カバレッジ期待値 vs 実測

| ユニット | 期待（指示書 §3） | 実測（HTML レポート） |
|----------|-------------------|----------------------|
| `lib/api.ts` | 100% | ✅ 100% |
| `lib/severity.ts` | 83.33% | ✅ 83.33% |
| `hooks/useKpiPolling.ts` | 100% | ✅ 100% |
| `components/dashboard/KpiSummary.tsx` | 100% | ✅ 100% |
| `components/dashboard/DashboardClient.tsx` | 92.85% | ✅ 92.85% |
| `app/page.tsx` | 100% | ✅ 100% |
| `types/api.ts` | 型のみ | 計測対象外 |

## 5. レディネス評価

| 観点 | 評価 | 根拠 |
|------|------|------|
| Build-ready | ✅ | lint + 型チェック + プロダクションビルド成功 |
| Test-ready | ✅ | 91 テスト全 Green・4 指標 80% 超（ゲート一致） |
| Deployment-ready | ⚠️ 条件付き | デモはローカル実行を主とし、余裕があれば AWS へ（team.md Deployment）。本番 CD パイプラインは未整備 |

## 6. 既知の制約・残課題

- **out-of-order 制約（既知・許容済み）**: `useKpiPolling` の `setInterval` は前回 in-flight 完了を
  待たず次回発火する（レスポンス > 5s 時に古いレスポンスが新しい値を上書きしうる）。既存
  `useAlertPolling` と同型の既知制約でデモスコープでは許容。将来はリクエスト連番で対策。
- **非スコープファイルの個別カバレッジ**: `SensorMap.tsx`（60%）等の既存非対象ファイルは個別に
  80% 未達だが、グローバル閾値のためゲート通過。本件スコープ外として据え置き。
- **バックエンド**: 変更対象外（BU-1 はフロントのみ）。ビルド・テスト指示書はフロント対象に限定。
- **コミット未実施**: ユーザー指示なし。CI Pipeline ステージ後のコミットを想定。
