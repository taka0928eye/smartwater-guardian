# SmartWater Guardian - コード構造

## リポジトリ構成（モノレポ）

- `backend/` — FastAPI アプリ（Python）
- `frontend/` — Next.js アプリ（TypeScript）
- `docs/` — PRD・ビジネスモデル・UI ワイヤーフレーム・Issue 一覧
- `.github/workflows/ci.yml` — CI ゲート（backend / frontend テスト）
- `aidlc/` — AI-DLC ワークフローレコード（フレームワーク内部・対象外）

## バックエンド構成（backend/）

| パス | 分類 | 責務 |
|------|------|------|
| `main.py` | ブートストラップ | FastAPI アプリ生成・CORS・4 ルーター登録・`GET /` ヘルス |
| `app/routers/` | API 層 | telemetry / alerts / sensors / kpi の 4 ルーター |
| `app/services/` | サービス層 | ledger.py（配管台帳照合）・kpi.py（KPI 算定） |
| `app/schemas/` | 契約層 | telemetry / alert / pipe / kpi の Pydantic v2 スキーマ |
| `app/store.py` | データ層 | スレッドセーフなインメモリストア・シングルトン・マスタローダー |
| `app/data/` | マスタデータ | hydrants.json（10 件）・pipes.json（10 路線） |
| `app/dependencies.py` | DI | `HttpClientDep`（現状未使用・BE-5 用の先取り） |
| `scripts/` | 運用・検証 | simulate_sensor.py（疑似センサー CLI）・check_*.py |
| `tests/` | テスト | pytest 9 ファイル（test_kpi / test_alerts / test_store / test_ledger / ...） |

### ファイル分類と役割

- **ルーター**: 薄く保つ。リクエスト→サービスの呼び出しとレスポンス組み立てのみ
- **サービス**: ビジネスルールを集約（ledger は台帳検索、kpi は算定定数 + 集計）
- **スキーマ**: 外部契約の境界。`STRICT_INPUT_CONFIG`（strict + extra=forbid）を共通利用
- **ストア**: デモ用の一時保持。`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`

## フロントエンド構成（frontend/src/）

| パス | 分類 | 責務 |
|------|------|------|
| `app/` | App Router | page.tsx（Server Component・force-dynamic）・layout.tsx・globals.css |
| `components/dashboard/` | ダッシュボード | Header・KpiSummary・DashboardClient |
| `components/alert/` | アラート | AlertList・AlertDetailDrawer |
| `components/common/` | 共通 UI | SeverityBadge |
| `components/map/` | 地図 | SensorMap（dynamic ssr:false）・SensorMapInner（Leaflet） |
| `hooks/` | カスタムフック | useAlertPolling |
| `lib/` | ユーティリティ | api.ts・severity.ts・alertSort.ts |
| `types/` | 契約型 | api.ts（API レスポンス 1:1）・sensor.ts（GeoJSON） |
| `test/` | テスト設定 | setup.ts（vitest 設定） |

### ファイル分類と役割

- **Server Component**: page.tsx・layout.tsx・KpiSummary・Header（表示専用・副作用なし）
- **Client Component**: DashboardClient（状態管理）・SensorMap（Leaflet）・AlertList / AlertDetailDrawer / SeverityBadge
- **フック**: useAlertPolling（ポーリングのライフサイクル管理を責務分離）
- **ライブラリ**: api.ts（境界変換）・severity.ts（表示メタ単一ソース）・alertSort.ts（並び順/フィルタ純粋関数）

## 主要コードパターン

### 1. snake_case → camelCase 境界（lib/api.ts）
バックエンドは snake_case（Pydantic v2）、フロントは camelCase。`unwrap()` が再帰的にキー変換し、
`ApiError` へ例外変換する。型契約は `types/*.ts` の camelCase のみを公開する（変換は API 境界で「1 回だけ」）。

### 2. `@lru_cache` マスタローダー（store.py / ledger.py）
`get_hydrants()` / `get_pipes()` は `@lru_cache(maxsize=1)` で初回呼び出し時に JSON を読み込み以後キャッシュ
（「リクエスト毎の再読み込みをしない」要件）。欠損は store が RuntimeError、ledger が
FileNotFoundError / ValueError を送出する。テスト分離のためストアシングルトンは `reset_store()` で破棄可能。

### 3. ポーリングフック（useAlertPolling.ts）
`useEffect` + `setInterval`。クリーンアップで `clearInterval` し、`cancelled` フラグでアンマウント後の
setState を防ぐ。失敗時は alerts / lastUpdatedAt を据え置き、控えめなエラー表示に留める。

### 4. 深刻度表示メタの単一ソース（lib/severity.ts）
`SEVERITY_META` にレベル別の label / color / badgeClass / accentClass を集約。Tailwind v4 JIT は動的クラス
連結を検出できないため、クラス名は必ずリテラル文字列で保持する。`SeverityLevel`（0|1|2|3）もここで定義し、
`types/api.ts` から re-export する方針（feasibility 学習済み。本 KB 時点ではまだ二重定義）。

### 5. スレッドセーフなストア（store.py）
`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`。満杯時は最古を明示的に破棄し索引から削除する。
`sensor_latest` は破棄せず「最後に知った状態」を保持する（デモで同一センサー多数送信時にマーカーが消えない
ための非対称設計。破棄済み ID の詳細は 404 だが地図には残る）。

### 6. 深刻度降順・新着順のソート（lib/alertSort.ts）
`sortAlerts()` は深刻度降順 → 検知時刻降順。`filterLevelZero()` は Level 0 を除く（「正常も表示」トグル）。
副作用のない純粋関数として AlertList から抽出し、テスト容易性を確保している。

## 命名規則

- **Python**: ファイル/関数 snake_case、クラス PascalCase、定数 UPPER_SNAKE_CASE、内部関数 `_leading_underscore`
- **TypeScript**: ファイル camelCase、型/インターフェース PascalCase、コンポーネント PascalCase ファイル
- 定型は `docs/ui-wireframe.md` の UI-1 を参照し、コンポーネントは責務単位で `components/<domain>/` に配置
