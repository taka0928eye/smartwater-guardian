# Unit Test Instructions — SmartWater Guardian（BE-8 KPI サマリ）

> テスト戦略: **Minimal（要求駆動）**。BE-8 の受け入れ条件（S-1〜S-6, D-1〜D-3）を直接検証する
> ユニットテストのみを作成・維持する（プロジェクト学習済みルール c1）。統合・性能・セキュリティの
> テスト指示書はスキップする — 統合境界は TestClient のエンドポイントテスト（`test_kpi.py` の
> `TestKpiSummaryEndpoint`）が実質カバーする（学習済みルール c4）。

## フレームワーク・設定

| 項目 | 値 |
|------|-----|
| フレームワーク | pytest 9.1 |
| テスト配置 | `backend/tests/test_kpi.py` |
| 共有フィクスチャ | `backend/tests/conftest.py`（`client` / `store` / autouse `_reset_store`） |
| カバレッジ基準 | プロジェクト全体で **80% 以上**（品質基準） |

> Pydantic 型制約（`ge=0` / strict / `extra="forbid"`）の検証は、プロジェクトに mypy 等の静的型
> チェッカーが存在しないため、実際に `ValidationError` が送出されることを確認するランタイムテストで
> 代替する（学習済みルール asc-c4）。

## 実行方法

```powershell
# backend ディレクトリで（pytest.exe ではなく python.exe -m pytest を使う）
.\venv\Scripts\python.exe -m pytest tests/test_kpi.py -v
```

全テスト・カバレッジ:

```powershell
.\venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

## テスト要件（受け入れ条件 → テスト）

### 1. 単価計算 `expected_cost_saved()`（S-5 / D-1 / §3.3）

`docs/business-model.md` §3 の式が単価を返すこと。

| テスト | 入力 | 期待値 |
|--------|------|--------|
| `test_level0_is_zero` | `0` | `0`（正常。回避コストなし） |
| `test_level1_matches_formula` | `1` | `121_800`（= 0.12 × (1,200,000 − 185,000)） |
| `test_level2_matches_formula` | `2` | `308_000`（= 0.35 × (1,200,000 − 320,000)） |
| `test_level3_is_fixed_response_saved` | `3` | `150_000`（固定 C_response_saved） |

### 2. サマリ集計 `calculate_kpi_summary()`（S-2 / S-3 / S-4）

アラート実データ（インメモリストア）から集計し、固定値を返さないこと。

| テスト | 検証内容 |
|--------|----------|
| `test_aggregates_from_store_data` | デモ内訳（L1×8 / L2×3 / L3×1）→ 件数 `8/3/1` と合計 `2_048_400`。`total_sensors` は `len(get_hydrants())`（実件数10）と一致。`is_estimate=True` / `assumption_doc` を検証（S-2 / S-3 / S-5） |
| `test_empty_store_returns_zero_counts_with_real_sensor_count` | 空ストアでも 500 にせず全項目0・`total_sensors` のみ実件数（S-4） |
| `test_level0_only_store_counts_zero` | Level 0（正常）は集計対象外。カウント・コストとも0 |

### 3. エンドポイント `GET /api/v1/kpi/summary`（S-1 / S-4 / S-5 / 統合境界）

| テスト | 検証内容 |
|--------|----------|
| `test_returns_200_with_seven_fields` | 200 と7項目（5項目 + `is_estimate` / `assumption_doc`）を返す（S-1） |
| `test_seeded_store_returns_demo_total` | シード済みストアでデモ内訳合計 `2_048_400` を返す（S-5） |
| `test_empty_store_returns_200_with_zeros` | 空ストアでも 200 で全項目0・`total_sensors=10`（S-4、500にしない） |

### 4. スキーマ型制約（asc-c4 ランタイム検証 / D-3）

`KpiSummary` の型制約が実際に `ValidationError` を送出すること。

| テスト | 検証内容 |
|--------|----------|
| `test_negative_count_rejected` | `level1_count=-1` が弾かれる（`ge=0`） |
| `test_negative_cost_rejected` | `estimated_cost_saved_yen=-1` が弾かれる |
| `test_wrong_type_rejected` | `total_sensors="ten"` が弾かれる（strict のため暗黙キャストなし） |
| `test_extra_field_rejected` | `today_detections` 等の契約外フィールドが弾かれる（`extra="forbid"` / D-3） |

## 合格基準

- `test_kpi.py` の全テスト（14件）が Green
- プロジェクト全体のカバレッジ **80% 以上**（BE-8 実測: 99%）
- テストは `conftest.py` の autouse `_reset_store` により実行順に依存しない（独立・再現可能）

## データ管理

- ストアは `store` フィクスチャ経由でシードする（`make_record()` / `seed_demo_alerts()`）。
- autouse の `_reset_store` が各テスト前にインメモリストアをリセットし、テスト間を完全に隔離する。
- 外部サービス・DB への接続は不要（インメモリのみ）。
