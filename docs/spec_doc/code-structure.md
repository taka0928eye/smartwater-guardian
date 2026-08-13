# SmartWater Guardian - コード構造

## リポジトリ構成（モノレポ）

- `backend/` — FastAPI アプリ（Python）
- `frontend/` — Next.js アプリ（TypeScript）
- `docs/` — PRD・ビジネスモデル・UI ワイヤーフレーム・LLM 原価・Issue 一覧
- `infra/` — AWS 本番環境（CloudFormation・INFRA-1）
- `.github/workflows/` — CI（ci.yml）・デプロイ（deploy.yml）
- `aidlc/` — AI-DLC ワークフローレコード（フレームワーク内部・対象外）

## バックエンド構成（backend/）

| パス | 分類 | 責務 |
|------|------|------|
| `main.py` | ブートストラップ | FastAPI アプリ生成・CORS（`ALLOWED_ORIGINS`）・**6 ルーター**登録・`RuntimeError`→502 / 例外→500 ハンドラ・`GET /` ヘルス |
| `app/routers/` | API 層 | telemetry / alerts / sensors / kpi / disaster / demo の 6 ルーター |
| `app/services/` | サービス層 | audio.py（SVM 音響解析・BE-3）・orcarouter.py（LLM 起票・BE-5）・llm_cost.py（原価・FR-6）・ledger.py（台帳照合・BE-4）・kpi.py（KPI 算定・BE-8）・prompts.py（LLM プロンプト管理） |
| `app/schemas/` | 契約層 | telemetry / alert / pipe / kpi / work_order / disaster / demo の Pydantic v2 スキーマ |
| `app/store.py` | データ層 | スレッドセーフなインメモリストア・シングルトン・マスタローダー |
| `app/data/` | マスタデータ | hydrants.json（10 件）・pipes.json（10 路線）・repair_parts.json（補修部材マスタ） |
| `app/models/` | 学習済みモデル | leak_svm_v1.joblib + metadata.json（BE-3 SVM・SHA-256 検証付き） |
| `app/dependencies.py` | DI | `HttpClientDep`（httpx クライアント注入。orcarouter で実使用） |
| `scripts/` | 運用・検証 | simulate_sensor.py（疑似センサー CLI）・check_telemetry.py / check_kpi.py / check_disaster.py |
| `tests/` | テスト | pytest（test_audio / test_work_order / test_telemetry / test_alerts / test_kpi / test_store / test_ledger / ...） |
| `requirements.txt` / `pyproject.toml` | 依存・静的検査 | == ピン固定 / ruff + mypy 設定 |

### ファイル分類と役割

- **ルーター**: 薄く保つ。リクエスト→サービスの呼び出しとレスポンス組み立てのみ
- **サービス**: ビジネスルールを集約（audio は音響判定、orcarouter は LLM 起票、ledger は台帳検索、kpi は算定）
- **スキーマ**: 外部契約の境界。`STRICT_INPUT_CONFIG`（strict + extra=forbid）を共通利用
- **ストア**: デモ用の一時保持。`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`

## フロントエンド構成（frontend/src/）

| パス | 分類 | 責務 |
|------|------|------|
| `app/` | App Router | page.tsx（Server Component・force-dynamic）・layout.tsx・globals.css・**api/docs/business-model/route.ts**（Route Handler） |
| `components/dashboard/` | ダッシュボード | Header・KpiSummary・BusinessModelDocLink・DashboardClient |
| `components/alert/` | アラート | AlertList・AlertDetailDrawer |
| `components/workorder/` | 作業指示書 | WorkOrderModal（FR-6 原価表示） |
| `components/chart/` | チャート | SpectrumChart・WaveformChart（Recharts・FE-4） |
| `components/common/` | 共通 UI | SeverityBadge |
| `components/map/` | 地図 | SensorMap（dynamic ssr:false）・SensorMapInner（Leaflet）・DisasterOverlay（防災クラスタ・BE-7） |
| `hooks/` | カスタムフック | useAlertPolling・useKpiPolling・useSensorPolling・useDisasterSummary |
| `lib/` | ユーティリティ | api.ts・severity.ts・alertSort.ts |
| `types/` | 契約型 | api.ts（API レスポンス 1:1）・sensor.ts（GeoJSON）・disaster.ts（防災） |
| `test/` | テスト設定 | setup.ts（vitest 設定） |
| `tests/e2e/` | E2E テスト | Playwright（global-setup・spec・fixtures・pages/DashboardPage） |

### ファイル分類と役割

- **Server Component**: page.tsx・layout.tsx・Header（表示専用・副作用なし）。KpiSummary は Client Component に属する配下（DashboardClient が取得・描画）
- **Client Component**: DashboardClient（状態管理・ポーリング統合）・SensorMap / DisasterOverlay（Leaflet）・AlertList / AlertDetailDrawer / WorkOrderModal / SpectrumChart / WaveformChart / SeverityBadge / BusinessModelDocLink
- **フック**: ポーリングのライフサイクル管理を責務分離（アラートは据え置き・KPI は再スケルトンと挙動が異なるため分離）
- **ライブラリ**: api.ts（境界変換）・severity.ts（表示メタ単一ソース）・alertSort.ts（並び順/フィルタ純粋関数）

## 主要コードパターン

### 1. snake_case → camelCase 境界（lib/api.ts）
バックエンドは snake_case（Pydantic v2）、フロントは camelCase。`unwrap()` が再帰的にキー変換し、
`ApiError` へ例外変換する。型契約は `types/*.ts` の camelCase のみを公開する（変換は API 境界で「1 回だけ」）。
`fetchKpiSummary` / `fetchDisasterSummary` / `simulateDisaster` / `createWorkOrder` もここで実装済み。

### 2. `@lru_cache` マスタローダー（store.py / ledger.py / orcarouter.py）
`get_hydrants()` / `get_pipes()` / `_load_repair_parts()` は `@lru_cache(maxsize=1)` で初回呼び出し時に
JSON を読み込み以後キャッシュ（「リクエスト毎の再読み込みをしない」要件）。欠損は store が
RuntimeError、ledger が FileNotFoundError / ValueError を送出する。テスト分離のためストアシングルトンは
`reset_store()` で破棄可能。

### 3. ポーリングフック（useAlertPolling / useKpiPolling / useSensorPolling / useDisasterSummary）
`useEffect` + `setInterval`。クリーンアップで `clearInterval` し、`cancelled` フラグでアンマウント後の
setState を防ぐ。**失敗時挙動が対象ごとに異なる**:
- アラート / センサー / 防災: 最終状態を据え置き、控えめなエラー表示
- KPI（FE-7）: 古い値を最新として見せないため null に破棄して**再スケルトン**（`requestSeq` で
  アウトオブオーダー防止）

### 4. 深刻度表示メタの単一ソース（lib/severity.ts）
`SEVERITY_META` にレベル別の label / color / badgeClass / accentClass を集約。Tailwind v4 JIT は動的クラス
連結を検出できないため、クラス名は必ずリテラル文字列で保持する。`SeverityLevel`（0|1|2|3）もここで定義し、
`types/api.ts` から re-export する（FE-7 で解消済み）。

### 5. スレッドセーフなストア（store.py）
`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`。満杯時は最古を明示的に破棄し索引から削除する。
`sensor_latest` は破棄せず「最後に知った状態」を保持する（デモで同一センサー多数送信時にマーカーが消えない
ための非対称設計。破棄済み ID の詳細は 404 だが地図には残る）。

### 6. 深刻度降順・新着順のソート（lib/alertSort.ts）
`sortAlerts()` は深刻度降順 → 検知時刻降順。`filterLevelZero()` は Level 0 を除く（「正常も表示」トグル）。
副作用のない純粋関数として AlertList から抽出し、テスト容易性を確保している。

### 7. LLM 起票の並行安全とフォールバック（services/orcarouter.py）
`create_work_order()` は `_work_order_lock`（asyncio.Lock）で生成処理全体を直列化し、成功時のみ
`_work_order_cache` にキャッシュ（フォールバック WorkOrder はキャッシュしない）。API キー未設定・
LLM 失敗時は `build_fallback_work_order()` で規定ルールによる算出（source == "fallback"）を返す。
設定値（`ORCAROUTER_API_KEY` 等）は呼び出し時点で環境変数から読む（テスト容易性）。

### 8. 原価算出の注記（FR-6・services/llm_cost.py）
`calc_cost_yen()` は input/output トークン単価（USD/1K）と為替（USD_JPY）から 1 起票あたりの API 原価を
算出し、`calculate_and_enrich_cost()` が WorkOrder に `prompt_tokens` / `completion_tokens` / `cost_yen` /
`model` / `latency_ms` / `is_estimated` を付与 + JSON 構造化ログを出す。WorkOrderModal がフッターに表示。

### 9. 防災モード（BE-7・routers/disaster.py）
Level 3 センサーを距離閾値（`threshold_meters` デフォルト 300m）でクラスタリングし、被災エリア Polygon を
GeoJSON で返す。`POST /disaster/simulate` は疑似被災レコード（`count` 1〜20）を生成して再集計。
`CACHE_FILE=/tmp/disaster_simulated_items.json` にシミュレーション投入分を永続化（テスト分離に配慮）。

### 10. デモシード（DEMO-1・routers/demo.py + routers/alerts.py）
- `POST /api/v1/alerts/seed`: E2E 用シード。実在マスタ（HYD-001〜010）へ L3×3 / L2×3 / L1×3 / L0×1 を決定論的投入
- `POST /api/v1/demo/seed`: デモ用。`DemoSeedRequest` の `level` 上書きで実音声の `analyze_audio` を実行後に
  `model_copy(update={"severity_level": payload.level})`

## 命名規則

- **Python**: ファイル/関数 snake_case、クラス PascalCase、定数 UPPER_SNAKE_CASE、内部関数 `_leading_underscore`
- **TypeScript**: ファイル camelCase、型/インターフェース PascalCase、コンポーネント PascalCase ファイル
- 定型は `docs/ui-wireframe.md` の UI-1 を参照し、コンポーネントは責務単位で `components/<domain>/` に配置
