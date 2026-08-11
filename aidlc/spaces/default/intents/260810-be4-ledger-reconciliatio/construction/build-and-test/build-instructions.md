# Build Instructions — BE-4 配管台帳照合サービス（ledger.py）

> 対象スコープ: be4-ledger-reconciliation（バックエンドのみ）
> 上流成果物: `construction/be4-ledger/code-generation/code-generation-plan.md`・`construction/be4-ledger/code-generation/code-summary.md`
> 言語・規約: Python 3.11+ / Pydantic v2 / コメント・ドキュメントは日本語

## 1. 依存関係の導入

```powershell
# プロジェクトルートから backend へ移動
cd backend

# 仮想環境が未作成の場合のみ（既存プロジェクトでは backend/venv が存在）
# python -m venv venv

# 依存ライブラリの導入（requirements.txt は固定バージョン）
venv\Scripts\pip.exe install -r requirements.txt
```

主な依存: `fastapi` / `pydantic`(v2) / `uvicorn` / `pytest` / `numpy` / `scipy` / `httpx`（テストクライアント）ほか。

## 2. 環境セットアップ

- **環境変数**: BE-4 では不要（認証・外部サービス・シークレットは使用しない。CLAUDE.md §3 のスコープ外）。
- **設定ファイル**: 不要。配管台帳は `backend/app/data/pipes.json`（JSON 固定パス、cwd 非依存で解決）。
- **ローカルサービス**: 不要（インメモリストア + JSON 台帳のみ。本番用 DB は構築しない）。

## 3. ビルドコマンド

Python バックエンドにはコンパイル工程がないため、「ビルド」を以下で定義する。

1. **依存導入の確認**
   ```powershell
   venv\Scripts\pip.exe list
   ```

2. **アプリ import スモークテスト**（実行環境の健全性を確認）
   ```bash
   venv/Scripts/python.exe -c "from main import app; from app.services.ledger import get_pipes; assert len(get_pipes()) == 10; print('import-smoke OK')"
   ```
   → 期待出力: `import-smoke OK`（pipes.json 10 路線が読める）

3. **フロントエンド（Next.js）**: 本スコープはバックエンドのみの変更で、`pipe_info` は従来から `AlertDetail` スキーマに null 許容で存在する（形は不変）。フロントエンドのビルド・テストは変更対象外のため実行不要。

## 4. ビルド検証

- **テスト**: `python -m pytest`（下記「Unit Test Instructions」参照）
- **動作検証スクリプト**: `python scripts/check_ledger.py` → 7/7 PASS・終了コード 0
- **サーバー起動確認（任意）**:
  ```powershell
  venv\Scripts\uvicorn.exe main:app --reload --port 8000
  ```
  `GET http://localhost:8000/api/v1/alerts` が 200 を返すこと。

## 5. トラブルシューティング

| 症状 | 原因・対処 |
|------|-----------|
| `pytest.exe` で `No module named 'app'` | `venv/Scripts/pytest.exe` は cwd を sys.path に挿入しない。**必ず `venv/Scripts/python.exe -m pytest`** で実行する（`python -m` は cwd を挿入するため `app` が import できる） |
| `No module named 'app.main'` | エントリポイントは `backend/main.py`。import は `from main import app`（`app.main` ではない） |
| `pipes.json` 欠損・破損で 500 | `backend/app/data/pipes.json` が存在し有効な JSON であることを確認（A4 の仕様どおり例外はそのまま伝播する） |
| キャッシュが更新されない | `get_pipes()` は `@lru_cache` でプロセス内キャッシュ。pipes.json を変更したらプロセスを再起動する（本番で台帳更新がある場合の再読込は既知の Minor 事項） |
