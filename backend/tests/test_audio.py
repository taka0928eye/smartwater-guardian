"""BE-3: SVM + DSP audio analysis contract tests."""

from __future__ import annotations

import base64
import hashlib
import importlib
import inspect
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "audio_feature_v1"
GOLDEN_PCM_PATH = FIXTURE_DIR / "golden_pcm16le.raw"
EXPECTED_FEATURES_PATH = FIXTURE_DIR / "expected_features.json"
EXPECTED_AUDIO_ERROR = (
    "audio_base64 を解析できません: "
    "BE-3 MVPは8000Hz・1.0秒（8000 PCM16 samples）のみ対応します"
)


def load_golden_metadata() -> dict[str, Any]:
    return json.loads(EXPECTED_FEATURES_PATH.read_text(encoding="utf-8"))


def golden_raw() -> bytes:
    return GOLDEN_PCM_PATH.read_bytes()


def golden_base64() -> str:
    return base64.b64encode(golden_raw()).decode("ascii")


@pytest.fixture
def audio_module() -> ModuleType:
    """Import at test time so every contract remains collectable during RED."""
    try:
        return importlib.import_module("app.services.audio")
    except ModuleNotFoundError as exc:
        pytest.fail(f"BE-3 production service is not implemented yet: {exc}")


class FakePipeline:
    """Minimal prediction boundary used without a fitted production artifact."""

    def __init__(self, prediction: int, decision_score: float) -> None:
        self.prediction = prediction
        self.decision_score = decision_score
        self.predict_inputs: list[np.ndarray] = []
        self.score_inputs: list[np.ndarray] = []

    def predict(self, features: np.ndarray) -> np.ndarray:
        self.predict_inputs.append(np.asarray(features))
        return np.asarray([self.prediction], dtype=np.int64)

    def decision_function(self, features: np.ndarray) -> np.ndarray:
        self.score_inputs.append(np.asarray(features))
        return np.asarray([self.decision_score], dtype=np.float64)


def valid_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sensor_id": "SNS-001",
        "hydrant_id": "HYD-001",
        "recorded_at": datetime.now(UTC).isoformat(),
        "location": {"latitude": 35.7022, "longitude": 139.7448},
        "sample_rate_hz": 8_000,
        "duration_sec": 1.0,
        "audio_base64": golden_base64(),
        "battery_pct": 87,
    }
    payload.update(overrides)
    return payload


class TestGoldenFixture:
    def test_fixture_integrity_and_contract(self):
        metadata = load_golden_metadata()
        raw = golden_raw()

        assert len(raw) == 16_000
        assert metadata["feature_schema_version"] == "audio_features_v1"
        assert metadata["sample_rate_hz"] == 8_000
        assert metadata["sample_count"] == 8_000
        assert metadata["duration_sec"] == 1.0
        assert hashlib.sha256(raw).hexdigest() == metadata["input_sha256"]
        assert len(metadata["feature_names"]) == 14
        assert len(metadata["expected_features"]) == 14

        feature_bytes = np.asarray(
            metadata["expected_features"], dtype="<f8"
        ).tobytes()
        assert (
            hashlib.sha256(feature_bytes).hexdigest()
            == metadata["feature_vector_sha256"]
        )


class TestPcm16InputContract:
    def test_decodes_pcm16_little_endian_to_float64(self, audio_module):
        decoded = audio_module.decode_pcm16(
            golden_base64(), sample_rate_hz=8_000, duration_sec=1.0
        )
        expected = np.frombuffer(golden_raw(), dtype="<i2").astype(np.float64)
        expected /= 32768.0

        assert decoded.dtype == np.float64
        assert decoded.shape == (8_000,)
        np.testing.assert_array_equal(decoded, expected)

    @pytest.mark.parametrize(
        ("audio_base64", "sample_rate_hz", "duration_sec"),
        [
            ("not-valid-base64!", 8_000, 1.0),
            (base64.b64encode(b"").decode("ascii"), 8_000, 1.0),
            (base64.b64encode(b"\x00" * 3).decode("ascii"), 8_000, 1.0),
            (golden_base64(), 16_000, 1.0),
            (golden_base64(), 8_000, 0.5),
            (golden_base64(), 8_000, 1.000001),
            (base64.b64encode(golden_raw()[:-2]).decode("ascii"), 8_000, 1.0),
        ],
        ids=[
            "invalid-base64",
            "empty",
            "odd-byte-length",
            "unsupported-sample-rate",
            "unsupported-duration",
            "inexact-duration",
            "wrong-sample-count",
        ],
    )
    def test_rejects_audio_outside_mvp_contract(
        self,
        audio_module,
        audio_base64: str,
        sample_rate_hz: int,
        duration_sec: float,
    ):
        with pytest.raises(audio_module.AudioValidationError):
            audio_module.decode_pcm16(
                audio_base64,
                sample_rate_hz=sample_rate_hz,
                duration_sec=duration_sec,
            )

    def test_all_zero_audio_is_rejected_before_model_inference(self, audio_module):
        model = FakePipeline(prediction=0, decision_score=-1.0)
        zeros = base64.b64encode(b"\x00" * 16_000).decode("ascii")

        with pytest.raises(audio_module.AudioValidationError):
            audio_module.analyze_audio(
                zeros,
                sample_rate_hz=8_000,
                duration_sec=1.0,
                model=model,
            )

        assert model.predict_inputs == []
        assert model.score_inputs == []


class TestFeatureSchema:
    def test_feature_schema_name_dimension_and_order(self, audio_module):
        metadata = load_golden_metadata()

        assert audio_module.FEATURE_SCHEMA_VERSION == "audio_features_v1"
        assert list(audio_module.FEATURE_NAMES) == metadata["feature_names"]
        assert len(audio_module.FEATURE_NAMES) == 14

    def test_features_match_poc_golden_vector(self, audio_module):
        metadata = load_golden_metadata()
        samples = audio_module.decode_pcm16(
            golden_base64(), sample_rate_hz=8_000, duration_sec=1.0
        )

        actual = audio_module.extract_features(samples, sample_rate_hz=8_000)

        assert actual.shape == (14,)
        assert np.isfinite(actual).all()
        np.testing.assert_allclose(
            actual,
            np.asarray(metadata["expected_features"], dtype=np.float64),
            rtol=1e-8,
            atol=1e-10,
        )

    @pytest.mark.parametrize("invalid_value", [np.nan, np.inf, -np.inf])
    def test_rejects_non_finite_samples_before_feature_extraction(
        self, audio_module, invalid_value: float
    ):
        samples = np.zeros(8_000, dtype=np.float64)
        samples[100] = invalid_value

        with pytest.raises(audio_module.AudioValidationError, match="有限"):
            audio_module.extract_features(samples, sample_rate_hz=8_000)


def valid_artifact_metadata(artifact_bytes: bytes) -> dict[str, Any]:
    fixture = load_golden_metadata()
    return {
        "artifact_schema_version": 1,
        "feature_schema_version": "audio_features_v1",
        "artifact_sha256": hashlib.sha256(artifact_bytes).hexdigest(),
        "feature_names": fixture["feature_names"],
        "sample_rate_hz": 8_000,
        "sample_count": 8_000,
        "duration_sec": 1.0,
        "classes": [0, 1],
        "n_features_in": 14,
        "pipeline_steps": ["scale", "model"],
        "versions": {
            "python": "3.14.6",
            "numpy": "2.5.2",
            "scipy": "1.18.0",
            "scikit_learn": "1.9.0",
            "joblib": "1.5.3",
        },
    }


class TestModelArtifactContract:
    def test_loads_fitted_scaler_and_rbf_svm_pipeline(self, audio_module):
        pipeline = audio_module.load_model_artifact()

        assert list(pipeline.named_steps) == ["scale", "model"]
        scaler = pipeline.named_steps["scale"]
        model = pipeline.named_steps["model"]
        assert scaler.n_features_in_ == 14
        assert scaler.n_samples_seen_ == 71
        assert model.kernel == "rbf"
        assert model.C == 1.0
        assert model.gamma == "scale"
        assert model.class_weight == "balanced"
        np.testing.assert_array_equal(model.classes_, np.asarray([0, 1]))

    def test_loads_when_runtime_python_differs_from_provenance(
        self, audio_module, monkeypatch
    ):
        original_loads = audio_module.json.loads

        def metadata_with_different_python(value: str) -> dict[str, Any]:
            metadata = original_loads(value)
            metadata["versions"]["python"] = "0.0.0-provenance-only"
            return metadata

        monkeypatch.setattr(audio_module.json, "loads", metadata_with_different_python)

        pipeline = audio_module.load_model_artifact()

        np.testing.assert_array_equal(
            pipeline.named_steps["model"].classes_, np.asarray([0, 1])
        )

    @pytest.mark.parametrize(
        ("module_name", "metadata_name"),
        [
            ("np", "numpy"),
            ("scipy", "scipy"),
            ("sklearn", "scikit_learn"),
            ("joblib", "joblib"),
        ],
    )
    def test_rejects_package_dependency_version_mismatch(
        self,
        audio_module,
        monkeypatch,
        module_name: str,
        metadata_name: str,
    ):
        monkeypatch.setattr(getattr(audio_module, module_name), "__version__", "0.0.0")

        with pytest.raises(
            audio_module.ModelArtifactError,
            match=f"dependency versionが一致しません: {metadata_name}",
        ):
            audio_module.load_model_artifact()

    def test_default_model_is_loaded_once_per_process(self, audio_module, monkeypatch):
        sentinel = object()
        load_calls = 0

        def fake_load_model_artifact():
            nonlocal load_calls
            load_calls += 1
            return sentinel

        audio_module._load_default_model.cache_clear()
        monkeypatch.setattr(audio_module, "load_model_artifact", fake_load_model_artifact)

        assert audio_module._load_default_model() is sentinel
        assert audio_module._load_default_model() is sentinel
        assert load_calls == 1
        audio_module._load_default_model.cache_clear()

    def test_rejects_artifact_sha256_mismatch(self, audio_module, tmp_path):
        artifact_path = tmp_path / "leak_svm_v1.joblib"
        metadata_path = tmp_path / "leak_svm_v1.metadata.json"
        artifact_path.write_bytes(b"not-a-trusted-artifact")
        metadata = valid_artifact_metadata(artifact_path.read_bytes())
        metadata["artifact_sha256"] = "0" * 64
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with pytest.raises(audio_module.ModelArtifactError, match="SHA-256"):
            audio_module.load_model_artifact(artifact_path, metadata_path)

    def test_rejects_valid_artifact_copied_outside_trusted_repository_path(
        self, audio_module, tmp_path
    ):
        artifact_path = tmp_path / "leak_svm_v1.joblib"
        metadata_path = tmp_path / "leak_svm_v1.metadata.json"
        artifact_path.write_bytes(audio_module.DEFAULT_ARTIFACT_PATH.read_bytes())
        metadata_path.write_bytes(audio_module.DEFAULT_METADATA_PATH.read_bytes())

        with pytest.raises(audio_module.ModelArtifactError, match="trusted repository"):
            audio_module.load_model_artifact(artifact_path, metadata_path)

    @pytest.mark.parametrize(
        ("field", "bad_value", "error_pattern"),
        [
            ("artifact_schema_version", 2, "artifact_schema_version"),
            ("feature_schema_version", "audio_features_v2", "feature_schema_version"),
            ("feature_names", ["wrong"] * 14, "feature_names"),
            ("classes", [1, 0], "classes"),
            ("n_features_in", 13, "n_features_in"),
            ("pipeline_steps", ["model"], "pipeline_steps"),
        ],
    )
    def test_rejects_incompatible_artifact_metadata(
        self,
        audio_module,
        tmp_path,
        field: str,
        bad_value: Any,
        error_pattern: str,
    ):
        artifact_path = tmp_path / "leak_svm_v1.joblib"
        metadata_path = tmp_path / "leak_svm_v1.metadata.json"
        artifact_path.write_bytes(b"not-a-joblib-artifact")
        metadata = valid_artifact_metadata(artifact_path.read_bytes())
        metadata[field] = bad_value
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with pytest.raises(audio_module.ModelArtifactError, match=error_pattern):
            audio_module.load_model_artifact(artifact_path, metadata_path)


class TestLeakScoreAndSeverity:
    @pytest.mark.parametrize(
        ("decision_score", "expected"),
        [(-1.0, 26.9), (0.0, 50.0), (1.0, 73.1)],
    )
    def test_ai_leak_score_is_fixed_non_probability_display_mapping(
        self, audio_module, decision_score: float, expected: float
    ):
        assert audio_module.ai_leak_score(decision_score) == expected

    @pytest.mark.parametrize(
        ("ratio", "expected_level"),
        [
            (0.0, 1),
            (0.12, 1),
            (0.175, 1),
            (0.299999, 1),
            (0.30, 2),
            (0.599999, 2),
            (0.60, 3),
            (1.0, 3),
        ],
    )
    def test_leak_uses_only_mvp_dsp_severity_boundaries(
        self, audio_module, ratio: float, expected_level: int
    ):
        assert audio_module.classify_severity(True, ratio) == expected_level

    @pytest.mark.parametrize("ratio", [0.0, 0.12, 0.175, 0.30, 0.60, 1.0])
    def test_no_leak_is_always_level_zero(self, audio_module, ratio: float):
        assert audio_module.classify_severity(False, ratio) == 0


class TestAnalysisPipeline:
    @pytest.mark.parametrize(
        ("prediction", "score", "expected_level"),
        [(0, 5.0, 0), (1, -5.0, 3)],
        ids=["predict-no-leak-despite-high-score", "predict-leak-despite-low-score"],
    )
    def test_predict_is_classification_source_of_truth(
        self,
        audio_module,
        prediction: int,
        score: float,
        expected_level: int,
    ):
        model = FakePipeline(prediction=prediction, decision_score=score)

        result = audio_module.analyze_audio(
            golden_base64(),
            sample_rate_hz=8_000,
            duration_sec=1.0,
            model=model,
        )

        assert result.severity_level == expected_level
        assert result.leak_confidence == audio_module.ai_leak_score(score)
        assert len(model.predict_inputs) == 1
        assert len(model.score_inputs) == 1
        assert model.predict_inputs[0].shape == (1, 14)
        assert np.isfinite(model.predict_inputs[0]).all()

    def test_analysis_returns_complete_spectrum_contract(self, audio_module):
        result = audio_module.analyze_audio(
            golden_base64(),
            sample_rate_hz=8_000,
            duration_sec=1.0,
            model=FakePipeline(prediction=0, decision_score=-1.0),
        )

        assert 0.0 <= result.leak_confidence <= 100.0
        assert result.severity_level == 0
        assert result.dominant_freq_hz >= 0.0
        assert 0.0 <= result.band_energy_ratio <= 1.0
        assert len(result.spectrum) == 128
        assert all(point.freq_hz >= 0.0 for point in result.spectrum)
        assert all(point.magnitude >= 0.0 for point in result.spectrum)

    def test_one_second_analysis_completes_within_three_seconds(self, audio_module):
        start = time.perf_counter()
        audio_module.analyze_audio(
            golden_base64(),
            sample_rate_hz=8_000,
            duration_sec=1.0,
            model=FakePipeline(prediction=0, decision_score=-1.0),
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 3.0


class TestTelemetryIntegration:
    def test_repo_fixture_passes_through_http_pipeline(self, client):
        response = client.post("/api/v1/telemetry", json=valid_payload())

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "accepted"
        assert body["analysis"] is not None
        assert len(body["analysis"]["spectrum"]) == 128

    @pytest.mark.parametrize(
        "overrides",
        [
            {"sample_rate_hz": 16_000},
            {"duration_sec": 2.0},
        ],
        ids=["sample-rate", "duration"],
    )
    def test_contract_mismatch_returns_fixed_422(self, client, overrides):
        response = client.post(
            "/api/v1/telemetry", json=valid_payload(**overrides)
        )

        assert response.status_code == 422
        assert response.json() == {"detail": EXPECTED_AUDIO_ERROR}

    def test_router_delegates_to_audio_service(self):
        from app.routers import telemetry

        source = inspect.getsource(telemetry)
        assert "_analyze_audio_mock" not in source
        assert "_classify_severity" not in source
        assert hasattr(telemetry, "analyze_audio")

    def test_openapi_describes_leak_confidence_as_ai_leak_score(self):
        from app.schemas.telemetry import AnalysisResult

        description = AnalysisResult.model_json_schema()["properties"][
            "leak_confidence"
        ]["description"]
        assert "AI Leak Score" in description
        assert "確率" not in description
