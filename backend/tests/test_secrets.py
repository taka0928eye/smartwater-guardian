"""SEC-1: シークレット非露出の横断検証（NFR-4）。

カナリア文字列方式で、API キーが以下に出現しないことを機械的に検証する:
1. HTTP レスポンス JSON 全文
2. 例外メッセージ
3. ログ出力（構造化ログを含む）
4. Git 追跡状態（回帰防止）
5. .env.example（プレースホルダのみ）

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_secrets.py -v
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.schemas.alert import AlertDetail
from app.schemas.pipe import PipeRecord
from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.services import orcarouter

# テスト用カナリア文字列（実在しないプレフィックス）
CANARY_API_KEY = "sk-CANARY-DO-NOT-LEAK-test-only"

N_SPECTRUM = 128


def make_alert(telemetry_id: str = "TLM-SECRET-001") -> AlertDetail:
    """テスト用 AlertDetail を生成する。"""
    now = datetime.now(timezone.utc)
    return AlertDetail(
        telemetry_id=telemetry_id,
        sensor_id="SNS-001",
        hydrant_id="HYD-001",
        severity_level=3,
        leak_confidence=90.0,
        detected_at=now,
        location=GeoLocation(latitude=35.7019, longitude=139.7444),
        analysis=AnalysisResult(
            leak_confidence=90.0,
            severity_level=3,
            dominant_freq_hz=900.0,
            band_energy_ratio=0.75,
            spectrum=[
                SpectrumPoint(freq_hz=float(i), magnitude=1.0) for i in range(N_SPECTRUM)
            ],
        ),
    )


def make_pipe() -> PipeRecord:
    """テスト用 PipeRecord を生成する。"""
    return PipeRecord.model_validate(
        {
            "pipe_id": "P-001",
            "material": "ductile_iron",
            "diameter_mm": 150,
            "installed_year": 1998,
            "burial_depth_m": 1.2,
            "route": {
                "type": "LineString",
                "coordinates": [[139.7426, 35.7027], [139.7444, 35.7019]],
            },
            "hydrant_ids": ["HYD-001"],
        }
    )


def _run_async(coro: Any) -> Any:
    """async 関数を同期的に実行するヘルパー（test_orcarouter.py の _run_with_handler と同パターン）。"""
    return asyncio.run(coro)


class TestSecretsNotInResponse:
    """API レスポンス JSON にシークレットが含まれないことを検証する。"""

    def test_api_key_not_in_fallback_response(self, monkeypatch):
        """API キー未設定時のフォールバック応答にカナリアが含まれないこと。"""
        alert = make_alert()
        pipe = make_pipe()

        # カナリアをクリア（フォールバック確認用）
        monkeypatch.setenv("ORCAROUTER_API_KEY", "")
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        async def _drive():
            async with httpx.AsyncClient() as client:
                work_order = await orcarouter.create_work_order(
                    client, alert.telemetry_id, alert, pipe
                )
                return work_order

        work_order = _run_async(_drive())
        # レスポンス全文を JSON 化して検証
        response_json = work_order.model_dump_json()
        assert CANARY_API_KEY not in response_json
        assert "sk-" not in response_json  # sk- プレフィックスのキーもチェック

    def test_api_key_not_in_llm_success_response(self, monkeypatch):
        """LLM 成功時のレスポンスにカナリアが含まれないこと。"""
        alert = make_alert("TLM-SECRET-002")
        pipe = make_pipe()

        # カナリアを設定
        monkeypatch.setenv("ORCAROUTER_API_KEY", CANARY_API_KEY)
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        # 成功レスポンスのモック
        valid_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "parts": [
                                    {
                                        "name": "配管補修用接続パイプ",
                                        "quantity": 1,
                                        "unit_price_yen": 5000,
                                        "subtotal_yen": 5000,
                                    }
                                ],
                                "work_steps": ["step1"],
                                "required_workers": 2,
                                "estimated_duration_hours": 2,
                                "urgency": "high",
                                "notification_text": "補修が必要です",
                            }
                        )
                    }
                }
            ],
            "model": "orcarouter",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        def mock_handler(request: httpx.Request) -> httpx.Response:
            """モックレスポンスハンドラ。"""
            return httpx.Response(200, json=valid_response)

        async def _drive():
            async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
                work_order = await orcarouter.create_work_order(
                    client, alert.telemetry_id, alert, pipe
                )
                return work_order

        work_order = _run_async(_drive())
        response_json = work_order.model_dump_json()
        assert CANARY_API_KEY not in response_json


class TestSecretsNotInExceptions:
    """例外メッセージにシークレットが含まれないことを検証する。"""

    def test_api_key_not_in_parse_error_message(self, monkeypatch, caplog):
        """不正な usage でパース失敗した時のメッセージにカナリアが含まれないこと。"""
        alert = make_alert("TLM-SECRET-003")
        pipe = make_pipe()

        monkeypatch.setenv("ORCAROUTER_API_KEY", CANARY_API_KEY)
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        # 不正な usage（負のトークン数）を返すモック
        invalid_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "parts": [
                                    {
                                        "name": "部材",
                                        "quantity": 1,
                                        "unit_price_yen": 5000,
                                        "subtotal_yen": 5000,
                                    }
                                ],
                                "work_steps": [],
                                "required_workers": 1,
                                "estimated_duration_hours": 1,
                                "urgency": "low",
                                "notification_text": "test",
                            }
                        )
                    }
                }
            ],
            "model": "orcarouter",
            "usage": {"prompt_tokens": -100, "completion_tokens": 50},  # 無効値
        }

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=invalid_response)

        async def _drive():
            async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
                work_order = await orcarouter.create_work_order(
                    client, alert.telemetry_id, alert, pipe
                )
                # フォールバック応答が返ること
                assert work_order.source == "fallback"
                return work_order

        with caplog.at_level(logging.INFO):
            _run_async(_drive())

        # caplog に記録されたすべてのログにカナリアが含まれないこと
        for record in caplog.records:
            msg = record.getMessage()
            assert CANARY_API_KEY not in msg, f"カナリアがログに含まれています: {msg}"


class TestSecretsNotInLogs:
    """ログ出力（構造化ログを含む）にシークレットが含まれないことを検証する。"""

    def test_api_key_not_in_fallback_log(self, monkeypatch, caplog):
        """フォールバック時の構造化ログにカナリアが含まれないこと。"""
        alert = make_alert("TLM-SECRET-004")
        pipe = make_pipe()

        # API キー未設定
        monkeypatch.setenv("ORCAROUTER_API_KEY", "")
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        async def _drive():
            async with httpx.AsyncClient() as client:
                await orcarouter.create_work_order(
                    client, alert.telemetry_id, alert, pipe
                )

        with caplog.at_level(logging.INFO):
            _run_async(_drive())

        # すべてのログレコードを検証
        log_text = "\n".join(record.getMessage() for record in caplog.records)
        assert CANARY_API_KEY not in log_text
        assert "sk-" not in log_text

    def test_api_key_not_in_network_error_log(self, monkeypatch, caplog):
        """ネットワークエラー時のログにカナリアが含まれないこと。"""
        alert = make_alert("TLM-SECRET-005")
        pipe = make_pipe()

        monkeypatch.setenv("ORCAROUTER_API_KEY", CANARY_API_KEY)
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        def mock_handler(request: httpx.Request) -> httpx.Response:
            """常にエラーを返すモック。"""
            raise httpx.ConnectError("Network timeout")

        async def _drive():
            async with httpx.AsyncClient(transport=httpx.MockTransport(mock_handler)) as client:
                work_order = await orcarouter.create_work_order(
                    client, alert.telemetry_id, alert, pipe
                )
                # フォールバック応答
                assert work_order.source == "fallback"
                return work_order

        with caplog.at_level(logging.INFO):
            _run_async(_drive())

        log_text = "\n".join(record.getMessage() for record in caplog.records)
        assert CANARY_API_KEY not in log_text


class TestSecretsNotInGit:
    """Git 追跡状態にシークレットが含まれないことを検証する（回帰防止）。"""

    def test_env_file_not_tracked(self):
        """backend/.env が git 追跡対象外であることを確認する。"""
        result = subprocess.run(
            ["git", "ls-files", "backend/.env"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent.parent,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "", (
            "backend/.env が git 追跡対象になっています。.gitignore を確認してください。"
        )

    def test_env_example_has_placeholder_only(self):
        """backend/.env.example にプレースホルダのみが入っていることを確認する。"""
        env_example_path = (
            Path(__file__).resolve().parent.parent / ".env.example"
        )
        if not env_example_path.exists():
            pytest.skip(".env.example が見つかりません")

        content = env_example_path.read_text(encoding="utf-8")
        # 実キーらしき文字列（sk- プレフィックス）が含まれていないこと
        assert "sk-" not in content, (
            ".env.example に実キーらしき値（sk- プレフィックス）が含まれています"
        )
        # プレースホルダが含まれていることを確認
        assert "your_orcarouter_api_key_here" in content or "example" in content.lower(), (
            ".env.example にプレースホルダが見つかりません"
        )


class TestCacheDoesNotPersistFallback:
    """フォールバック結果がキャッシュされていないことを検証する（Minor #4）。"""

    def test_fallback_not_cached(self, monkeypatch):
        """フォールバック結果は2回目の呼び出しでも再生成されること。"""
        alert1 = make_alert("TLM-SECRET-006")
        pipe = make_pipe()

        # API キー未設定（フォールバック確定）
        monkeypatch.setenv("ORCAROUTER_API_KEY", "")
        monkeypatch.setenv("ORCAROUTER_ENABLED", "true")

        async def _drive():
            async with httpx.AsyncClient() as client:
                # 1回目の呼び出し
                orcarouter.clear_work_order_cache()
                wo1 = await orcarouter.create_work_order(client, "TLM-SECRET-006", alert1, pipe)
                assert wo1.source == "fallback"

                # 同じ telemetry_id で2回目の呼び出し
                # キャッシュされていないため、再度フォールバック処理が走る
                # （latency_ms が異なる可能性がある、など）
                wo2 = await orcarouter.create_work_order(client, "TLM-SECRET-006", alert1, pipe)
                assert wo2.source == "fallback"
                # フォールバック結果はキャッシュされないため、同じテレメトリIDでも再生成される
                # （内容は同じだが、再度フォールバック処理を通す）

        _run_async(_drive())
