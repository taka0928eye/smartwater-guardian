"""DEMO-1: デモシードスクリプトとシードAPIのテスト。

Issue #23（DEMO-1）の受け入れ条件を検証する:

- ``build_demo_sequence()`` が Level 0 ベースラインから始まり、内訳が
  Level 1×8 / Level 2×3 / Level 3×1 になる
- 同一 ``seed`` で同一シーケンスが再現され、hydrant_id がマスタに実在する
- Level 1 のステップが Level 3 より先に現れる（山場は Level 1）
- シードAPI（``POST /api/v1/demo/seed``）が意図した深刻度でストアへ投入する
- ``run_seed`` が BE-2 の ``load_audio_file``（replay）で**実音響WAV**を読み込み、
  ``--seed`` 固定で送信でき、``--dry-run`` は送信しない
- replay ファイルはファイル名規約（``*_level{N}.wav`` の leak / no-leak）で
  決定論的に選定され、BE-3 MVP 契約（8000Hz / 1.0秒 / 8000サンプル）を
  満たす
"""

from __future__ import annotations

import random
import wave
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from scripts.seed_demo import (
    ADDITIONAL_LEVEL0_COUNT,
    BASELINE_LEVEL,
    DEFAULT_AUDIO_DIR,
    DEMO_COMPOSITION,
    build_demo_sequence,
    main,
    parse_args,
    resolve_replay_files,
    run_seed,
    select_replay_file,
    validate_mvp_contract,
)
from scripts.simulate_sensor import (
    SimulationError,
    encode_audio,
    generate_signal,
    load_hydrants,
)

SEED_SAMPLE_RATE_HZ = 8_000
SEED_DURATION_SEC = 1.0

# デモ既定値（docs/business-model.md §3.4）: Level 1×8 / Level 2×3 / Level 3×1
EXPECTED_STEP_COUNT = 1 + ADDITIONAL_LEVEL0_COUNT + sum(DEMO_COMPOSITION.values())


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


# --- シーケンス組み立て（build_demo_sequence）---


def test_sequence_starts_with_level0_baseline() -> None:
    """Level 0（正常）ベースラインが先頭にあり、対比の起点になる。"""
    steps = build_demo_sequence(seed=42)
    assert steps
    assert steps[0].level == BASELINE_LEVEL


def test_sequence_composition_matches_demo_defaults() -> None:
    """既存1件+追加10件のLevel 0と、異常レベルの既定内訳になる。"""
    steps = build_demo_sequence(seed=42)
    counts = Counter(step.level for step in steps)
    assert counts[0] == 11
    for level, expected in DEMO_COMPOSITION.items():
        assert counts[level] == expected


def test_same_seed_reproduces_identical_sequence() -> None:
    """同一 seed で2回呼ぶと同一シーケンスが返る（デモの再現性）。"""
    first = build_demo_sequence(seed=42)
    second = build_demo_sequence(seed=42)
    assert first == second


def test_different_seed_produces_different_order() -> None:
    """異なる seed では消火栓の割当順が変わる。"""
    assert build_demo_sequence(seed=42) != build_demo_sequence(seed=43)


def test_hydrant_ids_exist_in_master() -> None:
    """全ステップの hydrant_id が hydrants.json に実在する。"""
    valid_ids = {h["hydrant_id"] for h in load_hydrants()}
    for step in build_demo_sequence(seed=42):
        assert step.hydrant_id in valid_ids


def test_level1_steps_appear_before_level3() -> None:
    """Level 1 のステップが Level 3 より先に現れる（山場は Level 1）。"""
    steps = build_demo_sequence(seed=42)
    last_level1 = max(index for index, step in enumerate(steps) if step.level == 1)
    first_level3 = min(index for index, step in enumerate(steps) if step.level == 3)
    assert last_level1 < first_level3


def test_baseline_hydrant_is_not_reused() -> None:
    """Level 0 ベースラインの消火栓は後続ステップで再利用されない。

    センサー最新状態が上書きされると「Level 0（正常）が画面上に存在し、
    Level 1 との対比が成立する」という受け入れ条件が満たせないため。
    """
    steps = build_demo_sequence(seed=42)
    baseline_id = steps[0].hydrant_id
    assert all(step.hydrant_id != baseline_id for step in steps[1:])


def test_ten_additional_level0_sensors_are_unique_and_not_reused() -> None:
    """追加した正常10台は固有IDを持ち、異常イベントで上書きされない。"""
    steps = build_demo_sequence(seed=42)
    additional_level0 = [step for step in steps if step.level == 0][1:]
    abnormal_ids = {step.hydrant_id for step in steps if step.level > 0}

    assert len(additional_level0) == ADDITIONAL_LEVEL0_COUNT == 10
    assert len({step.hydrant_id for step in additional_level0}) == 10
    assert all(step.hydrant_id not in abnormal_ids for step in additional_level0)


# --- replay ファイル解決（BE-2 load_audio_file 再利用）---


def test_resolve_replay_files_separates_buckets(audio_dir: Path) -> None:
    """no-leak と leak をファイル名規約で分離する。"""
    no_leak, leak = resolve_replay_files(audio_dir)
    assert [path.name for path in no_leak] == ["BE3_demo_no-leak_level0.wav"]
    assert [path.name for path in leak] == [
        "BE3_demo_leak_level1.wav",
        "BE3_demo_leak_level2.wav",
        "BE3_demo_leak_level3.wav",
    ]


def test_resolve_replay_files_missing_leak_raises(tmp_path: Path) -> None:
    """leak が無いディレクトリは SimulationError（デモ内訳を投入できないため）。"""
    _write_wav(
        tmp_path / "BE3_demo_no-leak_level0.wav",
        generate_signal(
            0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        ),
    )
    with pytest.raises(SimulationError):
        resolve_replay_files(tmp_path)


def test_resolve_replay_files_rejects_unclassifiable_name(tmp_path: Path) -> None:
    """leak / no-leak を判別できないファイル名は SimulationError。"""
    _write_wav(
        tmp_path / "BE3_demo_mystery.wav",
        generate_signal(
            0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        ),
    )
    with pytest.raises(SimulationError):
        resolve_replay_files(tmp_path)


def test_select_replay_file_level0_uses_no_leak(audio_dir: Path) -> None:
    """Level 0 ステップは no-leak（正常音）を使う。"""
    no_leak, leak = resolve_replay_files(audio_dir)
    path = select_replay_file(no_leak, leak, level=0, rng=random.Random(42))
    assert "no-leak" in path.name


def test_select_replay_file_prefers_exact_level(audio_dir: Path) -> None:
    """Level 1 ステップは _level1 の leak 音を優先する。"""
    no_leak, leak = resolve_replay_files(audio_dir)
    path = select_replay_file(no_leak, leak, level=1, rng=random.Random(42))
    assert path.name == "BE3_demo_leak_level1.wav"


def test_select_replay_file_falls_back_when_level_missing(tmp_path: Path) -> None:
    """該当レベルのファイルが無い場合は同バケットの leak 音にフォールバックする。"""
    for name, level in [("no-leak_level0", 0), ("leak_level2", 2)]:
        _write_wav(
            tmp_path / f"BE3_demo_{name}.wav",
            generate_signal(
                level, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
            ),
        )
    no_leak, leak = resolve_replay_files(tmp_path)
    path = select_replay_file(no_leak, leak, level=1, rng=random.Random(42))
    assert "leak" in path.name


def test_select_replay_file_deterministic(audio_dir: Path) -> None:
    """同一 seed で選定結果が再現される（デモの再現性）。"""
    no_leak, leak = resolve_replay_files(audio_dir)
    rng_a = random.Random(7)
    rng_b = random.Random(7)
    picks_a = [
        select_replay_file(no_leak, leak, level, rng_a) for level in (1, 2, 3)
    ]
    picks_b = [
        select_replay_file(no_leak, leak, level, rng_b) for level in (1, 2, 3)
    ]
    assert picks_a == picks_b


def test_validate_mvp_contract_rejects_wrong_rate(tmp_path: Path) -> None:
    """8000Hz 以外の WAV は SimulationError（シードAPIが422する前の事前検知）。"""
    path = tmp_path / "bad_rate.wav"
    signal = generate_signal(
        0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
    )
    _write_wav(path, signal, rate=44_100)
    with pytest.raises(SimulationError):
        validate_mvp_contract(signal, sample_rate_hz=44_100, duration_sec=8_000 / 44_100, path=path)


def test_validate_mvp_contract_accepts_mvp() -> None:
    """MVP 契約（8000Hz / 1.0秒 / 8000サンプル）は受け付ける。"""
    signal = generate_signal(
        1, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
    )
    validate_mvp_contract(signal, sample_rate_hz=8_000, duration_sec=1.0, path=Path("ok.wav"))


# --- run_seed / CLI ---


def test_run_seed_posts_all_steps_with_level_field(audio_dir: Path) -> None:
    """run_seed が全ステップを送信し、各 payload に意図レベルと実音響が入る。"""
    captured: list[tuple[str, dict, float]] = []

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        captured.append((url, payload, timeout))
        return {"telemetry_id": f"tlm_{len(captured)}"}

    results = run_seed(
        seed=42,
        url="http://test.local/api/v1/demo/seed",
        audio_dir=audio_dir,
        post_func=fake_post,
    )
    assert len(results) == EXPECTED_STEP_COUNT
    assert len(captured) == EXPECTED_STEP_COUNT

    levels = [payload["level"] for _, payload, _ in captured]
    assert Counter(levels) == {0: 11, **DEMO_COMPOSITION}
    # 先頭は Level 0 ベースライン
    assert captured[0][1]["level"] == BASELINE_LEVEL
    # 実音響（replay）が使われる: MVP 契約の WAV を読み込んだ値になる
    for _, payload, _ in captured:
        assert payload["sample_rate_hz"] == SEED_SAMPLE_RATE_HZ
        assert payload["duration_sec"] == SEED_DURATION_SEC
        assert payload["audio_base64"]  # Base64 音声が入っている


def test_run_seed_contract_violation_raises(tmp_path: Path) -> None:
    """契約外（8000Hz以外）のWAVは投入前に SimulationError になる。"""
    _write_wav(
        tmp_path / "BE3_demo_no-leak_level0.wav",
        generate_signal(
            0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        ),
        rate=44_100,
    )
    _write_wav(
        tmp_path / "BE3_demo_leak_level2.wav",
        generate_signal(
            2, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        ),
    )

    def boom(url: str, payload: dict, timeout: float) -> dict:
        raise AssertionError("契約検証より先に送信してはいけない")

    with pytest.raises(SimulationError):
        run_seed(seed=42, audio_dir=tmp_path, post_func=boom)


def test_run_seed_dry_run_does_not_post(audio_dir: Path) -> None:
    """--dry-run では送信せず、組み立て結果だけを返す。"""

    def boom(url: str, payload: dict, timeout: float) -> dict:
        raise AssertionError("dry-run では送信してはいけない")

    results = run_seed(seed=42, audio_dir=audio_dir, dry_run=True, post_func=boom)
    assert results
    assert all(result["dry_run"] for result in results)
    assert all(result["level"] in (0, 1, 2, 3) for result in results)


def test_parse_args_requires_seed() -> None:
    """--seed が必須で、audio-dir は既定値（backend/dataset）。"""
    args = parse_args(["--seed", "42"])
    assert args.seed == 42
    assert args.dry_run is False
    assert args.audio_dir == DEFAULT_AUDIO_DIR


def test_parse_args_dry_run_flag() -> None:
    """--dry-run フラグを解釈する。"""
    args = parse_args(["--seed", "42", "--dry-run"])
    assert args.dry_run is True


def test_parse_args_audio_dir_override(tmp_path: Path) -> None:
    """--audio-dir で実音響ディレクトリを差し替えられる。"""
    args = parse_args(["--seed", "42", "--audio-dir", str(tmp_path)])
    assert args.audio_dir == tmp_path


def test_main_dry_run_returns_zero(capsys: pytest.CaptureFixture[str], audio_dir: Path) -> None:
    """CLI の --dry-run は送信せず成功終了する。"""
    rc = main(["--seed", "42", "--dry-run", "--audio-dir", str(audio_dir)])
    assert rc == 0
    assert "[DRY-RUN]" in capsys.readouterr().out


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


def test_clear_endpoint_clears_all_telemetry(client) -> None:
    """クリアエンドポイントが全テレメトリをストアから削除する。"""
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
    assert body["cleared_count"] == 2

    # クリア後、アラート一覧が空になる
    alerts_after = client.get("/api/v1/alerts").json()
    assert len(alerts_after) == 0


def test_clear_endpoint_clears_runtime_sensors(client) -> None:
    """クリアエンドポイントがランタイムセンサーもクリアし、センサー地図に反映される。"""
    from app.store import register_runtime_sensors

    # 防災シミュレーションで追加されるランタイムセンサーをシミュレート（HydrantMaster の完全な構造）
    runtime_sensor = {
        "sensor_id": "SNS-RUNTIME-001",
        "hydrant_id": "HYD-RUNTIME-001",
        "name": "ランタイムテスト消火栓",
        "latitude": 35.7022,
        "longitude": 139.7448,
        "pipe_id": "P-RUNTIME-001",
    }
    register_runtime_sensors([runtime_sensor])

    # シードデータを投入
    client.post("/api/v1/demo/seed", json=_build_seed_request(level=1))

    # クリア前の状態を確認
    sensors_before = client.get("/api/v1/sensors?format=json").json()
    # 実マスタのセンサー数 + ランタイムセンサー 1 件
    base_sensor_count = len(sensors_before) - 1

    # クリアを実行
    response = client.delete("/api/v1/demo/clear")
    assert response.status_code == 200

    # クリア後、ランタイムセンサーが削除される
    sensors_after = client.get("/api/v1/sensors?format=json").json()
    assert len(sensors_after) == base_sensor_count


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

    # クリア後、KPI サマリが全て 0 にリセット
    kpi_after = client.get("/api/v1/kpi/summary").json()
    assert kpi_after["level1_count"] == 0
    assert kpi_after["level2_count"] == 0
    assert kpi_after["level3_count"] == 0
    assert kpi_after["estimated_cost_saved_yen"] == 0


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
