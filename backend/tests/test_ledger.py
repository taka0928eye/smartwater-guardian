"""BE-4: 配管台帳照合サービス（app/services/ledger.py）のテスト。

受け入れ条件 A1〜A6 / D-4 / D-5 を検証する。``get_pipes()`` は ``@lru_cache`` のため、
autouse フィクスチャでテスト間のキャッシュを必ず破棄して隔離する。
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.schemas.pipe import PipeRecord
from app.services.ledger import (
    find_nearest_pipe,
    find_pipe_by_hydrant,
    get_pipe_age,
    get_pipes,
)


@pytest.fixture(autouse=True)
def _clear_ledger_cache():
    """各テスト前に get_pipes() のキャッシュを破棄し、状態を隔離する。"""
    get_pipes.cache_clear()
    yield
    get_pipes.cache_clear()


# --- A1 / A2: find_pipe_by_hydrant ---


def test_find_pipe_by_hydrant_resolves_all_hydrants():
    """A1: 全10消火栓（HYD-001〜010）が P-001〜P-010 と 1:1 で解決される。"""
    for index in range(1, 11):
        pipe = find_pipe_by_hydrant(f"HYD-{index:03d}")
        assert pipe is not None
        assert pipe.pipe_id == f"P-{index:03d}"


def test_find_pipe_by_hydrant_unknown_id_returns_none():
    """A2: 未知の hydrant_id は None を返す。"""
    assert find_pipe_by_hydrant("HYD-999") is None
    assert find_pipe_by_hydrant("") is None


# --- A3: find_nearest_pipe ---


def test_find_nearest_pipe_at_known_hydrant_location():
    """A3: 既知座標（消火栓位置 = 路線頂点）で最近接路線が非 None で返る。"""
    pipe = find_nearest_pipe(35.7019, 139.7444)  # HYD-001 の位置
    assert pipe is not None
    assert isinstance(pipe, PipeRecord)
    assert pipe.pipe_id == "P-001"


def test_find_nearest_pipe_empty_ledger_returns_none(monkeypatch):
    """A3: 空台帳では None を返す（| None が許容される唯一のケース）。"""
    monkeypatch.setattr("app.services.ledger.get_pipes", lambda: [])
    assert find_nearest_pipe(35.7019, 139.7444) is None


# --- D-5: get_pipe_age ---


def test_get_pipe_age_is_reference_year_minus_installed():
    """D-5: 経過年数 = 2026 - installed_year。"""
    assert get_pipe_age(1998) == 28
    assert get_pipe_age(2015) == 11
    assert get_pipe_age(1965) == 61


# --- A4: 明示例外 ---


def test_missing_pipes_path_raises_file_not_found(monkeypatch, tmp_path):
    """A4: pipes.json 欠損は FileNotFoundError をそのまま伝播する。"""
    missing = tmp_path / "no_such_pipes.json"
    monkeypatch.setattr("app.services.ledger.PIPES_PATH", missing)
    with pytest.raises(FileNotFoundError):
        get_pipes()


def test_corrupt_pipes_json_raises_value_error(monkeypatch, tmp_path):
    """A4: 不正 JSON は ValueError に変換して送出する。"""
    broken = tmp_path / "broken.json"
    broken.write_text("{ これは不正なJSONです !!", encoding="utf-8")
    monkeypatch.setattr("app.services.ledger.PIPES_PATH", broken)
    with pytest.raises(ValueError):
        get_pipes()


# --- A6: モジュールキャッシュ ---


def test_get_pipes_reads_json_once_when_cached(monkeypatch):
    """A6: get_pipes() を2回呼んでも json.loads は1回だけ実行される。"""
    calls: dict[str, int] = {"count": 0}
    original_loads = json.loads

    def counting_loads(text: str, *args, **kwargs):
        calls["count"] += 1
        return original_loads(text, *args, **kwargs)

    monkeypatch.setattr("app.services.ledger.json.loads", counting_loads)

    pipes_first = get_pipes()
    pipes_second = get_pipes()
    assert pipes_first == pipes_second
    assert calls["count"] == 1


def test_get_pipes_cache_info_currsize_is_one():
    """A6: キャッシュには台帳一式が1要素だけ保持される。"""
    get_pipes()
    assert get_pipes.cache_info().currsize == 1


# --- スキーマ境界（PipeRecord / GeoJSONLineString）のエッジケース ---


def _valid_pipe_payload() -> dict:
    """正常な PipeRecord ペイロードを組み立てる。"""
    return {
        "pipe_id": "P-999",
        "material": "ductile_iron",
        "diameter_mm": 100,
        "installed_year": 2000,
        "burial_depth_m": 1.2,
        "route": {
            "type": "LineString",
            "coordinates": [[139.74, 35.70], [139.75, 35.71]],
        },
        "hydrant_ids": ["HYD-001"],
    }


def test_pipe_record_rejects_vertex_with_wrong_length():
    """スキーマ境界: 頂点が [経度, 緯度] の2要素でない場合は検証エラー。"""
    payload = _valid_pipe_payload()
    payload["route"]["coordinates"] = [[139.74, 35.70, 1.0], [139.75, 35.71]]
    with pytest.raises(ValidationError):
        PipeRecord.model_validate(payload)


def test_pipe_record_rejects_coordinate_out_of_range():
    """スキーマ境界: 経緯度が範囲外の頂点は検証エラー。"""
    payload = _valid_pipe_payload()
    payload["route"]["coordinates"] = [[139.74, 35.70], [190.0, 35.71]]
    with pytest.raises(ValidationError):
        PipeRecord.model_validate(payload)


def test_pipe_record_rejects_invalid_material():
    """スキーマ境界: 許容外の素材は検証エラー。"""
    payload = _valid_pipe_payload()
    payload["material"] = "asbestos"
    with pytest.raises(ValidationError):
        PipeRecord.model_validate(payload)
