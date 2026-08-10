# センサーマップ 詳細パターン

## Point（センサー位置）と Polygon（漏水判定エリア）の型

```ts
// frontend/src/types/sensor.ts
export interface SensorProperties {
  sensorId: string
  severity: 1 | 2 | 3
  lastReadingAt: string // ISO8601
}

export interface LeakZoneProperties {
  zoneId: string
  severity: 1 | 2 | 3
  estimatedRepairCost?: number
}

export type SensorFeature = GeoJSON.Feature<GeoJSON.Point, SensorProperties>
export type SensorFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  SensorProperties
>

export type LeakZoneFeature = GeoJSON.Feature<GeoJSON.Polygon, LeakZoneProperties>
export type LeakZoneFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Polygon,
  LeakZoneProperties
>
```

Polygon の座標は「線形環（linear ring）の配列」で、各環は `[lng, lat]` の配列。
最初と最後の座標が一致していないと不正なGeoJSONになる：

```json
{
  "type": "Feature",
  "properties": { "zoneId": "zone-01", "severity": 3 },
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [139.767, 35.681],
        [139.768, 35.681],
        [139.768, 35.682],
        [139.767, 35.682],
        [139.767, 35.681]
      ]
    ]
  }
}
```

## 2レイヤー（センサー点 + 判定エリア面）を1つの地図に重ねる

```tsx
// frontend/src/components/map/SensorMapInner.tsx
'use client'

import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import '@/lib/leaflet-icon-fix'
import 'leaflet/dist/leaflet.css'
import type { SensorFeatureCollection, LeakZoneFeatureCollection } from '@/types/sensor'

interface Props {
  sensors: SensorFeatureCollection
  leakZones: LeakZoneFeatureCollection
}

export default function SensorMapInner({ sensors, leakZones }: Props) {
  return (
    <MapContainer center={[35.681, 139.767]} zoom={15} style={{ height: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {/* 面レイヤーを先、点レイヤーを後にして点が面の上に描画されるようにする */}
      <GeoJSON
        key={`zones-${leakZones.features.length}`}
        data={leakZones}
        style={(feature) => ({
          color: feature?.properties.severity === 3 ? '#ef4444' : '#f59e0b',
          fillOpacity: 0.2,
        })}
      />
      <GeoJSON key={`sensors-${sensors.features.length}`} data={sensors} pointToLayer={pointToLayer} />
    </MapContainer>
  )
}
```

`<GeoJSON>` を複数使う場合、それぞれの `key` は独立して管理する（片方のデータだけ
更新されても、もう片方まで無駄に再マウントしないように prefix を分ける）。

## `useMap()` で地図インスタンスを操作する（例: 新規センサーへのオートパン）

```tsx
'use client'

import { useMap } from 'react-leaflet'
import { useEffect } from 'react'

function FlyToNewSensor({ target }: { target: [number, number] | null }) {
  const map = useMap()

  useEffect(() => {
    if (target) {
      map.flyTo(target, 17)
    }
  }, [target, map])

  return null
}
```

`useMap()` は `<MapContainer>` の子孫コンポーネントの中でしか呼べない（Context経由で
地図インスタンスを受け取るため）。`SensorMapInner` の外に出すと `undefined` エラーに
なる。

## FastAPI 側から受け取るデータの想定形

バックエンドの `/sensors` エンドポイントは `SensorFeatureCollection` と互換の JSON を
返す想定にしておくと、フロント側で変換コードを書かずに `<GeoJSON data={...}>` へ
そのまま渡せる（`fastapi-pydantic-v2-patterns` スキルで Pydantic モデルを
GeoJSON準拠の構造にしておくと二重定義を避けられる）。
