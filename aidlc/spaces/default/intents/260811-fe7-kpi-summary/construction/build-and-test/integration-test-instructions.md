# Integration Test Instructions — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> 本指示書は `code-generation-plan.md`（BU-1 境界・US-1〜4）と `code-summary.md`
> （相互依存ファイルの単一 proto-Unit 方針、project.md scope-definition:c1）に基づく
> 統合境界テストの実行手順書。テスト戦略 **Standard**（主要境界・クロスユニット相互作用）。

## 1. 統合境界の定義

BU-1 はフロントエンドのみの変更であり、**フロント内部の統合境界**を対象とする：

```
app/page.tsx（Server Component）
  └─ DashboardClient.tsx ── useKpiPolling.ts ── lib/api.ts（fetchKpiSummary）
                                   │
                          components/dashboard/KpiSummary.tsx
```

- 外部 API（axios）は `vi.mock("@/lib/api")` の境界モックで遮断する。
- バックエンド統合境界は既存 `backend/tests/test_alerts.py`（TestClient エンドポイントテスト）が
  BE-8 で実質カバー済み（project.md build-and-test:c4 と整合）。本件では追加しない。

## 2. 実行コマンド

```powershell
cd frontend
npm run test                     # 全テスト（ユニット + 統合）を一度に実行
npm run test -- DashboardClient  # 統合境界テストのみ抽出
npm run test -- page             # ルート連携テストのみ抽出
```

## 3. 対象テスト（クロスユニット相互作用）

### 3.1 `DashboardClient.test.tsx`（FR-7 / US-3）
`useKpiPolling`（フック）→ `KpiSummary`（表示）→ ランドマーク所有の相互作用：
- [ ] KPI section のランドマーク（`section[aria-labelledby="kpi-summary-title"]` / `h2` / `aria-busy`）が
  `DashboardClient` に一元所有され、スケルトン中も維持される
- [ ] ポーリング成功で `kpi-skeleton` からカードグリッドへ切替（KpiSummary 実物が描画される）
- [ ] ポーリング失敗で再スケルトン（`kpi-skeleton` 復帰・stale 値非表示）

### 3.2 `page.test.tsx`（FR-4 / US-2・US-3）
Server Component（page.tsx）→ DashboardClient のデータフロー：
- [ ] 実データ（fetchSensorsGeoJson）が SensorMap へ渡され描画される
- [ ] 取得失敗時フォールバック（モック GeoJSON）で描画される
- [ ] モック KPI 由来の固定数値（`1,420,000` / `1,240` 等）が描画されない（C-4 / project.md Forbidden）

## 4. 期待カバレッジ

- 統合境界テストはグローバル 80% ゲートに寄与する（`DashboardClient.tsx` 92.85% / `page.tsx` 100%）。
- 外部 API モック境界の変換（`lib/api.ts` snake_case→camelCase）はユニットテスト（`api.test.ts`）で 100% 担保。

## 5. テストデータ管理

- `vi.mock("@/lib/api")` はテストファイルごとに宣言し、解決値を明示（`fetchKpiSummary` は BE-8 契約の 7 フィールドを camelCase で返す）。
- `act()` で非同期描画をフラッシュし、ポーリング初回の発火を待つ。
- テスト分離はファイルごとのモック再定義 + `vi.clearAllMocks()` で担保。

## 6. カバレッジ目標

- 統合境界テストを含む全テストで **4 指標各 80% 以上**（NFR-1。`vitest.config.mts` thresholds で強制）。
- バックエンド境界（BE-8）は変更対象外のため、本ステージのカバレッジ計測対象に含めない。
