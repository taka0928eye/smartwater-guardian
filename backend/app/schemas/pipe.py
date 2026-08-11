"""疑似GIS配管台帳（BE-4）のスキーマ（Pydantic v2）。

``app/data/pipes.json`` の1路線分を ``PipeRecord`` として検証する。
外部入力ではないが、台帳データの品質を境界で保証するため strict 入力に統一する。
座標順序は GeoJSON 標準どおり [経度, 緯度]（Leaflet 側の [緯度, 経度] 変換は FE-3 の責務）。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.telemetry import STRICT_INPUT_CONFIG

# 配管素材。実在する水道管の代表値に絞る。
PipeMaterial = Literal["ductile_iron", "cast_iron", "pvc", "steel"]

# 口径（mm）。東京都の配水本管・配水管で一般的な代表値に絞る。
PipeDiameterMm = Literal[75, 100, 150, 200]

# 布設年の許容範囲。東京都水道局の配水管整備が本格化した年代を下限とし、
# 台帳データの整備時点を上限とする。
MIN_INSTALL_YEAR = 1965
MAX_INSTALL_YEAR = 2015


class GeoJSONLineString(BaseModel):
    """GeoJSON の LineString ジオメトリ。座標は [経度, 緯度] の順。"""

    model_config = STRICT_INPUT_CONFIG

    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]] = Field(
        min_length=2, description="路線の頂点列（各頂点 [経度, 緯度]・2点以上）"
    )

    @field_validator("coordinates")
    @classmethod
    def _validate_vertices(cls, coordinates: list[list[float]]) -> list[list[float]]:
        """各頂点が [経度, 緯度] の2要素で、経緯度の範囲内であることを保証する。"""
        for vertex in coordinates:
            if len(vertex) != 2:
                raise ValueError(f"各頂点は [経度, 緯度] の2要素である必要があります: {vertex}")
            lng, lat = vertex
            if not (-180.0 <= lng <= 180.0 and -90.0 <= lat <= 90.0):
                raise ValueError(f"頂点の経緯度が範囲外です: {vertex}")
        return coordinates


class PipeRecord(BaseModel):
    """配管台帳の1路線（app/data/pipes.json の1要素）。"""

    model_config = STRICT_INPUT_CONFIG

    pipe_id: str = Field(description="配管識別子（例: P-001）")
    material: PipeMaterial = Field(description="配管素材")
    diameter_mm: PipeDiameterMm = Field(description="口径（mm）")
    installed_year: int = Field(ge=MIN_INSTALL_YEAR, le=MAX_INSTALL_YEAR, description="布設年")
    burial_depth_m: float = Field(gt=0.0, description="埋設深さ（m）")
    route: GeoJSONLineString = Field(description="路線ジオメトリ")
    hydrant_ids: list[str] = Field(min_length=1, description="路線に所属する消火栓ID列")
