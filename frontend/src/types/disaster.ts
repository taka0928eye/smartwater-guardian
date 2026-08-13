/**
 * BE-7: 防災モード API（GET /api/v1/disaster/summary / POST /simulate）のレスポンス型。
 *
 * バックエンドは snake_case（Pydantic v2）、フロントは camelCase で統一する。
 * snake_case -> camelCase 変換は src/lib/api.ts の境界で一度だけ行うため、
 * 本ファイルの型は camelCase 側のみを公開する（FE-1 規約 / project.md c2）。
 *
 * 座標順序の注意: クラスタ geometry（GeoJSON Polygon）は GeoJSON 標準の
 * [経度(lng), 緯度(lat)] 順。Leaflet の [緯度, 経度] とは逆順のため、
 * 変換箇所では必ずコメントで順序を明示すること（FE-3 と同じ規約）。
 */
import type { Feature, FeatureCollection, Polygon } from "geojson";

/** GeoJSON Polygon ジオメトリ（始点と終点が一致する外輪）。 */
export interface DisasterPolygonGeometry {
  type: "Polygon";
  /** [[[経度, 緯度], ...]] のネスト配列（外輪）。 */
  coordinates: number[][][];
}

/** 被災エリアクラスタ（backend/app/schemas/disaster.py の DisasterCluster 相当）。 */
export interface DisasterCluster {
  /** クラスタ識別子（例: CLS-001）。 */
  clusterId: string;
  /** 重心地の緯度。 */
  centerLat: number;
  /** 重心地の経度。 */
  centerLng: number;
  /** 影響を受けたセンサーID群。 */
  affectedSensorIds: string[];
  /** 影響を受けた配管ID群。 */
  affectedPipeIds: string[];
  /** 想定断水世帯数（口径から計算）。 */
  estimatedHouseholds: number;
  /** 優先閉栓バルブ（消火栓ID）。 */
  priorityValveHydrantId: string;
  /** クラスタ範囲を表す GeoJSON Polygon。 */
  geometry: DisasterPolygonGeometry;
}

/** GET /api/v1/disaster/summary のレスポンス。 */
export interface DisasterSummary {
  /** 検出されたクラスタ総数。 */
  totalClusters: number;
  /** 総想定断水世帯数。 */
  totalAffectedHouseholds: number;
  /** クラスタ一覧（Level 3 が 0 件なら空配列）。 */
  clusters: DisasterCluster[];
}

/** POST /api/v1/disaster/simulate のレスポンス。 */
export interface DisasterSimulateResponse {
  /** 投入された Level 3 アラート件数。 */
  insertedCount: number;
  /** ステータスメッセージ。 */
  message: string;
}

/** クラスタ描画用 GeoJSON Feature の properties。 */
export interface DisasterClusterProperties {
  /** クラスタ識別子（例: CLS-001）。 */
  clusterId: string;
  /** 想定断水世帯数。 */
  estimatedHouseholds: number;
  /** 優先閉栓バルブ（消火栓ID）。 */
  priorityValveHydrantId: string;
}

/** クラスタ 1 件分の GeoJSON Feature。 */
export type DisasterClusterFeature = Feature<Polygon, DisasterClusterProperties>;

/** クラスタ一覧の GeoJSON FeatureCollection。 */
export type DisasterClusterFeatureCollection = FeatureCollection<
  Polygon,
  DisasterClusterProperties
>;
