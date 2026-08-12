"""check_orcarouter.py: Orcarouter LLM 自動起票およびフォールバック（ORCAROUTER_ENABLED=false）の検証スクリプト。"""

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# backend ディレクトリを sys.path に追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.schemas.alert import AlertAnalysis, AlertDetail, Location
from app.schemas.pipe import PipeRecord
from app.services.orcarouter import create_work_order


async def test_fallback():
    # 強制的にフォールバックモードを有効化
    os.environ["ORCAROUTER_ENABLED"] = "false"

    mock_alert = AlertDetail(
        telemetry_id="TEL-OR3-TEST",
        sensor_id="SEN-001",
        hydrant_id="HYD-001",
        severity_level=2,
        leak_confidence=85,
        detected_at=datetime.now(UTC),
        location=Location(latitude=35.6812, longitude=139.7671),
        analysis=AlertAnalysis(
            leak_confidence=85,
            severity_level=2,
            dominant_freq_hz=450.0,
            band_energy_ratio=3.2,
        ),
    )

    mock_pipe = PipeRecord(
        pipe_id="PIPE-001",
        material="DIP",
        diameter_mm=150,
        installed_year=1998,
        burial_depth_m=1.2,
        address="東京都千代田区1-1",
    )

    async with httpx.AsyncClient() as client:
        work_order = await create_work_order(client, "TEL-OR3-TEST", mock_alert, mock_pipe)

        print("=== OR-3 フォールバック動作検証結果 ===")
        print(f"WorkOrder ID : {work_order.work_order_id}")
        print(f"Source       : {work_order.source}")
        print(f"Cost Yen     : {work_order.cost_yen}")
        print(f"Urgency      : {work_order.urgency}")
        print(f"Total Yen    : {work_order.total_estimate_yen}円")
        print(f"Parts Count  : {len(work_order.parts)}")
        print(f"Part Name    : {work_order.parts[0].name}")
        print("=========================================")

        # 受け入れ条件のアサーション
        assert work_order.source == "fallback", "source が fallback になっていません"
        assert work_order.cost_yen == 0.0, "cost_yen が 0 になっていません"
        assert len(work_order.parts) > 0, "部材が引き当てられていません"
        print("✔ すべてのフォールバック受け入れ条件をクリアしました！")


if __name__ == "__main__":
    asyncio.run(test_fallback())
