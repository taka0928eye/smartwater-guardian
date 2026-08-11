# Code Summary — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

| 項目 | 内容 |
|------|------|
| ユニット | `be8-kpi-summary`（単一イテレーション / 単一論理ユニット） |
| テスト戦略 | Minimal（要求駆動） |
| 手法 | TDD（Red → Green → Refactor）を全ステップで徹底 |

## 生成・変更ファイル

| 種別 | ファイル | 内容 |
|------|----------|------|
| 新規スキーマ | `backend/app/schemas/kpi.py` | `KpiSummary`（5項目 + `is_estimate` / `assumption_doc`、Pydantic v2 / `STRICT_INPUT_CONFIG`） |
| 新規サービス | `backend/app/services/kpi.py` | 算定定数を1箇所に定義 + `expected_cost_saved()` + `calculate_kpi_summary()` |
| 新規ルーター | `backend/app/routers/kpi.py` | `GET /api/v1/kpi/summary`（同期 `def`、`response_model=KpiSummary`） |
| 新規テスト | `backend/tests/test_kpi.py` | 単価計算 / サマリ集計 / エンドポイント統合 / スキーマ型制約の14件 |
| 既存修正 | `backend/main.py` | `app.routers` に `kpi` を追加し `app.include_router(kpi.router)` を登録 |

フロント（`frontend/src/app/page.tsx` の `MOCK_KPI_DATA`）はスコープ外のため変更していない。

## 主要な実装決定

- **定数の一元管理（D-2 / §3.2）**: `C_BURST` / `C_REPAIR_LEVEL1/2` / `P_LEVEL1/2` / `C_RESPONSE_SAVED` を `app/services/kpi.py` の1箇所に定義。フロントは算出済みの値のみ受け取る。
- **深刻度の再利用（D-1）**: `expected_cost_saved(severity_level: SeverityLevel)` は既存 `SeverityLevel`（Literal[0,1,2,3]）のみ受け付け、未対応値は `ValueError`。Level 0 は正常のため0円。
- **実データ集計（S-2）**: `get_store().list_alerts()` を**ハンドラ実行時に**呼び、レベル別件数と期待回避コスト合計を算出（import 時捕捉はテスト隔離を壊すため store.py の流儀に従う）。固定値は返さない。
- **total_sensors は実件数（S-3）**: `get_hydrants()`（`@lru_cache` 済みローダー）の件数をそのまま利用。
- **試算値の常時明示（§3.5）**: `is_estimate=True` と `assumption_doc="docs/business-model.md §3"` を必ず付与し、根拠のない金額を断定的に見せない。
- **500 にしない（S-4）**: 組み立てはサービスのみで完結し、ルーターは `HTTPException` を上げない。空ストアでも 200 で全項目0（`total_sensors` のみ実件数）を返す。
- **エンドポイントは同期 `def`**: FastAPI のスレッドプールで実行（軽量・インメモリ参照のため）。

## テストカバレッジ

- 全テスト: **123 passed（`--cov=app` で 99% カバレッジ）** — 品質基準 80% を満たす。
- `tests/test_kpi.py`: 14 件（単価計算 4 / サマリ集計 3 / エンドポイント 3 / スキーマ型制約 4）。
- 型安全性の受入条件は、プロジェクト学習済みルールに従い Pydantic の型制約（`ge=0` / strict / `extra="forbid"`）が実際に `ValidationError` を送出するランタイムテストで検証（`TestKpiSummarySchema`）。

## プランからの逸脱

- **逸脱なし**。計画どおり 8 ステップ（スキーマ → 単価計算テスト → 算定サービス → サマリ計算テスト → サマリ組み立て → エンドポイントテスト → ルーター+main.py 登録 → 自走確認）を完遂。
- 検証スクリプト（`scripts/check_*.py`）は作成しない（S-5 は pytest のエンドポイントテストで実値検証するため計画どおり）。
- `linter` / `type-check` センサーは対象外（本ステージは Python のみの変更で、**/*.{ts,tsx} に該当なし）。
