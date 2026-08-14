"""BE-2: デモ用消火栓マスタのテスト。"""

from __future__ import annotations

import json
from pathlib import Path

HYDRANTS_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "hydrants.json"


def load_hydrants() -> list[dict]:
    return json.loads(HYDRANTS_PATH.read_text(encoding="utf-8"))


def test_hydrants_json_contains_exactly_20_records():
    assert len(load_hydrants()) == 20


def test_hydrant_and_sensor_ids_are_unique():
    hydrants = load_hydrants()

    assert len({hydrant["hydrant_id"] for hydrant in hydrants}) == 20
    assert len({hydrant["sensor_id"] for hydrant in hydrants}) == 20


def test_hydrant_locations_are_valid_lat_lon_ranges():
    for hydrant in load_hydrants():
        assert -90.0 <= hydrant["latitude"] <= 90.0
        assert -180.0 <= hydrant["longitude"] <= 180.0


def test_all_hydrants_have_non_empty_pipe_id():
    for hydrant in load_hydrants():
        assert isinstance(hydrant["pipe_id"], str)
        assert hydrant["pipe_id"].strip()
