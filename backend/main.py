from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import alerts, demo, disaster, kpi, sensors, telemetry

# .env ファイルを読み込み、環境変数を設定する（BE-5: Orcarouter LLM API 接続用）
load_dotenv()

app = FastAPI(title="SmartWater Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
