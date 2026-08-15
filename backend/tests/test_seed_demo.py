"""DEMO-1/DEMO-2: デモシードAPI群（単体投入・一括投入・クリア）のテスト。

- シードAPI（``POST /api/v1/demo/seed``）が意図した深刻度でストアへ投入する
- 一括投入API（``POST /api/v1/demo/seed-batch``、DEMO-2）が
  ``app/services/demo_seed.py`` を使って23件（Lv0×11/Lv1×8/Lv2×3/Lv3×1）を
  一括投入する。内訳計算・音声選択ロジックは ``tests/test_demo_seed_service.py``
  で検証済みのため、ここではルーター経由の統合的な振る舞いのみ検証する。
- クリアAPI（``DELETE /api/v1/demo/clear``）が23件Lv0の初期状態に戻す
"""

from __future__ import annotations

import wave
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from app.services import demo_seed as demo_seed_service
from scripts.simulate_sensor import encode_audio, generate_signal

SEED_SAMPLE_RATE_HZ = 8_000
SEED_DURATION_SEC = 1.0


def _write_wav(path: Path, samples: np.ndarray, rate: int = 8_000) -> None:
    """テスト用の PCM16 モノラル WAV を書き出す。"""
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(samples.astype("<i2").tobytes())


@pytest.fixture
def audio_dir(tmp_path: Path) -> Path:
    """no-leak 1件 + leak 3件（level1/2/3）を含む音声ディレクトリを作る。"""
    for name, level in [
        ("no-leak_level0", 0),
        ("leak_level1", 1),
        ("leak_level2", 2),
        ("leak_level3", 3),
    ]:
        signal = generate_signal(
            level, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        )
        _write_wav(tmp_path / f"BE3_demo_{name}.wav", signal)
    return tmp_path


# --- 一括投入API（POST /api/v1/demo/seed-batch）---


def test_seed_batch_endpoint_inserts_twenty_three_records_with_new_distribution(
    client, audio_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """一括投入APIが23件（Lv0×11/Lv1×8/Lv2×3/Lv3×1）を投入する。"""
    monkeypatch.setattr(demo_seed_service, "DEFAULT_AUDIO_DIR", audio_dir)

    response = client.post("/api/v1/demo/seed-batch?seed=42")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "seeded"
    assert body["inserted_count"] == 23
    assert body["level_counts"] == {"0": 11, "1": 8, "2": 3, "3": 1}

    alerts = client.get("/api/v1/alerts").json()
    assert len(alerts) == 23


def test_seed_batch_endpoint_replaces_previous_state(
    client, audio_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """一括投入は既存レコードを破棄してから23件を書き直す（重複を作らない）。"""
    monkeypatch.setattr(demo_seed_service, "DEFAULT_AUDIO_DIR", audio_dir)

    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1))
    response = client.post("/api/v1/demo/seed-batch?seed=1")
    assert response.status_code == 200

    alerts = client.get("/api/v1/alerts").json()
    assert len(alerts) == 23


def test_seed_batch_endpoint_missing_dataset_returns_404(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """音声データセット未配置（gitignore対象）時は500ではなく404を返す。"""
    monkeypatch.setattr(demo_seed_service, "DEFAULT_AUDIO_DIR", tmp_path / "missing")

    response = client.post("/api/v1/demo/seed-batch?seed=1")
    assert response.status_code == 404


def test_seed_batch_endpoint_reproducible_with_same_seed(
    client, audio_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """同一seedで実行すると同一の消火栓レベル配分になる。"""
    monkeypatch.setattr(demo_seed_service, "DEFAULT_AUDIO_DIR", audio_dir)

    client.post("/api/v1/demo/seed-batch?seed=7")
    first = {
        item["hydrant_id"]: item["severity_level"]
        for item in client.get("/api/v1/alerts").json()
    }
    client.post("/api/v1/demo/seed-batch?seed=7")
    second = {
        item["hydrant_id"]: item["severity_level"]
        for item in client.get("/api/v1/alerts").json()
    }
    assert first == second


# --- シードAPI（POST /api/v1/demo/seed）---


def _build_seed_request(level: int, hydrant_id: str = "HYD-001") -> dict:
    """シードAPIに送る1件分のリクエストボディを組み立てる。"""
    signal = generate_signal(
        level, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
    )
    return {
        "level": level,
        "sensor_id": "SNS-001",
        "hydrant_id": hydrant_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": SEED_SAMPLE_RATE_HZ,
        "duration_sec": SEED_DURATION_SEC,
        "audio_base64": encode_audio(signal),
        "battery_pct": 87,
    }


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_seed_endpoint_stores_intended_severity(client, level: int) -> None:
    """シードAPIが意図した深刻度でストアへ投入する（SVM誤分類を補正）。"""
    response = client.post("/api/v1/demo/seed", json=_build_seed_request(level=level))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["analysis"]["severity_level"] == level
    assert len(body["analysis"]["spectrum"]) > 0  # 実スペクトルが算出される


def test_seed_endpoint_appears_in_alerts(client) -> None:
    """投入したレコードがアラート一覧に意図レベルで現れる。"""
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=0))
    alerts = client.get("/api/v1/alerts").json()
    assert any(
        alert["hydrant_id"] == "HYD-001" and alert["severity_level"] == 0
        for alert in alerts
    )


def test_seed_endpoint_rejects_invalid_base64(client) -> None:
    """不正な Base64 は 422（TelemetryRequest の検証を継承）。"""
    payload = _build_seed_request(level=1)
    payload["audio_base64"] = "これはBase64ではありません!!!"
    response = client.post("/api/v1/demo/seed", json=payload)
    assert response.status_code == 422


def test_seed_endpoint_rejects_all_zero_audio(client) -> None:
    """全ゼロ音声は解析不能のため 422（AudioValidationError 経路）。"""
    payload = _build_seed_request(level=1)
    payload["audio_base64"] = encode_audio(np.zeros(SEED_SAMPLE_RATE_HZ, dtype=np.int16))
    response = client.post("/api/v1/demo/seed", json=payload)
    assert response.status_code == 422


# --- クリアAPI（DELETE /api/v1/demo/clear）---


def test_clear_endpoint_resets_to_twenty_three_level0_records(client) -> None:
    """クリアエンドポイントは全テレメトリを破棄し、23件Lv0へ戻す。"""
    # 先にシードデータを投入
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1))
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=2))
    alerts = client.get("/api/v1/alerts").json()
    assert len(alerts) == 2

    # クリアを実行
    response = client.delete("/api/v1/demo/clear")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cleared"
    # クリア前（投入した2件）の件数が実績値として返る
    assert body["cleared_count"] == 2

    # クリア後、23件Lv0の初期状態に戻る
    alerts_after = client.get("/api/v1/alerts").json()
    assert len(alerts_after) == 23
    assert all(item["severity_level"] == 0 for item in alerts_after)


def test_clear_endpoint_clears_disaster_sensor_flags(client) -> None:
    """クリアエンドポイントが防災シミュレーションの選出記録もクリアする。"""
    from app.store import get_disaster_sensor_ids

    # シードして防災シミュレーションを実行し、選出記録を作る
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1))
    simulate_response = client.post("/api/v1/disaster/simulate?count=3")
    assert simulate_response.status_code == 200
    assert len(get_disaster_sensor_ids()) == 3

    # クリアを実行
    response = client.delete("/api/v1/demo/clear")
    assert response.status_code == 200

    # クリア後、選出記録も消え、被災エリアサマリは空になる
    assert get_disaster_sensor_ids() == set()
    summary = client.get("/api/v1/disaster/summary").json()
    assert summary["total_clusters"] == 0


def test_clear_endpoint_resets_kpi_summary(client) -> None:
    """クリアエンドポイント後、KPI サマリがリセット（監視センサー数も0）される。"""
    # シードデータを投入（複数レベル）
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1, hydrant_id="HYD-001"))
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=2, hydrant_id="HYD-002"))
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=3, hydrant_id="HYD-003"))

    kpi_before = client.get("/api/v1/kpi/summary").json()
    assert kpi_before["level1_count"] == 1
    assert kpi_before["level2_count"] == 1
    assert kpi_before["level3_count"] == 1
    assert kpi_before["estimated_cost_saved_yen"] > 0

    # クリアを実行
    response = client.delete("/api/v1/demo/clear")
    assert response.status_code == 200

    # クリア後、KPI サマリが全て 0 にリセット（Lv0はKPI集計対象外）
    kpi_after = client.get("/api/v1/kpi/summary").json()
    assert kpi_after["level1_count"] == 0
    assert kpi_after["level2_count"] == 0
    assert kpi_after["level3_count"] == 0
    assert kpi_after["estimated_cost_saved_yen"] == 0
    # 監視センサー数は常に23（クリアでも増減しない）
    assert kpi_after["total_sensors"] == 23


def test_clear_endpoint_message_indicates_reset_complete(client) -> None:
    """クリアエンドポイントのメッセージに地図・サマリのリセットが含まれる。"""
    # データを投入
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1))

    # クリアを実行
    response = client.delete("/api/v1/demo/clear")
    assert response.status_code == 200
    body = response.json()

    # メッセージが「地図・KPI サマリをリセット」を含む
    assert "リセット" in body["message"]
