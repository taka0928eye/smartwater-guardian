# GitHub Issues 概要一覧

> ハッカソン期間（8/10〜8/15）に実施する全オープンIssue（17件）の概要をまとめたドキュメント。
> 優先度（P0 / P1 / P2）・依存関係・実装方針の要点を俯瞰するために使用する。

- 集計日: 2026-08-10
- 対象: オープンIssue 全17件

---

## 1. 一覧表

| # | タスクID | タイトル | エリア | 優先度 | 依存タスク | 想定日 |
|---|---|---|---|---|---|---|
| 1 | UI-1 | 画面設計・ワイヤーフレーム確定 | design | **P0** | なし | 8/10 |
| 2 | BE-1 | センサテレメトリ受取API (`POST /api/v1/telemetry`) 型定義とダミー実装 | backend | **P0** | なし | 8/10 |
| 3 | BE-2 | 疑似センサーデータ生成スクリプトと消火栓マスタ作成 | backend | **P0** | BE-1 | 8/10 |
| 4 | BE-3 | `services/audio.py` によるFFT解析・漏水深刻度(Level 1〜3)判定 | backend | **P0** | BE-1, BE-2 | 8/11 |
| 5 | FE-1 | API型定義(TypeScript)とaxiosクライアント実装 | frontend | **P0** | BE-1 | 8/11 |
| 6 | FE-2 | ダッシュボードレイアウトとKPIサマリ実装 | frontend | **P0** | UI-1 | 8/11 |
| 7 | BE-6 | アラート参照API群とインメモリストア実装 | backend | **P0** | BE-3 | 8/12 |
| 8 | FE-3 | Leaflet GISマップ（漏水リスクノードのリアルタイム描画） | frontend | **P0** | FE-1, FE-2, BE-6 | 8/12 |
| 9 | FE-5 | アラート一覧と詳細ドロワー実装 | frontend | **P0** | FE-1, FE-2, FE-3, BE-6 | 8/12 |
| 10 | BE-4 | 疑似GIS配管台帳と位置照合ロジック実装 | backend | P1 | BE-2, BE-6 | 8/13 |
| 11 | OR-1 | httpxの導入とHTTPクライアント依存性注入 | llm | P1 | なし（ユーザー承認が前提） | 8/13 |
| 12 | OR-2 | Orcarouter自動起票プロンプトの設計 | llm | P1 | BE-3, BE-4 | 8/13 |
| 13 | BE-5 | `services/orcarouter.py` によるLLM自動起票の実装 | backend / llm | P1 | OR-1, OR-2, BE-4, BE-6 | 8/13 |
| 14 | OR-3 | LLM失敗時フォールバック（規定ルールによる部材・見積算出） | llm | P1 | BE-5, BE-4 | 8/13 |
| 15 | FE-4 | Rechartsによる音響波形・周波数スペクトル表示 | frontend | P1 | FE-1, FE-5, BE-3, BE-6 | 8/14 |
| 16 | FE-6 | AI自動起票モーダル実装 | frontend | P1 | FE-5, BE-5, OR-3 | 8/14 |
| 17 | BE-7 | 防災モード（震災時 一括被害エリアマッピング） | backend | P2（余力枠） | BE-2, BE-4, BE-6 | 8/15 |

---

## 2. 優先度別の内訳

### P0（デモの中核。まずここを固める） — 9件

バックエンドの「受信 → 解析 → 保存 → 参照」基盤（BE-1〜BE-6系）と、
フロントの「ダッシュボード → 地図 → アラート詳細」の一気通貫フロー（FE-1〜FE-5系）、
およびその設計前提となるワイヤーフレーム（UI-1）。

### P1（LLM自動起票の本命機能） — 7件

配管台帳照合（BE-4）→ LLM呼び出し基盤（OR-1/OR-2）→ 自動起票（BE-5）→
障害時フォールバック（OR-3）と、その可視化（FE-4のチャート / FE-6の起票モーダル）。

### P2（余力枠） — 1件

防災モード（BE-7）。**P0/P1がすべて完了した場合のみ着手**する。

---

## 3. 依存関係のクリティカルパス

```
UI-1(#1) ────────────────→ FE-2(#6) ──→ FE-3(#8) ─┐
BE-1(#2) ──→ BE-2(#3) ──→ BE-3(#4) ──→ BE-6(#7) ──┤→ FE-5(#9) ──→ FE-6(#16)
   │          │              │                      │
   └─→ FE-1(#5) ────────────┘                      │
                          BE-4(#10) ──→ OR-2(#12) ──┴→ BE-5(#13) ──→ OR-3(#14)
                          (BE-2, BE-6から)   OR-1(#11) ──→ BE-5(#13)     │
                                                                         └─→ FE-6(#16)
BE-7(#17) ←─ BE-2, BE-4, BE-6
```

**要点:**

- 最長のクリティカルパスは `BE-1 → BE-2 → BE-3 → BE-6 → FE-5 → FE-6`。デモの「検知 → 表示 → 自動起票」を一本化する。
- LLM系（OR-1/OR-2 → BE-5 → OR-3）は P0 基盤の上に積む。**OR-1（httpx導入）だけは P1 ながら依存が無く、ユーザー承認を得られ次第いつでも着手可能**。
- FE-4 / FE-6 は FE-5（ドロワー）と BE-6（詳細API）が揃ってから着手できる。FE-5 には事前にチャート差し込みスロットを用意して並行作業を可能にする設計。

---

## 4. 各Issueの詳細

### P0

#### [#1] UI-1: 画面設計・ワイヤーフレーム確定 — 8/10

- **目的**: FE-2〜FE-6の手戻りを防ぐため、単一ダッシュボードの画面構成・色定義・デモシナリオを文書で先に確定する。コードは書かない。
- **成果物**: `docs/ui-wireframe.md`（新規）
- **確定事項**:
  - レイアウト: ヘッダ（製品名/現在時刻/監視ステータス）+ KPI 5枚 + 左地図/右アラート一覧 + 詳細ドロワー（右スライドイン）+ 起票モーダル（中央）
  - 深刻度カラー: Level 1 `#22c55e` / Level 2 `#f59e0b` / Level 3 `#ef4444` / 正常 `#64748b`
  - KPI 5項目: 監視センサー数・Level 3件数・Level 2件数・本日の検知数・推定削減コスト
  - デモシナリオ（3分）: 正常時 → Level 1検知・地図点滅 → 波形/スペクトルで500〜1500Hzのピーク提示 → AI自動起票で部材・見積・作業指示書を生成

#### [#2] BE-1: センサテレメトリ受取APIの型定義とダミーエンドポイント — 8/10

- **目的**: 疑似IoT音響センサーからのテレメトリ受取エンドポイントを新設し、パッケージ構成とAPI契約を確定。解析はBE-3に委譲し、本Issueでは `analysis` を `null` で返すダミー。
- **変更**: `app/schemas/telemetry.py`（Pydantic v2モデル4種）、`app/routers/telemetry.py`（`POST /api/v1/telemetry`）、`backend/main.py`（router追加2行）、`scripts/check_telemetry.py`
- **方針の要点**:
  - `ConfigDict(strict=True, extra="forbid")`、`@field_validator` で `audio_base64` のBase64妥当性検証
  - ハンドラは同期 `def`（CPUバウンドのFFTをスレッドプール実行させるため）。`# TODO(BE-3)` を明示
  - Pydantic v1記法（`class Config` / `@validator` / `.dict()`）は不使用

#### [#3] BE-2: 疑似センサーデータ生成スクリプトと消火栓マスタ — 8/10

- **目的**: 実デバイスに頼らず、Level 1〜3・正常時の音響データを合成生成してテレメトリAPIへ送信するCLIを作成。BE-3の入力源かつデモ演出装置。
- **変更**: `app/data/hydrants.json`（消火栓10件）、`scripts/simulate_sensor.py`
- **方針の要点**:
  - `generate_signal(level, sample_rate_hz, duration_sec) -> np.ndarray` を送信処理から分離しBE-3から再利用可能に
  - level 0（環境ノイズ）/ 1（800〜1200Hz狭帯域トーン）/ 2（500〜1500Hz増幅）/ 3（広帯域大振幅）
  - `np.random.default_rng(seed)` による再現可能な乱数、float64でクリッピング後にint16へ
  - CLI: `--level {0,1,2,3}` / `--count` / `--interval` / `--hydrant` / `--url` / `--seed`

#### [#4] BE-3: `services/audio.py` によるFFT解析・深刻度判定 — 8/11

- **目的**: 音響データのノイズカットと周波数解析から漏水確信度（0〜100%）と深刻度（Level 1〜3）を判定。**ロジックは `app/services/audio.py` にのみ集約**（CLAUDE.md §5.3）。
- **変更**: `app/services/audio.py`、`AnalysisResult` に `spectrum` 追加、`routers/telemetry.py` のTODO解消、`scripts/check_audio.py`
- **方針の要点**:
  - 処理流れ: `decode_pcm16_mono` → ハイパス(100Hz以下除去) → `compute_psd`(Welch法) → `band_energy_ratio` → `classify_severity` / `leak_confidence`
  - **既知の地雷**: `np.trapz` は NumPy 2.5.2 で削除済み → `np.trapezoid` を使用 / `np.frombuffer` の `dtype=np.int16` 明示 / `rfftfreq` の `d` はサンプリング周期 / `butter` の `Wn` はナイキスト正規化 / `nperseg` を `min(1024, len(samples))` でガード / 実数信号は `rfft`・`rfftfreq`
  - 定数: `LEAK_BAND_HZ=(500,1500)` / `NOISE_CUTOFF_HZ=100` / `SEVERITY_THRESHOLDS={3:0.60, 2:0.30}`（仮値）
  - `spectrum` はFE-4描画用にPSDを128点へダウンサンプル
  - **NFR-1**: 2秒/16kHz 1件の解析が3秒以内に完了すること

#### [#5] FE-1: API型定義(TypeScript)とaxiosクライアント — 8/11

- **目的**: バックエンドのPydanticモデルと1:1対応するTS型を作り、型安全にAPIを呼ぶ土台を構築。`any` 使用禁止（CLAUDE.md §5.2）。
- **変更**: `src/types/api.ts`、`src/lib/api.ts`、`.env.local.example`
- **方針の要点**:
  - 型: `GeoLocation` / `SpectrumPoint` / `AnalysisResult` / `TelemetryResponse` / `AlertSummary` / `AlertDetail` / `SensorInfo` / `WorkOrder`。`severityLevel` は `1 | 2 | 3` のリテラルユニオン
  - snake_case(バックエンド) → camelCase(フロント) の変換は `lib/api.ts` の境界で1回だけ
  - 関数: `fetchSensors()` / `fetchAlerts(params)` / `fetchAlertDetail(id)` / `createWorkOrder(id)`
  - エラーは `axios.isAxiosError` 判定で `ApiError` 型に再送出。**`NEXT_PUBLIC_` にOrcarouterキーは置かない**

#### [#6] FE-2: ダッシュボードレイアウトとKPIサマリ — 8/11

- **目的**: UI-1確定レイアウトの外枠（自治体オペレーションセンター風）を実装。
- **変更**: `layout.tsx`（lang="ja"・metadata）、`page.tsx`、`components/dashboard/Header.tsx`・`KpiSummary.tsx`、`components/common/SeverityBadge.tsx`、`lib/severity.ts`
- **方針の要点**:
  - `page.tsx` は **Server Component のまま維持**（`'use client'` を削除）。状態はFE-5の `DashboardClient` へ
  - Next.js 16 の新型 `LayoutProps<"/">` 型注釈は変更しない
  - 深刻度の色・ラベルは `lib/severity.ts` の**1箇所のみ**に集約（FE-3/FE-5と共用）

#### [#7] BE-6: アラート参照API群とインメモリストア — 8/12

- **目的**: 解析済みテレメトリを保持し、フロントが参照するAPIを提供。本番DBは作らず `deque(maxlen=500)` + dictのインメモリストアで代替。
- **変更**: `app/store.py`、`app/schemas/alert.py`、`app/routers/alerts.py`・`sensors.py`、`routers/telemetry.py`、`main.py`、`scripts/check_alerts.py`
- **方針の要点**:
  - `threading.Lock` で保護（FastAPI同期 `def` はスレッドプール並行実行のため）
  - API: `GET /sensors`（`?format=geojson` 対応、座標 `[経度, 緯度]`）、`GET /alerts?level=&limit=`（深刻度降順・時刻降順）、`GET /alerts/{telemetry_id}`（無ければ404）、`POST /alerts/{telemetry_id}/work-order`（BE-5実装までは**501スタブ**、FE-6が契約を先に固められるように）

#### [#8] FE-3: Leaflet GISマップ（漏水リスクノードのリアルタイム描画） — 8/12

- **目的**: センサー位置と深刻度を地図上に可視化。Leafletは `window` 依存のためSSR無効の2段構成が必須。
- **変更**: `src/types/sensor.ts`（GeoJSON型）、`components/map/SensorMapInner.tsx`（`'use client'`）、`components/map/SensorMap.tsx`（dynamicラッパー）
- **方針の要点**（ビルドが壊れる地雷）:
  - `SensorMapInner` に `'use client'` + `MapContainer` + CSS import。`SensorMap` も `'use client'` で `dynamic(..., { ssr: false })` ラップ（**Server Componentから直接呼ぶとビルドエラー**）
  - 座標順序: GeoJSON `[経度, 緯度]` ↔ Leaflet `[緯度, 経度]` の変換箇所にコメント必須
  - `<GeoJSON>` はdata変更で再描画されない → `key` に `lastReadingAt` join文字列を渡して強制再マウント
  - 既定マーカーアイコンの404回避のため `CircleMarker`（SVGベース）を `pointToLayer` で使用
  - 色は `lib/severity.ts` から取得、タイルはOpenStreetMap、初期中心は `hydrants.json` の重心から算出
  - Level 3マーカーはCSSアニメーションで点滅（デモ演出）

#### [#9] FE-5: アラート一覧と詳細ドロワー — 8/12

- **目的**: 検知アラートの一覧表示と詳細ドロワー（解析結果・配管情報）。地図と一覧の選択状態を連動。
- **変更**: `components/dashboard/DashboardClient.tsx`、`components/alert/AlertList.tsx`、`components/alert/AlertDetailDrawer.tsx`、`app/page.tsx`
- **方針の要点**:
  - `DashboardClient`（`'use client'`）が `selectedAlertId` / `alerts` を保持し各コンポーネントへ配布。`page.tsx` はServer Componentのまま
  - 新着反映は **5秒間隔 `setInterval` ポーリング**（CLAUDE.md §3の「リアルタイム双方向チャット」には該当しない軽量方式）。クリーンアップで必ず `clearInterval`
  - 一覧は深刻度降順→時刻降順、Level 3は行全体強調
  - ドロワーにFE-4チャート差し込みスロットを用意（並行作業可能に）
  - ポーリング失敗時は画面を壊さず最終更新時刻を据え置き

### P1

#### [#10] BE-4: 疑似GIS配管台帳と位置照合ロジック — 8/13

- **目的**: センサー位置から水道管路（材質・口径・布設年）を引き当て、BE-5の部材選定入力を揃える。本番GISDBは作らず軽量JSONで代替。
- **変更**: `app/data/pipes.json`（10路線）、`app/services/ledger.py`、`app/schemas/pipe.py`、`scripts/check_ledger.py`
- **方針の要点**:
  - `pipes.json`: `material`（ductile_iron/cast_iron/pvc/steel）× `diameter_mm`（75/100/150/200）、`installed_year`（1965〜2015）、`burial_depth_m`、`route`（LineString）、`hydrant_ids`
  - `find_pipe_by_hydrant()`（主経路: `hydrants.json` の `pipe_id` で直接引く）/ `find_nearest_pipe()`（Haversine最近傍・フォールバック）
  - モジュールレベルで一度だけロードしてキャッシュ。ファイル欠損・破損時は**起動時に明確な例外**（サイレント空台帳にしない）
  - 布設年から経過年数を算出（BE-5プロンプトの劣化度根拠）

#### [#11] OR-1: httpxの導入とHTTPクライアント依存性注入 — 8/13

- **目的**: Orcarouterへの非同期HTTPクライアントを依存性注入で提供する基盤を作る。
- **変更**: `backend/requirements.txt`（httpx追記）、`app/dependencies.py`（新規）
- **方針の要点**:
  - **⚠️ CLAUDE.md §1 Human-in-the-Loopにより、ライブラリ追加はユーザー承認が前提**（承認記録をIssueコメントに残す）
  - `get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]` を `async with httpx.AsyncClient(timeout=30.0)` で提供
  - 型エイリアス `HttpClientDep = Annotated[httpx.AsyncClient, Depends(...)]` を公開（テスト時は `app.dependency_overrides` で差し替え）
  - 副次効果: Starlette `TestClient` が使え、以降の検証スクリプトはサーバー起動不要に

#### [#12] OR-2: Orcarouter自動起票プロンプトの設計 — 8/13

- **目的**: 解析結果＋配管台帳から補修部材・概算見積・作業指示書を構造化JSONで得るプロンプトを設計。**LLM出力のパース失敗を減らすのが主目的**。
- **変更**: `app/services/prompts.py`、`app/schemas/work_order.py`、`scripts/check_prompt.py`
- **方針の要点**:
  - `WorkOrder` をPydantic v2で先に定義し、**`WorkOrder.model_json_schema()` をプロンプトへ埋め込んで出力形式を強制**（スキーマとプロンプトが自動同期）
  - 構造: `parts`（name/spec/quantity/unit_price_yen/subtotal_yen）、`total_estimate_yen`、`work_steps`、`required_workers`、`estimated_duration_hours`、`urgency`（low/medium/high/critical）、`notification_text`、`source`（llm/fallback）
  - システムプロンプト: 「日本の水道事業体の補修設計担当者」の役割
  - **金額は概算であり正式見積ではない旨をプロンプトと出力双方に明記**。JSONのみ出力指示＋コードフェンス除去の後処理

#### [#13] BE-5: `services/orcarouter.py` によるLLM自動起票の実装 — 8/13

- **目的**: FR-3/FR-4の中核。解析結果と配管台帳からOrcarouter経由のLLM呼び出しで補修部材選定・概算見積・作業指示書を自動起票。**処理は `app/services/orcarouter.py` にカプセル化**（CLAUDE.md §5.3）。
- **変更**: `app/services/orcarouter.py`、`app/routers/alerts.py`（501スタブ→実装）、`.env.example`、`scripts/check_orcarouter.py`
- **方針の要点**:
  - APIキーは `os.environ["ORCAROUTER_API_KEY"]`（`.env` から `python-dotenv`）。**レスポンス・ログ・例外のいずれにもキーを含めない**
  - `.env.example` に `ORCAROUTER_API_KEY` / `_BASE_URL` / `_MODEL` / `_ENABLED` を追記（実キーはコミットしない）
  - 失敗分類: タイムアウト・5xx・NWエラー → **1回だけリトライ**→失敗でOR-3フォールバック / 4xx → 即フォールバック＋理由ログ / パース失敗・スキーマ不一致 → フォールバック
  - `POST /alerts/{id}/work-order` を `async def` + `HttpClientDep` に。同一アラート2回目以降はキャッシュを返す

#### [#14] OR-3: LLM失敗時フォールバック（規定ルールによる部材・見積算出） — 8/13

- **目的**: デモ中の外部API障害・レート制限・キー切れで画面が壊れないよう、配管台帳から静的ルールで部材と概算見積を返す代替経路を用意。**ハッカソン本番での事故防止が主目的**。
- **変更**: `app/services/orcarouter.py`（`_fallback_work_order()` 追加）、`app/data/repair_parts.json`（部材マスタ）、`scripts/check_orcarouter.py`
- **方針の要点**:
  - `repair_parts.json`: 材質4種 × 口径4種 = **16通り以上**の標準部材・単価（例: 鋳鉄管150mm → 割Tクランプ150mm 48,000円）
  - 工数ルール: Level 1→1名2h / Level 2→2名4h / Level 3→4名8h。urgency: 1→medium / 2→high / 3→critical
  - **`source = "fallback"` を必ず設定**し、フロント（FE-6）が「AI生成」/「規定ルール」のバッジを出し分け（**障害時でも嘘をつかない表示**）
  - `ORCAROUTER_ENABLED=false` で強制フォールバック（オフラインでのデモリハーサル用）

#### [#15] FE-4: Rechartsによる音響波形・周波数スペクトル表示 — 8/14

- **目的**: BE-3の解析結果を可視化し「なぜ漏水と判定したか」を審査員に示す。**漏水帯域500〜1500Hzのピーク強調がデモ上の要点**。
- **変更**: `components/chart/SpectrumChart.tsx`、`WaveformChart.tsx`（新規）、`components/alert/AlertDetailDrawer.tsx`（差し込み）
- **方針の要点**:
  - 両コンポーネントとも `'use client'`（Rechartsが状態・イベント使用）
  - `SpectrumChart`: 128点 `spectrum` を `AreaChart` で描画。**`ReferenceArea x1={500} x2={1500}` で漏水帯域ハイライト**、卓越周波数に `ReferenceLine` + ラベル
  - `WaveformChart`: 全32000点を**256点へ間引き**してから渡す
  - `ResponsiveContainer` + 親側の明示的高さ指定。データ未取得時はスケルトン（空配列を渡すと軸が壊れる）

#### [#16] FE-6: AI自動起票モーダル実装 — 8/14

- **目的**: BE-5/OR-3の自動起票結果を1画面で提示する**デモのクライマックス部分**。
- **変更**: `components/workorder/WorkOrderModal.tsx`、`components/alert/AlertDetailDrawer.tsx`（起票ボタン）、`src/types/api.ts`（`WorkOrder`型追加）
- **方針の要点**:
  - ドロワー「AI自動起票」→ `createWorkOrder(alertId)` → ローディング（スピナー＋進行メッセージ）→ モーダル表示
  - 内容: 部材テーブル / 見積合計（強調）/ 作業手順（番号付き）/ 人員・工期 / 緊急度バッジ / 通知文面（コピーボタン）
  - **`source` でバッジ出し分け**: `"llm"`→「AI生成」、`"fallback"`→「規定ルールによる自動算出」
  - **「概算であり正式見積ではない」注記を常時表示**
  - 失敗時はモーダル内エラー＋再試行（画面全体は壊さない）。Esc/オーバーレイクリックで閉じる

### P2（余力枠）

#### [#17] BE-7: 防災モード（震災時 一括被害エリアマッピング） — 8/15

- **目的**: FR-5。震災等で多発するLevel 3破裂を地理的クラスタリングし、被害エリアと優先閉栓バルブを提示。**P0/P1完了後にのみ着手**。
- **変更**: `app/schemas/disaster.py`、`app/routers/disaster.py`、`main.py`、`scripts/check_disaster.py`、`components/map/DisasterOverlay.tsx`（余力があれば）
- **方針の要点**:
  - `GET /api/v1/disaster/summary`: Level 3を距離閾値（例300m）でクラスタリング。**scikit-learn不使用、Haversine＋単純な貪欲法**（ライブラリ追加回避）
  - 各クラスタ: `cluster_id` / `center`（重心）/ `affected_sensor_ids` / `affected_pipe_ids` / `estimated_households` / `priority_valve`（最大口径の上流管路に接続する消火栓）
  - クラスタ範囲をGeoJSON Polygon（重心からの円の多角形近似）で返却
  - `POST /api/v1/disaster/simulate?count=N`: デモ用にLevel 3を一括投入（BE-2の生成関数を再利用）

---

## 5. エリア別の役割

| エリア | タスク | 責務 |
|---|---|---|
| **design** | #1 | 画面設計の文書確定（全フロントの前提） |
| **backend** | #2, #3, #4, #7, #10, #13, #17 | 受信・解析・保存・照合・自動起票・防災 |
| **frontend** | #5, #6, #8, #9, #15, #16 | 型定義・ダッシュボード・地図・一覧/詳細・可視化・起票UI |
| **llm** | #11, #12, #13, #14 | httpx基盤・プロンプト設計・LLM呼び出し・フォールバック |
