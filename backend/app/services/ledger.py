"""疑似GIS配管台帳の照合サービス（BE-4）。

``app/data/pipes.json``（10路線）を一度だけ読み込み、
- 消火栓ID から所属配管（``find_pipe_by_hydrant``）
- 座標から最近接路線（``find_nearest_pipe``）

を解決する。``get_pipes()`` は ``@lru_cache`` でリクエスト毎の再読み込みを防ぐ
（``app/store.get_hydrants`` と同じ流儀）。
"""

from __future__ import annotations

import json
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from app.schemas.pipe import PipeRecord

# 配管台帳 JSON のパス（cwd 非依存で解決する）
PIPES_PATH = Path(__file__).resolve().parent.parent / "data" / "pipes.json"

# 経過年数の基準年（D-5: 2026 - installed_year）。デモ用に固定する。
REFERENCE_YEAR = 2026

# 地球半径（km）。Haversine 距離の計算用。
EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """2地点間の大円距離（km）を Haversine 式で求める。"""
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = (
        sin(d_lat / 2.0) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2.0) ** 2
    )
    return EARTH_RADIUS_KM * 2.0 * asin(sqrt(a))


def _load_pipes(path: Path) -> list[PipeRecord]:
    """指定パスの配管台帳 JSON を読み込み、PipeRecord のリストへ検証する。

    - ファイル欠損: ``FileNotFoundError`` をそのまま伝播する（A4）
    - 不正 JSON: ``JSONDecodeError`` を ``ValueError`` に変換する（A4）
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"pipes.json を読み込めません: {path}") from exc
    return [PipeRecord.model_validate(item) for item in data]


@lru_cache(maxsize=1)
def get_pipes() -> list[PipeRecord]:
    """配管台帳を1度だけ読み込んでキャッシュする（A6）。

    ``@lru_cache`` の遅延初期化により、欠損・破損の例外は初回呼び出し時に送出される。
    """
    return _load_pipes(PIPES_PATH)


def find_pipe_by_hydrant(hydrant_id: str) -> PipeRecord | None:
    """指定した消火栓が所属する配管を返す。該当がなければ None（A1 / A2）。"""
    for pipe in get_pipes():
        if hydrant_id in pipe.hydrant_ids:
            return pipe
    return None


def find_nearest_pipe(lat: float, lng: float) -> PipeRecord | None:
    """指定座標から Haversine 距離で最近接の配管を返す（A3）。

    各路線の全頂点との最小距離を比較し、最も近い路線を返す。
    空台帳のときだけ None を返す。
    """
    nearest: PipeRecord | None = None
    nearest_distance = float("inf")
    for pipe in get_pipes():
        for vertex in pipe.route.coordinates:
            vertex_lng, vertex_lat = vertex
            distance = _haversine_km(lat, lng, vertex_lat, vertex_lng)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = pipe
    return nearest


def get_pipe_age(installed_year: int) -> int:
    """布設年から経過年数を算出する（D-5: 2026 - installed_year）。"""
    return REFERENCE_YEAR - installed_year
