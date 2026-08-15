# SmartWater Guardian - コンポーネントインベントリ

本インベントリの H2 見出しはスコープ検証（codekb-scope-diff）と正規表現で照合される。見出し文言を変更しないこと。

## FastAPI App (main.py)

- **責務**: FastAPI アプリの初期化。CORS ミドルウェア（環境変数 `ALLOWED_ORIGINS`）、**6 ルーター**の登録、ヘルスチェック `GET /`、`RuntimeError`→502 / 例外→500（構造化）ハンドラ
- **依存**: FastAPI / CORSMiddleware / app.routers.{alerts,demo,disaster,kpi,sensors,telemetry}
- **注記**: `load_dotenv()` で .env 読込（BE-5: Orcarouter 接続用）。CORS は INFRA-1 で環境変数化済み（`_get_allowed_origins()`）

## Router: telemetry.py

- **責務**: `POST /api/v1/telemetry` で音響テレメトリを受信・検証し、**SVM + DSP 解析（BE-3・services/audio.py）**してストアに登録する
- **主要関数**: `ingest_telemetry()`（解析は `analyze_audio` に委譲）
- **依存**: schemas/telemetry（TelemetryRequest / TelemetryResponse）、services/audio（analyze_audio / AudioValidationError）、store（get_store / StoredTelemetry）
- **関連**: BE-1（受信）＋ BE-3（SVM 解析）＋ BE-6（保存）。`_analyze_audio_mock` は廃止
- **注記**: 同期 `def`（FFT/SVM は CPU バウンド → スレッドプール実行）。`AudioValidationError` は 422

## Router: alerts.py

- **責務**: アラート一覧・詳細の参照、配管台帳照合による pipe_info 付与、**工事発注書の自動起票（BE-5）**、E2E 用シード投入
- **主要関数**: `_build_pipe_info()` / `_to_alert_summary()` / `list_alerts()` / `get_alert_detail()` / `create_work_order()` / `seed_alerts_for_e2e()`
- **依存**: schemas/alert（AlertSummary / AlertDetail / PipeInfo）、services/ledger（find_pipe_by_hydrant / get_pipe_age）、services/orcarouter（create_work_order）、store（get_store / StoredTelemetry）
- **関連**: BE-6 / BE-5。`create_work_order` は LLM（orcarouter）を呼び、source は llm / fallback
- **注記**: `_SEED_HYDRANT_LEVELS` で実在マスタ（HYD-001〜010）へ L3×3 / L2×3 / L1×3 / L0×1 を決定論的投入（E2E）

## Router: sensors.py

- **責務**: `GET /api/v1/sensors` で消火栓マスタ + 最新センサー状態を返す。`?format=geojson` で Leaflet 用 FeatureCollection
- **主要関数**: `_derive_status()` / `_to_sensor_info()` / `_to_sensor_feature()` / `list_sensors()`
- **依存**: schemas/alert（SensorInfo / HydrantMaster / GeoJSON 型一式）、schemas/telemetry（GeoLocation）、store（get_store / get_hydrants / StoredTelemetry）
- **関連**: FE-3 / FE-5。座標は [経度, 緯度] 順

## Router: kpi.py

- **責務**: `GET /api/v1/kpi/summary` で KPI サマリ（推定削減コスト）を返す（BE-8）
- **主要関数**: `get_kpi_summary()`
- **依存**: schemas/kpi（KpiSummary）、services/kpi（calculate_kpi_summary）
- **注記**: 組み立てはサービスで完結。空ストア・例外時も 200 を返す（500 にしない）。フロントは FE-7 で配線済み

## Router: disaster.py

- **責務**: 防災モード（BE-7 / DEMO-2 再設計）。`POST /api/v1/disaster/simulate` は実在20消火栓のうち無作為 `count` 件（既定6）を選び、合成Level3波形で信号データごと変化させる。`GET /api/v1/disaster/summary` はその選出分のみをクラスタリングし被災エリアを返す
- **主要関数**: `haversine_distance()` / `create_circle_polygon()` / `get_disaster_summary()` / `simulate_disaster()`
- **依存**: schemas/disaster（DisasterCluster / DisasterSummaryResponse / DisasterSimulateResponse / GeoJSONPolygon）、schemas/telemetry（GeoLocation）、services/audio（analyze_audio）、services/disaster_signal（generate_level3_signal / encode_signal_to_base64）、store（get_store / get_hydrants / register_disaster_sensors / get_disaster_sensor_ids / StoredTelemetry）
- **関連**: BE-7。`threshold_meters`（デフォルト 300m）でクラスタリング。想定断水世帯 = クラスタ内件数 × 120 + 50
- **注記**: 監視センサー数は常に20のまま増加しない（旧「東京駅周辺への架空センサー追加」方式を廃止）。選出 sensor_id は `register_disaster_sensors()` に累積記録され、`get_disaster_summary()` はこの記録分のみを対象とする（通常検知のLevel3は対象外）。旧 `TEL-DISASTER-*` プレフィックス判定・`/tmp/disaster_simulated_items.json` キャッシュは廃止

## Router: demo.py

- **責務**: デモ初期状態の投入・クリア（DEMO-1/DEMO-2）。`POST /api/v1/demo/seed` は実音声の `analyze_audio` を実行しつつ深刻度を `payload.level` に確定して1件投入。`POST /api/v1/demo/seed-batch` は20消火栓へLv0×8/Lv1×8/Lv2×3/Lv3×1を一括投入。`DELETE /api/v1/demo/clear` はクリア後に20件Lv0の初期状態へ戻す
- **主要関数**: `seed_demo()` / `seed_demo_batch()` / `clear_demo()`
- **依存**: schemas/demo（DemoSeedRequest / DemoSeedBatchResponse）、schemas/telemetry（TelemetryResponse）、services/audio（analyze_audio / AudioValidationError）、services/demo_seed（run_seed_batch / DemoSeedError）、store（get_store / initialize_sensors / clear_disaster_state / StoredTelemetry）
- **注記**: 実 SVM は合成波形（`generate_signal`）を意図レベルに分類できないため、デモシード専用の補正として深刻度を上書き（`model_copy(update={"severity_level": ...})`）。実録音のリプレイでも深刻度保証。`seed_demo_batch()` はデータセット未配置時に404を返す（500にしない）

## Store (store.py)

- **責務**: 解析済みテレメトリを保持するスレッドセーフなインメモリストア（BE-6）
- **主要要素**: `StoredTelemetry`（Pydantic・frozen / strict / extra=forbid）/ `InMemoryStore`（`deque(maxlen=500)` + `dict` 索引 + `threading.Lock`）/ `get_store()` / `reset_store()` / `get_hydrants()`（`@lru_cache`）
- **主要メソッド**: `add()` / `get()` / `get_all()` / `list_alerts()` / `latest_sensor_states()` / `clear()`
- **DEMO-2 追加関数**: `initialize_sensors(store)`（起動時・クリア時に20件Lv0を登録）/ `register_disaster_sensors()` / `get_disaster_sensor_ids()` / `clear_disaster_state()`（防災シミュレーション選出センサーの累積追跡。旧 `register_runtime_sensors`（架空センサー追加）を置き換え）
- **依存**: schemas/alert（HydrantMaster）、schemas/telemetry（AnalysisResult / GeoLocation）、data/hydrants.json
- **設計判断**: 満杯時は最古を索引と同期して破棄。`sensor_latest` は破棄しない（デモでマーカーを消さない非対称設計）。`get_all()` は防災クラスタリングで使用

## Service: demo_seed.py（DEMO-2）

- **責務**: デモ初期状態の一括投入（`POST /demo/seed-batch` / `scripts/seed_demo.py` の両方から呼ばれる単一の実体）
- **主要関数**: `build_seed_batch(hydrants, seed)`（20消火栓へ1レベルずつ重複なく割当て）/ `resolve_replay_files()` / `select_replay_file()` / `validate_mvp_contract()` / `load_audio_file()` / `run_seed_batch(store, audio_dir, seed)`
- **依存**: services/audio（analyze_audio）、store（get_hydrants / StoredTelemetry / clear_disaster_state）
- **注記**: `DemoSeedError` はマスタ・音源起因の失敗（ルーターで404に変換）。`run_seed_batch()` は以前の防災シミュレーション選出記録も `clear_disaster_state()` でクリアする（新しいベースラインのため）

## Service: disaster_signal.py（DEMO-2）

- **責務**: 防災シミュレーション用の合成Level3波形生成。外部音声ファイルに依存せず、AWS環境でもデータセット無しで常に動作する
- **主要関数**: `generate_level3_signal(seed)`（500-1500Hz帯域ノイズ + ブロードバンドノイズ、8000Hz/1.0秒/8000サンプル）/ `encode_signal_to_base64(signal)`
- **注記**: シード投入（実音響WAVのreplay）と意図的に手法を使い分けている

## Service: dataset_sync.py（DEMO-2・AWS向け）

- **責務**: `backend/dataset/`（Zenodo由来・ライセンス上git管理外）をAWS環境向けにプライベートS3バケットから同期
- **主要関数**: `sync_dataset_from_s3(s3_uri, target_dir)` / `_parse_s3_uri()`
- **依存**: boto3 / botocore（DEMO-2で追加）
- **注記**: `main.py` の `lifespan` が環境変数 `DEMO_DATASET_S3_URI` 設定時のみ起動時実行。失敗しても `DatasetSyncError` に変換され起動は継続する（`infra/README.md` 参照）

## Service: ledger.py

- **責務**: 疑似 GIS 配管台帳（pipes.json・10 路線）の照合サービス（BE-4）
- **主要関数**: `get_pipes()` / `find_pipe_by_hydrant()` / `find_nearest_pipe()` / `get_pipe_age()` / `_haversine_km()` / `_load_pipes()`
- **依存**: schemas/pipe（PipeRecord）、data/pipes.json、functools.lru_cache
- **注記**: `find_nearest_pipe` は各路線の LineString 頂点との Haversine 最小距離で判定。欠損は FileNotFoundError 伝播、破損は JSONDecodeError → ValueError

## Service: kpi.py

- **責務**: KPI「推定削減コスト」の算定（BE-8・docs/business-model.md §3）
- **主要関数**: `expected_cost_saved(severity_level)` / `calculate_kpi_summary()`
- **算定定数**: `C_BURST=1,200,000` / `C_REPAIR_LEVEL1=185,000` / `C_REPAIR_LEVEL2=320,000` / `P_LEVEL1=0.12` / `P_LEVEL2=0.35` / `C_RESPONSE_SAVED=150,000` / `KPI_ASSUMPTION_DOC`
- **依存**: schemas/kpi（KpiSummary）、schemas/telemetry（SeverityLevel）、store（get_store / get_hydrants）
- **注記**: `get_store()` はハンドラ実行時に呼ぶ（import 時捕捉はテスト隔離を壊す）。Level 0 は集計対象外。`round()` で整数化

## Service: audio.py

- **責務**: 音響テレメトリの SVM + DSP 解析（BE-3）。PCM16 デコード → 14 次元特徴量抽出 → SVM 漏水判定 → 深刻度分類
- **主要関数**: `analyze_audio()` / `classify_severity()` / `extract_features()` / `_load_model()` / `AudioValidationError`
- **依存**: scipy / numpy / scikit-learn / joblib、models/leak_svm_v1.joblib + metadata.json、schemas/telemetry（AnalysisResult / SpectrumPoint）
- **注記**: MVP 契約 8000Hz/1.0s（8000 PCM16 サンプル）。モデル読込は `@lru_cache` + SHA-256 検証（不一致は例外）。`classify_severity(is_leak, band_energy_ratio)`: ratio >= 0.60 → 3 / >= 0.30 → 2 / それ以外 → 1

## Service: orcarouter.py

- **責務**: 工事発注書の自動起票（BE-5）。LLM（Orcarouter API）で補修部材選定・概算見積・作業指示書を生成。API キー未設定・LLM 失敗時は規定ルールのフォールバック
- **主要関数**: `create_work_order()` / `build_fallback_work_order()` / `_post_with_retry()` / `_parse_llm_response()` / `_load_repair_parts()`（`@lru_cache`）
- **依存**: schemas/work_order（WorkOrder / RepairPart）、schemas/alert / schemas/pipe、services/prompts、services/llm_cost、app/dependencies（HttpClientDep）、data/repair_parts.json
- **設計判断**: `_work_order_cache`（LLM 成功時のみ・フォールバックは非キャッシュ）/ `_work_order_lock`（asyncio.Lock で直列化）/ 環境変数は呼び出し時点で読む（テスト容易性）

## Service: llm_cost.py

- **責務**: LLM 起票の API 原価算出（FR-6）。トークン単価（USD/1K）と為替（USD_JPY=155.0）から 1 起票あたり原価円を算出し、WorkOrder に原価フィールドを付与 + JSON 構造化ログ出力
- **主要関数**: `calc_cost_yen()` / `calculate_and_enrich_cost()`
- **算定定数**: `DEFAULT_UNIT_PRICE_INPUT_PER_1K=0.00015` / `DEFAULT_UNIT_PRICE_OUTPUT_PER_1K=0.00060` / `USD_JPY=155.0`
- **依存**: schemas/work_order（WorkOrder）、logger

## Service: prompts.py

- **責務**: Orcarouter LLM に送るプロンプトの構築（BE-5）。補修部材選定・見積・作業指示書の生成指示と JSON スキーマ（WorkOrder）を管理
- **依存**: schemas/alert / schemas/pipe / schemas/work_order

## Schemas (Pydantic v2)

- **責務**: 外部契約の境界。strict（`STRICT_INPUT_CONFIG` = `strict=True` + `extra="forbid"`）を共通利用
- **schemas/telemetry.py**: `SeverityLevel = Literal[0,1,2,3]` / `STRICT_INPUT_CONFIG` / `GeoLocation` / `TelemetryRequest`（Base64 検証・AwareDatetime）/ `SpectrumPoint` / `AnalysisResult` / `TelemetryResponse`
- **schemas/alert.py**: `AlertSummary` / `PipeInfo`（material は PipeMaterial）/ `AlertDetail` / `SensorInfo`（status は Literal 5 値）/ `HydrantMaster` / `GeoJSONPoint` / `SensorProperties` / `SensorFeature` / `SensorFeatureCollection`
- **schemas/pipe.py**: `PipeMaterial = Literal["ductile_iron","cast_iron","pvc","steel"]` / `PipeDiameterMm = Literal[75,100,150,200]` / `GeoJSONLineString`（頂点検証）/ `PipeRecord`
- **schemas/kpi.py**: `KpiSummary`（7 フィールド・`ge=0`）。`today_detections` は契約外（D-3）
- **schemas/work_order.py**: `RepairPart`（name / spec / quantity / unit_price_yen / subtotal_yen）/ `WorkOrder`（parts / total_estimate_yen / work_steps / required_workers / estimated_duration_hours / urgency / notification_text / source + FR-6 原価フィールド）
- **schemas/disaster.py**: `GeoJSONPolygon` / `DisasterCluster`（cluster_id / center_lat / center_lng / affected_sensor_ids / affected_pipe_ids / estimated_households / priority_valve_hydrant_id / geometry）/ `DisasterSummaryResponse` / `DisasterSimulateResponse`
- **schemas/demo.py**: `DemoSeedRequest(TelemetryRequest)` に `level: SeverityLevel` を追加
- **依存**: Pydantic v2 / datetime / typing。pipe.py は telemetry.py の STRICT_INPUT_CONFIG を再利用

## Frontend Page (page.tsx)

- **責務**: ダッシュボードルート（Server Component・`force-dynamic`）。GeoJSON 取得とフォールバック、DashboardClient の配置
- **主要要素**: `FALLBACK_SENSOR_FEATURES`（GeoJSON フォールバック・backend/app/data/hydrants.json 由来 10 件）/ `Home()`
- **依存**: components/dashboard（Header / DashboardClient）、lib/api（fetchSensorsGeoJson）、types/sensor
- **関連**: FE-2 / FE-3 / FE-5 / FE-7。**`MOCK_KPI_DATA` は撤去済み**（FE-7 で実データ配線）。`'use client'` を付けない（Server Component 維持）

## DashboardClient.tsx

- **責務**: ダッシュボード本体（Client Component）。アラート・KPI・センサー・防災のポーリングと選択状態を束ねる
- **主要要素**: `ALERT_POLL_INTERVAL_MS = 5000` / `useAlertPolling()` / `useKpiPolling()` / `useSensorPolling()` / `useDisasterSummary()` / `selectedAlertId` 状態 / `handleSelectMarker()` / 「シード投入」「シードクリア」「防災シミュレーション」ボタン（DEMO-2で3ボタン構成に）
- **依存**: hooks/{useAlertPolling,useKpiPolling,useSensorPolling,useDisasterSummary}、components/map/{SensorMap,DisasterOverlay}、components/alert/{AlertList,AlertDetailDrawer}、components/dashboard/KpiSummary、lib/api（simulateDisaster / seedDemoBatch / clearDemo）、types/sensor
- **関連**: FE-5 / FE-7 / BE-7 / DEMO-2。KPI ランドマーク（section / h2 / aria-labelledby / aria-busy / data-testid="kpi-skeleton"）を一元所有し、配下でスケルトンかカードグリッドを切替える（refined-mockups:c4）。「シード投入」「シードクリア」ボタンは押下後、各フックの `refresh()` を呼んでアラート・KPI・地図（クリア時は被災エリア含む）を即時反映する

## KpiSummary.tsx

- **責務**: KPI サマリ 5 枚の監視カード表示（FE-7・**表示専用**。値は実データ）
- **主要要素**: `KPI_CARD_COUNT = 5` / `KPI_GRID_CLASS` / `formatManYen()`（万円表記）/ `KpiCard` / `EstimateNote`（試算値 2 段注記 + BusinessModelDocLink）/ `KpiSummary()`
- **依存**: lib/severity（getSeverityMeta）、BusinessModelDocLink、prop `kpiData`（camelCase の `KpiSummary`）
- **関連**: FE-2 / FE-7。`KpiData` 型は `types/api.ts` の `KpiSummary`（7 フィールド）と契約整合済み。Level 1 カードは lime 黄緑（getSeverityMeta(1) 再利用）

## Header.tsx

- **責務**: ダッシュボード上部のヘッダー表示（`useSyncExternalStore` で時刻を更新）
- **依存**: React（useSyncExternalStore）
- **関連**: FE-2

## AlertList.tsx

- **責務**: アラート一覧の表示（深刻度降順・新着順、Level 0 フィルタ、「正常も表示」トグル）
- **依存**: components/common/SeverityBadge、lib/alertSort（sortAlerts / filterLevelZero）、types/api（AlertSummary）
- **関連**: FE-5

## AlertDetailDrawer.tsx

- **責務**: 選択中アラートの詳細ドロワー表示（解析結果・配管情報 pipe_info・音響チャート）。**AI 自動起票ボタン + WorkOrderModal 結合（FE-6）**
- **主要要素**: `fetchAlertDetail()` / `handleCreateWorkOrder()` → `createWorkOrder()` → `WorkOrderModal` / `SpectrumChart` / `WaveformChart`（FE-4）
- **依存**: lib/api（fetchAlertDetail, createWorkOrder）、types/api（AlertDetail / AlertSummary / WorkOrder）、components/chart/{SpectrumChart,WaveformChart}、components/workorder/WorkOrderModal、components/common/SeverityBadge
- **関連**: FE-5 / FE-6 / FE-4。選択が変わるたび `key` で再マウントし loading 状態をリセット。スペクトル・波形は `dominantFreqHz` から 128/512 点のデモデータを生成（FE-4 デモ表示）

## SeverityBadge.tsx

- **責務**: 深刻度レベルを表す共通バッジ
- **依存**: lib/severity（getSeverityMeta / getSeverityBadgeClass）、types/api（SeverityLevel）
- **関連**: FE-5 共通 UI

## SensorMap.tsx / SensorMapInner.tsx

- **責務**: Leaflet センサー地図。SensorMap は `dynamic(..., { ssr: false })` でクライアント専用化し、SensorMapInner が `MapContainer` / `GeoJSON` を描画
- **主要関数**: `calculateMapView` / `pointToLayer`（XSS エスケープ含む）
- **依存**: react-leaflet / leaflet / lib/severity（getSeverityColor）/ types/sensor（SensorFeatureCollection）
- **関連**: FE-3。座標は [lng, lat] → Leaflet LatLng の逆順変換をここで実施

## DisasterOverlay.tsx

- **責務**: 防災モードの被災エリアクラスタを地図に描画するコンポーネント（BE-7・表示専用）
- **主要関数**: `toClusterFeatureCollection()` / `buildDisasterLayerKey()` / `clusterStyle()` / `onEachCluster()`（popup は escapeHtml で XSS 対策）
- **依存**: react-leaflet（GeoJSON）/ leaflet / types/disaster（DisasterClusterFeatureCollection）
- **関連**: BE-7。Level 3 が 0 件のときは何も描画しない（受け入れ条件）。データ更新時は `key` で強制再マウント

## WorkOrderModal.tsx

- **責務**: AI 自動起票の結果（WorkOrder）をモーダル表示する（FE-6 / FR-6）
- **主要要素**: ESC キー / バックドロップクリックで閉じる / 緊急度・概算見積合計・想定作業時間 / FR-6 原価フッター（`source === "fallback"` なら「LLM未使用」、それ以外は `cost_yen` / `model` / `latency_ms`）
- **依存**: types/api（WorkOrder）
- **関連**: FE-6 / FR-6。`role="dialog"` / `aria-modal` でアクセシビリティ対応

## SpectrumChart.tsx / WaveformChart.tsx

- **責務**: Recharts による音響スペクトル（AreaChart・500〜1500Hz 漏水帯域ハイライト・卓越周波数基準線）と時間波形（ダウンサンプリング）の描画（FE-4）
- **依存**: recharts
- **関連**: FE-4。読み込み中はスケルトン（`animate-pulse`）。`dominantFreqHz` で基準線を描画

## useAlertPolling.ts

- **責務**: アラートのポーリングを担うカスタムフック（DashboardClient から抽出）
- **主要要素**: `useAlertPolling(intervalMs)` → `{ alerts, error, lastUpdatedAt, refresh }`
- **依存**: lib/api（fetchAlerts）、types/api（AlertSummary）
- **注記**: `useEffect` クリーンアップで `clearInterval` + `cancelled` フラグ。失敗時は最終状態を据え置く。`refresh()`（DEMO-2）はデモ操作ボタン押下直後の即時反映用

## useKpiPolling.ts

- **責務**: KPI サマリのポーリング（FE-7）。**失敗時は古い値を最新として見せないため null に破棄して再スケルトン**
- **主要要素**: `useKpiPolling(intervalMs)` → `{ kpiData, isLoading, refresh }`。`requestSeqRef` でアウトオブオーダー防止（ポーリングと `refresh()` で共有）
- **依存**: lib/api（fetchKpiSummary）、types/api（KpiSummary）
- **注記**: useAlertPolling（最終状態据え置き）とは失敗時挙動が異なるため共通フックに統合しない（application-design:c5）。`refresh()`（DEMO-2）はデモ操作ボタン押下直後の即時反映用

## useSensorPolling.ts

- **責務**: センサー一覧（GeoJSON）のポーリング（地図マーカー更新用）
- **主要要素**: `useSensorPolling(initialData, intervalMs)` → `{ sensorFeatures, error, refresh }`
- **依存**: lib/api（fetchSensorsGeoJson）、types/sensor
- **注記**: 失敗時は最終状態を据え置く（地図・画面を壊さない）。`refresh()`（DEMO-2）はデモ操作ボタン押下直後の即時反映用

## useDisasterSummary.ts

- **責務**: 防災サマリのポーリング（BE-7）。`refresh()` は「防災シミュレーション」ボタン押下直後の即時再取得用
- **主要要素**: `useDisasterSummary(intervalMs)` → `{ disasterSummary, error, refresh }`
- **依存**: lib/api（fetchDisasterSummary）、types/disaster（DisasterSummary）
- **注記**: 失敗時は最終状態を据え置き、控えめなエラー表示（useAlertPolling と同じ方式）

## lib/api.ts

- **責務**: axios クライアントと API 関数群。snake_case→camelCase 変換と `ApiError` 変換を境界で 1 回実施
- **主要要素**: `apiClient`（baseURL / timeout 10s）/ `ApiError` / `toCamelCase` / `unwrap` / `fetchSensors` / `fetchSensorsGeoJson` / `fetchAlerts` / `fetchAlertDetail` / `createWorkOrder` / `fetchKpiSummary` / `fetchDisasterSummary` / `simulateDisaster`
- **依存**: axios、types/api、types/sensor、types/disaster
- **関連**: FE-1 / FE-7 / BE-7。**`fetchKpiSummary` / `fetchDisasterSummary` / `simulateDisaster` / `createWorkOrder` は実装済み**

## lib/severity.ts

- **責務**: 漏水深刻度の表示メタ単一ソース（UI-1 深刻度カラー定義）
- **主要要素**: `SeverityLevel = 0|1|2|3`（**単一ソース**）/ `SeverityMeta` / `SEVERITY_META` / `getSeverityMeta` / `getSeverityLabel` / `getSeverityColor` / `getSeverityBadgeClass` / `getSeverityAccentClass`
- **依存**: なし（純粋モジュール）
- **関連**: FE-2 / FE-3 / FE-5 / FE-7。`types/api.ts` が re-export（二重定義は FE-7 で解消済み）。Tailwind v4 JIT のためクラス名はリテラル文字列で保持

## lib/alertSort.ts

- **責務**: アラート一覧の並び順・フィルタを担う純粋関数（AlertList から抽出）
- **主要関数**: `sortAlerts()`（深刻度降順 → 検知時刻降順）/ `filterLevelZero()`（Level 0 除外。includeLevelZero で全件）
- **依存**: types/api（AlertSummary）
- **関連**: FE-5。受け取った配列を変更しない（不変）

## BusinessModelDocLink.tsx

- **責務**: KPI コストカードの「前提: docs/business-model.md」リンクボタン（FE-7）。クリックで `GET /api/docs/business-model` から本文を取得しモーダル表示
- **依存**: `app/api/docs/business-model/route.ts`（fetch）、react-dom（createPortal）
- **注記**: 取得失敗時はモーダル内に控えめなエラー表示（画面を壊さない）。マークダウンはデモスコープのため raw テキスト表示（描画ライブラリ追加は Human-in-the-Loop の承認が必要）

## app/api/docs/business-model/route.ts

- **責務**: `docs/business-model.md` の内容を配信する Next.js Route Handler（FE-7）。取得成功 `{ content }`・失敗 `{ content: null, error }` を 404 で返す
- **依存**: node:fs/promises・node:path（`process.cwd()/../docs/business-model.md` を解決）
- **関連**: FE-7。500 にしない（バックエンドのエラーハンドリング方針に合わせる）

---

### コンポーネント間の主な依存グラフ

```
page.tsx
  -> Header / DashboardClient / lib/api(fetchSensorsGeoJson)
DashboardClient
  -> useKpiPolling / useAlertPolling / useSensorPolling / useDisasterSummary
  -> KpiSummary / SensorMap / DisasterOverlay / AlertList / AlertDetailDrawer
  -> lib/api(seedDemoBatch, clearDemo)  # DEMO-2: シード投入・シードクリアボタン
useKpiPolling -> lib/api(fetchKpiSummary)  # refresh() あり（DEMO-2）
useAlertPolling -> lib/api(fetchAlerts)  # refresh() あり（DEMO-2）
useSensorPolling -> lib/api(fetchSensorsGeoJson)  # refresh() あり（DEMO-2）
useDisasterSummary -> lib/api(fetchDisasterSummary)  # refresh() あり
AlertDetailDrawer -> lib/api(fetchAlertDetail, createWorkOrder) / SpectrumChart / WaveformChart / WorkOrderModal
lib/api -> types/api / types/sensor / types/disaster / types/demo（DEMO-2）
main.py -> routers(telemetry, alerts, sensors, kpi, disaster, demo)
main.py -> services/dataset_sync（lifespan: DEMO_DATASET_S3_URI 設定時のみ・DEMO-2）
main.py -> store(initialize_sensors)（lifespan: 起動時に20件Lv0を構築・DEMO-2）
routers/telemetry -> services/audio / store / schemas/telemetry
routers/demo -> services/audio / services/demo_seed / store / schemas/demo（DEMO-2）
routers/alerts -> store / services/ledger / services/orcarouter / schemas/alert
routers/sensors -> store / schemas/alert
routers/kpi -> services/kpi / schemas/kpi
routers/disaster -> services/audio / services/disaster_signal / store / schemas/disaster（DEMO-2）
services/orcarouter -> services/prompts / services/llm_cost / schemas/work_order / app/dependencies / data/repair_parts.json
services/audio -> schemas/telemetry / models/leak_svm_v1.joblib
services/demo_seed -> services/audio / store(get_hydrants, clear_disaster_state) / backend/dataset/（DEMO-2）
services/disaster_signal -> services/audio（DEMO-2）
services/dataset_sync -> boto3 / botocore（DEMO-2）
services/kpi -> store(get_store, get_hydrants) / schemas/kpi
services/ledger -> schemas/pipe / data/pipes.json
store -> data/hydrants.json / schemas/alert / schemas/telemetry
```

### オーナーシップ・マトリクス（Issue 対応）

| コンポーネント | 関連 Issue | 状態 |
|----------------|------------|------|
| Router: telemetry.py | BE-1 / BE-3 / BE-6 | 実装済み（SVM 解析） |
| Router: alerts.py | BE-5 / BE-6 | 実装済み（work-order / seed） |
| Router: sensors.py | BE-6 | 実装済み |
| Router: kpi.py | BE-8 | 実装済み |
| Router: disaster.py | BE-7 / DEMO-2 | 実装済み（実在20消火栓を書き換える方式に再設計） |
| Router: demo.py | DEMO-1 / DEMO-2 | 実装済み（seed-batch / clear の20件Lv0契約を追加） |
| Store (store.py) | BE-6 / DEMO-2 | 実装済み |
| Service: ledger.py | BE-4 | 実装済み |
| Service: kpi.py | BE-8 | 実装済み |
| Service: audio.py | BE-3 | 実装済み（SVM + DSP） |
| Service: orcarouter.py | BE-5 / FR-6 | 実装済み（LLM / フォールバック / キャッシュ） |
| Service: llm_cost.py | FR-6 | 実装済み |
| Service: prompts.py | BE-5 | 実装済み |
| Service: demo_seed.py | DEMO-2 | 実装済み |
| Service: disaster_signal.py | DEMO-2 | 実装済み |
| Service: dataset_sync.py | DEMO-2 | 実装済み（AWS向け） |
| Frontend Page (page.tsx) | FE-2/3/5/7 | 実装済み（モック KPI 撤去済み） |
| DashboardClient.tsx | FE-5 / FE-7 / BE-7 / DEMO-2 | 実装済み（KPI・防災ポーリング配線 + シード投入/クリアボタン） |
| KpiSummary.tsx | FE-2 / FE-7 | 実装済み（契約整合・表示専用） |
| AlertDetailDrawer.tsx | FE-4 / FE-5 / FE-6 | 実装済み（チャート + 自動起票ボタン） |
| WorkOrderModal.tsx | FE-6 / FR-6 | 実装済み |
| DisasterOverlay.tsx | BE-7 | 実装済み |
| lib/api.ts | FE-1 / FE-7 / BE-7 / DEMO-2 | 実装済み（fetchKpiSummary / seedDemoBatch / clearDemo 等） |
| lib/severity.ts | FE-2/3/5/7 | 実装済み（単一ソース） |
