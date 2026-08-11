# Code Generation Plan — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

| 項目 | 内容 |
|------|------|
| ユニット | `be8-kpi-summary`（単一イテレーション / 単一論理ユニット） |
| テスト戦略 | Minimal（要求駆動のユニットテスト、コンポーネント毎にハッピーパス下限） |
| 手法 | TDD（Red → Green → Refactor）を各ステップで徹底 |
| 言語 / 規約 | Python 3.11 / Pydantic v2（STRICT_INPUT_CONFIG）/ コメント・ドキュメントは日本語 / `any` 禁止 |

## 成果物マップ

| 種別 | ファイル | 対応 |
|------|----------|------|
| 新規スキーマ | `backend/app/schemas/kpi.py` | `KpiSummary`（レスポンス5項目 + `is_estimate`・`assumption_doc`） |
| 新規サービス | `backend/app/services/kpi.py` | 算定定数（1箇所）+ E_avoided 計算 + サマリ組み立て |
| 新規ルーター | `backend/app/routers/kpi.py` | `GET /api/v1/kpi/summary` |
| 新規テスト | `backend/tests/test_kpi.py` | 単価計算・サマリ計算・エンドポイント統合テスト |
| 既存修正 | `backend/main.py` | `kpi.router` の登録 |

> フロント（`frontend/src/app/page.tsx` の `MOCK_KPI_DATA`）は**変更しない**（スコープ外）。
> 本ステージは Python のみの変更のため、`linter` / `type-check` センサー（**/*.{ts,tsx}）は該当なし。

## トレーサビリティ（要求 → 実装ステップ）

Inception がスキップ（Minimal スコープ）のため、イデエーション段階の成功指標・決定（decision-log.md D-1〜D-4）へ対応付ける:

| 要求 | 内容 | 実装ステップ |
|------|------|--------------|
| S-1 | 200 と5項目（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen`）+ `is_estimate`・`assumption_doc` を返す | Step 1, 5, 6 |
| S-2 | KPI はアラート実データ（インメモリストア）から算出し、固定値を返さない | Step 2, 3, 4, 5 |
| S-3 | `total_sensors` は `hydrants.json` 実件数（現状10件）と一致 | Step 3, 6 |
| S-4 | 空ストアでも 200 で全項目0（500にしない） | Step 4, 6 |
| S-5 | デモ内訳（L1×8, L2×3, L3×1）で合計 2,048,400 円 | Step 2, 3, 6 |
| S-6 | pytest カバレッジ 80% 以上 | Step 7 |
| D-1 | 深刻度は既存 `SeverityLevel`（Literal[0,1,2,3]）を再利用 | Step 2, 3 |
| D-2 | 定数はバックエンドの1箇所に定義（business-model.md §3.5） | Step 3 |
| D-3 | `today_detections` は今回の対象外 | 実装しない（計画外） |

---

## 実装ステップ（TDD 順序）

### Step 1: スキーマ `app/schemas/kpi.py`（Green の土台）

- [x] `KpiSummary`（Pydantic v2、`STRICT_INPUT_CONFIG`）を定義
  - `total_sensors: int`（`ge=0`）
  - `level1_count: int`（`ge=0`）
  - `level2_count: int`（`ge=0`）
  - `level3_count: int`（`ge=0`）
  - `estimated_cost_saved_yen: int`（`ge=0`）
  - `is_estimate: bool`（試算値である旨を常時明示）
  - `assumption_doc: str`（`docs/business-model.md §3` を参照）
  - 各フィールドに `Field(description=...)` を付与（`app/schemas/alert.py` の流儀）

> 本ステップは Step 4/6 のテスト・実装が依存する型を先に固定する。スキーマ自体の網羅テストは
> エンドポイントテストとランタイム検証（ValidationError 送出）で間接的に検証する（Minimal 戦略・
> プロジェクト学習済みルール）。

### Step 2: 単価計算テスト `tests/test_kpi.py`（Red）

- [x] `expected_cost_saved(severity_level)` が business-model.md §3.3 の単価を返す
  - Level 0 → `0`（E_avoided(0) = 0）
  - Level 1 → `121_800`（0.12 × (1,200,000 − 185,000)）
  - Level 2 → `308_000`（0.35 × (1,200,000 − 320,000)）
  - Level 3 → `150_000`（固定 C_response_saved）
- [x] `SeverityLevel`（Literal[0,1,2,3]）の許容値のみ受け付ける（不正値は `ValidationError` のランタイム検証で代替）

### Step 3: 算定サービス `app/services/kpi.py`（Green）

- [x] 算定定数を**この1箇所**に定義（D-2 / business-model.md §3.2）:
  - `C_BURST = 1_200_000` / `C_REPAIR_LEVEL1 = 185_000` / `C_REPAIR_LEVEL2 = 320_000`
  - `P_LEVEL1 = 0.12` / `P_LEVEL2 = 0.35` / `C_RESPONSE_SAVED = 150_000`
  - `KPI_ASSUMPTION_DOC = "docs/business-model.md §3"`（レスポンスの `assumption_doc` に使用）
- [x] `expected_cost_saved(severity_level: SeverityLevel) -> int` を実装
  - §3.1 の式をそのまま実装（`round()` で整数化、`int` を返す）
- [x] `backend/venv/Scripts/python.exe -m pytest tests/test_kpi.py -v` が Green になることを確認

### Step 4: サマリ計算テスト `tests/test_kpi.py`（Red）

- [x] `calculate_kpi_summary()` がストア実データから集計する（S-2）
  - シード: Level1×8 / Level2×3 / Level3×1 → `level1_count=8` / `level2_count=3` / `level3_count=1`、
    `estimated_cost_saved_yen=2_048_400`（S-5）
  - `total_sensors` が `get_hydrants()` の実件数（10）と一致（S-3）
  - `is_estimate=True`・`assumption_doc` が `docs/business-model.md §3` を指す
- [x] 空ストアで `level1_count=0` / `level2_count=0` / `level3_count=0` / `estimated_cost_saved_yen=0`、
      `total_sensors` のみ実件数を返す（S-4）
- [x] Level 0 のみのストアでカウント・コストが全て0（レベル0は集計対象外）になる

### Step 5: サマリ組み立て `app/services/kpi.py`（Green）

- [x] `calculate_kpi_summary() -> KpiSummary` を実装
  - `get_store().list_alerts()` をハンドラ実行時に呼ぶ（import 時捕捉はテスト隔離を壊すため、store.py の流儀に従う）
  - 各レコードの `analysis.severity_level` をレベル別にカウント（Level 0 は対象外）
  - `estimated_cost_saved_yen = Σ expected_cost_saved(severity_level)` を算出
  - `total_sensors = len(get_hydrants())`（`@lru_cache` 済みローダーを再利用）
  - `is_estimate=True`・`assumption_doc=KPI_ASSUMPTION_DOC` を常時設定（試算値の明示）
- [x] `backend/venv/Scripts/python.exe -m pytest tests/test_kpi.py -v` が Green になることを確認

### Step 6: エンドポイントテスト `tests/test_kpi.py`（Red → Green）

- [x] `GET /api/v1/kpi/summary` が 200 と7項目（5項目 + `is_estimate`・`assumption_doc`）を返す（S-1）
- [x] シード済みストアでデモ内訳合計 2,048,400 を返す（S-5、TestClient 統合境界）
- [x] 空ストアでも 200 で全項目0・`total_sensors=10` を返す（500にしない）（S-4）

### Step 7: ルーター `app/routers/kpi.py` + `main.py` 登録（Green）

- [x] `kpi.py` に `router = APIRouter(prefix="/api/v1", tags=["kpi"])` を定義
  - `GET /kpi/summary` → `calculate_kpi_summary()` を返す（同期 `def`、`response_model=KpiSummary`）
  - 空ストア・例外時も 500 にしない（サービスのみで組み立て、HTTPException を上げない）
- [x] `main.py` の import に `kpi` を追加し、`app.include_router(kpi.router)` を登録
- [x] `backend/venv/Scripts/python.exe -m pytest tests/test_kpi.py -v` が Green になることを確認

### Step 8: 自走確認（Refactor）

- [x] `backend/venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing` で全テスト Green + カバレッジ **80% 以上**
- [x] コード品質: `any` 禁止、Pydantic v2 徹底、`list_alerts()` の level/limit 既定値を活かして不要コードなし
- [x] スキーマの `ValidationError` ランタイム検証（負値・型不正が弾かれること）
- [x] git status で変更対象ファイル（4 新規 + 1 修正）が期待通り

---

## 計画外（スコープ外の明示）

- フロント連携（`page.tsx` の `MOCK_KPI_DATA` 置換・camelCase マッピング）は後続ストーリー（FE-7 等）で対応（D-3、intent-statement.md レビュー指摘 #3）
- `today_detections` はレスポンスに含めない（D-3）
- 本番用 GIS DB、認証、リアルタイム通知は CLAUDE.md §3 により実装しない
- 検証スクリプト（`scripts/check_*.py`）は本ステージの受け入れ条件に存在しないため作成しない（S-5 は pytest のエンドポイントテストで実値検証する）

---

## Review

**Reviewer:** aidlc-architecture-reviewer-agent
**Verdict:** READY

### Findings（重大度順）

1. **[Minor]** `expected_cost_saved()` の防御的 `raise ValueError` 分岐が未テスト（プランの記載と実装のずれ）。プラン Step 2 は「不正値は ValidationError のランタイム検証で代替」と述べるが、`expected_cost_saved` は素の関数であり、範囲外の入力（例: 4）に対しては `ValidationError` ではなく `ValueError` を送出する。テストは `KpiSummary` モデルの型制約（`ge=0` / strict / `extra="forbid"`）のみで、この関数のエラーパスは検証されていない。`calculate_kpi_summary` 経由では `StoredTelemetry.analysis.severity_level` が `Literal[0,1,2,3]` に `add()` 時点で Pydantic 検証されるため、この `raise` 分岐は実質デッドコードであり、カバレッジ99%の残り1%に相当する。（根拠: `backend/app/services/kpi.py` L52 / `backend/tests/test_kpi.py` `TestExpectedCostSaved` / `code-generation-plan.md` Step 2）推奨: `pytest.raises(ValueError)` による1件のテスト追加、またはプラン記載を「ValueError」に訂正。

2. **[Minor]** エンドポイントテストの `total_sensors == 10` がデータフィクスチャをハードコード。`test_empty_store_returns_200_with_zeros` は `assert body["total_sensors"] == 10` と、現在の `hydrants.json` 件数に直結した値を直接検証している。サービス層テスト `test_aggregates_from_store_data` は `len(get_hydrants()) == 10` と堅牢。`hydrants.json` の件数が変わると仕様上正しい実装でもテストが壊れる。受け入れ条件（S-3）が「現状10件」と明記しているため許容されるが、保守性の観点ではエンドポイントテストも `len(get_hydrants())` による検証が望ましい。（根拠: `backend/tests/test_kpi.py` L171）

3. **[Minor]** 集計ループで Level 0 レコードにも `expected_cost_saved(0)` を実行（0円加算）。機能的には正しいが、レベル別カウントの if/elif とコスト関数の分岐に深刻度→値の対応が重複しており、「Level 0 は集計対象外」という意図が読み手に伝わりにくい。任意の改善として、深刻度→単価のマッピング（`{0: 0, 1: ..., 2: ..., 3: ...}`）を `services/kpi.py` の定数群に1箇所定義し、`expected_cost_saved` と集計ループの双方から参照する方式がある。（根拠: `backend/app/services/kpi.py` L63-75）

4. **[Info]** KPI は「検知アラート単位」で集計する（`list_alerts()` の全レコードを1件ずつ計上）。同一センサーが同一漏水事象で複数レコードを送信した場合も各々1件として `E_avoided` が加算される。これは business-model.md §3.1 の定義（「検知アラートごとの期待回避コスト」）どおりであり現スコープでは仕様適合だが、実運用で「漏水イベント単位」へ集計粒度を変えたい場合は将来の設計課題として認識しておくと良い。（根拠: `backend/app/services/kpi.py` L67-75 / `docs/business-model.md` §3.1）

5. **[Info]** ステージ観察日誌 `construction/be8-kpi-summary/code-generation/memory.md` が空（Interpretations / Deviations / Tradeoffs / Open questions がすべて未記入）。コードの健全性には影響しないが、ステージ定義（code-generation.md の Learn 節）が要求する観察記録が残っていない。承認ゲートでの参考情報として報告する。（根拠: `aidlc/spaces/default/intents/260811-be8-kpi-summary/construction/be8-kpi-summary/code-generation/memory.md`）
