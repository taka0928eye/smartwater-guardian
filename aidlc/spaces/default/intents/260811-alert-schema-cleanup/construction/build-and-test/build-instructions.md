# Build Instructions — alert-schema-cleanup

## 参照元

- 承認済みプラン: `aidlc/spaces/default/intents/260811-alert-schema-cleanup/construction/alert-schema-cleanup/code-generation/code-generation-plan.md`
- 実装サマリー: `aidlc/spaces/default/intents/260811-alert-schema-cleanup/construction/alert-schema-cleanup/code-generation/code-summary.md`

このバグ修正は `backend/app/schemas/pipe.py`・`backend/app/schemas/alert.py`（および対応するテストファイル）のみを変更する。フロントエンドは変更対象外（requirements.md Out of Scope に明記）のため、ビルド対象はバックエンドのみ。

## 対象範囲

- **バックエンド**: `backend/`（Python、FastAPI）— ビルド手順の対象
- **フロントエンド**: `frontend/`（Next.js）— 本修正では変更なし、ビルド対象外

project.md の学習事項（cid:build-and-test:c2）に従い、バックエンド Python のビルドは「依存導入の確認 + アプリ import スモークテスト + 検証スクリプト実行」で定義する（Python にはコンパイル工程がないため）。

## 前提環境

- Python 3.11+（本プロジェクトの venv は Python 3.14.5 で構築済み）
- 仮想環境: `backend/venv/`（既存、`backend/venv/Scripts/python.exe` を使用）
- OS: Windows（コマンドはこの環境に合わせて記載）

## 依存関係の導入確認

```
cd backend
venv/Scripts/python.exe -m pip install -r requirements.txt
```

本修正はどのパッケージも追加・変更していないため、`requirements.txt` は据え置き。既存 venv に対する再インストールは冪等であることを確認する。

## ビルド検証コマンド

Python にはコンパイル工程がないため、「ビルド成功」は以下の2段階で判定する：

### 1. アプリ import スモークテスト

```
cd backend
venv/Scripts/python.exe -c "from main import app; print('OK: app import succeeded')"
```

`app/schemas/alert.py` と `app/schemas/pipe.py` の変更（`PipeMaterial` の相互インポート、`STRICT_INPUT_CONFIG` の参照）が循環インポート等を引き起こしていないことを、このスモークテストで確認する。

### 2. 検証スクリプト実行（型構築の健全性）

```
cd backend
venv/Scripts/python.exe -c "
from app.schemas.pipe import PipeMaterial, MIN_INSTALL_YEAR, MAX_INSTALL_YEAR
from app.schemas.alert import PipeInfo
print(f'PipeMaterial: {PipeMaterial}')
print(f'MIN_INSTALL_YEAR={MIN_INSTALL_YEAR}, MAX_INSTALL_YEAR={MAX_INSTALL_YEAR}')
info = PipeInfo(pipe_id='P-001', material='ductile_iron', diameter_mm=150, installed_year=1998, burial_depth_m=1.2, age_years=28)
print(f'OK: PipeInfo constructed with material={info.material!r}')
"
```

このスクリプトは、FR-1（型統一）・FR-4（named constant）で導入したシンボルが実際にインポート可能で、正常系の構築が成功することを確認する。

## トラブルシューティング

| 症状 | 原因候補 | 対処 |
|------|---------|------|
| `ImportError: cannot import name 'PipeMaterial'` | `alert.py` のインポート文の記述ミス | `from app.schemas.pipe import PipeMaterial` の綴りを確認 |
| `ImportError: cannot import name 'MIN_INSTALL_YEAR'` | `pipe.py` に定数が定義されていない | Step 1（FR-4）の実装漏れを確認 |
| 循環インポートエラー | `pipe.py` が `alert.py` を逆参照している | 依存方向は `alert.py → pipe.py` の一方向のみであることを確認（`pipe.py` は `alert.py` を import しない） |
| `pytest: command not found` | `pytest.exe` を直接実行しようとした | project.md 学習事項（cid:build-and-test:c3）の通り `venv/Scripts/python.exe -m pytest` を使用する |

## ビルド完了の判定基準

- アプリ import スモークテストが `OK: app import succeeded` を出力する
- 検証スクリプトが `OK: PipeInfo constructed with material='ductile_iron'` を出力する
- いずれかが失敗した場合、ビルド失敗として test-results.md に記録し、承認ゲートで報告する
