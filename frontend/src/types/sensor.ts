/**
 * FE-3: センサー地図（Leaflet）用の GeoJSON 型定義。
 *
 * バックエンド BE-6 の GET /api/v1/sensors?format=geojson レスポンスと1:1対応する。
 * プロパティ名は FE-1 の規約に合わせ camelCase で定義する
 * （snake_case からの変換は src/lib/api.ts の境界で行う）。
 *
 * 座標順序の注意: GeoJSON 仕様は [経度(lng), 緯度(lat)]。
 * Leaflet の LatLng は [緯度(lat), 経度(lng)] で逆順のため、
 * 変換箇所では必ずコメントで順序を明示すること。
 */
import type { Feature, FeatureCollection, Point } from "geojson";

/** GeoJSON Feature.properties（マーカー描画に使うセンサー状態）。 */
export interface SensorProperties {
  /** センサー識別子（例: SNS-001）。 */
  sensorId: string;
  /** 監視状態（normal / warning / critical / unknown）。 */
  status: string;
  /** 漏水深刻度（0〜3。0=正常）。最新レコード未読込の場合は null。 */
  severityLevel: 0 | 1 | 2 | 3 | null;
  /** 最終計測時刻（ISO8601）。未計測なら null。 */
  lastReadingAt: string | null;
}

/**
 * センサー1台分の GeoJSON Feature。
 * `@types/geojson` の GeoJSON.Feature<GeoJSON.Point, SensorProperties> 相当。
 */
export type SensorFeature = Feature<Point, SensorProperties>;

/** センサー一覧の GeoJSON FeatureCollection。 */
export type SensorFeatureCollection = FeatureCollection<
  Point,
  SensorProperties
>;
