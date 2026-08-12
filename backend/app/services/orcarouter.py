"""Orcarouter LLM 自動起票サービス（BE-5）。

FR-3 / FR-4 の中核。解析結果（AlertDetail）と配管台帳（PipeRecord）から
Orcarouter 経由で LLM を呼び、補修部材選定・概算見積・作業指示書（WorkOrder）を
自動起票する。CLAUDE.md §5.3 の通り LLM 呼び出しは本モジュールにカプセル化する。

設計方針
- 環境変数は import 時ではなく**呼び出し時**に ``os.environ`` から読む（テスト分離を保つ）。
- API キー未設定 / ``ORCAROUTER_ENABLED=false`` は HTTP 呼び出しなしでフォールバック。
- リトライ分類: タイムアウト・ネットワーク・5xx は1回リトライ → 再失敗でフォールバック。
  4xx・パース失敗はリトライせず即フォールバック（理由ログ出力）。
- FR-6: ``llm_cost.calculate_and_enrich_cost()`` に usage / 実モデル名 / latency_ms を委譲し、
  原価計測・構造化ログを行う。フォールバック時は本モジュールで構造化ログを出力する。
- キャッシュ: 同一 telemetry_id の2回目以降はモジュールレベル dict から返す（LLM 再呼び出し・
  原価再計上なし）。**LLM 成功時のみ保存**し、フォールバック結果はキャッシュしない（一時的障害の
  永続化を防ぎ、次回 LLM を再試行する — Minor #4）。``asyncio.Lock`` で get / 検証 / set を
  直列化し、並行 POST でも LLM が二重呼び出しされないようにする（Minor #3）。
- usage 検証: LLM レスポンスの usage は Pydantic v2（``_UsageTokens``）で検証し、非数値・負値・
  キー欠落はパース失敗としてフォールバックへ落とす（``llm_cost`` の ``int()`` 変換が未捕捉の
  ValueError → 500 に化けるのを防ぐ — Major #1）。
- NFR-4: API キーはログ・例外メッセージ・HTTP レスポンス・コード内リテラルに含めない。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas.alert import AlertDetail
from app.schemas.pipe import PipeRecord
from app.schemas.work_order import RepairPart, WorkOrder
from app.services import llm_cost
from app.services.ledger import get_pipe_age
from app.services.prompts import (
    build_system_prompt,
    build_user_prompt,
    extract_json_from_response,
)

logger = logging.getLogger(__name__)

# 既定の接続先（実エンドポイントはデモ直前に ORCAROUTER_BASE_URL で注入する）
DEFAULT_ORCAROUTER_BASE_URL = "https://orcarouter.example.com/v1"
DEFAULT_ORCAROUTER_MODEL = "orcarouter"

# 補修部材マスタ JSON のパス（cwd 非依存で解決する）
REPAIR_PARTS_PATH = Path(__file__).resolve().parent.parent / "data" / "repair_parts.json"

# ワークオーダー生成結果のキャッシュ（telemetry_id キー。同一アラートの再起票を防ぐ）
# LLM 成功時のみ保存する。フォールバック結果は保存しない（Minor #4: 一時的障害の永続化防止）。
_work_order_cache: dict[str, WorkOrder] = {}

# キャッシュ get / 検証 / set を直列化するロック（Minor #3: 並行 POST での LLM 二重呼び出し防止）。
# デモスコープの単一ワーカーで安全に動作するよう、キャッシュ判定を await を跨がない
# クリティカル区間に収める代わりに、生成処理全体をロックで囲むシンプル構成を採用する。
_work_order_lock = asyncio.Lock()

# 緊急度の型（WorkOrder.urgency と一致させる）
UrgencyLevel = Literal["low", "medium", "high", "critical"]


class _UsageTokens(BaseModel):
    """LLM レスポンス usage のトークン数（Pydantic v2 で検証）。

    非数値・負値・必須キー欠落は ValidationError を上げる。呼び出し側ではパース失敗
    （フォールバック）へ振り分け、``llm_cost.calculate_and_enrich_cost()`` 内の ``int()``
    変換による未捕捉 ValueError（500）を防ぐ（Major #1）。extra フィールド
    （total_tokens 等）は既定どおり無視する。
    """

    model_config = ConfigDict(extra="ignore")

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)


def clear_work_order_cache() -> None:
    """テスト分離用: ワークオーダーキャッシュを空にする。"""
    _work_order_cache.clear()


# --- 環境変数（呼び出し時読込） ---


def _get_model() -> str:
    """ORCAROUTER_MODEL を呼び出し時に読み込む。未設定なら既定値。"""
    return os.environ.get("ORCAROUTER_MODEL", DEFAULT_ORCAROUTER_MODEL).strip() or DEFAULT_ORCAROUTER_MODEL


# --- 補修部材マスタ（フォールバック用） ---


# 補修部材エントリの必須キー（フォールバック安全網の破損検知 — Minor #5）
_REQUIRED_ENTRY_KEYS = frozenset(
    {"parts", "work_steps", "required_workers", "estimated_duration_hours"}
)


def _validate_entry_shape(entry: dict[str, Any], path: str) -> None:
    """補修部材エントリに必須キーが揃っているか検証する。欠落は TypeError を上げる。"""
    missing = _REQUIRED_ENTRY_KEYS.difference(entry)
    if missing:
        raise TypeError(
            f"repair_parts.json の {path} に必須キー {sorted(missing)} がありません"
        )


@lru_cache(maxsize=1)
def _load_repair_parts() -> dict[str, Any]:
    """repair_parts.json を1度だけ読み込んでキャッシュする（store.py 先例）。

    欠損・破損・必須キー（entries / default）欠落はサイレントな空マスタにせず
    例外を上げる。エントリ内の必須キー（parts / work_steps / required_workers /
    estimated_duration_hours）も検証し、部分破損がフォールバック安全網の
    KeyError → 500 に化けないようにする（Minor #5）。``@lru_cache`` の遅延初期化により、
    例外は初回呼び出し時に送出される。
    """
    try:
        data = json.loads(REPAIR_PARTS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"repair_parts.json を読み込めません: {REPAIR_PARTS_PATH}") from exc
    entries = data.get("entries")
    default_entry = data.get("default")
    if not isinstance(entries, dict):
        raise TypeError("repair_parts.json の entries はオブジェクトである必要があります")
    if not isinstance(default_entry, dict):
        raise TypeError("repair_parts.json の default はオブジェクトである必要があります")
    for material, material_entries in entries.items():
        if not isinstance(material_entries, dict):
            continue  # 非 dict の材質エントリは _lookup_repair_parts が default へ落とす
        for diameter, entry in material_entries.items():
            if isinstance(entry, dict):
                _validate_entry_shape(entry, f"entries.{material}.{diameter}")
    _validate_entry_shape(default_entry, "default")
    return data


def _lookup_repair_parts(pipe: PipeRecord | None) -> dict[str, Any]:
    """pipe の材質×口径に対応する補修部材エントリを返す。該当なしは default。"""
    master = _load_repair_parts()
    if pipe is None:
        return master["default"]
    material_entries = master["entries"].get(pipe.material, {})
    if not isinstance(material_entries, dict):
        return master["default"]
    entry = material_entries.get(str(pipe.diameter_mm))
    if not isinstance(entry, dict):
        return master["default"]
    return entry


def _severity_to_urgency(severity_level: int) -> UrgencyLevel:
    """深刻度 Level から緊急度を導出する（3→critical / 2→high / 1→medium / 0→low）。"""
    mapping: dict[int, UrgencyLevel] = {3: "critical", 2: "high", 1: "medium", 0: "low"}
    return mapping.get(severity_level, "low")


def _build_notification_text(alert: AlertDetail, total_estimate_yen: int, urgency: UrgencyLevel) -> str:
    """フォールバック用の通知文面（日本語）を組み立てる。"""
    return (
        f"【漏水検知】消火栓 {alert.hydrant_id}（テレメトリ {alert.telemetry_id}）で補修が必要と"
        f"判定されました。緊急度: {urgency}、概算見積: {total_estimate_yen}円。"
        "金額は概算であり正式な見積ではありません。"
    )


def build_fallback_work_order(alert: AlertDetail, pipe: PipeRecord | None) -> WorkOrder:
    """LLM 呼び出しを使わず、部材マスタから最小の WorkOrder を生成する。

    pipe が None（台帳該当なし）、または材質×口径がマスタに無い場合は default エントリを使う。
    source == "fallback" ・ cost_yen == 0.0 で固定する（LLM 未使用のため原価計上しない）。
    """
    entry = _lookup_repair_parts(pipe)
    parts = [RepairPart.model_validate(item) for item in entry["parts"]]
    total_estimate_yen = sum(part.subtotal_yen for part in parts)
    urgency = _severity_to_urgency(alert.severity_level)
    return WorkOrder(
        parts=parts,
        total_estimate_yen=total_estimate_yen,
        work_steps=entry["work_steps"],
        required_workers=entry["required_workers"],
        estimated_duration_hours=entry["estimated_duration_hours"],
        urgency=urgency,
        notification_text=_build_notification_text(alert, total_estimate_yen, urgency),
        source="fallback",
        prompt_tokens=0,
        completion_tokens=0,
        cost_yen=0.0,
        model=_get_model(),
        latency_ms=0,
        is_estimated=False,
    )


# --- プロンプト用データ組み立て ---


def _to_telemetry_data(alert: AlertDetail) -> dict[str, Any]:
    """AlertDetail からプロンプト用のテレメトリ解析情報を組み立てる。"""
    return {
        "telemetry_id": alert.telemetry_id,
        "sensor_id": alert.sensor_id,
        "hydrant_id": alert.hydrant_id,
        "severity_level": alert.severity_level,
        "leak_confidence": alert.leak_confidence,
        "detected_at": alert.detected_at.isoformat(),
        "location": {
            "latitude": alert.location.latitude,
            "longitude": alert.location.longitude,
        },
        "analysis": {
            "leak_confidence": alert.analysis.leak_confidence,
            "severity_level": alert.analysis.severity_level,
            "dominant_freq_hz": alert.analysis.dominant_freq_hz,
            "band_energy_ratio": alert.analysis.band_energy_ratio,
        },
    }


def _to_pipe_info(pipe: PipeRecord | None) -> dict[str, Any]:
    """PipeRecord からプロンプト用の配管台帳情報を組み立てる。None は空 dict。"""
    if pipe is None:
        return {}
    return {
        "pipe_id": pipe.pipe_id,
        "material": pipe.material,
        "diameter_mm": pipe.diameter_mm,
        "installed_year": pipe.installed_year,
        "burial_depth_m": pipe.burial_depth_m,
        "age_years": get_pipe_age(pipe.installed_year),
    }


# --- Orcarouter API 呼び出し ---


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> httpx.Response | None:
    """Orcarouter へ POST し、回復可能な失敗に対して1回だけリトライする。

    タイムアウト・ネットワークエラー・5xx は1回だけリトライし、それでも失敗したら
    None を返す（呼び出し側でフォールバック）。4xx はリトライせずレスポンスを返す。
    """
    try:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code < 500:
            return response
    except httpx.TransportError:
        pass
    # 初回失敗（タイムアウト・ネットワーク・5xx）→ 1回だけリトライ
    try:
        response = await client.post(url, headers=headers, json=payload)
    except httpx.TransportError:
        return None
    if response.status_code >= 500:
        return None
    return response


def _parse_llm_response(
    response: httpx.Response, fallback_model: str
) -> tuple[WorkOrder, str, dict[str, Any] | None]:
    """Orcarouter の 2xx レスポンスを WorkOrder へパースする。

    - choices 欠落・message/content 不正・非 JSON・スキーマ不整合は ValueError /
      ValidationError を上げる（呼び出し側でフォールバックに振り分ける）。
    - 戻り値は (WorkOrder, 実モデル名, usage)。実モデル名が無い場合は fallback_model を使う。
    """
    data = response.json()  # 非 JSON は json.JSONDecodeError（ValueError のサブクラス）
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("レスポンスに choices が含まれていません")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise TypeError("choices[0].message が存在しません")
    content = message.get("content")
    if not isinstance(content, str):
        raise TypeError("choices[0].message.content が存在しません")

    parsed = extract_json_from_response(content)  # 非 JSON は ValueError
    work_order = WorkOrder.model_validate(parsed)  # スキーマ不整合は ValidationError

    actual_model = data.get("model")
    if not isinstance(actual_model, str) or not actual_model:
        actual_model = fallback_model
    usage = data.get("usage")
    if usage is None:
        return work_order, actual_model, None
    if not isinstance(usage, dict):
        raise TypeError("レスポンス usage が不正です")
    # 非数値・負値・キー欠落は ValidationError → 呼び出し側でフォールバック（Major #1）
    tokens = _UsageTokens.model_validate(usage)
    return work_order, actual_model, {
        "prompt_tokens": tokens.prompt_tokens,
        "completion_tokens": tokens.completion_tokens,
    }


# --- 構造化ログ（フォールバック時。API キーは含めない） ---


def _log_fallback(telemetry_id: str, model: str, latency_ms: int, reason: str) -> None:
    """フォールバック時の1行 JSON 構造化ログを出力する。"""
    log_payload = {
        "event": "work_order_fallback",
        "telemetry_id": telemetry_id,
        "model": model,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_yen": 0.0,
        "source": "fallback",
        "latency_ms": latency_ms,
        "reason": reason,
    }
    logger.info(json.dumps(log_payload, ensure_ascii=False))


def _fallback(
    telemetry_id: str,
    alert: AlertDetail,
    pipe: PipeRecord | None,
    model: str,
    latency_ms: int,
    reason: str,
) -> WorkOrder:
    """フォールバック WorkOrder を生成し、理由付き構造化ログを出力する。

    フォールバック結果はキャッシュ**しない**（Minor #4）。一時的な障害が telemetry_id
    に永続化せず、次回呼び出しで LLM を再試行できるようにする。
    """
    work_order = build_fallback_work_order(alert, pipe)
    _log_fallback(telemetry_id, model, latency_ms, reason)
    return work_order


# --- 公開インターフェース ---


async def create_work_order(
    client: httpx.AsyncClient,
    telemetry_id: str,
    alert: AlertDetail,
    pipe: PipeRecord | None,
) -> WorkOrder:
    """Orcarouter LLM を呼び出して WorkOrder を生成する（BE-5 公開インターフェース）。

    - 同一 telemetry_id の2回目以降はキャッシュを返す（LLM 再呼び出し・原価再計上なし）。
      **フォールバック結果はキャッシュしない**（Minor #4: 一時的障害の永続化防止）。
    - ``_work_order_lock`` でキャッシュ get / 検証 / set を直列化し、並行 POST で LLM が
      二重呼び出し・原価二重ログされないようにする（Minor #3）。
    - API キー未設定 or ``ORCAROUTER_ENABLED=false`` は HTTP 呼び出しなしでフォールバック。
    - タイムアウト・5xx は1回リトライ → 再失敗でフォールバック。
    - 4xx・パース失敗（不正 usage 含む）はリトライせず即フォールバック + 理由ログ。
    """
    async with _work_order_lock:
        cached = _work_order_cache.get(telemetry_id)
        if cached is not None:
            return cached
        return await _generate_work_order(client, telemetry_id, alert, pipe)


async def _generate_work_order(
    client: httpx.AsyncClient,
    telemetry_id: str,
    alert: AlertDetail,
    pipe: PipeRecord | None,
) -> WorkOrder:
    """キャッシュ未ヒット時の実生成処理（LLM 呼び出し・フォールバック）。

    ``create_work_order()`` がロックを保持した状態で呼び出す。LLM 成功時のみ
    ``_work_order_cache`` へ保存する（フォールバックは保存しない — Minor #4）。
    """
    api_key = os.environ.get("ORCAROUTER_API_KEY", "").strip()
    enabled = os.environ.get("ORCAROUTER_ENABLED", "true").strip().lower()
    model = _get_model()

    if enabled == "false" or not api_key:
        return _fallback(telemetry_id, alert, pipe, model, 0, "APIキー未設定または無効")

    base_url = os.environ.get("ORCAROUTER_BASE_URL", DEFAULT_ORCAROUTER_BASE_URL).rstrip("/")
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",  # NFR-4: ログ・例外・レスポンスに出力しない
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": build_user_prompt(_to_telemetry_data(alert), _to_pipe_info(pipe))},
        ],
    }

    start = time.perf_counter()
    response = await _post_with_retry(client, url, headers, payload)
    latency_ms = max(1, round((time.perf_counter() - start) * 1000.0))

    if response is None:
        return _fallback(telemetry_id, alert, pipe, model, latency_ms, "リトライ後も失敗")
    if response.status_code >= 400:
        return _fallback(telemetry_id, alert, pipe, model, latency_ms, f"HTTP {response.status_code}")

    # 2xx 成功パス
    try:
        work_order, actual_model, usage = _parse_llm_response(response, model)
    except (TypeError, ValueError, ValidationError) as exc:
        return _fallback(telemetry_id, alert, pipe, model, latency_ms, f"応答パース失敗: {exc}")

    work_order = llm_cost.calculate_and_enrich_cost(
        work_order,
        usage=usage,
        model_name=actual_model,
        latency_ms=latency_ms,
        telemetry_id=telemetry_id,
    )
    # LLM 成功時のみキャッシュ（フォールバックは保存しない — Minor #4）
    _work_order_cache[telemetry_id] = work_order
    return work_order
