// @vitest-environment jsdom
/**
 * FE-3: センサー地図（components/map/SensorMapInner.tsx / SensorMap.tsx）の TDD テスト。
 *
 * react-leaflet と next/dynamic はモックし、Leaflet 本体（L.circleMarker 等）は
 * 実物を使う。モックの props に記録された center / zoom / data / コールバックを
 * 取り出して検証する（React の <GeoJSON> は key を props に渡さないため、
 * 再マウントはマウント回数で検証する）。
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import L from "leaflet";

import { getSeverityColor, getSeverityLabel } from "@/lib/severity";
import type {
  SensorFeature,
  SensorFeatureCollection,
  SensorProperties,
} from "@/types/sensor";
import SensorMap from "../SensorMap";
import SensorMapInner, {
  buildLayerKey,
  calculateMapView,
  onEachFeature,
  pointToLayer,
} from "../SensorMapInner";

// --- モック共通の記録領域（vi.mock より先に初期化されるため vi.hoisted） ---
const { captured, dynamicMock } = vi.hoisted(() => {
  const captured = {
    mapProps: [] as Record<string, unknown>[],
    geoProps: [] as Record<string, unknown>[],
    geoMountCount: 0,
  };
  return { captured, dynamicMock: vi.fn() };
});

// react-leaflet のモック。center / zoom / data / コールバックを記録しつつ
// 子（GeoJSON 等）を描画する。MapContainer の props には children が含まれるため、
// 必ず children を描画して下流の GeoJSON がマウントされるようにする。
function MapContainerMock(props: {
  center?: unknown;
  zoom?: unknown;
  children?: React.ReactNode;
}) {
  captured.mapProps.push(props);
  return React.createElement("div", null, props.children);
}

function TileLayerMock() {
  return null;
}

function GeoJSONMock(props: Record<string, unknown>) {
  // マウント時のみカウントする（key による強制再マウントの検証用）。
  // React は親の再レンダー時に子関数を再実行するため、関数本体のカウントでは
  // 再マウントと再レンダーを区別できない。useEffect([]) はマウント時のみ発火する。
  React.useEffect(() => {
    captured.geoMountCount += 1;
  }, []);
  captured.geoProps.push(props);
  return null;
}

vi.mock("react-leaflet", () => ({
  MapContainer: MapContainerMock,
  TileLayer: TileLayerMock,
  GeoJSON: GeoJSONMock,
}));

// next/dynamic のモック。dynamic(importFn, options) の呼び出しを動的 import 時
// （モジュール評価時）に記録しつつ、内側コンポーネントの代役（PassThrough）を返す。
// これにより SensorMap の props 透過を同期検証できる。
vi.mock("next/dynamic", () => ({
  default: (importFn: () => Promise<unknown>, opts: unknown) => {
    dynamicMock(importFn, opts);
    const PassThrough = (props: Record<string, unknown>) =>
      React.createElement(
        "div",
        { "data-testid": "dynamic-inner" },
        props.data === undefined ? "no-data" : "has-data",
      );
    return PassThrough;
  },
}));

// --- フィクスチャ生成ヘルパー ---
function makeFeature(
  sensorId: string,
  lng: number,
  lat: number,
  severityLevel: SensorProperties["severityLevel"],
  lastReadingAt: SensorProperties["lastReadingAt"],
): SensorFeature {
  return {
    type: "Feature",
    properties: { sensorId, status: "normal", severityLevel, lastReadingAt },
    // GeoJSON 標準の座標順序: [経度, 緯度]
    geometry: { type: "Point", coordinates: [lng, lat] },
  };
}

function makeCollection(features: SensorFeature[]): SensorFeatureCollection {
  return { type: "FeatureCollection", features };
}

describe("calculateMapView", () => {
  it("全 feature の重心（平均緯度・経度）を [lat, lng] で返す", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "t1"),
      makeFeature("SNS-002", 139.9, 35.9, 2, "t2"),
    ]);
    // 入力 coordinates は GeoJSON[lng, lat] で、出力 center は Leaflet[lat, lng]
    expect(calculateMapView(fc).center).toEqual([35.8, 139.8]);
  });

  it("座標の広がりに応じてズームを算出する", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "t1"),
      makeFeature("SNS-002", 139.9, 35.9, 2, "t2"),
    ]);
    // latSpan=0.2 => round(16 - 0.2*8)=14
    expect(calculateMapView(fc).zoom).toBe(14);
  });

  it("単一点の場合は最大ズームを返す", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7444, 35.7019, 1, "t1"),
    ]);
    expect(calculateMapView(fc).center).toEqual([35.7019, 139.7444]);
    expect(calculateMapView(fc).zoom).toBe(16);
  });

  it("広がりが大きい場合は最小ズームにクランプする", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.0, 35.0, 1, "t1"),
      makeFeature("SNS-002", 140.0, 36.5, 2, "t2"),
    ]);
    // maxSpan=1.5 => round(16 - 12)=4 => クランプで 11
    expect(calculateMapView(fc).zoom).toBe(11);
  });

  it("データが空の場合はデフォルトビューを返す", () => {
    const view = calculateMapView(makeCollection([]));
    expect(view.center).toEqual([35.6812, 139.7671]);
    expect(view.zoom).toBe(12);
  });
});

describe("buildLayerKey", () => {
  it("同一データからは同一のキーを返す", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
      makeFeature("SNS-002", 139.9, 35.9, 2, "2026-08-10T00:00:01Z"),
    ]);
    const same = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
      makeFeature("SNS-002", 139.9, 35.9, 2, "2026-08-10T00:00:01Z"),
    ]);
    expect(buildLayerKey(fc)).toBe(buildLayerKey(same));
  });

  it("lastReadingAt の変更でキーが変化する", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
    ]);
    const updated = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:05:00Z"),
    ]);
    expect(buildLayerKey(fc)).not.toBe(buildLayerKey(updated));
  });

  it("severityLevel の変更でもキーが変化する", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
    ]);
    const escalated = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 3, "2026-08-10T00:00:00Z"),
    ]);
    expect(buildLayerKey(fc)).not.toBe(buildLayerKey(escalated));
  });

  it("null の lastReadingAt / severityLevel を含んでも安全に生成できる", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, null, null),
    ]);
    expect(typeof buildLayerKey(fc)).toBe("string");
    expect(buildLayerKey(fc)).toContain("0");
  });
});

describe("pointToLayer", () => {
  const latlng = L.latLng(35.7, 139.7);

  it.each([
    { level: 1 as const, expected: getSeverityColor(1) },
    { level: 2 as const, expected: getSeverityColor(2) },
    { level: 3 as const, expected: getSeverityColor(3) },
  ])(
    "severity $level は getSeverityColor と一致する色の CircleMarker を返す",
    ({ level, expected }) => {
      const feature = makeFeature(
        "SNS-001",
        139.7,
        35.7,
        level,
        "2026-08-10T00:00:00Z",
      );
      const layer = pointToLayer(feature, latlng);
      expect(layer.options.color).toBe(expected);
    },
  );

  it("severity が null の場合はレベル0（正常）の色を返す", () => {
    const feature = makeFeature("SNS-001", 139.7, 35.7, null, null);
    const layer = pointToLayer(feature, latlng);
    expect(layer.options.color).toBe(getSeverityColor(0));
  });

  it("Level 3 のみ点滅アニメーション用クラスを付与する", () => {
    const level3 = pointToLayer(
      makeFeature("SNS-003", 139.7, 35.7, 3, "t"),
      latlng,
    );
    expect(level3.options.className).toBe("sensor-pulse-3");

    const level1 = pointToLayer(
      makeFeature("SNS-001", 139.7, 35.7, 1, "t"),
      latlng,
    );
    expect(level1.options.className).toBeUndefined();
  });
});

describe("onEachFeature", () => {
  it("ポップアップにセンサーID・深刻度ラベル・最終計測時刻を含める", () => {
    const bindPopup = vi.fn();
    const feature = makeFeature(
      "SNS-001",
      139.7,
      35.7,
      2,
      "2026-08-10T00:00:00Z",
    );
    onEachFeature(feature, { bindPopup } as unknown as L.Layer);

    expect(bindPopup).toHaveBeenCalledTimes(1);
    const content = bindPopup.mock.calls[0]?.[0] as string | undefined;
    expect(content).toContain("SNS-001");
    expect(content).toContain(getSeverityLabel(2));
    expect(content).toContain("2026-08-10T00:00:00Z");
  });
});

describe("SensorMapInner", () => {
  beforeEach(() => {
    captured.mapProps.length = 0;
    captured.geoProps.length = 0;
    captured.geoMountCount = 0;
  });

  it("重心から算出した中心・ズームを MapContainer に渡す", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
      makeFeature("SNS-002", 139.9, 35.9, 2, "2026-08-10T00:00:01Z"),
    ]);
    render(<SensorMapInner data={fc} />);

    const mapProps = captured.mapProps[0] as {
      center?: [number, number];
      zoom?: number;
    };
    expect(mapProps.center).toEqual([35.8, 139.8]);
    expect(mapProps.zoom).toBe(14);
  });

  it("GeoJSON に data と pointToLayer / onEachFeature を渡す", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
    ]);
    render(<SensorMapInner data={fc} />);

    const geo = captured.geoProps[0] as {
      data?: SensorFeatureCollection;
      pointToLayer?: typeof pointToLayer;
      onEachFeature?: typeof onEachFeature;
    };
    expect(geo.data).toBe(fc);
    expect(geo.pointToLayer).toBe(pointToLayer);
    expect(geo.onEachFeature).toBe(onEachFeature);
  });

  it("データ更新時は key の変化で GeoJSON が再マウントされる", () => {
    const data1 = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
    ]);
    const { rerender } = render(<SensorMapInner data={data1} />);
    expect(captured.geoMountCount).toBe(1);

    // 同一データの再レンダーでは再マウントしない
    rerender(<SensorMapInner data={data1} />);
    expect(captured.geoMountCount).toBe(1);

    // 深刻度が変わると key が変わり、再マウントする
    const data2 = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 3, "2026-08-10T00:00:00Z"),
    ]);
    rerender(<SensorMapInner data={data2} />);
    expect(captured.geoMountCount).toBe(2);
  });
});

describe("SensorMap", () => {
  it("next/dynamic を ssr:false + loading オプションで呼び出す", () => {
    render(<SensorMap data={makeCollection([])} />);
    // dynamic() はモジュール評価時に1回だけ呼ばれる（呼び出しは import 時点で記録済み）。
    expect(dynamicMock).toHaveBeenCalledTimes(1);
    const options = dynamicMock.mock.calls[0]?.[1] as
      | { ssr?: boolean; loading?: unknown }
      | undefined;
    expect(options?.ssr).toBe(false);
    expect(typeof options?.loading).toBe("function");
  });

  it("受け取った data を内側コンポーネントへ透過する", () => {
    const fc = makeCollection([
      makeFeature("SNS-001", 139.7, 35.7, 1, "2026-08-10T00:00:00Z"),
    ]);
    render(<SensorMap data={fc} />);
    expect(screen.getByTestId("dynamic-inner").textContent).toBe("has-data");
  });
});
