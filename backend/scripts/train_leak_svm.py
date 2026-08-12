"""ZenodoのGit管理外データからBE-3 SVM artifactを再生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import wave
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import scipy
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.audio import (
    DURATION_SEC,
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    SAMPLE_COUNT,
    SAMPLE_RATE_HZ,
    extract_features,
)

SMALL_LEAK_FLOWS = {0.01, 0.05, 0.08, 0.10, 0.11, 0.13, 0.15}
ARCHIVE_SHA256 = {
    "leak acoustic data.rar": "3d42060b8a5b2feb19c4ffc7a77c2f0325779f8634a26468572aee473842dc55",
    "no leak acoustic data.rar": "5bb0f298fdd171dcb199ac9b22d85bdb57c94a7daec31e71a4af66946843405f",
}
DEFAULT_ARTIFACT = BACKEND_DIR / "app" / "models" / "leak_svm_v1.joblib"
DEFAULT_METADATA = BACKEND_DIR / "app" / "models" / "leak_svm_v1.metadata.json"


def _parse_file(path: Path, label: int) -> dict[str, Any]:
    tokens = path.stem.split("-")
    if len(tokens) < 5:
        raise ValueError(f"filenameをparseできません: {path.name}")
    material, region, pressure, flow_raw = tokens[:4]
    tail = "-".join(tokens[4:]).lower()
    device = "noise logger" if "noise logger" in tail else "other"
    match = re.search(r"\d+(?:\.\d+)?", flow_raw)
    flow = float(match.group()) if match and flow_raw != "NA" else None
    return {
        "path": path,
        "label": label,
        "material": material,
        "region": region,
        "pressure": pressure,
        "flow": flow,
        "device": device,
        "group": f"{material}|{region}|{device}",
    }


def _load_pcm16_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as wav:
        if (
            wav.getcomptype() != "NONE"
            or wav.getnchannels() != 1
            or wav.getsampwidth() != 2
            or wav.getframerate() != SAMPLE_RATE_HZ
            or wav.getnframes() != SAMPLE_COUNT
        ):
            raise ValueError(f"MVP WAV契約外です: {path.name}")
        raw = wav.readframes(wav.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0


def select_training_rows(
    dataset_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    for label, subdir in ((1, "leak"), (0, "no_leak")):
        rows.extend(
            _parse_file(path, label)
            for path in sorted((dataset_root / subdir).rglob("*.wav"))
        )
    challenge = [
        row
        for row in rows
        if row["label"] == 1
        and row["device"] == "noise logger"
        and row["flow"] in SMALL_LEAK_FLOWS
    ]
    held_groups = sorted({row["group"] for row in challenge})
    training = [
        row
        for row in rows
        if row["device"] == "noise logger" and row["group"] not in held_groups
    ]
    training.sort(key=lambda row: str(row["path"]))
    if len(challenge) != 13 or Counter(row["label"] for row in training) != Counter(
        {0: 37, 1: 34}
    ):
        raise ValueError(
            "PoCで固定した13件holdout / 71件training構成と一致しません"
        )
    return training, held_groups


def _fitted_state_sha256(scaler: StandardScaler) -> str:
    state = np.concatenate((scaler.mean_, scaler.scale_)).astype("<f8").tobytes()
    return hashlib.sha256(state).hexdigest()


def train(
    dataset_root: Path, artifact_path: Path, metadata_path: Path
) -> dict[str, Any]:
    rows, held_groups = select_training_rows(dataset_root)
    features = np.asarray(
        [
            extract_features(_load_pcm16_wav(row["path"]), sample_rate_hz=SAMPLE_RATE_HZ)
            for row in rows
        ]
    )
    labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
    pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", SVC(kernel="rbf", class_weight="balanced")),
        ]
    )
    pipeline.fit(features, labels)

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact_path, compress=3)
    artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    scaler = pipeline.named_steps["scale"]
    model = pipeline.named_steps["model"]
    metadata: dict[str, Any] = {
        "artifact_filename": artifact_path.name,
        "artifact_sha256": artifact_sha256,
        "artifact_schema_version": 1,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "sample_rate_hz": SAMPLE_RATE_HZ,
        "sample_count": SAMPLE_COUNT,
        "duration_sec": DURATION_SEC,
        "n_features_in": len(FEATURE_NAMES),
        "classes": model.classes_.tolist(),
        "pipeline_steps": list(pipeline.named_steps),
        "preprocessing": {
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
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "svc": {
            "kernel": model.kernel,
            "C": model.C,
            "gamma": model.gamma,
            "effective_gamma": model._gamma,
            "class_weight": model.class_weight,
            "tol": model.tol,
            "shrinking": model.shrinking,
            "n_support": model.n_support_.tolist(),
            "support_vectors_shape": list(model.support_vectors_.shape),
        },
        "standard_scaler": {
            "n_features_in": int(scaler.n_features_in_),
            "n_samples_seen": int(scaler.n_samples_seen_),
            "fitted_state_sha256": _fitted_state_sha256(scaler),
        },
        "dataset": {
            "doi": "10.5281/zenodo.18631450",
            "record_id": 18631450,
            "archive_sha256": ARCHIVE_SHA256,
            "training_samples": len(rows),
            "class_counts": {
                str(key): value for key, value in sorted(Counter(labels).items())
            },
            "condition_groups": sorted({row["group"] for row in rows}),
            "excluded_condition_groups": held_groups,
            "small_leak_candidate_count": 13,
            "small_leak_candidates_used_for_training_or_tuning": False,
            "manual_e2e_files_used_for_training_or_tuning": False,
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset_root",
        type=Path,
        help="展開済みのleak/とno_leak/を含むGit管理外ディレクトリ",
    )
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()
    metadata = train(args.dataset_root, args.artifact, args.metadata)
    print(f"artifact: {args.artifact}")
    print(f"metadata: {args.metadata}")
    print(f"SHA-256: {metadata['artifact_sha256']}")


if __name__ == "__main__":
    main()
