---
name: geojson-leaflet-integration
description: >
  GeoJSON構造の設計、react-leaflet（5.0.0）/ Leaflet（1.9.4）でのセンサー位置・
  漏水判定エリアの地図可視化パターン（カスタムマーカー・ポップアップ・再描画の
  ハマりどころ）。Triggers on: センサー位置や漏水エリアのGeoJSONデータ設計、
  Leaflet/react-leafletでのマーカー・ポップアップ・ヒートマップ描画、地図データの
  更新が画面に反映されない不具合、Leafletのデフォルトアイコンが表示されない不具合。
---

# GeoJSON + Leaflet 統合パターン（センサーマップ向け）

Leaflet を使う地図コンポーネントは必ずクライアント専用（`window` 依存）。
`next-app-router-best-practices` スキルの「実体（'use client'）＋ dynamic ラッパー
（ssr:false）」の2段構成が前提。このスキルは地図の**中身**（データ構造と描画）に
フォーカスする。

## GeoJSON の基本構造

センサー・漏水エリアは `FeatureCollection` としてまとめる：

```ts
// frontend/src/types/sensor.ts
export interface SensorProperties {
  sensorId: string
  severity: 1 | 2 | 3
  lastReadingAt: string // ISO8601
}

export type SensorFeature = GeoJSON.Feature<GeoJSON.Point, SensorProperties>
export type SensorFeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Point, SensorProperties>
```

- 座標順序は **[経度, 緯度]**（`[lng, lat]`）。Leaflet の `LatLng`（`[lat, lng]`）と
  逆順になる典型的なバグの原因なので、GeoJSON→Leaflet変換をまたぐ箇所では必ず
  どちらの順序かをコメントで明示する。
- 漏水判定エリアのように面で表す場合は `geometry.type: "Polygon"` を使う
  （`references/sensor-map-patterns.md` に例あり）。

## react-leaflet の `<GeoJSON>` は data が変わっても再描画されない

`<GeoJSON data={...} />` は内部で Leaflet の `L.geoJSON` レイヤーを**マウント時に
一度だけ**生成する。`data` prop を差し替えても既存レイヤーは更新されない
（Leafletの生データレイヤーはReactの再レンダーモデルと相性が悪い、react-leafletの
既知の制約）。データが変わったら `key` を変えて強制的に再マウントするのが定石：

```tsx
'use client'

import { GeoJSON } from 'react-leaflet'

function SensorLayer({ data }: { data: SensorFeatureCollection }) {
  // データのバージョン/更新時刻をkeyに使い、変化したら再マウントさせる
  const layerKey = data.features.map((f) => f.properties.lastReadingAt).join('|')

  return (
    <GeoJSON
      key={layerKey}
      data={data}
      pointToLayer={pointToLayer}
      onEachFeature={onEachFeature}
    />
  )
}
```

## deverity別カスタムマーカー（`pointToLayer`）

```tsx
import L from 'leaflet'
import { CircleMarker } from 'react-leaflet'

const SEVERITY_COLOR: Record<1 | 2 | 3, string> = {
  1: '#22c55e', // 経過観察
  2: '#f59e0b', // 要点検
  3: '#ef4444', // 緊急対応
}

function pointToLayer(feature: SensorFeature, latlng: L.LatLng) {
  return L.circleMarker(latlng, {
    radius: 8,
    color: SEVERITY_COLOR[feature.properties.severity],
    fillOpacity: 0.8,
  })
}

function onEachFeature(feature: SensorFeature, layer: L.Layer) {
  layer.bindPopup(
    `センサー: ${feature.properties.sensorId}<br/>最終計測: ${feature.properties.lastReadingAt}`
  )
}
```

`CircleMarker`（SVGベース）は自前で色分けしやすく、既定アイコン画像の問題も回避できる
ので、severity別の色分けが必要なこのユースケースでは既定マーカーより扱いやすい。

## 既定マーカー画像がバンドラーで404になる問題

`L.Icon.Default` を素朴に使うと、Webpack/Turbopack環境ではマーカー画像
（`marker-icon.png` 等）へのパス解決が壊れ、地図上にアイコンが表示されない
（Leaflet自体が抱える既知の問題で、Next.jsに限らずバンドラー全般で起きる）。
`CircleMarker`/`DivIcon` を使わず既定の `Marker` アイコンを使う場合は、モジュール
読み込み時に明示的にパスを差し替える：

```ts
// frontend/src/lib/leaflet-icon-fix.ts
'use client'

import L from 'leaflet'
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

// @ts-expect-error Leaflet内部プロパティの直接削除（公式のワークアラウンド）
delete L.Icon.Default.prototype._getIconUrl

L.Icon.Default.mergeOptions({
  iconUrl: icon.src ?? icon,
  shadowUrl: iconShadow.src ?? iconShadow,
})
```

このファイルを地図の Client Component（`SensorMapInner.tsx` 相当）の先頭で import
する。

## ヒートマップが必要な場合

漏水判定エリアを密度ヒートマップで見せたい場合、`leaflet.heat` は
**`frontend/package.json` に未インストール**。追加する場合は
`npm install leaflet.heat @types/leaflet.heat`（CLAUDE.mdのHuman-in-the-Loop原則により
新規ライブラリ追加はユーザー承認を得てから）。`leaflet.heat` はLeafletのプラグインで
ESM/型定義が弱いため、`useEffect` 内で `L.heatLayer(points, opts).addTo(map)` を
命令的に呼ぶ形になる（react-leafletの宣言的コンポーネントは提供されていない）。

## 詳細な型・パターン集

`Feature<Point, {...}>` の完全な型定義、Polygonでの漏水エリア表現、
`useMap()` フックでの地図インスタンス操作などは
[references/sensor-map-patterns.md](references/sensor-map-patterns.md) を参照。
