"use client";

/**
 * FE-3: センサー地図の dynamic ラッパー（Client Component）。
 *
 * Leaflet の window 依存による SSR エラーを避けるため、SensorMapInner を
 * dynamic(..., { ssr: false }) で読み込む。
 * ssr: false は Client Component 内でのみ有効（Next.js 16）で、Server Component
 * から直接呼ぶとビルドエラーになる。page.tsx は本コンポーネントを普通に import する。
 */
import dynamic from "next/dynamic";
import { memo } from "react";

import type { SensorMapInnerProps } from "./SensorMapInner";

const SensorMapInner = dynamic(
  () => import("./SensorMapInner"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[500px] w-full items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-500">
        地図を読み込み中…
      </div>
    ),
  },
);

export type SensorMapProps = SensorMapInnerProps;

/** React.memo: props（data / selectedAlertId / onSelectMarker）が不変な再描画
 *  （例: KPI ポーリングによる親の再描画）ではスキップする。 */
function SensorMap(props: SensorMapProps) {
  return <SensorMapInner {...props} />;
}

export default memo(SensorMap);
