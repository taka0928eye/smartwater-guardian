"""DEMO-2: app/services/demo_seed.py（シード一括投入サービス）のテスト。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_demo_seed_service.py -v
"""

from __future__ import annotations

import wave
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from app.schemas.telemetry import AnalysisResult, GeoLocation
from app.services.demo_seed import (
    DemoSeedError,
    build_seed_batch,
    resolve_replay_files,
    run_seed_batch,
    select_replay_file,
    validate_mvp_contract,
)
from app.store import InMemoryStore, StoredTelemetry, get_hydrants
from scripts.simulate_sensor import generate_signal

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


class TestBuildSeedBatch:
    """23消火栓への1:1レベル配分（Lv0×11/Lv1×8/Lv2×3/Lv3×1）。"""

    def test_matches_new_composition_exactly(self) -> None:
        hydrants = get_hydrants()
        steps = build_seed_batch(hydrants, seed=42)
        counts = Counter(step.level for step in steps)
        assert counts == {0: 11, 1: 8, 2: 3, 3: 1}
        assert len(steps) == 23

    def test_one_level_per_hydrant_no_overlap(self) -> None:
        """現行のサイクリング上書きを廃止し、1消火栓=1レベルを保証する。"""
        hydrants = get_hydrants()
        steps = build_seed_batch(hydrants, seed=42)
        hydrant_ids = [step.hydrant_id for step in steps]
        assert len(hydrant_ids) == len(set(hydrant_ids)) == 23

    def test_reproducible_with_same_seed(self) -> None:
        hydrants = get_hydrants()
        assert build_seed_batch(hydrants, seed=1) == build_seed_batch(hydrants, seed=1)

    def test_different_seed_changes_assignment(self) -> None:
        hydrants = get_hydrants()
        assert build_seed_batch(hydrants, seed=1) != build_seed_batch(hydrants, seed=2)

    def test_requires_twenty_three_hydrants(self) -> None:
        with pytest.raises(DemoSeedError):
            build_seed_batch(get_hydrants()[:22], seed=1)


class TestReplayFileResolution:
    """resolve_replay_files / select_replay_file / validate_mvp_contract。"""

    def test_resolve_replay_files_separates_buckets(self, audio_dir: Path) -> None:
        no_leak, leak = resolve_replay_files(audio_dir)
        assert [path.name for path in no_leak] == ["BE3_demo_no-leak_level0.wav"]
        assert len(leak) == 3

    def test_resolve_replay_files_missing_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DemoSeedError):
            resolve_replay_files(tmp_path / "missing")

    def test_reports_all_missing_required_filenames(self, tmp_path: Path) -> None:
        signal = generate_signal(
            0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        )
        _write_wav(tmp_path / "BE3_demo_no-leak_level0.wav", signal)

        with pytest.raises(DemoSeedError) as exc_info:
            resolve_replay_files(tmp_path)

        message = str(exc_info.value)
        assert "BE3_demo_leak_level1.wav" in message
        assert "BE3_demo_leak_level2.wav" in message
        assert "BE3_demo_leak_level3.wav" in message
        assert "BE3_demo_no-leak_level0.wav" not in message

    def test_rejects_invalid_wav_with_filename_and_invalid_fields(
        self, audio_dir: Path
    ) -> None:
        invalid_path = audio_dir / "BE3_demo_leak_level2.wav"
        samples = np.zeros(4_000, dtype=np.int16)
        with wave.open(str(invalid_path), "wb") as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44_100)
            wav_file.writeframes(np.repeat(samples, 2).astype("<i2").tobytes())

        with pytest.raises(DemoSeedError) as exc_info:
            resolve_replay_files(audio_dir)

        message = str(exc_info.value)
        assert "BE3_demo_leak_level2.wav" in message
        assert "mono" in message
        assert "8000Hz" in message
        assert "1秒" in message

    def test_rejects_non_pcm16_wav(self, audio_dir: Path) -> None:
        invalid_path = audio_dir / "BE3_demo_leak_level1.wav"
        with wave.open(str(invalid_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(1)
            wav_file.setframerate(8_000)
            wav_file.writeframes(bytes(8_000))

        with pytest.raises(DemoSeedError) as exc_info:
            resolve_replay_files(audio_dir)

        assert "BE3_demo_leak_level1.wav" in str(exc_info.value)
        assert "PCM16" in str(exc_info.value)

    def test_select_replay_file_level0_uses_no_leak(self, audio_dir: Path) -> None:
        import random

        no_leak, leak = resolve_replay_files(audio_dir)
        path = select_replay_file(no_leak, leak, level=0, rng=random.Random(42))
        assert "no-leak" in path.name

    def test_validate_mvp_contract_rejects_wrong_rate(self, tmp_path: Path) -> None:
        path = tmp_path / "bad_rate.wav"
        signal = generate_signal(
            0, sample_rate_hz=SEED_SAMPLE_RATE_HZ, duration_sec=SEED_DURATION_SEC, seed=1
        )
        with pytest.raises(DemoSeedError):
            validate_mvp_contract(
                signal, sample_rate_hz=44_100, duration_sec=8_000 / 44_100, path=path
            )


class TestRunSeedBatch:
    """run_seed_batch: ストアを23件・新内訳で一括再構築する。"""

    def test_inserts_exactly_twenty_three_records_with_new_distribution(
        self, audio_dir: Path
    ) -> None:
        store = InMemoryStore()
        result = run_seed_batch(store, audio_dir, seed=42)
        records = store.get_all()
        assert len(records) == 23
        counts = Counter(record.analysis.severity_level for record in records)
        assert counts == {0: 11, 1: 8, 2: 3, 3: 1}
        assert result.inserted_count == 23
        assert result.level_counts == {"0": 11, "1": 8, "2": 3, "3": 1}

    def test_clears_previous_store_state(self, audio_dir: Path) -> None:
        store = InMemoryStore()
        store.add(
            StoredTelemetry(
                telemetry_id="stale",
                sensor_id="SNS-999",
                hydrant_id="HYD-999",
                recorded_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
                location=GeoLocation(latitude=0.0, longitude=0.0),
                analysis=AnalysisResult(
                    severity_level=2,
                    leak_confidence=1.0,
                    dominant_freq_hz=1.0,
                    band_energy_ratio=0.1,
                ),
            )
        )
        run_seed_batch(store, audio_dir, seed=42)
        assert store.get("stale") is None
        assert len(store.get_all()) == 23

    def test_missing_dataset_raises_demo_seed_error(self, tmp_path: Path) -> None:
        store = InMemoryStore()
        with pytest.raises(DemoSeedError):
            run_seed_batch(store, tmp_path / "missing", seed=1)

    def test_real_spectrum_is_computed(self, audio_dir: Path) -> None:
        """severity_levelは意図値に上書きされるが、スペクトルは実信号から算出される。"""
        store = InMemoryStore()
        run_seed_batch(store, audio_dir, seed=42)
        for record in store.get_all():
            assert len(record.analysis.spectrum) > 0
            assert record.audio_pcm16 is not None
            assert record.sample_rate_hz == SEED_SAMPLE_RATE_HZ

    def test_clears_stale_disaster_sensor_flags(self, audio_dir: Path) -> None:
        """以前の防災シミュレーション選出記録を持ち越さない（新しいベースラインのため）。

        シード投入は新しい基準状態を作る操作であり、以前 register_disaster_sensors()
        で記録されたセンサーIDが新しい状態でも Lv3 のまま「被災エリア」として
        表示され続けるのは不整合（DEMO-2）。
        """
        from app.store import (
            clear_disaster_state,
            get_disaster_sensor_ids,
            register_disaster_sensors,
        )

        register_disaster_sensors(["SNS-001", "SNS-002"])
        assert get_disaster_sensor_ids() == {"SNS-001", "SNS-002"}

        store = InMemoryStore()
        run_seed_batch(store, audio_dir, seed=42)

        assert get_disaster_sensor_ids() == set()
        clear_disaster_state()
