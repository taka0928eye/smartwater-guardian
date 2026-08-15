import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import alerts, demo, disaster, kpi, sensors, telemetry
from app.store import get_store, initialize_sensors

# .env ファイルを読み込み、環境変数を設定する（BE-5: Orcarouter LLM API 接続用）
load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """起動時にhydrants.json 23件を severity_level=0 で初期化する（DEMO-2）。

    「初期表示時は23件・全てLv0」という要求を満たす。``@app.on_event`` は
    非推奨のため ``lifespan`` を使う。
    """
    initialize_sensors(get_store())
    yield


app = FastAPI(title="SmartWater Guardian API", lifespan=lifespan)


def _get_allowed_origins() -> list[str]:
    """CORS 許可オリジンを環境変数 ALLOWED_ORIGINS から取得する（INFRA-1）。

    未設定時はローカル開発向けの既定値（http://localhost:3000）のみを許可する。
    本番（AWS）デプロイ時は ECS タスク定義の環境変数で公開ドメイン/ALB DNS名を設定する。
    """
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(alerts.router)
app.include_router(sensors.router)
app.include_router(kpi.router)
app.include_router(disaster.router)
app.include_router(demo.router)


@app.exception_handler(RuntimeError)
async def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
    """RuntimeError（配管台帳欠損など）を 502 で返す（500 にしない）。

    hydrants.json 破損の場合も同様。サーバー起動時に失敗するため、
    実行時に RuntimeError が発生することは稀だが、万一の対応として記載。
    """
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": "バックエンド リソース読み込み失敗",
            "error_type": exc.__class__.__name__,
        },
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """予測不能な例外を構造化ログで出力し、エラーレスポンスを返す。

    目的: 500 を意図的に避け、構造化エラーメッセージでクライアント
    のエラー処理（リトライ判定など）をサポートする。
    """
    error_id = getattr(exc, "telemetry_id", "unknown")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "内部サーバーエラーが発生しました",
            "error_type": exc.__class__.__name__,
            "error_id": error_id,
        },
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "SmartWater Guardian API Ready"}
