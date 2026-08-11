# Build and Test Results — alert-schema-cleanup

## 参照元

- ビルド手順: `build-instructions.md`
- 単体テスト手順: `unit-test-instructions.md`

## ビルド結果

**ステータス**: ✅ 成功

### アプリ import スモークテスト

```
$ venv/Scripts/python.exe -c "from main import app; print('OK: app import succeeded')"
OK: app import succeeded
```

### 型構築検証スクリプト

```
$ venv/Scripts/python.exe -c "..."
PipeMaterial: typing.Literal['ductile_iron', 'cast_iron', 'pvc', 'steel']
MIN_INSTALL_YEAR=1965, MAX_INSTALL_YEAR=2015
OK: PipeInfo constructed with material='ductile_iron'
```

## テスト結果

**ステータス**: ✅ 全件成功

### 実行コマンド

```
cd backend
venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing
```

### 集計

| 項目 | 値 |
|------|-----|
| 総テスト数 | 109 |
| 成功 | 109 |
| 失敗 | 0 |
| スキップ | 0 |
| 警告 | 1（本修正と無関係の既存 `httpx`/`starlette` 非推奨警告） |
| 実行時間 | 1.17秒 |

### カバレッジレポート

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app\__init__.py                0      0   100%
app\data\__init__.py           0      0   100%
app\dependencies.py            7      0   100%
app\routers\__init__.py        0      0   100%
app\routers\alerts.py         28      0   100%
app\routers\sensors.py        23      0   100%
app\routers\telemetry.py      62      0   100%
app\schemas\__init__.py        0      0   100%
app\schemas\alert.py          60      0   100%
app\schemas\pipe.py           31      0   100%
app\schemas\telemetry.py      48      0   100%
app\services\__init__.py       0      0   100%
app\services\ledger.py        41      0   100%
app\store.py                  75      0   100%
--------------------------------------------------------
TOTAL                        375      0   100%
```

**カバレッジ**: 100%（CLAUDE.md §4 の80%以上の要求を満たす）

### 新規テスト（本修正で追加）

| テスト | 結果 |
|--------|------|
| `test_alerts.py::TestPipeInfoSchema::test_material_outside_pipe_material_literal_raises_validation_error` | PASSED |
| `test_pipes.py::test_installed_year_boundary_rejects_below_min_accepts_min_and_max` | PASSED |

### 失敗・障害

なし。

## 総合判定

ビルド・テストともに成功。カバレッジ・テストスイートの回帰要件（org.md Testing Posture: bugfix — 既存テストスイートはgreen維持）を満たしている。承認ゲートに進む準備が整っている。
