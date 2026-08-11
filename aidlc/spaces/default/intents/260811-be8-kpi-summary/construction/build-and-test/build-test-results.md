# Build / Test Results — SmartWater Guardian（BE-8 KPI サマリ）

> 実測日時: 2026-08-11（ビルド・テストステージ実行時）
> 実行環境: Windows 11 / Python 3.14.5 / pytest 9.1.1 / pytest-cov 7.1.0

## ビルド結果

| 項目 | 結果 | 出力 |
|------|------|------|
| import スモーク | ✅ 成功 | `OK: 9 routes`（`main.py` が `kpi` ルーターを含めて正常 import。エンドポイントを含む全ルート登録を確認） |

> Python はコンパイル工程を持たないため、「依存導入の確認 + import スモークテスト」でビルド成立を確認した
> （プロジェクト学習済みルール c2）。依存は `requirements.txt` から導入済み。

## テスト結果

| 項目 | 値 |
|------|-----|
| 収集テスト数 | 123 |
| 成功 (passed) | **123** |
| 失敗 (failed) | 0 |
| スキップ | 0 |
| 実行時間 | 1.12s |
| 警告 | 1（`StarletteDeprecationWarning` — httpx テストクライアントの非推奨警告。既存・無害） |

### ファイル別実行結果

| テストファイル | 結果 |
|----------------|------|
| `test_alerts.py` | ✅ 19 passed |
| `test_dependencies.py` | ✅ 1 passed |
| `test_hydrants.py` | ✅ 4 passed |
| `test_kpi.py`（BE-8 対象） | ✅ 14 passed |
| `test_ledger.py` | ✅ 12 passed |
| `test_pipes.py` | ✅ 8 passed |
| `test_simulate_sensor.py` | ✅ 23 passed |
| `test_store.py` | ✅ 19 passed |
| `test_telemetry.py` | ✅ 23 passed |

## カバレッジレポート（`--cov=app`）

| 指標 | 値 |
|------|-----|
| 合計カバレッジ | **99%**（431 ステートメント中 1 未実行） |
| 品質基準 | 80% 以上 → **達成** |

### ファイル別

| モジュール | Stmts | Miss | Cover | 備考 |
|------------|------:|-----:|------:|------|
| `app/services/kpi.py` | 36 | 1 | 97% | L52 `raise ValueError` のみ未実行（デッドコード、レビュー Minor #1） |
| `app/schemas/kpi.py` | 12 | 0 | 100% | |
| `app/routers/kpi.py` | 8 | 0 | 100% | |
| その他 | 375 | 0 | 100% | |

> BE-8 の未カバー箇所は `expected_cost_saved()` の防御的 `raise ValueError` 分岐のみ。これはコード生成
> レビューで Minor #1 として指摘済みのデッドコードで、`calculate_kpi_summary` 経由では到達しない
> （`StoredTelemetry.analysis.severity_level` が `add()` 時点で Pydantic 検証されるため）。品質基準の
> 80% は大きく満たしており、修正判断は承認ゲートに委ねる。

## 失敗詳細

- 該当なし（全テスト Green）。

## 補足（レビュー Minor 指摘との対応）

| 指摘 | 本ステージでの扱い |
|------|--------------------|
| Minor #1 `ValueError` 未テスト | デッドコードのためカバレッジ影響は1行のみ。修正は承認ゲートで判断。 |
| Minor #2 エンドポイントテストの `total_sensors == 10` ハードコード | サービス層テストは `len(get_hydrants())` で堅牢。実測は Green。 |
| Minor #3 Level 0 への `expected_cost_saved(0)` 実行 | 機能的に正しい（0円加算）。任意リファクタリング。 |
