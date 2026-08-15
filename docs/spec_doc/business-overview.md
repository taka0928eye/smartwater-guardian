# SmartWater Guardian - ビジネス概要

## 事業ドメイン

SmartWater Guardian は、**消火栓貼付型 IoT 音響センサー**と**ハイブリッド AI 解析**を組み合わせ、
水道管の**微小漏水を早期に検知**し、**自動アセットマネジメント**を実現するインフラ DX Web アプリ。

- 水道管の微小漏水は放置すると管路破裂（道路陥没・断水・高額な復旧費）へ進展する
- 音響センサーが漏水音を常時監視し、AI（SVM + FFT 周波数解析）で深刻度を判定する
- 疑似 GIS 配管台帳と照合して対象管路を特定し、予防保全・計画補修を支援する
- **検知から修繕手配（作業指示書の自動起票）まで**を即時自動化する（次世代性の訴求点）
- 従来の事後対応から**予防保全へのシフト**が価値の核

## 目的と価値提案

- **早期検知**: 目に見えない微小漏水（Level 1）を音響解析で捉える（人間には検知不能な Level 1 を主役に据える）
- **コスト削減**: 破裂を未然に防ぎ、推定削減コスト（KPI）を可視化する
- **資産管理**: 配管の布設年・素材・口径から経年劣化リスクを管理する
- **自動手配**: Orcarouter API（LLM）で補修部材選定・概算見積・作業指示書を自動起票する
- **デモ志向**: 8/10〜8/15 のデモ完成を最優先とし、最もシンプルな実装で成立させる
  （MVP & Scope Control: CLAUDE.md §1）

## 主要機能

### 1. テレメトリ受信（BE-1）
疑似 IoT センサー（`backend/scripts/simulate_sensor.py`）が送る PCM16 音響テレメトリ（Base64）を
`POST /api/v1/telemetry` で受信・検証（Pydantic v2 strict / extra=forbid）・保存する。

### 2. AI 音響解析（BE-3 実装済み）
`app/services/audio.py` が PCM16 をデコードし、14 次元特徴量（帯域エネルギー比・スペクトル形状等）を
FFT で抽出。SVM（`leak_svm_v1.joblib`・SHA-256 検証付き）で漏水判定し、`band_energy_ratio` から
深刻度 Level 1〜3 を分類する。MVP 契約は 8000Hz / 1.0s。

### 3. アラート検知と配管台帳照合（BE-6 / BE-4）
解析済みテレメトリをアラートとして一覧・詳細参照できる。詳細取得時は疑似 GIS 配管台帳
（`app/data/pipes.json`）と消火栓 ID を照合し、対象管路（PipeInfo: 素材・口径・布設年・経過年数）を自動付与する。

### 4. センサー地図（FE-3）
Leaflet 地図上にセンサー位置を GeoJSON（`GET /api/v1/sensors?format=geojson`）で描画する。
深刻度でマーカーを色分けし、最新状態・Level 3 の点滅を反映する。

### 5. AI 自動起票（BE-5 / FE-6）
アラート詳細の「AI自動起票」ボタンで `POST /alerts/{id}/work-order` を呼び、Orcarouter API（LLM）が
**補修部材選定・概算見積・作業指示書**を自動生成する（`WorkOrderModal` 表示）。LLM 未設定・失敗時は
規定ルールのフォールバック（`source: "fallback"`）で可用性を担保。FR-6 で 1 起票あたりの API 原価
（`cost_yen` / `latency_ms`）も算出・表示する。

### 6. KPI サマリ（BE-8 実装済み / FE-7 配線済み）
アラート実データから「推定削減コスト」とレベル別検知件数を集計する
（`docs/business-model.md` §3 の算定式。`GET /api/v1/kpi/summary`）。
`DashboardClient` 配下の `useKpiPolling` が 5 秒ポーリングし、5 枚カード（監視センサー数 /
Level 3 / Level 2 / Level 1 / 推定削減コスト）を降順表示。**モック値は使わず実データのみ**。
`is_estimate=True` / `assumption_doc` で試算値である旨を常時明示し、コストカードは「試算値」注記 + 
`docs/business-model.md` リンク（モーダル表示）を備える。

### 7. 防災モード（BE-7）
`POST /api/v1/disaster/simulate` で Level 3 アラートを一括シミュレーション投入し、
`GET /api/v1/disaster/summary` が距離閾値でクラスタリングして**被災エリア・想定断水世帯・優先閉栓バルブ**を
地図上に描画する（`DisasterOverlay`）。災害時の緊急対応シミュレーションをデモで実演可能。

### 8. デモ初期状態（DEMO-1 / DEMO-2）
バックエンド起動時、hydrants.json 実在20消火栓が常に **severity_level=0（正常）** で
自動初期化される（コマンド不要）。ダッシュボードの「シード投入」ボタン（`POST
/api/v1/demo/seed-batch`）で20消火栓へ Lv0×8 / Lv1×8 / Lv2×3 / Lv3×1 を一括投入し、
「シードクリア」ボタン（`DELETE /api/v1/demo/clear`）で20件Lv0の初期状態に戻せる。
「防災シミュレーション」ボタン（`POST /api/v1/disaster/simulate`）は実在20消火栓の
うち無作為6件を信号データごと Level 3 へ変化させる。いずれも実音声の `analyze_audio`
を実行しつつ深刻度を意図値に確定するハイブリッド方針。単体投入は `POST
/api/v1/demo/seed`、E2E 用は `POST /api/v1/alerts/seed`。

## 深刻度モデル（Level）

| Level | 意味 | 想定アクション |
|-------|------|----------------|
| 0 | 正常 | 表示対象外（FE-5 の既定では非表示） |
| 1 | 微小漏水（AI 検知） | 要注視・計画補修 |
| 2 | 進行性漏水 | 警告・早期補修 |
| 3 | 管路破裂 | 緊急対応（地図マーカー点滅・防災クラスタ） |

## 対象外（CLAUDE.md §3）

認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB は実装しない。
デモ評価者向けの内部機能であり、PII なし・認証スコープ外のため、規制・コンプライアンス要件は N/A。
本番クラウドインフラ（AWS）は INFRA-1 でデモ受け渡し用に最小構成で構築可能（コスト最適化済み）。

## 関連ドキュメント

- `docs/PRD.md` — 製品要件
- `docs/business-model.md` — ビジネスモデルと KPI 算定式（§3）
- `docs/llm-cost.md` — LLM 原価の実測・削減策（FR-6）
- `docs/ui-wireframe.md` — UI-1 ワイヤーフレーム（深刻度カラー定義）
- `docs/issues-summary.md` — Issue 一覧（BE-1〜BE-8 / FE-1〜FE-7 / OR-* / DEMO-1 / INFRA-1）
