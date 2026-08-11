"""BE-4: 疑似GIS配管台帳（app/data/pipes.json）のデータ整合テスト。

hydrants.json（BE-2）との参照整合を含め、配管台帳の品質をデータ単位で保証する。
``app.services.ledger`` は使わず、生 JSON に対して検証する（test_hydrants.py と同流儀）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.pipe import MAX_INSTALL_YEAR, MIN_INSTALL_YEAR, PipeRecord

PIPES_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "pipes.json"
HYDRANTS_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "hydrants.json"

# 許容される素材・口径（app/schemas/pipe.py の Literal と一致させる）
ALLOWED_MATERIALS = {"ductile_iron", "cast_iron", "pvc", "steel"}
ALLOWED_DIAMETERS = {75, 100, 150, 200}


def load_pipes() -> list[dict]:
    return json.loads(PIPES_PATH.read_text(encoding="utf-8"))


def load_hydrants() -> list[dict]:
    return json.loads(HYDRANTS_PATH.read_text(encoding="utf-8"))


def test_pipes_json_contains_exactly_10_records():
    assert len(load_pipes()) == 10


def test_pipe_ids_are_unique_and_match_hydrants():
    pipes = load_pipes()
    pipe_ids = [pipe["pipe_id"] for pipe in pipes]

    # pipe_id はユニークでなければならない
    assert len(set(pipe_ids)) == len(pipe_ids)
    # D-4: P-001〜P-010 の形式（Issue 例示の PIPE-001 は不採用）
    assert sorted(pipe_ids) == [f"P-{i:03d}" for i in range(1, 11)]


def test_material_and_diameter_within_allowed_values():
    for pipe in load_pipes():
        assert pipe["material"] in ALLOWED_MATERIALS
        assert pipe["diameter_mm"] in ALLOWED_DIAMETERS


def test_installed_year_within_range():
    for pipe in load_pipes():
        assert 1965 <= pipe["installed_year"] <= 2015


def test_burial_depth_is_positive():
    for pipe in load_pipes():
        assert isinstance(pipe["burial_depth_m"], (int, float))
        assert pipe["burial_depth_m"] > 0


def test_route_is_line_string_with_valid_vertices():
    for pipe in load_pipes():
        route = pipe["route"]
        assert route["type"] == "LineString"
        coordinates = route["coordinates"]
        assert len(coordinates) >= 2
        for vertex in coordinates:
            assert len(vertex) == 2
            lng, lat = vertex
            assert -180.0 <= lng <= 180.0
            assert -90.0 <= lat <= 90.0


def _valid_pipe_record_payload(installed_year: int) -> dict:
    """installed_year 境界値検証用の最小 PipeRecord ペイロードを組み立てる。"""
    return {
        "pipe_id": "P-999",
        "material": "ductile_iron",
        "diameter_mm": 150,
        "installed_year": installed_year,
        "burial_depth_m": 1.2,
        "route": {
            "type": "LineString",
            "coordinates": [[139.7444, 35.7019], [139.7450, 35.7025]],
        },
        "hydrant_ids": ["HYD-001"],
    }


def test_installed_year_boundary_rejects_below_min_accepts_min_and_max():
    """PipeRecord.installed_year は MIN_INSTALL_YEAR 未満を拒否し、
    MIN_INSTALL_YEAR / MAX_INSTALL_YEAR の境界値自体は受理する（Pydantic 検証境界）。

    test_installed_year_within_range は生JSON（app/data/pipes.json の実データ）を
    検証する別観点のテストであり、本テストは PipeRecord スキーマの境界値検証
    （Field(ge=MIN_INSTALL_YEAR, le=MAX_INSTALL_YEAR)）そのものを対象にする。
    """
    with pytest.raises(ValidationError):
        PipeRecord.model_validate(_valid_pipe_record_payload(MIN_INSTALL_YEAR - 1))

    # 境界値そのものは受理される
    PipeRecord.model_validate(_valid_pipe_record_payload(MIN_INSTALL_YEAR))
    PipeRecord.model_validate(_valid_pipe_record_payload(MAX_INSTALL_YEAR))


def test_hydrant_ids_reference_consistency():
    """各路線の hydrant_ids が hydrants.json と整合する。

    - 全 hydrant_ids は実在する消火栓 ID である
    - 各消火栓が参照する pipe_id の路線に、その消火栓が hydrant_ids で所属している
    """
    pipes = load_pipes()
    hydrants = load_hydrants()
    hydrant_ids = {hydrant["hydrant_id"] for hydrant in hydrants}
    pipe_by_id = {pipe["pipe_id"]: pipe for pipe in pipes}

    # 全 hydrant_ids が実在する消火栓 ID
    for pipe in pipes:
        assert set(pipe["hydrant_ids"]).issubset(hydrant_ids)
        assert pipe["hydrant_ids"], "hydrant_ids は空でないこと"

    # 各消火栓が参照する pipe_id の路線に所属している（1:1 対応）
    for hydrant in hydrants:
        pipe = pipe_by_id[hydrant["pipe_id"]]
        assert hydrant["hydrant_id"] in pipe["hydrant_ids"]
