"""LLM統合の確認テスト"""
import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.alert import AlertDetail
from app.schemas.telemetry import AnalysisResult, GeoLocation
from app.services import orcarouter


@pytest.mark.asyncio
async def test_llm_is_called_when_enabled():
    """ORCAROUTER_ENABLED=true と API キーが設定されている場合、LLM が呼ばれることを確認"""

    # テスト用の環境変数
    with patch.dict(os.environ, {
        "ORCAROUTER_ENABLED": "true",
        "ORCAROUTER_API_KEY": "sk-test-key-12345",
        "ORCAROUTER_BASE_URL": "https://api.example.com/v1"
    }):
        # モック HTTP クライアント
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "parts": [
                            {
                                "name": "パイプ",
                                "spec": "100mm",
                                "quantity": 1,
                                "unit_price_yen": 5000,
                                "subtotal_yen": 5000,
                            }
                        ],
                        "total_estimate_yen": 50000,
                        "work_steps": ["修理"],
                        "required_workers": 2,
                        "estimated_duration_hours": 4.0,
                        "urgency": "high",
                        "notification_text": "テスト",
                    })
                }
            }],
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
            },
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        # テスト用アラート
        alert = AlertDetail(
            telemetry_id="test-001",
            sensor_id="SNS-001",
            hydrant_id="HY-001",
            severity_level=2,
            leak_confidence=85.0,
            detected_at=datetime(2026, 8, 13, 10, 0, 0),
            location=GeoLocation(latitude=35.6812, longitude=139.7671),
            analysis=AnalysisResult(
                leak_confidence=85.0,
                severity_level=2,
                dominant_freq_hz=800,
                band_energy_ratio=0.75
            ),
            pipe_info=None
        )

        # LLM を呼び出す
        orcarouter.clear_work_order_cache()
        result = await orcarouter.create_work_order(mock_client, "test-001", alert, None)

        # 検証
        print("SUCCESS: WorkOrder generated")
        print(f"  Source: {result.source}")
        print(f"  Model: {result.model}")
        print(f"  Cost: {result.cost_yen}")
        print(f"  Total Estimate: {result.total_estimate_yen}")

        # LLM が呼ばれたことを確認
        assert mock_client.post.called, "LLM API should be called"
        print("SUCCESS: LLM API was called")

        # source が "llm" であることを確認
        assert result.source == "llm", f"source should be 'llm', got {result.source}"
        print("SUCCESS: Source is 'llm'")

        # cost が計算されていることを確認
        assert result.cost_yen is not None and result.cost_yen > 0, "Cost should be calculated"
        print(f"SUCCESS: Cost calculated: {result.cost_yen} yen")

        return result


if __name__ == "__main__":
    result = asyncio.run(test_llm_is_called_when_enabled())
    print("\n=== ALL TESTS PASSED ===")
    print(f"Final result - source: {result.source}, cost: {result.cost_yen}")
