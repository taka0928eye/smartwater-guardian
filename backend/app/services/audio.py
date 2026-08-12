"""BE-3: 学習済みSVMとDSPによる音響テレメトリ解析。"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import scipy
import sklearn
from scipy.signal import butter, sosfiltfilt, welch
from scipy.special import expit
from scipy.stats import kurtosis

from app.schemas.telemetry import AnalysisResult, SeverityLevel, SpectrumPoint

FEATURE_SCHEMA_VERSION = "audio_features_v1"
FEATURE_NAMES = (
    "band_ratio_500_1500",
    "band_ratio_100_250",
    "band_ratio_250_500",
    "band_ratio_500_750",
    "band_ratio_750_1000",
    "band_ratio_1000_1250",
    "band_ratio_1250_1500",
    "band_ratio_1500_2000",
    "band_ratio_2000_3000",
    "rms",
    "spectral_centroid",
    "spectral_flatness",
    "spectral_entropy",
    "kurtosis",
)

SAMPLE_RATE_HZ = 8_000
SAMPLE_COUNT = 8_000
DURATION_SEC = 1.0
N_SPECTRUM = 128
LEAK_BAND_HZ = (500.0, 1500.0)
SUB_BANDS_HZ = (
    (100.0, 250.0),
    (250.0, 500.0),
    (500.0, 750.0),
    (750.0, 1_000.0),
    (1_000.0, 1_250.0),
    (1_250.0, 1_500.0),
    (1_500.0, 2_000.0),
    (2_000.0, 3_000.0),
)

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
DEFAULT_ARTIFACT_PATH = MODEL_DIR / "leak_svm_v1.joblib"
DEFAULT_METADATA_PATH = MODEL_DIR / "leak_svm_v1.metadata.json"
MVP_CONTRACT_ERROR = "BE-3 MVPは8000Hz・1.0秒（8000 PCM16 samples）のみ対応します"
PREPROCESSING_METADATA = {
    "normalization_divisor": 32768.0,
    "high_pass": {
        "order": 4,
        "cutoff_hz": 100.0,
        "output": "sos",
        "filter": "sosfiltfilt",
    },
    "welch": {"window": "hann", "nperseg": 1024},
    "integration": "numpy.trapezoid",
    "kurtosis": {"fisher": True, "bias": False},
}


class AudioValidationError(ValueError):
    """入力音声がBE-3 MVP契約を満たさない。"""


class ModelArtifactError(RuntimeError):
    """学習済みartifactの整合性を確認できない。"""


def decode_pcm16(
    audio_base64: str, *, sample_rate_hz: int, duration_sec: float
) -> np.ndarray:
    """PCM16LE mono raw bytesを検証し、正規化済みfloat64へ変換する。"""
    try:
        raw = base64.b64decode(audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AudioValidationError("audio_base64が妥当なBase64ではありません") from exc

    if not raw:
        raise AudioValidationError("音声データが空です")
    if len(raw) % 2:
        raise AudioValidationError("PCM16のbyte lengthが不正です")
    if sample_rate_hz != SAMPLE_RATE_HZ or duration_sec != DURATION_SEC:
        raise AudioValidationError(MVP_CONTRACT_ERROR)

    samples = np.frombuffer(raw, dtype="<i2")
    if samples.size != SAMPLE_COUNT or duration_sec != samples.size / sample_rate_hz:
        raise AudioValidationError(MVP_CONTRACT_ERROR)
    return samples.astype(np.float64) / 32768.0


def _filtered_psd(
    samples: np.ndarray, sample_rate_hz: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sos = butter(
        4,
        100.0 / (sample_rate_hz / 2.0),
        btype="highpass",
        output="sos",
    )
    filtered = sosfiltfilt(sos, samples)
    frequencies, psd = welch(
        filtered,
        fs=sample_rate_hz,
        window="hann",
        nperseg=min(1024, len(filtered)),
    )
    return filtered, frequencies, psd


def _band_ratio(
    frequencies: np.ndarray,
    psd: np.ndarray,
    band: tuple[float, float],
    total_energy: float,
) -> float:
    mask = (frequencies >= band[0]) & (frequencies <= band[1])
    return float(np.trapezoid(psd[mask], frequencies[mask]) / total_energy)


def _extract_features_with_psd(
    samples: np.ndarray, sample_rate_hz: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise AudioValidationError("音声sampleが有限なmono配列ではありません")

    filtered, frequencies, psd = _filtered_psd(values, sample_rate_hz)
    total_energy = float(np.trapezoid(psd, frequencies))
    if total_energy <= 0.0 or not np.isfinite(total_energy):
        raise AudioValidationError("音声エネルギーを算出できません")

    epsilon = np.finfo(np.float64).tiny
    psd_sum = float(np.sum(psd))
    distribution = psd / (psd_sum + epsilon)
    features = np.asarray(
        [
            _band_ratio(frequencies, psd, LEAK_BAND_HZ, total_energy),
            *(
                _band_ratio(frequencies, psd, band, total_energy)
                for band in SUB_BANDS_HZ
            ),
            float(np.sqrt(np.mean(filtered * filtered))),
            float(np.sum(frequencies * psd) / psd_sum),
            float(
                np.exp(np.mean(np.log(psd + epsilon)))
                / (np.mean(psd) + epsilon)
            ),
            float(
                -np.sum(distribution * np.log(distribution + epsilon))
                / np.log(len(distribution))
            ),
            float(kurtosis(filtered, fisher=True, bias=False)),
        ],
        dtype=np.float64,
    )
    if features.shape != (len(FEATURE_NAMES),) or not np.isfinite(features).all():
        raise AudioValidationError("有限な14次元特徴量を生成できません")
    return features, frequencies, psd


def extract_features(samples: np.ndarray, *, sample_rate_hz: int) -> np.ndarray:
    """PoCと同じ前処理・順序で14次元の音響特徴量を返す。"""
    features, _, _ = _extract_features_with_psd(samples, sample_rate_hz)
    return features


def _validate_metadata(metadata: dict[str, Any]) -> None:
    expected = {
        "artifact_schema_version": 1,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "classes": [0, 1],
        "n_features_in": len(FEATURE_NAMES),
        "pipeline_steps": ["scale", "model"],
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "sample_count": SAMPLE_COUNT,
        "duration_sec": DURATION_SEC,
        "artifact_filename": DEFAULT_ARTIFACT_PATH.name,
        "preprocessing": PREPROCESSING_METADATA,
    }
    for field, value in expected.items():
        if metadata.get(field) != value:
            raise ModelArtifactError(f"artifact metadataの{field}が不正です")

    scaler_metadata = metadata.get("standard_scaler", {})
    if scaler_metadata.get("n_features_in") != len(FEATURE_NAMES):
        raise ModelArtifactError("artifact metadataのStandardScaler次元が不正です")
    if scaler_metadata.get("n_samples_seen") != 71:
        raise ModelArtifactError("artifact metadataのStandardScaler学習件数が不正です")

    dataset_metadata = metadata.get("dataset", {})
    expected_dataset_fields = {
        "training_samples": 71,
        "class_counts": {"0": 37, "1": 34},
        "small_leak_candidate_count": 13,
        "small_leak_candidates_used_for_training_or_tuning": False,
        "manual_e2e_files_used_for_training_or_tuning": False,
    }
    for field, value in expected_dataset_fields.items():
        if dataset_metadata.get(field) != value:
            raise ModelArtifactError(f"artifact metadataのdataset.{field}が不正です")


def _validate_dependency_versions(metadata: dict[str, Any]) -> None:
    expected_versions = {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }
    versions = metadata.get("versions", {})
    for package, version in expected_versions.items():
        if versions.get(package) != version:
            raise ModelArtifactError(f"dependency versionが一致しません: {package}")


def _validate_fitted_pipeline(pipeline: Any, metadata: dict[str, Any]) -> None:
    if list(getattr(pipeline, "named_steps", {})) != ["scale", "model"]:
        raise ModelArtifactError("Pipeline stepsが一致しません")
    scaler = pipeline.named_steps["scale"]
    model = pipeline.named_steps["model"]
    if getattr(scaler, "n_features_in_", None) != len(FEATURE_NAMES):
        raise ModelArtifactError("StandardScalerのn_features_in_が一致しません")
    if getattr(scaler, "n_samples_seen_", None) != 71:
        raise ModelArtifactError("StandardScalerのn_samples_seen_が一致しません")

    scaler_state = np.concatenate((scaler.mean_, scaler.scale_)).astype("<f8").tobytes()
    scaler_sha256 = hashlib.sha256(scaler_state).hexdigest()
    if metadata.get("standard_scaler", {}).get("fitted_state_sha256") != scaler_sha256:
        raise ModelArtifactError("StandardScalerのfitted state checksumが一致しません")

    model_classes = getattr(model, "classes_", None)
    if model_classes is None or not np.array_equal(
        np.asarray(model_classes), np.asarray([0, 1])
    ):
        raise ModelArtifactError("SVM classes_が一致しません")
    if getattr(model, "n_features_in_", None) != len(FEATURE_NAMES):
        raise ModelArtifactError("SVMのn_features_in_が一致しません")
    expected_svc = {
        "kernel": "rbf",
        "C": 1.0,
        "gamma": "scale",
        "class_weight": "balanced",
        "tol": 0.001,
        "shrinking": True,
    }
    metadata_svc = metadata.get("svc", {})
    for field, value in expected_svc.items():
        if metadata_svc.get(field) != value or getattr(model, field, None) != value:
            raise ModelArtifactError(f"SVM parameterが一致しません: {field}")
    if not np.isclose(metadata_svc.get("effective_gamma", np.nan), model._gamma):
        raise ModelArtifactError("SVM effective gammaが一致しません")
    if metadata_svc.get("n_support") != model.n_support_.tolist():
        raise ModelArtifactError("SVM n_supportが一致しません")
    if metadata_svc.get("support_vectors_shape") != list(model.support_vectors_.shape):
        raise ModelArtifactError("SVM support vectors shapeが一致しません")


def load_model_artifact(
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
) -> Any:
    """SHAとschemaを確認してrepository同梱のfitted Pipelineをloadする。"""
    try:
        artifact_bytes = artifact_path.read_bytes()
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelArtifactError("model artifactまたはmetadataを読み込めません") from exc

    actual_sha = hashlib.sha256(artifact_bytes).hexdigest()
    if metadata.get("artifact_sha256") != actual_sha:
        raise ModelArtifactError("model artifactのSHA-256が一致しません")
    _validate_metadata(metadata)
    _validate_dependency_versions(metadata)

    try:
        trusted_artifact = artifact_path.resolve(strict=True) == DEFAULT_ARTIFACT_PATH.resolve(
            strict=True
        )
        trusted_metadata = metadata_path.resolve(strict=True) == DEFAULT_METADATA_PATH.resolve(
            strict=True
        )
    except OSError as exc:
        raise ModelArtifactError("trusted repository artifactを確認できません") from exc
    if not trusted_artifact or not trusted_metadata:
        raise ModelArtifactError("trusted repository artifact以外はloadできません")

    try:
        pipeline = joblib.load(io.BytesIO(artifact_bytes))
    except Exception as exc:
        raise ModelArtifactError("model artifactをloadできません") from exc
    _validate_fitted_pipeline(pipeline, metadata)
    return pipeline


@lru_cache(maxsize=1)
def _load_default_model() -> Any:
    """検証済みの既定artifactをprocess内で一度だけloadする。"""
    return load_model_artifact()


def ai_leak_score(decision_score: float) -> float:
    """decision scoreを表示用0〜100スコアへ固定変換する（確率ではない）。"""
    if not np.isfinite(decision_score):
        raise AudioValidationError("SVM decision scoreが有限値ではありません")
    return round(100.0 * float(expit(decision_score)), 1)


def classify_severity(is_leak: bool, band_energy_ratio: float) -> SeverityLevel:
    """Leak時だけMVP暫定DSP閾値でLevel 1〜3を返す。"""
    if not is_leak:
        return 0
    if band_energy_ratio >= 0.60:
        return 3
    if band_energy_ratio >= 0.30:
        return 2
    return 1


def _spectrum_points(
    frequencies: np.ndarray, psd: np.ndarray
) -> list[SpectrumPoint]:
    target_frequencies = np.linspace(frequencies[0], frequencies[-1], N_SPECTRUM)
    magnitudes = np.interp(target_frequencies, frequencies, psd)
    return [
        SpectrumPoint(freq_hz=float(freq), magnitude=float(magnitude))
        for freq, magnitude in zip(target_frequencies, magnitudes)
    ]


def analyze_audio(
    audio_base64: str,
    *,
    sample_rate_hz: int,
    duration_sec: float,
    model: Any | None = None,
) -> AnalysisResult:
    """MVP入力を検証し、SVM二値判定とDSP severityを返す。"""
    samples = decode_pcm16(
        audio_base64,
        sample_rate_hz=sample_rate_hz,
        duration_sec=duration_sec,
    )
    if not np.any(samples):
        raise AudioValidationError("全ゼロ音声は解析できません")

    features, frequencies, psd = _extract_features_with_psd(samples, sample_rate_hz)
    model_input = features.reshape(1, -1)
    pipeline = model if model is not None else _load_default_model()
    prediction = int(np.asarray(pipeline.predict(model_input)).reshape(-1)[0])
    decision_score = float(
        np.asarray(pipeline.decision_function(model_input)).reshape(-1)[0]
    )
    if prediction not in (0, 1):
        raise ModelArtifactError("SVM predictionが既知classではありません")

    band_ratio = float(features[0])
    return AnalysisResult(
        leak_confidence=ai_leak_score(decision_score),
        severity_level=classify_severity(prediction == 1, band_ratio),
        dominant_freq_hz=float(frequencies[int(np.argmax(psd))]),
        band_energy_ratio=band_ratio,
        spectrum=_spectrum_points(frequencies, psd),
    )
