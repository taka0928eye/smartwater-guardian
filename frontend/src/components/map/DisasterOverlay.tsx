"use client";

/**
 * BE-7: 防災モードの被災エリアクラスタを地図に描画するコンポーネント（表示専用）。
 *
 * DashboardClient が useDisasterSummary で取得した DisasterSummary を props で受け取り、
 * 各クラスタの GeoJSON Polygon（中心から距離閾値の円近似）を react-leaflet の
 * <GeoJSON> で描画する。データ更新時は key で強制再マウントする（FE-3 と同じ方式）。
 *
 * クラスタは赤系の半透明で塗り、ポップアップに「被災エリア / 想定断水世帯 /
 * 優先閉栓バルブ」を表示する。Leaflet の popup は innerHTML として挿入されるため、
 * API 由来の値を埋め込む前に必ず HTML エスケープする（SensorMapInner と同じ XSS 対策）。
 */
import type { Feature } from "geojson";
import L from "leaflet";
import type { Layer } from "leaflet";
import type { JSX } from "react";
import { GeoJSON } from "react-leaflet";

import type {
  DisasterClusterFeature,
  DisasterClusterFeatureCollection,
  DisasterSummary,
} from "@/types/disaster";

export interface DisasterOverlayProps {
  /** 被災エリアクラスタ一覧（null なら非表示）。 */
  summary: DisasterSummary | null;
}

/** クラスタ Polygon の描画スタイル（赤系・半透明）。 */
export function clusterStyle(): L.PathOptions {
  return {
    color: "#ef4444",
    weight: 2,
    fillColor: "#ef4444",
    fillOpacity: 0.2,
    // e2e テスト（disaster.spec.ts）がクラスタ Polygon を特定するための CSS クラス。
    className: "disaster-cluster",
  };
}

/** HTML メタ文字をエスケープする（SensorMapInner と同じ XSS 対策）。 */
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * onEachFeature: クラスタ Polygon にポップアップ（被災エリア / 想定断水世帯 /
 * 優先閉栓バルブ）を設定する。Leaflet の bindPopup は innerHTML のため、
 * 文字列値は escapeHtml を通してから埋め込む。
 */
export function onEachCluster(
  feature: DisasterClusterFeature,
  layer: Layer,
): void {
  const { clusterId, estimatedHouseholds, priorityValveHydrantId } =
    feature.properties;
  layer.bindPopup(
    `被災エリア: ${escapeHtml(clusterId)}<br/>` +
      `想定断水世帯: ${estimatedHouseholds} 世帯<br/>` +
      `優先閉栓バルブ: ${escapeHtml(priorityValveHydrantId)}`,
  );
}

/**
 * クラスタ一覧を GeoJSON FeatureCollection へ変換する。
 * geometry（GeoJSON Polygon）の座標は [経度, 緯度] 順のまま保持する。
 */
export function toClusterFeatureCollection(
  summary: DisasterSummary | null,
): DisasterClusterFeatureCollection {
  const features: DisasterClusterFeature[] = (summary?.clusters ?? []).map(
    (cluster) => ({
      type: "Feature",
      properties: {
        clusterId: cluster.clusterId,
        estimatedHouseholds: cluster.estimatedHouseholds,
        priorityValveHydrantId: cluster.priorityValveHydrantId,
      },
      geometry: cluster.geometry,
    }),
  );
  return { type: "FeatureCollection", features };
}

/**
 * <GeoJSON> をデータ更新時に強制再マウントするためのキー文字列。
 * クラスタ ID を連結する（データ非存在時は空文字）。
 */
export function buildDisasterLayerKey(summary: DisasterSummary | null): string {
  return (summary?.clusters ?? []).map((c) => c.clusterId).join("|");
}

export default function DisasterOverlay({
  summary,
}: DisasterOverlayProps): JSX.Element | null {
  if (!summary || summary.clusters.length === 0) {
    // Level 3 が 0 件のときは何も描画しない（受け入れ条件）。
    return null;
  }
  return (
    <GeoJSON
      key={buildDisasterLayerKey(summary)}
      data={toClusterFeatureCollection(summary)}
      style={clusterStyle}
      onEachFeature={(feature: Feature, layer: Layer) =>
        onEachCluster(feature as DisasterClusterFeature, layer)
      }
    />
  );
}
