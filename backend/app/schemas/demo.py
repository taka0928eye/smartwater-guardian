"""DEMO-1/DEMO-2: デモシード投入 API の入出力スキーマ。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.telemetry import SeverityLevel, TelemetryRequest


class DemoSeedRequest(TelemetryRequest):
    """デモシード1件分。``TelemetryRequest`` に意図した深刻度を追加する。

    BE-3 の実 SVM は合成波形（``generate_signal``）を意図レベルに分類できない
    ため、デモシード専用に ``level`` をクライアントから確定させる（DEMO-1 調査）。
    音響解析値（スペクトル等）はサーバーが実信号から算出し、実データを装わない。
    """

    level: SeverityLevel = Field(description="意図した深刻度（デモ確定値）")


class DemoSeedBatchResponse(BaseModel):
    """POST /api/v1/demo/seed-batch の応答スキーマ（DEMO-2）。"""

    model_config = ConfigDict(strict=True, extra="forbid")

    status: str = Field(description="投入結果ステータス")
    inserted_count: int = Field(description="投入件数（常に23件）")
    level_counts: dict[str, int] = Field(description="深刻度別の件数内訳")
    message: str = Field(description="ステータスメッセージ")
