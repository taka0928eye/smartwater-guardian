# GitHub Issues 概要一覧

> ハッカソン期間（8/10〜8/15）に実施する全Issue（23件）の概要をまとめたドキュメント。
> 優先度（P0 / P1 / P2）・依存関係・実装方針の要点を俯瞰するために使用する。

- 集計日: 2026-08-10（PRD更新反映により #18〜#23 を追加）
- 対象: 全Issue 23件（オープン 18件 / クローズ 5件）

---

## 1. 一覧表

| # | タスクID | タイトル | エリア | 優先度 | 依存タスク | 想定日 |
|---|---|---|---|---|---|---|
| 1 | UI-1 | 画面設計・ワイヤーフレーム確定 | design | **P0** | なし | 8/10 |
| 2 | BE-1 | センサテレメトリ受取API (`POST /api/v1/telemetry`) 型定義とダミー実装 | backend | **P0** | なし | 8/10 |
| 3 | BE-2 | 疑似センサーデータ生成スクリプトと消火栓マスタ作成 | backend | **P0** | BE-1 | 8/10 |
| 4 | BE-3 | `services/audio.py` によるFFT解析・漏水深刻度(Level 0〜3)判定 | backend | **P0** | BE-1, BE-2 | 8/11 |
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
| 18 | BE-8 | KPI「推定削減コスト」の算定ロジックとサマリAPI | backend | **P0** | BE-3, BE-6 | 8/12 |
| 19 | FE-7 | KPIサマリの実データ連携と「試算値」注記 | frontend | **P0** | BE-8, FE-1, FE-2 | 8/12 |
| 20 | OR-4 | LLM原価の計測・可視化（FR-6） | llm | P1 | OR-2, BE-5, OR-3, FE-6 | 8/14 |
| 21 | DOC-1 | 社会課題の出典検証と現場ヒアリング記録の作成 | design | P1 | なし | 8/13 |
| 22 | SEC-1 | シークレット非露出の横断検証（NFR-4） | backend | P1 | BE-5, OR-4 | 8/14 |
| 23 | DEMO-1 | デモ通しリハーサルとシード投入スクリプト | backend | P1 | BE-2〜BE-8, FE-5, FE-6, OR-3 | 8/15 |

---

## 2. 優先度別の内訳

### P0（デモの中核。まずここを固める） — 11件

バックエンドの「受信 → 解析 → 保存 → 参照」基盤（BE-1〜BE-6系）と、
フロントの「ダッシュボード → 地図 → アラート詳細」の一気通貫フロー（FE-1〜FE-5系）、
その設計前提となるワイヤーフレーム（UI-1）、
および根拠のあるKPI算出（BE-8 / FE-7）。

### P1（LLM自動起票の本命機能 + 評価軸対応） — 11件

配管台帳照合（BE-4）→ LLM呼び出し基盤（OR-1/OR-2）→ 自動起票（BE-5）→
障害時フォールバック（OR-3）と、その可視化（FE-4のチャート / FE-6の起票モーダル）。
加えて、評価軸に直接対応する横断タスク（OR-4 LLM原価 / DOC-1 出典検証 / SEC-1 シークレット / DEMO-1 リハーサル）。

### P2（余力枠） — 1件

防災モード（BE-7）。**P0/P1がすべて完了した場合のみ着手**する。

---

## 2.1 評価軸とIssueの対応（PRD §6）

| # | 評価軸 | 対応Issue |
|---|---|---|
| 1 | デモ完成度 | UI-1, FE-2〜FE-7, **DEMO-1(#23)** |
| 2 | 課題の実在性 | **DOC-1(#21)** |
| 3 | ビジネス成立性 | **BE-8(#18)**, **FE-7(#19)** |
| 4 | LLMコスト | **OR-4(#20)**, OR-2, BE-5, FE-6 |
| 5 | AI必然性 | **BE-3(#4)**（Level 0/1 の分離）, BE-5, OR-2 |
| 6 | 技術作りこみ | BE-3, 全Issue（TDD・カバレッジ80%） |
| 7 | セキュリティ | **SEC-1(#22)**, BE-5, OR-1 |
| 8 | 次世代性 | BE-5, OR-3, FE-6 |

---

## 3. 依存関係のクリティカルパス

```
UI-1(#1) ────────────────→ FE-2(#6) ──→ FE-3(#8) ─┐
BE-1(#2) ──→ BE-2(#3) ──→ BE-3(#4) ──→ BE-6(#7) ──┤→ FE-5(#9) ──→ FE-6(#16) ──→ OR-4(#20)
   │          │              │            │         │                              │
   └─→ FE-1(#5) ────────────┘            └→ BE-8(#18) ──→ FE-7(#19) ─┘            │
                          BE-4(#10) ──→ OR-2(#12) ──┴→ BE-5(#13) ──→ OR-3(#14) ────┤
                          (BE-2, BE-6から)   OR-1(#11) ──→ BE-5(#13)                │
                                                                                    ↓
                                          BE-5, OR-4 ──→ SEC-1(#22)          DEMO-1(#23)
BE-7(#17) ←─ BE-2, BE-4, BE-6                                          （ほぼ全Issueに依存）
DOC-1(#21) ←─ 依存なし（いつでも着手可能）
```

**要点:**

- 最長のクリティカルパスは `BE-1 → BE-2 → BE-3 → BE-6 → FE-5 → FE-6 → OR-4`。デモの「検知 → 表示 → 自動起票 → 原価提示」を一本化する。
- LLM系（OR-1/OR-2 → BE-5 → OR-3）は P0 基盤の上に積む。**OR-1（httpx導入）だけは P1 ながら依存が無く、ユーザー承認を得られ次第いつでも着手可能**。
- FE-4 / FE-6 は FE-5（ドロワー）と BE-6（詳細API）が揃ってから着手できる。FE-5 には事前にチャート差し込みスロットを用意して並行作業を可能にする設計。
- **BE-8 → FE-7（KPI算定）は BE-6 の直後に着手できる**。LLM系の完了を待たないため、LLM系が詰まった場合の並行レーンになる。
- **DOC-1(#21) は依存が無い唯一のIssue**。実装が詰まっている待ち時間に着手できる。
- **DEMO-1(#23) はほぼ全Issueに依存する最終工程**。8/15 に置き、ここで通し確認とオフラインリハーサルを行う。

---

## 4. 各Issueの詳細

### P0

#### [#1] UI-1: 画面設計・ワイヤーフレーム確定 — 8/10

- **目的**: FE-2〜FE-6の手戻りを防ぐため、単一ダッシュボードの画面構成・色定義・デモシナリオを文書で先に確定する。コードは書かない。
- **成果物**: `docs/ui-wireframe.md`（新規）
- **確定事項**:
  - レイアウト: ヘッダ（製品名/現在時刻/監視ステータス）+ KPI 5枚 + 左地図/右アラート一覧 + 詳細ドロワー（右スライドイン）+ 起票モーダル（中央）
  - 深刻度カラー（**PRD §2 更新により Level 0〜3 の4段階**）: Level 0（正常）`#64748b` グレー / **Level 1 `#84cc16` 黄緑** / Level 2 `#f59e0b` / Level 3 `#ef4444`
    - ⚠️ **Level 1 を緑＝正常系の色に置いてはならない**（`docs/ui-wireframe.md`）。Level 1 は「AIだけが検知できる微小漏水」であり、正常と誤読させると差別化の訴求が崩れる
  - KPI 5項目: 監視センサー数・Level 3件数・Level 2件数・本日の検知数・推定削減コスト
    - 推定削減コストの算定は BE-8(#18) / FE-7(#19) で `docs/business-model.md` §3 の式に置き換える
  - デモシナリオ（3分）: **Level 0（正常）のベースライン提示** → Level 1検知・地図点滅 → 波形/スペクトルで500〜1500Hzのピーク提示 → AI自動起票で部材・見積・作業指示書を生成（**実測API原価つき**）

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

- **目的**: 音響データのノイズカットと周波数解析から漏水確信度（0〜100%）と深刻度（**Level 0〜3**）を判定。**ロジックは `app/services/audio.py` にのみ集約**（CLAUDE.md §5.3）。
- **現状**: `app/services/` **未作成**。判定ロジックが `routers/telemetry.py` の `_analyze_audio_mock()` / `_classify_severity()` に暫定実装されており、**CLAUDE.md §5.3 に反した状態**。本Issueで解消する。
- **変更**: `app/services/audio.py`、`AnalysisResult` に `spectrum` / `status` 追加、`routers/telemetry.py` の暫定実装削除、`tests/test_audio.py`
- **方針の要点**:
  - 処理流れ: `decode_pcm16_mono` → ハイパス(100Hz以下除去) → `compute_psd`(Welch法) → `band_energy_ratio` → `classify_severity` / `leak_confidence`
  - **Level 0〜3 と status のマッピング**: 0→`normal` / 1→`watch` / 2→`warning` / 3→`critical`
  - ⭐ **Level 0 と Level 1 の分離がこのIssueの最重要要件**。PRD §2 のとおり「AIでなければ成立しない」と言えるのは Level 1 の検知に限られるため、この境界を誤ると差別化そのものが成立しない
  - **既知の地雷**: `np.trapz` は NumPy 2.5.2 で削除済み → `np.trapezoid` を使用 / `np.frombuffer` の `dtype=np.int16` 明示 / `rfftfreq` の `d` はサンプリング周期 / `butter` の `Wn` はナイキスト正規化 / `nperseg` を `min(1024, len(samples))` でガード / 実数信号は `rfft`・`rfftfreq`
  - 定数: `LEAK_BAND_HZ=(500,1500)` / `NOISE_CUTOFF_HZ=100` / `SEVERITY_THRESHOLDS={3:0.60, 2:0.30, 1:0.12}`（仮値）
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

#### [#18] BE-8: KPI「推定削減コスト」の算定ロジックとサマリAPI — 8/12

- **目的**: 評価軸3。`docs/business-model.md` §3 の算定式をバックエンド**1箇所**に実装し、根拠のない `1,420,000` を破棄する。
- **背景**: `frontend/src/app/page.tsx` の `MOCK_KPI_DATA` に `estimatedCostSavedYen: 1_420_000` / `totalSensors: 1240` がハードコードされているが、**142万円には算定根拠が存在しない**（`docs/business-model.md` §3.4 で破棄が明記済み）。`hydrants.json` は10件しか無いため `1240` も架空値。
- **変更**: `app/services/kpi.py`、`app/schemas/kpi.py`、`app/routers/kpi.py`、`main.py`、`tests/test_kpi.py`
- **方針の要点**:
  - 定数6種（`C_burst` / `C_repair1` / `C_repair2` / `p1` / `p2` / `C_response_saved`）を `app/services/kpi.py` に集約。**すべて仮説である旨をコメント**
  - `E_avoided(0)=0` / `(1)=¥121,800` / `(2)=¥308,000` / `(3)=¥150,000`
  - デモ内訳（L1×8 / L2×3 / L3×1）で合計 **¥2,048,400**
  - `is_estimate` フラグを返し、フロントが「試算値」注記を出せるようにする（**根拠のない金額を断定的に見せない**）

#### [#19] FE-7: KPIサマリの実データ連携と「試算値」注記 — 8/12

- **目的**: 評価軸3。`MOCK_KPI_DATA` を破棄しBE-8のAPI値を表示。**あわせて `SeverityLevel` 型の二重定義を解消**する。
- **背景**: `src/types/api.ts` は `SeverityLevel = 1 | 2 | 3`、`src/lib/severity.ts` は `0 | 1 | 2 | 3` で**矛盾しており、API型が Level 0 を表現できない**（バックエンドは `Literal[0,1,2,3]`）。
- **変更**: `src/types/api.ts`、`src/lib/api.ts`、`src/app/page.tsx`、`components/dashboard/KpiSummary.tsx`、各 `__tests__`
- **方針の要点**:
  - `SeverityLevel` の実体を `lib/severity.ts` に置き、`types/api.ts` は再エクスポート（**定義を2箇所に持たない**）
  - `page.tsx` は Server Component のまま維持
  - KPIカードに「試算値（前提: `docs/business-model.md`）」を常時表示

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

#### [#20] OR-4: LLM原価の計測・可視化（FR-6） — 8/14

- **目的**: 評価軸4。`docs/llm-cost.md` §2 の計測設計を実装し、**起票1件あたりの実測原価を画面上で審査員に見せる**。同 §2.3 は「実測原価を画面で見せられることが評価軸4における最大の差別化」と位置づけている。
- **背景**: PRD に FR-6 が追加されたが、**対応するIssueが1件も存在せず評価軸4が丸ごと未追跡だった**ため新設。
- **変更**: `app/services/llm_cost.py`、`app/schemas/work_order.py`、`app/services/orcarouter.py`、`WorkOrderModal.tsx`、`docs/llm-cost.md`、`tests/test_llm_cost.py`
- **方針の要点**:
  - 記録: `prompt_tokens` / `completion_tokens` / `cost_yen` / `model` / `latency_ms`
  - **`source="fallback"` のとき `cost_yen = 0.0`。推定値で埋めない**（実測でないものを実測として見せない）
  - usage 欠損時は事前指定モデル単価で算出し `is_estimated` を立て「概算」と明記
  - 1行JSONの構造化ログ（**APIキーを含めない**）+ モーダル脚注表示 + `docs/llm-cost.md` §3 への実測値転記（10件以上）

#### [#21] DOC-1: 社会課題の出典検証と現場ヒアリング記録 — 8/13

- **目的**: 評価軸2。PRD §1.1 の S-1〜S-5 を「要検証 / 未取得」から前進させる。**コードは書かない**（UI-1 と同種）。
- **背景**: `docs/field-research.md` は PRD §7 の関連ドキュメント表に記載されているが**ファイルが存在しない**。S-4 は一次情報が未取得。
- **変更**: `docs/field-research.md`（新規）、`docs/PRD.md` §1.1、`docs/business-model.md` §4
- **方針の要点**:
  - S-1/S-2: 「水道統計」の年度・数値・単位を出典URL付きで確定
  - S-3: 「7割」の母集団（全事業体か給水人口5万人以下か）を明確化
  - S-4: ヒアリング未実施なら**「未取得」と明記した空テンプレート**を置き、欠落を可視化する
  - S-5: 「1/5削減」の**比較対象**（音聴棒人力巡回 or 相関式漏水探知機委託）を明記
  - **検証未完了の項目を断定形で述べない**（PRD §1.1 運用ルール）

#### [#22] SEC-1: シークレット非露出の横断検証（NFR-4） — 8/14

- **目的**: 評価軸7。NFR-4 の4つの非出現経路（リポジトリ・git履歴 / クライアントバンドル / ログ / レスポンス・例外）を**テストで機械的に保証**する。
- **背景**: `.gitignore:9` で `.env` は除外済みだが、**ログ・例外・レスポンス・ビルド成果物への非出現は未検証**で横断確認のIssueが無かった。
- **変更**: `tests/test_secrets.py`、`app/services/orcarouter.py`、`backend/README.md`
- **方針の要点**:
  - **カナリア方式**: 検出可能なダミーキーを注入し、出力に現れないことを assert
  - ローテーション手順を NFR-4 の優先順どおり記載 — **追跡解除では無効化されないため、旧キー失効＋再発行を最優先し、その後に履歴から除去する**

#### [#23] DEMO-1: デモ通しリハーサルとシード投入スクリプト — 8/15

- **目的**: 評価軸1。PRD §6.1 のシナリオを1コマンドで再現し、当日の事故を防ぐ。
- **方針の要点**:
  - **Level 0（正常）のベースラインを先に投入**。PRD §6.1 のとおりデモは Level 0 との対比から入るため、Level 0 が画面に無いと訴求が成立しない
  - 内訳は `docs/business-model.md` §3.4 に合わせ **Level 1×8 / Level 2×3 / Level 3×1** → KPI が **¥2,048,400** で一致する
  - BE-2 の `generate_signal()` を再利用（音響生成を重複させない）
  - **`ORCAROUTER_ENABLED=false` でも完走すること**（オフラインリハーサル）
  - `docs/demo-runbook.md` に3分タイムラインと当日の復旧手順を記載

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
| **design** | #1, #21 | 画面設計の文書確定（全フロントの前提）・出典検証 |
| **backend** | #2, #3, #4, #7, #10, #13, #17, #18, #22, #23 | 受信・解析・保存・照合・自動起票・防災・KPI算定・セキュリティ検証・デモ運用 |
| **frontend** | #5, #6, #8, #9, #15, #16, #19 | 型定義・ダッシュボード・地図・一覧/詳細・可視化・起票UI・KPI連携 |
| **llm** | #11, #12, #13, #14, #20 | httpx基盤・プロンプト設計・LLM呼び出し・フォールバック・原価計測 |

---

## 6. 開発規約（全Issue共通）

- **TDD徹底**（CLAUDE.md §1・§5）: 全Issueの作業内容は **Red（失敗するテスト）→ Green（最小実装）→ Refactor** の3ステップで構成する。テストは `backend/tests/` および `frontend/src/**/__tests__/` に置く（両基盤とも整備済み）
- **カバレッジ80%以上**: `backend/venv/Scripts/pytest.exe --cov=app --cov-report=term-missing` / `npm run test`
- **`any` 禁止 / Pydantic v2 徹底**
- **ロジックの集約**（CLAUDE.md §5.3）: FFT解析は `app/services/audio.py`、LLM呼び出しは `app/services/orcarouter.py` にのみ置く
- **ドキュメントとの単一情報源**:
  - 深刻度カラー → `frontend/src/lib/severity.ts`（フロント側で再定義しない）
  - KPI算定定数 → `backend/app/services/kpi.py`（`docs/business-model.md` §3.2 準拠）
  - LLM単価定数 → `backend/app/services/llm_cost.py`（`docs/llm-cost.md` §2.2 準拠）
