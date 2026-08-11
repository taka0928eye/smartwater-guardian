# Build Instructions — SmartWater Guardian（BE-8 KPI サマリ）

> BE-8（`be8-kpi-summary`）のビルド手順。本ユニットは **バックエンド（Python/FastAPI）のみ** の変更で、
> フロントエンド（Next.js）はスコープ外（`frontend/src/app/page.tsx` の `MOCK_KPI_DATA` は変更しない）。
> したがって、ビルド対象はバックエンドに限定する（プロジェクト学習済みルール c2）。

## 前提条件

| 項目 | 値 |
|------|-----|
| Python | 3.11+（`backend/venv` に仮想環境を配置） |
| 依存パッケージ | `backend/requirements.txt`（FastAPI 0.141 / Pydantic 2.13 / NumPy 2.5 / SciPy 1.18 / pytest 9.1） |
| 作業ディレクトリ | `backend/`（すべてのコマンドはここから実行） |

## Step 1: 依存パッケージの導入確認

`venv` が存在し、必要なパッケージが導入済みであることを確認する。

```powershell
# backend ディレクトリで
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip freeze | Select-String -Pattern "fastapi|pydantic|pytest|numpy|scipy"
```

> 導入済みなら再インストールは不要。`requirements.txt` が変わった場合のみ実行する。

## Step 2: アプリ import スモークテスト

コンパイル工程がないため、「アプリが起動時に import できること」を import スモークで確認する。

```powershell
# backend ディレクトリで
.\venv\Scripts\python.exe -c "from main import app; print('OK:', len(app.routes), 'routes')"
```

期待出力（`kpi` ルーター登録後は4ルーター分の経路を含む）:

```
OK: <n> routes
```

`ImportError` や `ModuleNotFoundError` が出る場合は、`main.py` の import 文・依存関係を確認する。

## Step 3: サーバー起動確認（任意）

```powershell
# backend ディレクトリで
.\venv\Scripts\uvicorn.exe main:app --port 8000
```

起動後、`http://localhost:8000/api/v1/kpi/summary` に GET して 200 を確認する。
停止は Ctrl+C。

## Step 4: テスト・カバレッジ実行

品質基準（カバレッジ 80% 以上）の確認はユニットテスト指示書（`unit-test-instructions.md`）の手順に従う。

```powershell
# backend ディレクトリで
.\venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `ModuleNotFoundError: No module named 'app'` | `pytest.exe` 直呼び出しではなく `python.exe -m pytest` を使う（プロジェクト学習済みルール c3）。cwd（`backend/`）を `sys.path` に含めるため。 |
| ポート 8000 が使用中 | 別の uvicorn が起動中。プロセスを止めるか `--port 8001` で回避。 |
| カバレッジが 80% 未満 | 新規モジュール（`app/schemas/kpi.py` / `app/services/kpi.py` / `app/routers/kpi.py`）の未テスト分岐を確認。 |
