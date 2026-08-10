---
name: fastapi-pydantic-v2-patterns
description: >
  FastAPI（このプロジェクトは 0.141.1）+ Pydantic v2（2.13.4）でのスキーマ定義、
  strict validation、非同期エンドポイント（async def + httpx）、CORS設定、Depends()
  による依存性注入の作法をまとめたリファレンス。センサーデータ受信スキーマや
  Orcarouter への非同期APIリクエスト実装で使う。
  Triggers on: backend/app 配下のPydanticモデル・エンドポイント作成、FastAPIの
  リクエスト/レスポンススキーマ定義、CORS設定、外部API（Orcarouter等）への非同期
  リクエスト実装、依存性注入(Depends)の設計。
---

# FastAPI + Pydantic v2 パターン（このプロジェクト向け）

## このプロジェクトの前提

- インストール済み: FastAPI **0.141.1**, Pydantic **2.13.4**, pydantic-core, uvicorn
  **0.52.1**, NumPy, SciPy。
- **httpx は未インストール**。Orcarouter への非同期リクエストを実装する際は先に
  `backend/venv/Scripts/python.exe -m pip install httpx` が必要（CLAUDE.md の規約に
  従い、コマンドは必ず venv のパスを使うこと）。
- **依存関係マニフェスト（`requirements.txt` / `pyproject.toml`）がまだ存在しない**。
  新しい依存を追加したら `backend/venv/Scripts/python.exe -m pip freeze >
  backend/requirements.txt` のような形で固定することを検討する（ライブラリ追加は
  CLAUDE.md の Human-in-the-Loop 原則によりユーザー承認が必要）。
- CLAUDE.md の規約：Orcarouter の APIキー等の機密情報は必ず `backend/.env` に置き、
  Next.js フロントエンドへ露出させない。FFT解析・深刻度判定ロジックは
  `backend/app/services/audio.py` に集約する（→ `numpy-scipy-signal-processing`
  スキール参照）。

## Pydantic v2 の作法（v1 遺物を書かない）

Pydantic v2 では設定・シリアライズ方法が変わっている。v1時代の書き方が訓練データに
混ざりやすいので注意する：

| v1（使わない） | v2（使う） |
|---|---|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `@validator` | `@field_validator` |
| `model.dict()` | `model.model_dump()` |
| `model.json()` | `model.model_dump_json()` |
| `Model.parse_obj(data)` | `Model.model_validate(data)` |

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SensorReading(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)

    sensor_id: str = Field(min_length=1)
    recorded_at: datetime
    audio_base64: str
    sample_rate_hz: int = Field(gt=0)

    @field_validator("audio_base64")
    @classmethod
    def must_be_base64(cls, v: str) -> str:
        import base64

        try:
            base64.b64decode(v, validate=True)
        except Exception as exc:
            raise ValueError("audio_base64 must be valid base64") from exc
        return v
```

`strict=True` を `ConfigDict` に指定すると、型が完全一致しない入力（例: 文字列
`"1"` を `int` フィールドに渡す）を拒否する。センサー由来の外部入力を受けるエンド
ポイントでは、暗黙の型強制より strict validation の方が異常データを早期に弾ける。

`...`（Ellipsis）をデフォルト値として使わない。必須フィールドは単に型注釈だけで
表現する（FastAPI公式skillでも明記されている非推奨パターン）。

## 非同期エンドポイント + Orcarouter への非同期リクエスト

`backend/app/services/orcarouter.py`（CLAUDE.md が指定するモジュール）は非同期I/Oを
行うので `async def` + `httpx.AsyncClient` を使う。クライアントは `Depends()` 経由で
注入し、アプリのライフサイクルで使い回す：

```python
# backend/app/dependencies.py
from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
from fastapi import Depends


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


HttpClientDep = Annotated[httpx.AsyncClient, Depends(get_http_client)]
```

```python
# backend/app/services/orcarouter.py
import os

import httpx


async def request_repair_estimate(
    client: httpx.AsyncClient, payload: dict
) -> dict:
    api_key = os.environ["ORCAROUTER_API_KEY"]  # backend/.env から読む。フロントには渡さない
    response = await client.post(
        "https://api.orcarouter.example/v1/estimates",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    response.raise_for_status()
    return response.json()
```

`async def` はイベントループをブロックしない処理（`await` で完結する I/O）専用。
NumPy/SciPy によるFFT計算のような CPU バウンドな同期処理を `async def` の中に
そのまま書くとイベントループを止めてしまうため、通常の `def` エンドポイント
（FastAPIがスレッドプールで実行する）にするか、`run_in_threadpool` で明示的に
逃がす。

```python
from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/{sensor_id}/readings")
async def ingest_reading(sensor_id: str, reading: SensorReading) -> AnalysisResult:
    # audio.py のFFT解析はCPUバウンドなのでスレッドプールに逃がす
    result = await run_in_threadpool(analyze_audio, reading)
    return result
```

## CORS 設定

フロントエンド（`next dev` は既定で `http://localhost:3000`）からバックエンド
（`uvicorn --port 8000`）への呼び出しを許可する：

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

本番相当のオリジンを追加する際は `allow_origins=["*"]` にせず、明示的なリストで
管理する（機微データを扱うインフラアプリのため）。

## 依存性注入（`Depends`）の最適化

- 型エイリアスを `Annotated[T, Depends(...)]` で作り、エンドポイントの引数として
  使い回す（上記 `HttpClientDep` の例）。シグネチャが読みやすくなり、テスト時に
  `app.dependency_overrides` で差し替えやすい。
- ルーター単位で共有する依存は `APIRouter(dependencies=[Depends(...)])` に置き、
  各エンドポイントに個別指定しない。
- `yield` を使う依存（DB接続やHTTPクライアントのライフサイクル管理）は、`yield`
  以降を `finally` 相当のクリーンアップとして使える。

## 実行コマンド（CLAUDE.md 規約）

```powershell
backend/venv/Scripts/uvicorn.exe main:app --reload --port 8000
backend/venv/Scripts/python.exe <script_name>.py
```

Windows環境のため、素の `python`/`uvicorn` コマンドではなく必ず venv 配下の実行
ファイルを直接指定する。
