// @vitest-environment jsdom
/**
 * BE-7: 被災エリアクラスタ描画（components/map/DisasterOverlay.tsx）の TDD テスト。
 *
 * react-leaflet はモックし、Leaflet 本体（L.PathOptions 等）は実物を使う。
 * 純関数（toClusterFeatureCollection / buildDisasterLayerKey / clusterStyle /
 * onEachCluster）は直接検証し、コンポーネントは GeoJSON の props 記録で検証する。
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import L from "leaflet";

import type { DisasterSummary } from "@/types/disaster";
import DisasterOverlay, {
  buildDisasterLayerKey,
  clusterStyle,
  onEachCluster,
  toClusterFeatureCollection,
} from "../DisasterOverlay";

// --- モック共通の記録領域（vi.mock より先に初期化されるため vi.hoisted） ---
const { captured } = vi.hoisted(() => {
  const captured = {
    geoProps: [] as Record<string, unknown>[],
    geoMountCount: 0,
  };
  return { captured };
});

/** react-leaflet の GeoJSON モック。props を記録しつつ子を描画する。 */
function GeoJSONMock(props: Record<string, unknown>) {
  React.useEffect(() => {
    captured.geoMountCount += 1;
  }, []);
  captured.geoProps.push(props);
  return null;
}

vi.mock("react-leaflet", () => ({
  MapContainer: () => null,
  TileLayer: () => null,
  GeoJSON: GeoJSONMock,
}));

/** BE-7 契約フィクスチャ（クラスタ 1 件）。 */
const SUMMARY: DisasterSummary = {
  totalClusters: 1,
  totalAffectedHouseholds: 170,
  clusters: [
    {
      clusterId: "CLS-001",
      centerLat: 35.6812,
      centerLng: 139.7671,
      affectedSensorIds: ["SEN-DISASTER-001"],
      affectedPipeIds: ["PIPE-1"],
      estimatedHouseholds: 170,
      priorityValveHydrantId: "HYD-001",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [139.7671, 35.6812],
            [139.7691, 35.6832],
            [139.7671, 35.6812],
          ],
        ],
      },
    },
  ],
};

/** クラスタが 2 件に増えた更新版。 */
const SUMMARY_UPDATED: DisasterSummary = {
  ...SUMMARY,
  totalClusters: 2,
  totalAffectedHouseholds: 340,
  clusters: [
    ...SUMMARY.clusters,
    {
      clusterId: "CLS-002",
      centerLat: 35.7,
      centerLng: 139.7,
      affectedSensorIds: ["SEN-DISASTER-002"],
      affectedPipeIds: ["PIPE-2"],
      estimatedHouseholds: 170,
      priorityValveHydrantId: "HYD-002",
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [139.7, 35.7],
            [139.702, 35.702],
            [139.7, 35.7],
          ],
        ],
      },
    },
  ],
};

beforeEach(() => {
  captured.geoProps.length = 0;
  captured.geoMountCount = 0;
});

describe("toClusterFeatureCollection", () => {
  it("クラスタを GeoJSON FeatureCollection（Polygon）へ変換し、座標は [経度, 緯度] 順を保持する", () => {
    const fc = toClusterFeatureCollection(SUMMARY);

    expect(fc.type).toBe("FeatureCollection");
    expect(fc.features).toHaveLength(1);
    const feature = fc.features[0];
    expect(feature?.geometry.type).toBe("Polygon");
    // coordinates は入力の geometry をそのまま保持（[経度, 緯度] 順）
    expect(feature?.geometry.coordinates).toEqual(SUMMARY.clusters[0]?.geometry.coordinates);
  });

  it("properties に clusterId / estimatedHouseholds / priorityValveHydrantId を格納する", () => {
    const fc = toClusterFeatureCollection(SUMMARY);
    expect(fc.features[0]?.properties).toEqual({
      clusterId: "CLS-001",
      estimatedHouseholds: 170,
      priorityValveHydrantId: "HYD-001",
    });
  });

  it("null / クラスタ 0 件の場合は空の FeatureCollection を返す", () => {
    expect(toClusterFeatureCollection(null).features).toEqual([]);
    expect(
      toClusterFeatureCollection({
        totalClusters: 0,
        totalAffectedHouseholds: 0,
        clusters: [],
      }).features,
    ).toEqual([]);
  });
});

describe("buildDisasterLayerKey", () => {
  it("clusterId を連結したキーを返す", () => {
    expect(buildDisasterLayerKey(SUMMARY)).toBe("CLS-001");
    expect(buildDisasterLayerKey(SUMMARY_UPDATED)).toBe("CLS-001|CLS-002");
  });

  it("null / クラスタ 0 件の場合は空文字を返す", () => {
    expect(buildDisasterLayerKey(null)).toBe("");
    expect(
      buildDisasterLayerKey({ totalClusters: 0, totalAffectedHouseholds: 0, clusters: [] }),
    ).toBe("");
  });
});

describe("clusterStyle", () => {
  it("赤系の半透明スタイルを返す", () => {
    const style = clusterStyle();
    expect(style.color).toBe("#ef4444");
    expect(style.fillColor).toBe("#ef4444");
    expect(style.fillOpacity).toBe(0.2);
  });

  it("e2e テストでクラスタを特定するための CSS クラスを付与する", () => {
    expect(clusterStyle().className).toBe("disaster-cluster");
  });
});

describe("onEachCluster", () => {
  it("ポップアップにクラスタID・想定断水世帯・優先閉栓バルブを含める", () => {
    const bindPopup = vi.fn();
    const feature = toClusterFeatureCollection(SUMMARY).features[0]!;
    onEachCluster(feature, { bindPopup } as unknown as L.Layer);

    expect(bindPopup).toHaveBeenCalledTimes(1);
    const content = bindPopup.mock.calls[0]?.[0] as string | undefined;
    expect(content).toContain("CLS-001");
    expect(content).toContain("170 世帯");
    expect(content).toContain("HYD-001");
  });

  it("clusterId / hydrantId の HTML メタ文字はエスケープしてポップアップに渡す（XSS対策）", () => {
    const bindPopup = vi.fn();
    const feature = {
      type: "Feature" as const,
      properties: {
        clusterId: "<img src=x onerror=alert(1)>",
        estimatedHouseholds: 170,
        priorityValveHydrantId: "&lt;script&gt;",
      },
      geometry: {
        type: "Polygon" as const,
        coordinates: [
          [
            [139.7, 35.7],
            [139.702, 35.702],
            [139.7, 35.7],
          ],
        ],
      },
    };
    onEachCluster(feature, { bindPopup } as unknown as L.Layer);

    const content = bindPopup.mock.calls[0]?.[0] as string | undefined;
    expect(content).not.toContain("<img");
    expect(content).toContain("&lt;img");
    expect(content).not.toContain("&lt;script&gt;");
    expect(content).toContain("&amp;lt;script&amp;gt;");
  });
});

describe("DisasterOverlay", () => {
  it("クラスタがある場合は GeoJSON に FeatureCollection を渡す", () => {
    render(<DisasterOverlay summary={SUMMARY} />);

    expect(captured.geoProps).toHaveLength(1);
    const geo = captured.geoProps[0] as {
      data?: ReturnType<typeof toClusterFeatureCollection>;
    };
    expect(geo.data?.features).toHaveLength(1);
    expect(geo.data?.features[0]?.properties.clusterId).toBe("CLS-001");
  });

  it("GeoJSON に style と onEachFeature を渡す", () => {
    render(<DisasterOverlay summary={SUMMARY} />);

    const geo = captured.geoProps[0] as {
      style?: typeof clusterStyle;
      onEachFeature?: typeof onEachCluster;
    };
    expect(geo.style).toBe(clusterStyle);
    expect(geo.onEachFeature).toBeDefined();
  });

  it("データ更新時は key の変化で GeoJSON が再マウントされる", () => {
    const { rerender } = render(<DisasterOverlay summary={SUMMARY} />);
    expect(captured.geoMountCount).toBe(1);

    // 同一データの再レンダーでは再マウントしない
    rerender(<DisasterOverlay summary={SUMMARY} />);
    expect(captured.geoMountCount).toBe(1);

    // クラスタ増加で key が変わり再マウントする
    rerender(<DisasterOverlay summary={SUMMARY_UPDATED} />);
    expect(captured.geoMountCount).toBe(2);
  });

  it("summary が null / クラスタ 0 件の場合は何も描画しない", () => {
    const { rerender } = render(<DisasterOverlay summary={null} />);
    expect(captured.geoProps).toHaveLength(0);

    rerender(
      <DisasterOverlay
        summary={{ totalClusters: 0, totalAffectedHouseholds: 0, clusters: [] }}
      />,
    );
    expect(captured.geoProps).toHaveLength(0);
  });
});
