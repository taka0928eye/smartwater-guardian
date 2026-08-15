# SmartWater Guardian Frontend

消火栓貼付型IoT音響センサーとハイブリッドAI解析により、水道管の微小漏水を早期検知する
「SmartWater Guardian」のダッシュボード Web アプリ（Next.js / TypeScript）。

- **現状のスコープ**: FE-2（深刻度共通ユーティリティ）/ FE-3（Leaflet センサー地図）/
  FE-4（音響スペクトル・波形チャート）/ FE-5（アラート一覧・詳細ドロワー）/
  FE-6（AI 自動起票 UI・WorkOrderModal）/ FE-7（KPIサマリの実データ連携・「試算値」注記）まで実装済み。
  さらに BE-7（防災モード）の被災エリア描画（`DisasterOverlay`）と、DEMO-2 で「シード投入」
  「シードクリア」「防災シミュレーション」の3操作ボタンをダッシュボード画面に配線済み。
- **バックエンド連携**: [`../backend`](../backend)（FastAPI）が別プロセスで起動している前提。
  未応答時はフォールバック表示に切り替わり、画面を白紙にしない。

---

## 1. 技術スタック

| 項目 | 内容 |
|---|---|
| フレームワーク | Next.js 16（App Router） |
| 言語 | TypeScript（strict / `any` 禁止） |
| スタイル | Tailwind CSS v4 |
| 地図 | Leaflet 1.9 / react-leaflet 5（`next/dynamic` で SSR 無効化） |
| グラフ | Recharts |
| アイコン | lucide-react |
| HTTP クライアント | axios（`lib/api.ts` で `ApiError` に変換） |
| テスト | Vitest + Testing Library（jsdom） |
| Lint | ESLint 9（flat config）+ `eslint-config-next` |

---

## 2. ディレクトリ構成

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # ルートレイアウト
│   │   ├── page.tsx                # ダッシュボードルート（Server Component / force-dynamic。モック KPI 撤去済み）
│   │   ├── api/docs/business-model/route.ts  # docs/business-model.md 配信（Route Handler。FE-7）
│   │   └── __tests__/
│   │       └── page.test.tsx
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── Header.tsx          # ヘッダー
│   │   │   ├── DashboardClient.tsx # ダッシュボード本体（Client Component。アラート/KPI/センサー/防災のポーリングと選択状態を束ねる）
│   │   │   ├── KpiSummary.tsx      # KPI サマリ 5 カード（表示専用・実データ。FE-7）
│   │   │   ├── BusinessModelDocLink.tsx # 「前提: docs/business-model.md」モーダル表示（FE-7）
│   │   │   └── __tests__/
│   │   ├── alert/
│   │   │   ├── AlertList.tsx           # アラート一覧（FE-5）
│   │   │   ├── AlertDetailDrawer.tsx   # アラート詳細ドロワー（FE-5。音響チャート + AI 自動起票ボタン）
│   │   │   └── __tests__/
│   │   ├── chart/
│   │   │   ├── SpectrumChart.tsx       # 周波数スペクトル（Recharts・漏水帯域ハイライト。FE-4）
│   │   │   └── WaveformChart.tsx       # 時間波形（ダウンサンプリング。FE-4）
│   │   ├── map/
│   │   │   ├── SensorMap.tsx       # Leaflet ラッパー（next/dynamic で SSR 無効化。FE-3）
│   │   │   ├── SensorMapInner.tsx  # 実描画（'use client'）
│   │   │   ├── DisasterOverlay.tsx # 防災被災エリア描画（GeoJSON クラスタ。BE-7）
│   │   │   └── __tests__/
│   │   ├── workorder/
│   │   │   └── WorkOrderModal.tsx      # AI 自動起票結果モーダル（FE-6。FR-6 原価フッター）
│   │   └── common/
│   │       ├── SeverityBadge.tsx   # 深刻度バッジ（severity.ts のメタ情報を利用）
│   │       └── __tests__/
│   ├── hooks/
│   │   ├── useAlertPolling.ts      # アラート一覧の 5 秒ポーリング + 即時 refresh（失敗時は最終状態を据え置き。DEMO-2で refresh 追加）
│   │   ├── useKpiPolling.ts        # KPI サマリの 5 秒ポーリング + 即時 refresh（失敗時は再スケルトンへ戻す。FE-7 / DEMO-2）
│   │   ├── useSensorPolling.ts     # センサー GeoJSON のポーリング + 即時 refresh（地図マーカー更新。DEMO-2で refresh 追加）
│   │   ├── useDisasterSummary.ts   # 防災サマリのポーリング + 即時 refresh（BE-7）
│   │   └── __tests__/
│   ├── lib/
│   │   ├── api.ts                  # axios クライアント（snake_case→camelCase 変換はここで1回だけ。seedDemoBatch/clearDemo 含む）
│   │   ├── severity.ts             # SeverityLevel 型 + 表示メタ情報の単一ソース（FE-7 で二重定義を解消）
│   │   ├── alertSort.ts            # アラート一覧の並び替え
│   │   └── __tests__/
│   ├── types/
│   │   ├── api.ts                  # API 契約型（SeverityLevel は severity.ts から re-export）
│   │   ├── sensor.ts               # GeoJSON 型（SensorFeatureCollection 等）
│   │   ├── disaster.ts             # 防災クラスタ型（DisasterCluster 等。BE-7）
│   │   └── demo.ts                 # シード投入/クリア型（DemoSeedBatchResponse / DemoClearResponse。DEMO-2）
│   └── test/
│       └── setup.ts                # jest-dom マッチャーのセットアップ
├── tests/e2e/                       # Playwright E2E（global-setup・8 spec・pages）
│   ├── global-setup.ts            # バックエンド起動確認 + POST /alerts/seed でシード投入
│   ├── alerts.spec.ts / dashboard.spec.ts / map.spec.ts / workorder.spec.ts / offline.spec.ts / disaster.spec.ts
│   └── pages/DashboardPage.ts     # Page Object Model
├── playwright.config.ts             # webServer（backend + frontend）・projects（main → disaster）
├── vitest.config.mts                # coverage.thresholds（80%）の単一ソース
├── eslint.config.mjs
├── next.config.ts
├── package.json
├── .env.local.example              # NEXT_PUBLIC_API_BASE_URL のサンプル
└── AGENTS.md / CLAUDE.md           # Next.js バージョン固有の注意点（node_modules/next/dist/docs/ 参照を指示）
```

---

## 3. セットアップ

### 3.1 依存パッケージ

```powershell
cd frontend
npm install
```

> ライブラリの新規追加は CLAUDE.md §1（Human-in-the-Loop）により**事前承認が必要**。

### 3.2 環境変数

`frontend/.env.local` を作成する（`.env.local.example` 参照）。未設定時は `http://localhost:8000` を既定値として使用する。

```
# 例: frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> `NEXT_PUBLIC_*` はクライアントバンドルに含まれるため、機密情報は置かないこと（CLAUDE.md §5.1）。

---

## 4. 実行方法

### 4.1 開発サーバー起動

バックエンド（[`../backend`](../backend)）を別ターミナルで先に起動しておく。

```powershell
cd frontend
npm run dev
```

[http://localhost:3000](http://localhost:3000) で表示を確認する。

### 4.2 本番ビルド

```powershell
cd frontend
npm run build
npm run start
```

---

## 5. テスト実行方法

Vitest + Testing Library（jsdom）。`npm run test` は `vitest run`（1回実行 + カバレッジ計測）。

```powershell
cd frontend
npm run test
```

- カバレッジ 4 指標（lines / functions / branches / statements）**各 80%** を `vitest.config.mts` の
  `coverage.thresholds` で強制する。ローカル実行と CI（GitHub Actions）で同一コマンド・同一ゲート。
- 環境は既定 `node`。DOM を要する component テストはファイル先頭の `// @vitest-environment jsdom` で切り替える。

### 5.1 Lint

```powershell
cd frontend
npm run lint
```

---

## 6. 画面構成・実装状況

| 機能 | 実装コンポーネント | 状態 |
|---|---|---|
| センサー地図（GeoJSON マーカー・深刻度色分け） | `components/map/SensorMap*` | 実装済み（FE-3） |
| アラート一覧・詳細ドロワー | `components/alert/AlertList` / `AlertDetailDrawer` | 実装済み（FE-5・5秒ポーリング） |
| 音響スペクトル・波形チャート | `components/chart/SpectrumChart` / `WaveformChart` | 実装済み（FE-4・Recharts） |
| KPI サマリ（監視センサー数 / Level 1〜3件数 / 推定削減コスト） | `components/dashboard/KpiSummary` | 実装済み（FE-7・実データ連携） |
| 補修部材選定・見積の自動起票 | `components/alert/AlertDetailDrawer` + `components/workorder/WorkOrderModal` | 実装済み（FE-6・`POST /alerts/{id}/work-order` 連携） |
| 防災モード（被災エリア描画・シミュレーション） | `components/map/DisasterOverlay` + `DashboardClient` のシミュレーションボタン | 実装済み（BE-7・DEMO-2で実センサー書換え方式に再設計） |
| デモ操作（シード投入・シードクリア） | `DashboardClient` のボタン2種 | 実装済み（DEMO-2・`seedDemoBatch` / `clearDemo`） |

### 自動起票（FE-6）と防災モード（BE-7）の補足

- **自動起票**: アラート詳細の「AI自動起票」ボタンで `POST /alerts/{id}/work-order`（BE-5）を呼び、
  補修部材・概算見積・作業指示書を `WorkOrderModal` に表示する。バックエンドが LLM 未設定・失敗時は
  `source: "fallback"` で表示し、可用性を担保する。FR-6 の原価（`cost_yen` / `latency_ms`）もフッターに表示。
- **防災モード**（DEMO-2 で再設計）: 「防災シミュレーション」ボタンが `POST
  /api/v1/disaster/simulate`（BE-7）を呼び、実在23消火栓のうち無作為6件を信号データごと Level 3 へ
  変化させる（架空センサーの新規追加はしない。監視センサー数は常に23）。`GET /api/v1/disaster/summary`
  のクラスタリング結果（被災エリア・想定断水世帯・優先閉栓バルブ）を `DisasterOverlay` で地図上に
  描画する。シミュレーション未実施時は何も描画しない。
- **デモ操作**（DEMO-2）: 「シード投入」ボタンが `POST /api/v1/demo/seed-batch` を呼び、23消火栓へ
  Lv0×11/Lv1×8/Lv2×3/Lv3×1 を一括投入する（`backend/dataset/` の音源が必要。AWS環境で未配置の場合は
  404で失敗するが画面は壊れない）。「シードクリア」ボタンが `DELETE /api/v1/demo/clear` を呼び、
  23件Lv0の初期状態に戻す。いずれも押下後、`useAlertPolling` / `useKpiPolling` / `useSensorPolling`
  （+ シードクリアは `useDisasterSummary`）の `refresh()` を呼び、ポーリング間隔を待たず即時反映する。

### KPI サマリの表示仕様（FE-7）

- カード5枚を降順で表示: 監視センサー数 → Level 3 破裂リスク → Level 2 警告 → Level 1 微小漏水（AI検知） →
  推定削減コスト。値はバックエンド `GET /api/v1/kpi/summary`（BE-8）の実データ。
- 推定削減コストのカードのみ、下部に2段の注記「試算値」+「前提: docs/business-model.md」を表示する
  （固定の数値モックは表示しない。根拠のない金額を断定的に見せないため）。
- 取得中・失敗直後はスケルトン（`data-testid="kpi-skeleton"`）を表示し、成功時のみカードへ切り替える。
  KPI section のランドマーク（`section` / `h2` / `aria-labelledby` / `aria-busy`）は
  `DashboardClient` が一元所有し、スケルトン中も維持する。

---

## 7. API 連携

- `lib/api.ts` が axios クライアントの単一窓口。バックエンドの `snake_case` レスポンスは
  ここで**1回だけ** `camelCase` に変換する（他レイヤーでは変換しない）。
- API エラーは `ApiError` に変換して throw する（axios 以外の例外は透過）。
- 取得失敗時は最終状態を据え置いて控えめにエラー表示するか（アラート一覧）、再スケルトンへ戻す
  （KPI サマリ）。いずれも画面を白紙にしない。ポーリングは `useEffect` のクリーンアップで
  `clearInterval` と `cancelled` フラグを徹底する。
- `app/page.tsx`（Server Component）はセンサー GeoJSON をリクエスト時に取得し、バックエンド未応答時は
  `hydrants.json` 由来のフォールバックデータで描画する（表示崩れ防止が目的。KPI 等の固定数値モックを
  実データの代わりに表示する用途には使わない）。

---

## 8. 関連ドキュメント・規約

- プロジェクト規約: [../CLAUDE.md](../CLAUDE.md)
- 要件定義: [../docs/PRD.md](../docs/PRD.md)
- 事業モデル・KPI算定根拠: [../docs/business-model.md](../docs/business-model.md)
- GitHub Issues 概要: [../docs/issues-summary.md](../docs/issues-summary.md)
- バックエンド API 仕様: [../backend/README.md](../backend/README.md)
- Next.js のバージョン固有の注意点は [AGENTS.md](./AGENTS.md)（`node_modules/next/dist/docs/` 参照）を参照。
