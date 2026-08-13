"""BE-5: Orcarouter LLM自動起票サービスの単体テスト.

``httpx.MockTransport`` で LLM をモックし、``create_work_order()`` /
``build_fallback_work_order()`` の挙動（成功・リトライ分類・フォールバック・キャッシュ・
FR-6 計測・NFR-4）を検証する。実 HTTP 通信は行わない。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_orcarouter.py -v
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.schemas.alert import AlertDetail
from app.schemas.pipe import PipeRecord
from app.schemas.telemetry import AnalysisResult, GeoLocation, SpectrumPoint
from app.schemas.work_order import WorkOrder
from app.services import orcarouter
from app.services.orcarouter import (
    build_fallback_work_order,
    clear_work_order_cache,
    create_work_order,
)

N_SPECTRUM = 128


def make_alert(telemetry_id: str = "TLM-001", severity_level: int = 3) -> AlertDetail:
    """テスト用 AlertDetail を1件生成する."""
    now = datetime.now(timezone.utc)
    return AlertDetail(
        telemetry_id=telemetry_id,
        sensor_id="SNS-001",
        hydrant_id="HYD-001",
        severity_level=severity_level,
        leak_confidence=90.0,
        detected_at=now,
        location=GeoLocation(latitude=35.7019, longitude=139.7444),
        analysis=AnalysisResult(
            leak_confidence=90.0,
            severity_level=severity_level,
            dominant_freq_hz=900.0,
            band_energy_ratio=0.75,
            spectrum=[
                SpectrumPoint(freq_hz=float(i), magnitude=1.0) for i in range(N_SPECTRUM)
            ],
        ),
    )


def make_pipe(material: str = "ductile_iron", diameter_mm: int = 150) -> PipeRecord:
    """テスト用 PipeRecord を生成する（既定は ductile_iron / 150mm）。"""
    return PipeRecord.model_validate(
        {
            "pipe_id": "P-001",
            "material": material,
            "diameter_mm": diameter_mm,
            "installed_year": 1998,
            "burial_depth_m": 1.2,
            "route": {
                "type": "LineString",
                "coordinates": [[139.7426, 35.7027], [139.7444, 35.7019]],
            },
            "hydrant_ids": ["HYD-001"],
        }
    )


def _valid_work_order_json() -> str:
    """WorkOrder 契約を満たす JSON 文字列（LLM が返す本文）。"""
    return json.dumps(
        {
            "parts": [
                {
                    "name": "ダクタイル鋳鉄管継手",
                    "spec": "A形 150mm",
                    "quantity": 2,
                    "unit_price_yen": 15000,
                    "subtotal_yen": 30000,
                }
            ],
            "total_estimate_yen": 30000,
            "work_steps": ["漏水箇所を止水する。", "損傷部材を交換する。", "通水試験を実施する。"],
            "required_workers": 2,
            "estimated_duration_hours": 3.5,
            "urgency": "critical",
            "notification_text": "漏水検知に伴う補修工事が必要です。",
            "source": "llm",
        },
        ensure_ascii=False,
    )


async def _success_response(request: httpx.Request | None = None) -> httpx.Response:
    """正常な Orcarouter レスポンス（usage / 実モデル名付き）を返す。"""
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": _valid_work_order_json()}}],
            "usage": {"prompt_tokens": 800, "completion_tokens": 200},
            "model": "orcarouter-pro-2026",
        },
    )


class _CountingHandler:
    """呼び出し回数とリクエストを記録する MockTransport ハンドラ。"""

    def __init__(self, handler: Any) -> None:
        self.calls = 0
        self.handler = handler
        self.requests: list[httpx.Request] = []

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        self.requests.append(request)
        return await self.handler(request)


def _run_with_handler(wrapped: _CountingHandler, *args: Any) -> WorkOrder:
    """MockTransport 経由で create_work_order を実行する。"""

    async def _drive() -> WorkOrder:
        transport = httpx.MockTransport(wrapped)
        async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
            return await create_work_order(client, *args)

    return asyncio.run(_drive())


def _run_create(
    handler: Any, *args: Any
) -> tuple[WorkOrder, _CountingHandler]:
    """ハンドラをラップして create_work_order を実行し、(WorkOrder, 呼び出し記録) を返す。"""
    wrapped = _CountingHandler(handler)
    order = _run_with_handler(wrapped, *args)
    return order, wrapped


@pytest.fixture(autouse=True)
def _clear_cache():
    """各テスト前にワークオーダーキャッシュを空にしてテスト間を隔離する."""
    clear_work_order_cache()
    yield
    clear_work_order_cache()


class TestCreateWorkOrder:
    """create_work_order() の正常系・FR-6 計測。"""

    def test_t1_success_returns_llm_work_order_with_full_content(self, monkeypatch):
        """正常応答で source=="llm" かつ部材・見積・手順・文面が埋まる（受入2）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        order, handler = _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        assert order.source == "llm"
        assert order.parts
        assert order.total_estimate_yen == sum(p.subtotal_yen for p in order.parts)
        assert order.work_steps
        assert order.notification_text
        assert handler.calls == 1

    def test_t2_fr6_usage_and_real_model_and_latency(self, monkeypatch):
        """usage のトークン数・実モデル名・latency_ms が反映される（受入3・4・5）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        order, _ = _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        assert order.prompt_tokens == 800
        assert order.completion_tokens == 200
        assert order.model == "orcarouter-pro-2026"  # 事前指定と異なる実測値を優先
        assert order.latency_ms > 0
        assert order.cost_yen > 0.0
        assert order.is_estimated is False

    def test_success_without_usage_and_model_uses_env_defaults(self, monkeypatch):
        """usage・実モデル名が無い応答では env 既定値と概算フラグが使われる。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        monkeypatch.setenv("ORCAROUTER_MODEL", "custom-model")

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": _valid_work_order_json()}}]},
            )

        order, _ = _run_create(handler, "TLM-001", make_alert(), make_pipe())

        assert order.source == "llm"
        assert order.model == "custom-model"
        assert order.is_estimated is True
        assert order.cost_yen > 0.0

    def test_5xx_then_success_returns_llm_work_order(self, monkeypatch):
        """一時的な 5xx は1回リトライし、2回目で成功したら llm 応答を返す。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        state = {"count": 0}

        async def handler(request: httpx.Request) -> httpx.Response:
            state["count"] += 1
            if state["count"] == 1:
                return httpx.Response(503, json={"error": "unavailable"})
            return await _success_response()

        order, handler_wrapped = _run_create(handler, "TLM-001", make_alert(), make_pipe())

        assert handler_wrapped.calls == 2
        assert order.source == "llm"

    def test_success_with_pipe_none(self, monkeypatch):
        """配管台帳該当なし（pipe=None）でも LLM 成功応答で WorkOrder を返す。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        order, _ = _run_create(_success_response, "TLM-001", make_alert(), None)

        assert order.source == "llm"
        assert order.total_estimate_yen == 30000
        assert order.parts

    @pytest.mark.parametrize(
        "usage",
        [
            pytest.param(
                {"prompt_tokens": "abc", "completion_tokens": 200},
                id="non_numeric_prompt",
            ),
            pytest.param(
                {"prompt_tokens": 800, "completion_tokens": "xyz"},
                id="non_numeric_completion",
            ),
            pytest.param({"prompt_tokens": 800}, id="missing_completion_tokens"),
            pytest.param({"completion_tokens": 200}, id="missing_prompt_tokens"),
            pytest.param(
                {"prompt_tokens": -1, "completion_tokens": 200},
                id="negative_tokens",
            ),
            pytest.param("usage-string", id="usage_not_dict"),
        ],
    )
    def test_invalid_usage_falls_back_without_500(
        self, monkeypatch, caplog, usage
    ):
        """usage 不正でも 500 にせずフォールバック（Major #1）。

        非数値・キー欠落・負値・非 dict 時に不正値がint()変換で
        ValueError→500 になるため、orcarouter側で検証してフォールバック。
        """
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": _valid_work_order_json()}}],
                    "usage": usage,
                    "model": "orcarouter-pro-2026",
                },
            )

        caplog.set_level(logging.INFO)
        order, handler_wrapped = _run_create(handler, "TLM-001", make_alert(), make_pipe())

        assert handler_wrapped.calls == 1  # 2xx 成功応答のためリトライしない
        assert order.source == "fallback"
        assert "応答パース失敗" in caplog.text


class TestFallback:
    """フォールバック系（受入6・7・8・9・13）。"""

    def test_t3_missing_api_key_falls_back_without_http(self, monkeypatch):
        """API キー未設定では HTTP 呼び出し0回で source=="fallback"（受入6）。"""
        monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
        order, handler = _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 0
        assert order.source == "fallback"
        assert order.cost_yen == 0.0
        assert order.prompt_tokens == 0

    def test_enabled_false_forces_fallback(self, monkeypatch):
        """ORCAROUTER_ENABLED=false は API キーがあってもフォールバック強制。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        monkeypatch.setenv("ORCAROUTER_ENABLED", "false")
        order, handler = _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 0
        assert order.source == "fallback"

    def test_t4_timeout_retries_once_then_fallback(self, monkeypatch):
        """タイムアウトは1回リトライ（呼び出し2回）→ 再失敗でフォールバック（受入7）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def timeout_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timeout")

        order, handler = _run_create(timeout_handler, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 2
        assert order.source == "fallback"

    def test_t6_5xx_retries_once_then_fallback(self, monkeypatch):
        """5xx は1回リトライ（呼び出し2回）→ 再失敗でフォールバック。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler_500(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "unavailable"})

        order, handler = _run_create(handler_500, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 2
        assert order.source == "fallback"

    def test_t6_4xx_no_retry_immediate_fallback(self, monkeypatch, caplog):
        """4xx はリトライせず（呼び出し1回）即フォールバック + 理由ログ（受入8）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler_401(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "unauthorized"})

        caplog.set_level(logging.INFO)
        order, handler = _run_create(handler_401, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 1
        assert order.source == "fallback"
        assert "401" in caplog.text

    @pytest.mark.parametrize(
        "response_factory",
        [
            pytest.param(
                lambda: httpx.Response(200, json={"unexpected": True}),
                id="missing_choices",
            ),
            pytest.param(
                lambda: httpx.Response(200, json={"choices": []}),
                id="empty_choices",
            ),
            pytest.param(
                lambda: httpx.Response(200, json={"choices": [{"message": "oops"}]}),
                id="non_dict_message",
            ),
            pytest.param(
                lambda: httpx.Response(200, json={"choices": [{"message": {"content": 123}}]}),
                id="non_str_content",
            ),
            pytest.param(
                lambda: httpx.Response(
                    200, json={"choices": [{"message": {"content": "not json"}}]}
                ),
                id="non_json_content",
            ),
            pytest.param(
                lambda: httpx.Response(
                    200,
                    json={
                        "choices": [{"message": {"content": json.dumps({"foo": 1})}}]
                    },
                ),
                id="schema_mismatch",
            ),
        ],
    )
    def test_t7_parse_failure_no_retry_fallback(
        self, monkeypatch, caplog, response_factory
    ):
        """パース失敗（非 JSON / choices 欠落 / スキーマ不整合）はリトライなし即フォールバック。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler(request: httpx.Request) -> httpx.Response:
            return response_factory()

        caplog.set_level(logging.INFO)
        order, handler = _run_create(handler, "TLM-001", make_alert(), make_pipe())

        assert handler.calls == 1
        assert order.source == "fallback"
        assert "応答パース失敗" in caplog.text

    def test_t5_fallback_content_from_repair_parts(self, monkeypatch):
        """フォールバック時も部材・見積合計・手順・文面が repair_parts.json 由来（受入9）。"""
        monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
        order, _ = _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        assert order.source == "fallback"
        assert order.parts
        assert order.total_estimate_yen == sum(p.subtotal_yen for p in order.parts)
        assert order.work_steps
        assert order.notification_text
        assert order.required_workers > 0

    def test_fallback_not_cached_retries_llm_on_next_call(self, monkeypatch):
        """フォールバック結果はキャッシュせず、次回呼び出しで LLM を再試行する（Minor #4）。

        一時的な障害（5xx）が telemetry_id に永続化しないよう、LLM 成功時のみキャッシュする。
        2回目も LLM を再試行するため、各回1リトライで計4回の呼び出しになる。
        """
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler_503(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"error": "unavailable"})

        wrapped = _CountingHandler(handler_503)
        first = _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())
        second = _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())

        assert first.source == "fallback"
        assert second.source == "fallback"
        assert wrapped.calls == 4


class TestNfrAndCache:
    """NFR-4・キャッシュ・構造化ログ（受入10・11・12・13）。"""

    def test_t8_api_key_not_in_logs_or_work_order(self, monkeypatch, caplog):
        """ログ・WorkOrder に API キーが含まれない（認証ヘッダーには使われる）（受入10）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-supersecret")

        async def handler_401(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "unauthorized"})

        caplog.set_level(logging.INFO)
        order, handler = _run_create(handler_401, "TLM-001", make_alert(), make_pipe())

        assert "sk-supersecret" not in caplog.text
        assert "sk-supersecret" not in order.model_dump_json()
        # キーは Authorization ヘッダーで送信されている（実装確認）
        assert handler.requests[0].headers["authorization"] == "Bearer sk-supersecret"

    def test_t9_cache_second_call_no_http_and_no_double_cost(
        self, monkeypatch, caplog
    ):
        """同一 telemetry_id の2回目は HTTP 呼び出し0回・原価再計上なし（受入11・12）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler(request: httpx.Request) -> httpx.Response:
            return await _success_response()

        wrapped = _CountingHandler(handler)
        caplog.set_level(logging.INFO)
        first = _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())
        second = _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())

        assert wrapped.calls == 1  # 2回目は LLM を呼ばない
        assert first.cost_yen == second.cost_yen
        assert first.prompt_tokens == second.prompt_tokens
        # 原価の構造化ログは1回だけ（二重計上しない）
        assert caplog.text.count("llm_cost_measured") == 1

    def test_cache_cleared_by_clear_work_order_cache(self, monkeypatch):
        """clear_work_order_cache() で分離すると再び LLM を呼ぶ。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        wrapped = _CountingHandler(_success_response)
        _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())
        clear_work_order_cache()
        _run_with_handler(wrapped, "TLM-001", make_alert(), make_pipe())
        assert wrapped.calls == 2

    def test_concurrent_same_id_calls_llm_once(self, monkeypatch):
        """同一 telemetry_id への並行 POST でも LLM は1回だけ呼ばれる（Minor #3）。

        キャッシュ get → await（HTTP）→ set の間に並行リクエストが割り込んでも、
        asyncio.Lock による直列化で LLM 二重呼び出し・原価二重ログを防ぐ。
        """
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")

        async def handler(request: httpx.Request) -> httpx.Response:
            await asyncio.sleep(0.02)  # 並行割り込みを確実に発生させる
            return await _success_response(request)

        wrapped = _CountingHandler(handler)

        async def _drive_concurrent() -> list[WorkOrder]:
            transport = httpx.MockTransport(wrapped)
            async with httpx.AsyncClient(transport=transport, timeout=30.0) as client:
                alert = make_alert()
                pipe = make_pipe()
                return await asyncio.gather(
                    create_work_order(client, "TLM-001", alert, pipe),
                    create_work_order(client, "TLM-001", alert, pipe),
                )

        results = asyncio.run(_drive_concurrent())
        assert wrapped.calls == 1
        assert [r.source for r in results] == ["llm", "llm"]
        assert results[0].prompt_tokens == results[1].prompt_tokens

    def test_t10_success_structured_log_contains_required_keys(
        self, monkeypatch, caplog
    ):
        """成功時の1行 JSON 構造化ログが必須キーを含む（受入13）。"""
        monkeypatch.setenv("ORCAROUTER_API_KEY", "sk-test")
        caplog.set_level(logging.INFO)
        _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        log_line = next(
            ln for ln in caplog.text.splitlines() if "llm_cost_measured" in ln
        )
        payload = json.loads(log_line[log_line.index("{") :])
        for key in (
            "telemetry_id",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "cost_yen",
            "source",
            "latency_ms",
        ):
            assert key in payload
        assert payload["telemetry_id"] == "TLM-001"
        assert payload["source"] == "llm"

    def test_t10_fallback_structured_log_contains_required_keys(
        self, monkeypatch, caplog
    ):
        """フォールバック時の1行 JSON 構造化ログが必須キー・cost_yen=0.0 を含む（受入13）。"""
        monkeypatch.delenv("ORCAROUTER_API_KEY", raising=False)
        caplog.set_level(logging.INFO)
        _run_create(_success_response, "TLM-001", make_alert(), make_pipe())

        log_line = next(
            ln for ln in caplog.text.splitlines() if "work_order_fallback" in ln
        )
        payload = json.loads(log_line[log_line.index("{") :])
        for key in (
            "telemetry_id",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "cost_yen",
            "source",
            "latency_ms",
        ):
            assert key in payload
        assert payload["source"] == "fallback"
        assert payload["cost_yen"] == 0.0


class TestBuildFallbackWorkOrder:
    """build_fallback_work_order() の単体テスト（部材マスタ・緊急度導出）。"""

    def test_known_material_and_diameter(self):
        """既知の材質×口径から repair_parts.json 由来の WorkOrder が生成される。"""
        order = build_fallback_work_order(make_alert(), make_pipe())
        assert order.source == "fallback"
        assert order.parts
        assert order.total_estimate_yen == sum(p.subtotal_yen for p in order.parts)
        assert order.cost_yen == 0.0
        assert order.work_steps
        assert order.notification_text

    def test_pipe_none_uses_default(self):
        """pipe が None（台帳該当なし）のときは default エントリが使われる。"""
        order = build_fallback_work_order(make_alert(), None)
        assert order.source == "fallback"
        assert order.parts
        assert order.total_estimate_yen == sum(p.subtotal_yen for p in order.parts)

    def test_unknown_combination_uses_default(self, monkeypatch):
        """材質×口径の未知の組合わせは default エントリが使われる。"""
        entry = {
            "parts": [
                {
                    "name": "仮部材",
                    "spec": "X",
                    "quantity": 1,
                    "unit_price_yen": 1000,
                    "subtotal_yen": 1000,
                }
            ],
            "work_steps": ["仮作業"],
            "required_workers": 1,
            "estimated_duration_hours": 1.0,
        }
        default_entry = {**entry, "required_workers": 3}
        partial = {
            "entries": {"ductile_iron": {"150": entry}},
            "default": default_entry,
        }
        monkeypatch.setattr(orcarouter, "_load_repair_parts", lambda: partial)

        # steel / 75 の組合わせはマスタに存在しない → default（required_workers=3）が使われる
        order = build_fallback_work_order(make_alert(), make_pipe(material="steel", diameter_mm=75))
        assert order.required_workers == 3
        assert order.source == "fallback"

    def test_broken_material_entry_uses_default(self, monkeypatch):
        """材質エントリがオブジェクトでない破損マスタでも default にフォールバックする。"""
        entry = {
            "parts": [
                {
                    "name": "仮部材",
                    "spec": "X",
                    "quantity": 1,
                    "unit_price_yen": 1000,
                    "subtotal_yen": 1000,
                }
            ],
            "work_steps": ["仮作業"],
            "required_workers": 1,
            "estimated_duration_hours": 1.0,
        }
        partial = {
            "entries": {"steel": "broken", "ductile_iron": {"150": entry}},
            "default": {**entry, "required_workers": 3},
        }
        monkeypatch.setattr(orcarouter, "_load_repair_parts", lambda: partial)

        order = build_fallback_work_order(make_alert(), make_pipe(material="steel", diameter_mm=75))
        assert order.required_workers == 3
        assert order.source == "fallback"

    def test_urgency_from_severity(self):
        """深刻度 Level から緊急度が導出される。"""
        level3_order = build_fallback_work_order(make_alert(severity_level=3), make_pipe())
        assert level3_order.urgency == "critical"
        level2_order = build_fallback_work_order(make_alert(severity_level=2), make_pipe())
        assert level2_order.urgency == "high"
        level1_order = build_fallback_work_order(make_alert(severity_level=1), make_pipe())
        assert level1_order.urgency == "medium"
        level0_order = build_fallback_work_order(make_alert(severity_level=0), make_pipe())
        assert level0_order.urgency == "low"


class TestRepairPartsLoader:
    """repair_parts.json ローダーの例外系。"""

    def test_missing_file_raises_runtime_error(self, monkeypatch):
        """ファイル欠損は RuntimeError を上げる（サイレントな空マスタにしない）。"""
        monkeypatch.setattr(
            orcarouter, "REPAIR_PARTS_PATH", Path("does/not/exist/repair_parts.json")
        )
        orcarouter._load_repair_parts.cache_clear()
        with pytest.raises(RuntimeError):
            orcarouter._load_repair_parts()

    def test_invalid_structure_raises_type_error(self, monkeypatch, tmp_path):
        """必須キー（default）欠落は TypeError を上げる。"""
        bad = tmp_path / "repair_parts.json"
        bad.write_text(json.dumps({"entries": {}}), encoding="utf-8")
        monkeypatch.setattr(orcarouter, "REPAIR_PARTS_PATH", bad)
        orcarouter._load_repair_parts.cache_clear()
        with pytest.raises(TypeError):
            orcarouter._load_repair_parts()

    def test_entries_missing_raises_type_error(self, monkeypatch, tmp_path):
        """entries キー欠落は TypeError を上げる。"""
        bad = tmp_path / "repair_parts.json"
        bad.write_text(json.dumps({"default": {}}), encoding="utf-8")
        monkeypatch.setattr(orcarouter, "REPAIR_PARTS_PATH", bad)
        orcarouter._load_repair_parts.cache_clear()
        with pytest.raises(TypeError):
            orcarouter._load_repair_parts()

    def test_entry_missing_required_key_raises_type_error(self, monkeypatch, tmp_path):
        """エントリ内の必須キー欠落（parts 等）は TypeError を上げる（Minor #5）。

        フォールバック安全網が KeyError → 500 にならないよう、ローダーでエントリ形状
        （parts / work_steps / required_workers / estimated_duration_hours）を検証する。
        """
        bad = tmp_path / "repair_parts.json"
        bad.write_text(
            json.dumps(
                {
                    "entries": {"ductile_iron": {"150": {"parts": []}}},
                    "default": {"parts": []},
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(orcarouter, "REPAIR_PARTS_PATH", bad)
        orcarouter._load_repair_parts.cache_clear()
        with pytest.raises(TypeError):
            orcarouter._load_repair_parts()

    def test_non_dict_material_entry_ignored_by_loader(self, monkeypatch, tmp_path):
        """非 dict の材質エントリはローダー検証をスキップし、default 検証は実施される。

        材質エントリがオブジェクトでない破損マスタでもローダーは TypeError にせず、
        ``_lookup_repair_parts`` が default へ落とす挙動と整合させる。
        """
        part = {
            "name": "仮部材",
            "spec": "X",
            "quantity": 1,
            "unit_price_yen": 100,
            "subtotal_yen": 100,
        }
        valid_entry = {
            "parts": [part],
            "work_steps": ["仮作業"],
            "required_workers": 1,
            "estimated_duration_hours": 1.0,
        }
        data = {
            "entries": {"steel": "broken", "ductile_iron": {"150": valid_entry}},
            "default": valid_entry,
        }
        path = tmp_path / "repair_parts.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(orcarouter, "REPAIR_PARTS_PATH", path)
        orcarouter._load_repair_parts.cache_clear()
        loaded = orcarouter._load_repair_parts()
        assert loaded["entries"]["steel"] == "broken"
        assert loaded["default"]["required_workers"] == 1

    def test_non_dict_diameter_entry_ignored_by_loader(self, monkeypatch, tmp_path):
        """非 dict の口径エントリはローダー検証をスキップする（_lookup が default へ落とす）。"""
        part = {
            "name": "仮部材",
            "spec": "X",
            "quantity": 1,
            "unit_price_yen": 100,
            "subtotal_yen": 100,
        }
        valid_entry = {
            "parts": [part],
            "work_steps": ["仮作業"],
            "required_workers": 1,
            "estimated_duration_hours": 1.0,
        }
        data = {
            "entries": {"ductile_iron": {"150": "broken", "75": valid_entry}},
            "default": valid_entry,
        }
        path = tmp_path / "repair_parts.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(orcarouter, "REPAIR_PARTS_PATH", path)
        orcarouter._load_repair_parts.cache_clear()
        loaded = orcarouter._load_repair_parts()
        assert loaded["entries"]["ductile_iron"]["150"] == "broken"
        assert loaded["entries"]["ductile_iron"]["75"]["required_workers"] == 1
