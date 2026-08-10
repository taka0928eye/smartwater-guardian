"use client";

/**
 * FE-3: センサー地図の実体（Client Component）。
 *
 * Leaflet は window に依存するため、本ファイルが SSR 実行されないよう
 * SensorMap.tsx が dynamic(..., { ssr: false }) でラップする。
 * MapContainer と leaflet.css の import はこのファイルに集約する。
 *
 * react-leaflet の <GeoJSON> は data 変更で再描画されない既知制約があるため、
 * buildLayerKey の文字列を key に渡し、データ更新時に強制再マウントする。
 */

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";

import { getSeverityColor, getSeverityLabel } from "@/lib/severity";
import type { SensorFeature, SensorFeatureCollection } from "@/types/sensor";

export interface SensorMapInnerProps {
  /** BE-6 の GET /api/v1/sensors?format=geojson レスポンス。 */
  data: SensorFeatureCollection;
}

/** 地図の初期ビュー。center は Leaflet[緯度, 経度] の順。 */
export interface MapView {
  center: [number, number];
  zoom: number;
}

/**
 * 全 feature の重心（平均座標）から初期ビューを算出する。
 * 入力 coordinates は GeoJSON[lng, lat]、出力 center は Leaflet[lat, lng] で逆順。
 */
export function calculateMapView(fc: SensorFeatureCollection): MapView {
  if (fc.features.length === 0) {
    // データが空の場合のフォールバック（東京中心）。
    return { center: [35.6812, 139.7671], zoom: 12 };
  }
  // GeoJSON[lng, lat] -> Leaflet[lat, lng]: coordinates[0]=経度, coordinates[1]=緯度
  const lats = fc.features.map((f) => f.geometry.coordinates[1]);
  const lngs = fc.features.map((f) => f.geometry.coordinates[0]);
  const centerLat = lats.reduce((sum, v) => sum + v, 0) / lats.length;
  const centerLng = lngs.reduce((sum, v) => sum + v, 0) / lngs.length;
  const latSpan = Math.max(...lats) - Math.min(...lats);
  const lngSpan = Math.max(...lngs) - Math.min(...lngs);
  const maxSpan = Math.max(latSpan, lngSpan);
  // 広がりが大きいほどズームアウトする（[11, 16] にクランプ）。
  const zoom = Math.max(11, Math.min(16, Math.round(16 - maxSpan * 8)));
  return { center: [centerLat, centerLng], zoom };
}

/**
 * <GeoJSON> をデータ更新時に強制再マウントするためのキー文字列。
 * 各 feature の最終計測時刻と深刻度を連結する（lastReadingAt だけだと
 * null 時の変更を検知できないため、severityLevel も含める）。
 */
export function buildLayerKey(fc: SensorFeatureCollection): string {
  return fc.features
    .map(
      (f) =>
        `${f.properties.lastReadingAt ?? ""}:${f.properties.severityLevel ?? 0}`,
    )
    .join("|");
}

/**
 * pointToLayer: 深刻度に応じて色分けした CircleMarker を返す。
 * 既定ピンアイコン画像はバンドラーで404になるため使用禁止（CircleMarker を採用）。
 * 色は必ず src/lib/severity.ts の getSeverityColor を参照する（再定義禁止）。
 * Level 3（管路破裂）は点滅アニメーション用クラスを付与する。
 */
export function pointToLayer(
  feature: SensorFeature,
  latlng: L.LatLng,
): L.CircleMarker {
  const level = feature.properties.severityLevel ?? 0;
  const color = getSeverityColor(level);
  return L.circleMarker(latlng, {
    radius: 8,
    color,
    fillColor: color,
    fillOpacity: 0.7,
    weight: 2,
    className: level === 3 ? "sensor-pulse-3" : undefined,
  });
}

/**
 * HTML メタ文字をエスケープする。
 * Leaflet の bindPopup は文字列コンテンツを innerHTML としてそのまま挿入するため、
 * API から取得した値（sensorId 等）を埋め込む前に必ず通す（XSS対策）。
 */
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * onEachFeature: ポップアップ（センサーID / 深刻度ラベル / 最終計測時刻）を設定する。
 */
export function onEachFeature(feature: SensorFeature, layer: L.Layer): void {
  const { sensorId, severityLevel, lastReadingAt } = feature.properties;
  const label = getSeverityLabel(severityLevel ?? 0);
  const readingAt = lastReadingAt ?? "—";
  layer.bindPopup(
    `センサーID: ${escapeHtml(sensorId)}<br/>深刻度: ${escapeHtml(label)}<br/>最終計測: ${escapeHtml(readingAt)}`,
  );
}

export default function SensorMapInner({ data }: SensorMapInnerProps) {
  const view = calculateMapView(data); // Leaflet[lat, lng] の中心
  const layerKey = buildLayerKey(data);
  return (
    <MapContainer
      center={view.center}
      zoom={view.zoom}
      className="h-[500px] w-full rounded-xl"
      style={{ height: "500px" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        key={layerKey}
        data={data}
        pointToLayer={pointToLayer}
        onEachFeature={onEachFeature}
      />
    </MapContainer>
  );
}
