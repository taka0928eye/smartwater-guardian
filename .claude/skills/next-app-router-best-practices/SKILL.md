---
name: next-app-router-best-practices
description: >
  Next.js App Router（このプロジェクトは 16.3.0）における 'use client' の設計、
  next/dynamic による SSR 無効化読み込み（Leaflet など window 依存ライブラリの
  ハイドレーションエラー回避）、Route Handlers の設計パターンをまとめたリファレンス。
  Triggers on: frontend/src/app 配下のコンポーネント作成・編集、Leaflet/react-leaflet
  など window/document に依存するライブラリの組み込み、"window is not defined" エラー、
  app/api 配下の Route Handler 追加、'use client' の要否判断、next/dynamic の利用。
---

# Next.js App Router ベストプラクティス（このプロジェクト向け）

## 最初にやること：訓練データを信用しない

`frontend/AGENTS.md`（`frontend/CLAUDE.md` から `@AGENTS.md` で読み込まれる）が明言している
通り、このプロジェクトの Next.js は **16.3.0** で、App Router の挙動は訓練データより新しい
破壊的変更を含む。コードを書く前に、該当トピックのドキュメントを
`frontend/node_modules/next/dist/docs/01-app/` 配下で必ず確認すること（ネットワーク不要、
インストール済みバージョンと完全に一致する）。このスキルは「どのページを読むべきか」の
索引と、実際に読んで確認済みの要点をまとめたものであり、断定的な記述はすべて
`node_modules/next/dist/docs/` の該当ファイルで裏取り済み。

主要な索引：

| トピック | 読むファイル |
|---|---|
| Server/Client Component の境界 | `01-getting-started/05-server-and-client-components.md` |
| Route Handlers | `01-getting-started/15-route-handlers.md` |
| 遅延読み込み・SSR無効化（`next/dynamic`） | `02-guides/lazy-loading.md` |
| キャッシュ全般（Cache Components, `"use cache"`） | `01-getting-started/08-caching.md` |
| データ取得 | `01-getting-started/06-fetching-data.md` |

このプロジェクトの `next.config.ts` には `cacheComponents` は設定されておらず、Cache
Components は未有効化（デフォルトの挙動）。将来 `"use cache"` / `cacheLife` を使う場合は
先に `08-caching.md` を読むこと。

## `'use client'` の境界

- `app/` 配下のコンポーネントは既定で Server Component。`useState`/`useEffect`/イベント
  ハンドラ（`onClick` 等）/ `window`・`localStorage`・`navigator.geolocation` などブラウザ
  API / カスタムフックを使うファイルの**先頭**（import より前）に `'use client'` を書く。
- `'use client'` は「サーバー/クライアントのモジュールグラフの境界」を切るもので、その
  ファイルが import しているモジュールと直接レンダーするコンポーネントは全てクライアント
  バンドルに含まれる。逆に、Client Component に `children`/props として渡された Server
  Component はサーバーでレンダーされたまま渡されるので、`'use client'` を親まで波及させる
  必要はない（Modal などの「スロット」パターンを使うと Server Component をクライアント側の
  枠に差し込める）。
- サードパーティ製コンポーネント（ライブラリ側に `'use client'` が付いていないもの）を
  Server Component から直接使うとエラーになる。自分で `'use client'` 付きの薄いラッパーを
  作って re-export する（下記 Leaflet の例と同じパターン）。
- 機密情報（APIキー等）を扱う関数は `server-only` パッケージで明示的にクライアント
  バンドルへの混入を防げる（任意。Next.js は `NEXT_PUBLIC_` 以外の環境変数をクライアント
  バンドルから自動的に空文字に置換するが、意図しない import を早期にビルドエラーとして
  検出できる）。

## Leaflet を SSR なしで読み込む（`next/dynamic` + `ssr: false`）

`react-leaflet` の `MapContainer` はマウント時に `window`/`document` を参照するため、
サーバーサイドでレンダーすると `window is not defined` になる。ここで重要な制約：

> `ssr: false` オプションは **Client Component 内でのみ有効**。Server Component の中で
> `next/dynamic` に `ssr: false` を渡すとビルドエラーになる
> （`node_modules/next/dist/docs/01-app/02-guides/lazy-loading.md` で確認済み）。

そのため、地図を使う画面は次の2ファイル構成にする：

1. 実体となる Client Component（`'use client'` 付き、ここに `MapContainer` を書く）
2. それを `dynamic(..., { ssr: false })` でラップする**別の** Client Component
   （import する側も `'use client'` が必要）

```tsx
// frontend/src/components/map/SensorMapInner.tsx
'use client'

import { MapContainer, TileLayer } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

export default function SensorMapInner() {
  return (
    <MapContainer center={[35.681, 139.767]} zoom={13} style={{ height: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    </MapContainer>
  )
}
```

```tsx
// frontend/src/components/map/SensorMap.tsx
'use client'

import dynamic from 'next/dynamic'

const SensorMapInner = dynamic(() => import('./SensorMapInner'), {
  ssr: false,
  loading: () => <p>地図を読み込み中...</p>,
})

export default function SensorMap() {
  return <SensorMapInner />
}
```

`app/page.tsx`（Server Component のまま）は `<SensorMap />` を普通に import して使える——
`ssr: false` の制約は `dynamic()` を**呼び出す**ファイルにのみ適用され、呼び出し元の
`page.tsx` 自体を Client Component にする必要はない。

## Route Handlers（`app/api/.../route.ts`）

- `app/api/sensors/route.ts` のように `route.ts` を置くと、そのセグメントで
  `GET`/`POST`/`PUT`/`PATCH`/`DELETE`/`HEAD`/`OPTIONS` を個別 export できる。同じ
  セグメントに `page.tsx` と `route.ts` は共存できない。
- Web標準の `Request`/`Response` に加えて `NextRequest`/`NextResponse`（`next/server`）が
  使える。
- 動的セグメントの型付けはグローバルな `RouteContext` ヘルパーを使う：

```ts
// frontend/src/app/api/sensors/[sensorId]/route.ts
import type { NextRequest } from 'next/server'

export async function GET(
  _req: NextRequest,
  ctx: RouteContext<'/api/sensors/[sensorId]'>
) {
  const { sensorId } = await ctx.params
  const res = await fetch(`${process.env.BACKEND_URL}/sensors/${sensorId}`)
  return Response.json(await res.json())
}
```

- Route Handler はデフォルトでキャッシュされない（`GET` のみ `export const dynamic =
  'force-static'` で静的化可能）。FastAPI バックエンドの秘密情報（APIキー等）を
  フロントの `NEXT_PUBLIC_*` に漏らさず中継したい場合、Route Handler をプロキシとして
  使うのは有効なパターン——ただし CLAUDE.md の規約通り、Orcarouter の APIキー自体は
  FastAPI 側（`backend/.env`）に置き、Next.js 側では環境変数を保持しない。
- `RouteContext` の型はプロジェクトのビルド時（`next dev` / `next build` / `next typegen`）
  に生成される。型エラーが出る場合はまず `next dev` を一度動かす。

## チェックリスト

- [ ] `window`/`document`/`localStorage`/イベントハンドラ/`useState` を使うファイルに
      `'use client'` を付けたか
- [ ] Leaflet 等 window 依存ライブラリは「実体（'use client'）＋ dynamic ラッパー
      （'use client' + ssr:false）」の2段構成になっているか
- [ ] `next/dynamic` に `ssr: false` を渡している呼び出し元ファイルが Client Component か
      （Server Component から直接呼んでいないか）
- [ ] 新しい App Router の挙動を仮定する前に `node_modules/next/dist/docs/` を見たか
