"""DEMO-1: デモシード投入 API の入力スキーマ。"""

from __future__ import annotations

from pydantic import Field

from app.schemas.telemetry import SeverityLevel, TelemetryRequest


class DemoSeedRequest(TelemetryRequest):
    """デモシード1件分。``TelemetryRequest`` に意図した深刻度を追加する。

    BE-3 の実 SVM は合成波形（``generate_signal``）を意図レベルに分類できない
    ため、デモシード専用に ``level`` をクライアントから確定させる（DEMO-1 調査）。
    音響解析値（スペクトル等）はサーバーが実信号から算出し、実データを装わない。
    """

    level: SeverityLevel = Field(description="意図した深刻度（デモ確定値）")
