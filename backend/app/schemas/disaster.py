"""防災モード用レスポンス・要求スキーマ。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon ジオメトリ（始点と終点が一致する環）。"""

    model_config = ConfigDict(strict=True)

    type: str = "Polygon"
    coordinates: list[list[list[float]]] = Field(
        ...,
        description="[[[経度, 緯度], ...]] のネスト配列（外輪）。始点と終点は同じ座標",
    )


class DisasterCluster(BaseModel):
    """被災エリアクラスタ。"""

    model_config = ConfigDict(strict=True, extra="forbid")

    cluster_id: str = Field(..., description="クラスタ識別子")
    center_lat: float = Field(..., description="重心地の緯度")
    center_lng: float = Field(..., description="重心地の経度")
    affected_sensor_ids: list[str] = Field(..., description="影響を受けたセンサーID群")
    affected_pipe_ids: list[str] = Field(..., description="影響を受けた配管ID群")
    estimated_households: int = Field(..., description="想定断水世帯数（口径から計算）")
    priority_valve_hydrant_id: str = Field(..., description="優先閉栓バルブ（消火栓ID）")
    geometry: GeoJSONPolygon = Field(..., description="クラスタ範囲を表すGeoJSON Polygon")


class DisasterSummaryResponse(BaseModel):
    """GET /api/v1/disaster/summary のレスポンス。"""

    model_config = ConfigDict(strict=True, extra="forbid")

    total_clusters: int = Field(..., description="検出されたクラスタ総数")
    total_affected_households: int = Field(..., description="総想定断水世帯数")
    clusters: list[DisasterCluster] = Field(default_factory=list, description="クラスタ一覧")


class DisasterSimulateResponse(BaseModel):
    """POST /api/v1/disaster/simulate のレスポンス。"""

    model_config = ConfigDict(strict=True, extra="forbid")

    inserted_count: int = Field(..., description="投入された Level 3 アラート件数")
    message: str = Field(..., description="ステータスメッセージ")


class DisasterResetResponse(BaseModel):
    """DELETE /simulate のレスポンス。"""

    model_config = ConfigDict(strict=True, extra="forbid")

    removed_count: int = Field(..., description="削除したシミュレーション件数")
    message: str = Field(..., description="ステータスメッセージ")
