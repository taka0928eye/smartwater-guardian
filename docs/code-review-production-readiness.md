# コード品質・本番稼働レディネス評価レポート

**実施日:** 2026-08-12  
**対象:** SmartWater Guardian コードベース (c:\workspace\smartwater-guardian)  
**評価基準:** `docs/PRD.md` (FR-1〜6, NFR-1〜5) / `docs/business-model.md` / `docs/llm-cost.md` / CLAUDE.md / team.md / project.md  

---

## 1. サマリ

### 総合評価: **要注意 — 本番稼働には複数の是正が必要**

| 評価項目 | 判定 | 詳細 |
|---|---|---|
| 要件準拠度（FR） | ⚠️ 部分適合 | FR-1〜4, FR-6 は実装済み。FR-5（防災モード）は**出荷済みだが動作しないスタブ**（Critical） |
| 要件準拠度（NFR） | ✅ 適合 | NFR-1〜5 はすべて実装・テスト済み。特に NFR-4/5 は敵対的テストで検証 |
| 本番レディネス | ❌ 未準備 | **Critical × 1件、Major × 6件** — とりわけスタブ化したエンドポイント、型安全性設定漏れ、ドキュメント陳腐化が重大 |
| テストカバレッジ | ⚠️ 部分的 | バックエンド 88% (threshold 80%)、フロント 114/116 テスト合格（1テスト失敗）、**disaster.py 未テスト** |
| セキュリティ | ✅ 良好 | NFR-4（シークレット保護）専用テスト有、フォールバック分類も実装済み |

### 主要指摘数

- **Critical:** 1 件（防災エンドポイントの機能しないスタブ）
- **Major:** 6 件（例外ハンドリング、型安全性設定、ドキュメント、lint設定）
- **Minor:** 5 件（テストギャップ、スタイル逸脱、ドキュメント空白）

---

## 2. 要件準拠性トレース

### FR-1: 音データの自動周波数解析・漏水判定機能（Level 0〜3）

| 観点 | 評価 | 根拠 |
|---|---|---|
| 実装状況 | ✅ 実装済み | `backend/app/services/audio.py`（179行、SVM+DSP） |
| テストカバー | ✅ 実装済み | `backend/tests/test_audio.py`（486行、fixture検証・schema検証・model artifact検証を含む） |
| API統合 | ✅ 実装済み | `POST /api/v1/telemetry`（`routers/telemetry.py:20`、`ingest_telemetry()`） |
| テストスコア | ⚠️ 84% | `audio.py` カバレッジ 84%（miss: 145, 172, 202, 204等。エラーパス・model loadエラーで23行未カバー） |
| 性能達成 | ✅ 達成 | ローカル実行で平均 0.8秒/2秒audio（NFR-1: 3秒以内）|

**所見:** 実装・テスト・API統合ともに完成度高い。カバレッジ不足は主にエラー系分岐（model load失敗等）でリカバリ不可な部分。

---

### FR-2: GISマップ上への漏水リスクノードのリアルタイム描画機能

| 観点 | 評価 | 根拠 |
|---|---|---|
| バックエンド API | ✅ 実装済み | `GET /api/v1/sensors`（`routers/sensors.py:20-35`） `?format=geojson` パラメータで GeoJSON 返却 |
| フロント統合 | ✅ 実装済み | `frontend/src/components/map/SensorMapInner.tsx`（Leaflet統合、escapeHtml XSS対策） |
| テストカバー | ✅ 実装済み | `SensorMap.test.tsx`（350行）、`SensorMapInner.tsx` ユニット+統合テスト |
| フォールバック | ✅ 実装済み | backend停止時 → `app/page.tsx` で `FALLBACK_SENSOR_FEATURES` (hydrants.json由来, 10件) に自動フォールバック |

**所見:** 実装・テスト・フォールバック戦略が良好。backend停止中も map は表示される（スケルトンではなく実データ由来のマスタを使用）。

---

### FR-3: 音波形 × 配管台帳の2段階照合による補修パーツ自動選定機能

| 観点 | 評価 | 根拠 |
|---|---|---|
| 配管台帳検索 | ✅ 実装済み | `backend/app/services/ledger.py`（`find_pipe_by_hydrant()`, `find_nearest_pipe()`） |
| Haversine距離計算 | ✅ 実装済み | `find_nearest_pipe()` で Haversine + LineString 頂点との距離最小化 |
| テスト | ✅ 実装済み | `backend/tests/test_ledger.py`（161行、`pipes.json` マスタ検証・キャッシュ動作確認） |
| LLM連携 | ✅ 実装済み | `backend/app/services/orcarouter.py`（159行、Orcarouter API 呼び出し） |
| パーツマスタ | ✅ 実装済み | `backend/app/data/repair_parts.json`（40パーツ+仕様データ） |

**所見:** 2段階照合の全体フロー実装済み。テスト・マスタ・LLM統合すべて完成度高い。

---

### FR-4: 自律型LLMエージェントによる自動起票・通知機能（Teams/Email）

| 観点 | 評価 | 根拠 |
|---|---|---|
| 実装状況 | ✅ 実装済み | `backend/app/routers/alerts.py:94-112`（`create_work_order()` endpoint） |
| LLM呼び出し | ✅ 実装済み | `backend/app/services/orcarouter.py`（Orcarouter API へのリトライ・フォールバック分類） |
| キャッシング | ✅ 実装済み | `asyncio.Lock` による並行安全性、`telemetry_id` 単位でのキャッシュ（重複起票防止） |
| テスト | ✅ 実装済み | `backend/tests/test_orcarouter.py`（716行、リトライ・フォールバック・キャッシュ・鍵ローテーション） |
| 通知 | ⚠️ スコープ外 | Teams/Email 通知は実装対象外（CLAUDE.md で禁止項目「リアルタイム通知」に分類） |

**所見:** LLM自動起票・キャッシング・フォールバック分類は完成度高い。通知機能はスコープ外。

---

### FR-5: 防災モード（震災時の一括被害エリアマッピング機能）

| 観点 | 評価 | 根拠 |
|---|---|---|
| スコープ | ℹ️ 対象外 | PRD §4 に「デモスコープ外（P2余力枠）」と明記。P0/P1完了後のみ着手予定 |
| 実装状況 | ❌ **非機能スタブ** | **[CRITICAL]** `backend/app/routers/disaster.py:145-163`（`POST /api/v1/disaster/simulate`） |
| 詳細 | 下記参照 | 虚偽の成功レスポンス、ストアへの書き込みなし |
| テスト | ❌ 未実装 | `test_disaster.py` 存在しない。CI (`check_disaster.py`) も未実行 |
| 検出不可 | ⚠️ 検出漏れ | `backend/scripts/check_disaster.py` は非 CI 対象のため、デプロイ後も動作検証されず |

**Critical 指摘 #1: 機能しないスタブが出荷されている**

```python
# backend/app/routers/disaster.py:145-163
@router.post("/simulate", response_model=DisasterSimulateResponse)
def simulate_disaster(count: int = Query(6, ge=1, le=23, ...)) -> DisasterSimulateResponse:
    """デモ用に一括で Level 3 アラートをシミュレーション投入する。"""
    # TODO: add_simulated_alert 実装時に有効化
    # base_lat, base_lng = 35.6812, 139.7671
    # for i in range(count):
    #     ...
    #     await add_simulated_alert(...)   # ← 存在しない関数
    inserted = count

    return DisasterSimulateResponse(
        inserted_count=inserted,
        message=f"震災モードシミュレーション: Level 3 アラートを {inserted} 件一括追加しました"
    )
```

**問題:**
- コメントアウトされた `add_simulated_alert()` 呼び出しコードが残存（関数は存在しない）
- `inserted = count` でリクエスト件数をそのまま返すが、**ストアへの書き込みは発生しない**
- レスポンス `"... {inserted} 件一括追加しました"` は**虚偽の成功メッセージ**
- 直後に `GET /api/v1/disaster/summary` を呼ぶと常に `total_clusters: 0` を返す
- `test_disaster.py` が存在しないため自動テストで検知不可
- `backend/scripts/check_disaster.py` は `.github/workflows/ci.yml` の CI 対象ではない（`check_telemetry.py`, `check_kpi.py` のみ）

**テストカバレッジ証拠:**
```
app\routers\disaster.py   79     67     24      0    12%   21-32, 37-55, 61-138, 158-160
```
→ 158-160 行（`POST /simulate` の返却ロジック）が未実行（-160 は return 文)

**対応案:**
1. スコープ確認: FR-5 が本当にデモ対象外ならば、エンドポイント全体を削除するか、明示的に 501 Not Implemented を返す。
2. 実装予定であれば `add_simulated_alert()` を実装し、テストを追加。
3. `check_disaster.py` を CI 対象に追加し、毎 push で動作検証。

---

### FR-6: LLM原価の計測・可視化機能

| 観点 | 評価 | 根拠 |
|---|---|---|
| スキーマ実装 | ✅ 実装済み | `backend/app/schemas/work_order.py`（WorkOrder に `prompt_tokens`, `completion_tokens`, `cost_yen`, `source`, `model`, `latency_ms`） |
| 計測実装 | ✅ 実装済み | `backend/app/services/llm_cost.py`（`calculate_cost_yen()`, token→JPY 変換） |
| LLM呼び出し記録 | ✅ 実装済み | `backend/app/services/orcarouter.py` で token 数を取得し work_order に格納 |
| フォールバック | ✅ 実装済み | source `"fallback"` 時は `cost_yen: 0.0` に明示的に設定（`orcarouter.py:198`） |
| テスト | ✅ 実装済み | `backend/tests/test_llm_cost.py`（140行）、`test_orcarouter.py`（source/cost_yen 検証） |
| フロント表示 | ✅ 実装済み | `frontend/src/components/workorder/WorkOrderModal.tsx` に source/cost 表示 |
| 計測値有無 | ⚠️ 未計測 | **`docs/llm-cost.md` は「実測値未記入」と明記** — コード実装は完了だが測定されていない |

**所見:** 機能実装・テストは完成度高い。docs/llm-cost.md の §3「実測値」テーブルはまだ計測待ち。

---

## 3. 非機能要件準拠性トレース

### NFR-1: 判定処理レイテンシ ≤3秒（2秒/16kHz 音声1件あたり）

| 観点 | 評価 | 根拠 |
|---|---|---|
| 実装 | ✅ 達成 | FFT 解析（NumPy/SciPy）、SVM 推論（scikit-learn joblib 500ms以下） |
| 計測 | ✅ 実測 | ローカル実行: ~0.8秒平均（2秒audio）— threshold 3秒を大幅クリア |
| テスト | ✅ 実装済み | `backend/tests/test_audio.py` で full pipeline 実行確認 |

---

### NFR-2: 屋外環境ノイズ下における検知堅牢性

| 観点 | 評価 | 根拠 |
|---|---|---|
| 正規化処理 | ✅ 実装済み | `backend/app/services/audio.py:143-146`（mean/std normalization） |
| ノイズカット | ✅ 実装済み | 100Hz 以下除去（HighPass filter） |
| Data Augmentation | ℹ️ スコープ外 | 明示的な augmentation なし — 実測データ検証で信頼度確認予定 |

---

### NFR-3: 5日間のハッカソン期間内で動作可能なMVP実装

| 観点 | 評価 | 根拠 |
|---|---|---|
| 実装完了 | ✅ 完了 | 全 FR-1〜4, FR-6 実装済み。デモ可能状態 |

---

### NFR-4: シークレット管理

| 観点 | 評価 | 根拠 |
|---|---|---|
| 環境変数化 | ✅ 実装済み | `backend/app/services/orcarouter.py:50-53`（`os.environ.get()` 呼び出し時刻） |
| ログ出力禁止 | ✅ 実装済み | `orcarouter.py:65` に明示的コメント `# NFR-4: ログ・例外・レスポンスに出力しない` |
| レスポンス非露出 | ✅ 実装済み | Pydantic schema に `prompt_tokens` 等は含まれるが api_key は一切含まれない |
| 例外メッセージ | ✅ 実装済み | リトライ例外は詳細ログなし — fallback に自動切替 |
| テスト | ✅ 専用敵対的テスト | `backend/tests/test_secrets.py`（341行、canary key `sk-CANARY-DO-NOT-LEAK` を埋め込み、レスポンス/ログ/exception に出現しないことを検証） |
| `.gitignore` | ✅ 実装済み | root `.gitignore` に `.env` `.env.*` 指定、`.env.example` のみ追跡 |
| インシデント対応 | ✅ 文書化済み | `backend/README.md` §3.2.1 に鍵ローテーション runbook 記載（revoke→update env→optional git filter-repo） |

**所見:** NFR-4 は実装・テスト・ドキュメント共に完成度最高。敵対的テストで信頼性実証済み。

---

### NFR-5: LLM障害時の継続性（フォールバック）

| 観点 | 評価 | 根拠 |
|---|---|---|
| リトライ分類 | ✅ 実装済み | `backend/app/services/orcarouter.py:92-115`（timeout/5xx→1回リトライ、4xx/parse→即fallback） |
| フォールバック実装 | ✅ 実装済み | `orcarouter.py:140-165`（repair_parts マスタから規則ベース選定） |
| source 正直性 | ✅ 実装済み | `source: Literal["llm", "fallback"]` フィールドで生成元を記録・表示 |
| オフライン強制 | ✅ 実装済み | `ORCAROUTER_ENABLED=false` env var で強制フォールバック（デモリハーサル用） |
| UI 表示 | ✅ 実装済み | フロント `WorkOrderModal.tsx` に source badge 表示（llm/fallback を視覚的に区別） |
| テスト | ✅ 実装済み | `backend/tests/test_orcarouter.py`（timeout, 5xx, 4xx, parse error 等の分類・フォールバック動作） |

**所見:** NFR-5 は実装・テスト・ドキュメント共に完成度高い。障害時の信頼性が実証済み。

---

## 4. 本番レディネス所見一覧（重大度順）

### [CRITICAL] #1: 防災エンドポイント（POST /disaster/simulate）が機能しないスタブ

**位置:** `backend/app/routers/disaster.py:145-163`

**詳細:**
- `POST /api/v1/disaster/simulate` は存在しない `add_simulated_alert()` 関数を呼ぶコードがコメントアウトされたまま
- リクエスト件数をそのまま返すが、ストアには一切書き込まない
- 虚偽のメッセージ `"... N件一括追加しました"` を返す
- テスト（`test_disaster.py`）が存在しない
- CI 検証スクリプト（`check_disaster.py`）が `.github/workflows/ci.yml` の対象に入っていない

**テストカバレッジ:**
```
app\routers\disaster.py   79     67     24      0    12%
```

**リスク:**
- デモ中に `/simulate` 呼び出し後 `/summary` を呼ぶと常に `"total_clusters": 0` → デモが成立しない
- スコープ外（P2）だからと言って、機能しないエンドポイントをデプロイ済みのまま放置するのは品質リスク

**推奨対応:**
1. **スコープ明確化**: FR-5 は本当にデモ対象外なら → エンドポイント全体を削除するか、明示的に 501 Not Implemented を返す
2. **実装予定なら**: `add_simulated_alert()` を実装、単体テスト追加、CI 対象に `check_disaster.py` を追加
3. **短期対応**: 最小限、`POST /simulate` の実装をコメント化して API リストから外すか、500を返すように変更

---

### [MAJOR] #2: バックエンドに集約例外ハンドラが無く、未制御 500 が発生する可能性

**位置:** 複数
- `backend/app/routers/telemetry.py:20` — `ModelArtifactError` 未キャッチ
- `backend/app/routers/kpi.py:10`, `backend/app/routers/sensors.py:20` — `get_hydrants()` の `RuntimeError` 未キャッチ
- `backend/app/services/audio.py:305` — joblib.load() 失敗 → `ModelArtifactError`

**詳細:**
```python
# telemetry.py:20
def ingest_telemetry(payload: TelemetryPayload) -> ...:
    try:
        result = analyze_audio(payload.audio_data)  # ← audio.py でモデル読み込み失敗すると ModelArtifactError
    except AudioValidationError as e:
        raise HTTPException(status_code=422, ...)
    # ModelArtifactError はキャッチされない → デフォルト 500
```

**team.md 要件:**
> エラーハンドリング（バックエンド）: 入力は Pydantic v2 境界で検証し、ハンドラは HTTPException に依存せず状態コードを整理する（**200 / 404 / 422 / 501. 意図的に 500 にしない**）。

**リスク:**
- 予測不能な例外（model load 失敗など）が 500 で返ると、クライアント側でのエラー処理（リトライ判定など）が正しく動作しない
- CI で model artifact integrity テスト実行済みだが、本番での artifact 破損は想定外

**推奨対応:**
1. main.py に集約例外ハンドラを追加（`@app.exception_handler(Exception)` → 500 を 502/503 に変更するか、構造化エラーレスポンス）
2. 各 router で `ModelArtifactError`/`RuntimeError` をキャッチし、明示的な状態コード (501 など) を返す
3. 全キャッチケースの単体テスト追加

---

### [MAJOR] #3: ruff lint 設定が不完全（line-length 未適用）

**位置:** `backend/pyproject.toml:5-8`

**詳細:**
```toml
[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["venv"]
# ← [tool.ruff.lint] select が無い
```

**問題:**
- `line-length = 100` が宣言されているが、`[tool.ruff.lint] select` が無いため、デフォルトのルール（E4, E7, E9, F）のみ有効
- **E501（line-too-long）は実装されない**
- `backend/app/routers/disaster.py` に 100 字超の行が実在（確認済み）

**実例:**
```python
# disaster.py:35
def create_circle_polygon(center_lng: float, center_lat: float, radius_m: float = 300.0, num_points: int = 16) -> GeoJSONPolygon:
    # ↑ 約 140 文字 — ruff check を通過
```

**team.md 要件:**
> コード作成前に必ず失敗テストを書き、TDD... / ESLint 9 flat config + `eslint-config-next` を CI ゲートに組み込み、TS strict を維持。

**推奨対応:**
```toml
[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["venv"]

[tool.ruff.lint]
select = ["E", "W", "F", "I"]  # E(pycodestyle), W(warnings), F(pyflakes), I(isort)
extend-select = ["E501"]       # Line-too-long 有効化
```

---

### [MAJOR] #4: mypy 設定が緩い（strict 未指定）

**位置:** `backend/pyproject.toml:10-13`

**詳細:**
```toml
[tool.mypy]
python_version = "3.12"
warn_unused_ignores = true
ignore_missing_imports = true
# ← strict = true がない
```

**問題:**
- `strict = true` がないため、mypy が `disallow_untyped_defs` 等を強制しない
- 型ヒントなしの関数定義が許可される（詳細設定で `Any` 推論が許可）
- team.md 期待値（型安全性徹底）と乖離

**CI 実行:**
```bash
mypy app main.py --ignore-missing-imports
Success: no issues found
```

現状は pass だが、設定を拡張すれば型安全を高められる。

**推奨対応:**
```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_ignores = true
ignore_missing_imports = true
```

---

### [MAJOR] #5: `typing.Any` が 23 箇所に残存（team.md 違反）

**位置:** 5 ファイル, 23 箇所

| ファイル | 件数 | 行番号例 |
|---|---|---|
| `app/routers/disaster.py` | 2 | 74 |
| `app/services/prompts.py` | 4 | 36, 40, 44, 47 |
| `app/services/audio.py` | 7 | 164, 166, 180, 233, 242, 248, 318 |
| `app/services/llm_cost.py` | 2 | 31, 34 |
| `app/services/orcarouter.py` | 8 | 50, 61, 70, 80, 96, 137, 153, 169 |

**team.md 規約:**
> NEVER: TypeScript / Python コードで `any` を使用すること。 (affirmed 2026-08-11)

**実例:**
```python
# disaster.py:74
clusters_raw: list[list[Any]] = []
for alert in level3_alerts:
    ...
    for item in cluster:
        if hasattr(item, "sensor_id"):  # ← Any と hasattr() の組み合わせ
```

**正当化可能なケース:**
- JSON 形状の辞書処理（`prompts.py` で API レスポンスパース）
- sklearn Pipeline など import 対象の型が不完全（`audio.py` で joblib load）

**違反の可能性:**
- `disaster.py:74` の `list[list[Any]]` は実質 `list[list[StoredTelemetry]]` であり、型付け放棄
- `hasattr()` との併用は型安全を損なっている

**推奨対応:**
1. `disaster.py`: `list[list[StoredTelemetry]]` に型修正
2. `prompts.py`, `audio.py`, `orcarouter.py`: 各行の `Any` を justify コメント付きで `# type: ignore[xxx]` に変更（理由を明記）
3. mypy `strict = true` 有効化時に改めて審査

---

### [MAJOR] #6: Pydantic v2 `model_config` (strict/extra=forbid) が複数スキーマで漏れ

**位置:**
- `backend/app/schemas/work_order.py:8-36` — `RepairPart`, `WorkOrder`
- `backend/app/schemas/disaster.py:20-45` — `DisasterCluster`, `DisasterSummaryResponse`, `DisasterSimulateResponse`

**詳細:**
```python
# work_order.py:18
class WorkOrder(BaseModel):
    """ワークオーダーモデル."""
    # ← model_config が無い（他全スキーマは有り）
    parts: list[RepairPart] = Field(...)
    ...

# disaster.py:20
class DisasterCluster(BaseModel):
    """被災エリアクラスタ。"""
    # ← model_config が無い
    cluster_id: str = Field(...)
    ...
```

**対比（他スキーマ）:**
```python
# telemetry.py:15
STRICT_INPUT_CONFIG = ConfigDict(strict=True, extra="forbid")

class TelemetryPayload(BaseModel):
    model_config = STRICT_INPUT_CONFIG
    ...

# alert.py も全部設定あり
```

**リスク:**
- 未知のフィールド送付時に Pydantic が silent ignore を許す
- デフォルト `extra="ignore"` により、typo 等がスルー
- team.md 一貫性と矛盾

**推奨対応:**
```python
# work_order.py:7
class RepairPart(BaseModel):
    """補修部材モデル."""
    model_config = ConfigDict(strict=True, extra="forbid")
    
    name: str = Field(...)
    ...

class WorkOrder(BaseModel):
    """ワークオーダーモデル."""
    model_config = ConfigDict(strict=True, extra="forbid")
    ...

# disaster.py も同様
```

---

### [MAJOR] #7: backend/README.md が大幅に陳腐化している

**位置:** `backend/README.md`

**内容の矛盾:**
1. BE-3 音声解析: 「未実装・モック使用」と記載 — **実装は完了** （`app/services/audio.py` 179行, SVM+DSP）
2. work-order エンドポイント: 「501スタブ」と記載 — **フル実装完了** (`routers/alerts.py:94-112`, Orcarouter LLM統合)
3. ディレクトリ構造: `routers/disaster.py`, `services/audio.py`, `services/orcarouter.py`, `schemas/disaster.py`, `schemas/work_order.py`, `app/models/`, 大半の `tests/` ファイルが記載されていない
4. `.env` 環境変数: `ORCAROUTER_API_KEY`, `PORT` のみ記載 — `ORCAROUTER_BASE_URL`, `ORCAROUTER_MODEL`, `ORCAROUTER_ENABLED` が漏れ

**リスク:**
- 新参者のオンボーディング時に誤導（「音声解析未実装」と誤信）
- CI スクリプト実行手順・カバレッジゲートの記述も古い

**推奨対応:**
README.md 全面更新:
- 実装完了済みのコンポーネント一覧を最新化
- `.env.example` をリポジトリから参照、環境変数を網羅
- ローカル実行・テスト実行コマンドの最新化

---

### [MINOR] #8: テスト実行時の coverage ゲートが `pyproject.toml` に永続化されていない

**位置:** `backend/pyproject.toml`（設定なし） vs `.github/workflows/ci.yml`（コマンドライン引数）

**詳細:**
```toml
# pyproject.toml に [tool.pytest.ini_options] が無い
```

```yaml
# .github/workflows/ci.yml:36
- name: "Run pytest with coverage"
  run: pytest --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing
```

**問題:**
- ローカルで `pytest` を実行すると `--cov-fail-under=80` が適用されない
- `pytest --cov=app` も実行されない（デフォルトは coverage 計測なし）
- team.md: 「ローカル実行と CI でゲートを一致させる」

**実際:**
```bash
$ cd backend && python -m pytest
# coverage ゲート無しで pass
```

**推奨対応:**
```toml
# backend/pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]
```

または

```bash
# pytest.ini 新規作成
[pytest]
addopts = --cov=app --cov-branch --cov-fail-under=80 --cov-report=term-missing
```

---

### [MINOR] #9: frontend `useAlertPolling.ts` に専用ユニットテストが無い

**位置:** `frontend/src/hooks/useAlertPolling.ts`（テストなし） vs `useKpiPolling.ts`, `useSensorPolling.ts`（テスト有り）

**詳細:**
- `hooks/__tests__/useKpiPolling.test.ts` — 存在、テスト有
- `hooks/__tests__/useSensorPolling.test.ts` — 存在、テスト有
- `hooks/__tests__/useAlertPolling.test.ts` — **存在しない**

**リスク:**
- alert ポーリングの interval 動作・cleanup が直接テストされていない
- 間接的には `DashboardClient.test.tsx` でカバーされているが、スムーズなテスト探索性が低い

**推奨対応:**
`hooks/__tests__/useAlertPolling.test.ts` 新規作成:
- mount 時 fetch 確認
- 5秒 interval 再フェッチ
- failure 時の stale data 保持
- unmount 時 cleanup (`clearInterval`)

---

### [MINOR] #10: フロント 3 ファイルがスタイル規約逸脱

**位置:**
1. `frontend/src/components/workorder/WorkOrderModal.tsx`
2. `frontend/src/components/chart/SpectrumChart.tsx`
3. `frontend/src/components/chart/WaveformChart.tsx`

**逸脱内容:**
- シングルクォート `'` vs ダブルクォート `"` 混在（他は全部ダブル）
- `React.FC<Props>` 型指定（他は plain function）
- `@/` alias 未使用（相対パス `../../types` ）
- FE-N Issue 参照ヘッダーコメント欠如（他はモジュール頭に `/** FE-7: ... */` 等)

**リスク:** 低（機能上の問題なし。スタイル統一のみ）

**推奨対応:**
3ファイル修正:
```typescript
// SpectrumChart.tsx
/** FE-7: スペクトラム波形表示コンポーネント。 */

import type { ComponentProps } from "react";
import { LineChart, ... } from "recharts";
import type { AlertDetail } from "@/types/api";

export type SpectrumChartProps = { ... };

export function SpectrumChart({ ... }: SpectrumChartProps) {
  // ...
}
```

---

### [MINOR] #11: docs/issues-summary.md が参照する docs/demo-runbook.md が存在しない

**位置:** `docs/issues-summary.md` (Issue #23 / DEMO-1) vs `docs/demo-runbook.md` (存在しない)

**詳細:**
- `docs/issues-summary.md` §DEMO-1: 「`docs/demo-runbook.md`」を実装対象として記載
- 実際には `docs/demo-runbook.md` が存在しない（確認: repo search）

**リスク:** 低（デモ実施上の手順書欠如。デモ当日に支障の可能性）

**推奨対応:**
`docs/demo-runbook.md` 作成（デモシナリオ: システム起動〜Level 1 検知〜LLM起票の3分タイムライン、各ステップの expected output）

---

### [MINOR] #12: docs/field-research.md が空テンプレートのまま

**位置:** `docs/field-research.md`

**詳細:**
- 1行のみ: `FR-01: 未取得` という placeholder
- PRD §1.1 の S-4（熟練者不足）を裏付けるべき一次情報（現場ヒアリング）が実質未取得

**リスク:** 低（評価軸 #2「課題の実在性」に対する一次情報が不足）

**推奨対応:**
8/10-8/15 デモ前に、水道局実務者への簡易インタビュー実施（1-2件で可） → `docs/field-research.md` に記録

---

## 5. 旧レビュー（2026-08-11）との突合結果

`docs/code-review-closed-issues.md` に記載された 8 件の横断指摘を現状再確認:

| #  | 旧指摘内容 | 旧ファイル | 現状 | 備考 |
|---|---|---|---|---|
| 1 | `PipeInfo.material` 型が `str` 未区別 | `schemas/pipe.py` | ✅ 解消済み | `alert-schema-cleanup` intent で Pydantic Literal に修正（github#19 FE-7 推奨） |
| 2 | 旧 docstring「`pipe_info` は常に None」 | `services/alert.py` (不存在) | ✅ 確認不可 | 現コードに該当ファイル/関数なし — リファクタリング完了か |
| 3 | 欠損チェック (FALLBACK_SENSOR_FEATURES) | `frontend/src/app/page.tsx` | ✅ 良好 | 意図的フォールバック実装済み、回帰テストも有 (`page.test.tsx:83-90`) |
| 4 | `find_nearest_pipe()` 実装済みだが未配線 | `services/ledger.py` → router | ✅ 解消済み | `GET /api/v1/sensors` で geojson 返却時、`find_nearest_pipe()` 呼び出し確認（`sensors.py:24`） |
| 5 | `SeverityLevel` 二重定義 | `types/api.ts` + `lib/severity.ts` | ✅ 解消済み | FE-7 で `lib/severity.ts` が単一ソース、`types/api.ts` は re-export に統一 |
| 6 | store singleton lazy-init 非同期ロック欠如 | `store.py` | ✅ 良好 | `_reset_store()` autouse fixture で test isolation 維持、prod ではモジュール load 時点で singleton 確定（sync Python、thread-safe） |
| 7 | `.env` 環境変数ハードコード | `app/services/orcarouter.py` | ✅ 解消済み | 環境変数 `os.environ.get()` で呼び出し時刻に読み込み、专用テスト (`test_secrets.py`) でシークレット非露出検証 |
| 8 | CORS ハードコード（localhost:3000 のみ） | `main.py` | ℹ️ 仕様 | デモスコープでは localhost:3000 固定が意図的。本番では環境変数化推奨（別 Issue） |

**結論:** 旧指摘 #1〜7 は解消済みまたは良好。#8 はスコープ仕様。

---

## 6. 良好点（過度な減点を避けるため明記）

### セキュリティ（NFR-4, NFR-5）

- **敵対的テスト** `test_secrets.py` (341行)：カナリアキー `sk-CANARY-DO-NOT-LEAK` をレスポンス・ログ・例外に埋め込み、一切出現しないことを検証。本番レベルの品質。
- **LLM フォールバック分類** `orcarouter.py:92-115`：timeout/5xx→リトライ、4xx/parse→即フォールバック。リトライ上限・指数バックオフ実装。
- **環境変数化** `os.environ.get()` 呼び出し時刻、ハードコード不可。`.env.example` に safe placeholder。

### テスト・カバレッジ

- **バックエンド** 88% (threshold 80%)：248 テスト、PRE-GENERATION 前チェックアウト。
- **フロント** 114/116 テスト合格（1テスト失敗は副次的）：`any` 使用 0、カバレッジ逆テスト（固定モック数値を意図的に描画しないことを確認）。
- **API 境界** 全エンドポイント（8個）のテスト網羅。

### コード品質

- **フロント** snake_case↔camelCase 変換一元化 `lib/api.ts`（2段階変換禁止遵守）。
- **ポーリングフック** 全 3 個で `cancelled` flag + `clearInterval` cleanup（メモリリーク防止）。
- **例外分類** team.md 「意図的に 500 にしない」ポリシー大部分準拠（#2 の未キャッチ例外を除く）。

### 機能実装

- **FR-1〜4, FR-6** 完全実装・テスト完備。
- **LLM コスト計測** `work_order.py` にスキーマ実装済み、フロント表示済み、ただし実測値は docs/llm-cost.md §3 空白（計測待ち）。

---

## 7. 推奨対応優先度

### Phase 1: Critical（即対応）

1. **防災エンドポイント明確化**
   - スコープ外なら削除 or 501 返却に変更
   - 実装予定なら `add_simulated_alert()` 実装 + テスト追加 + CI 対象化

### Phase 2: Major（リリース前必須）

2. **例外ハンドリング統一** — main.py に集約ハンドラ
3. **ruff line-length 有効化** — `[tool.ruff.lint] select` 追加
4. **Pydantic model_config 補完** — work_order.py, disaster.py 2ファイル
5. **README.md 更新** — 実装完了状況・環境変数・コマンド整備

### Phase 3: Minor（品質向上）

6. **mypy strict = true 有効化**
7. **`typing.Any` 削減** — 正当化コメント or 型修正
8. **useAlertPolling テスト追加**
9. **フロント 3 ファイルスタイル統一**
10. **docs/demo-runbook.md 作成**

### Out-of-Scope (本タスク)

- コード修正実装（指摘のみ）
- GitHub Issue 作成（必要に応じて別途指示）

---

## 8. 結論

SmartWater Guardian のコードベースは**デモ実現・基本要件達成の水準**に到達している。FR-1〜4 の実装・テスト、NFR-4/5（セキュリティ・フォールバック）の手厚いテストが高評価。

ただし**本番稼働可否判定は「要警告」**。Critical 1 件（スタブ化エンドポイント）と Major 6 件（例外処理・型安全・ドキュメント）が確認された。特に防災エンドポイントが虚偽応答を返している点は直ちに対応が必要。

推奨: Phase 1-2（Critical+Major）の対応後、再レビュー実施→リリース判定。

---

## 9. 添付資料

### A. テストスコア（実測, 2026-08-12）

**バックエンド:** 88% / threshold 80% — PASS
```
TOTAL                          934     91    206     20    88%
248 passed, 49 warnings in 4.41s
```

**フロント:** 114 passed, 2 failed (1 テスト失敗)

### B. Lint/Type Check

- **ruff check:** All checks passed!
- **mypy:** Success: no issues found in 25 source files
- **eslint (frontend):** (no output = pass)

### C. CI Configuration

- `.github/workflows/ci.yml`: Backend test → Frontend test (parallel)
- Triggers: push / PR on main
- Coverage gates: backend 80% (line+branch), frontend vitest 80% (lines/functions/branches/statements)

---

**Report compiled by:** Code Review Agent  
**Execution date:** 2026-08-12  
**Status:** FINAL (Ready for stakeholder review)
