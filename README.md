# SmartWater Guardian

消火栓貼付型 IoT 音響センサーとハイブリッド AI 解析により、水道管の微小漏水を早期検知し、自動アセットマネジメントを実現するインフラ DX Web アプリ。

---

## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [クイックスタート](#クイックスタート)
3. [技術スタック](#技術スタック)
4. [リポジトリ構成](#リポジトリ構成)
5. [実装状況](#実装状況)
6. [開発ワークフロー](#開発ワークフロー)
7. [テスト実行](#テスト実行)
8. [本番デプロイ](#本番デプロイ)
9. [関連ドキュメント](#関連ドキュメント)
10. [開発規約](#開発規約)
11. [ソースコード規模（ステップ数）](#ソースコード規模ステップ数)

---

## プロジェクト概要

### 課題と価値

**課題:**
- 水道事業者が肉眼では検知不可能な微小漏水（Level 1）を早期発見できない
- 従来の漏水調査は人手費用が高く、対応に 1-2 週間要する
- IoT センサーは価格が高く、既存の GPS 機能では精度が限定的

**SmartWater Guardian の解決：**
- **AI 音響解析**: 消火栓マウント型 IoT センサーで 24/7 自動監視
- **微小漏水検知**: 周波数分析（FFT）+ SVM 機械学習で Level 1-3 リスク分類
- **自動起票**: LLM（Orcarouter API）が補修部材・見積を自動生成
- **GIS 統合**: 疑似 GIS 配管台帳と Haversine 照合で位置特定
- **防災モード**: Level 3 アラート一括投入で被災エリア クラスタリング

### デモスコープ（2026-08-10 ～ 08-15）

- インメモリストア + JSON マスタで完全に動作するデモ
- 消火栓 20 台・配管 10 路線の疑似センサーネットワーク
- 実スペクトル算出と 1:1 自動起票ワークフローの実演
- WAF・Secrets Manager・本番 DB は不使用（コスト削減）
- AWS デプロイオプション（余裕がある場合）

---

## クイックスタート

### 前提条件

- **Windows 11** / **PowerShell 7+**（開発環境）
- **Python 3.12** + `python -m venv`
- **Node.js 18+** + `npm`
- **Docker Desktop**（AWS デプロイ用）
- **Git**

### ローカル実行（ターミナル 2 個）

#### ターミナル 1: バックエンド起動

```powershell
cd backend
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\uvicorn.exe main:app --reload --port 8000
```

- API ドキュメント: http://localhost:8000/docs（Swagger UI）
- ヘルスチェック: http://localhost:8000/

#### ターミナル 2: フロントエンド起動

```powershell
cd frontend
npm install
npm run dev
```

- ダッシュボード: http://localhost:3000/

### デモシード投入

バックエンド起動直後は、監視センサー20台が自動的に **Level 0（正常）** で初期化される
（コマンド不要）。デモの山場（Level 0/1/2/3 の対比）を作るには、受領した音声フォルダを
`backend/dataset/` に配置する（WAV、mono、PCM16、8000Hz、1秒）。

```text
backend/dataset/
├── BE3_demo_no-leak_level0.wav
├── BE3_demo_leak_level1.wav
├── BE3_demo_leak_level2.wav
└── BE3_demo_leak_level3.wav
```

Windows（PowerShell）:

```powershell
cd backend
venv\Scripts\python.exe scripts/seed_demo.py --seed 42
```

macOS / Linux:

```bash
cd backend
venv/bin/python scripts/seed_demo.py --seed 42
```

監視センサー20台へ Level 0×8 / Level 1×8 / Level 2×3 / Level 3×1、合計20件を投入する。
成功時は `[OK] 20 件を ... へ投入しました` と表示される。
ダッシュボード画面右上の「シード投入」「シードクリア」「防災シミュレーション」ボタンから
同じ操作をブラウザだけで実行することもできる。
フロントエンドをリロードすると、センサー地図・アラート一覧・KPI が反映される。

詳細な手順と再投入方法は [`docs/demo-runbook.md`](docs/demo-runbook.md) を参照。

---

## 技術スタック

### バックエンド

| 項目 | 内容 |
|---|---|
| フレームワーク | **FastAPI 0.141** / Starlette |
| 言語・検証 | **Python 3.12** / **Pydantic v2** (strict / extra="forbid") |
| 数値解析 | **NumPy 2.5** / **SciPy** (FFT 解析) |
| 機械学習 | **scikit-learn** SVM (joblib ロード) |
| HTTP クライアント | **httpx** (Orcarouter 連携) |
| テスト | **pytest** + FastAPI TestClient |
| 静的チェック | **ruff** (lint) + **mypy** (型検査) |
| カバレッジ | **pytest-cov** (**行・branch 各 80%**) |

### フロントエンド

| 項目 | 内容 |
|---|---|
| フレームワーク | **Next.js 16** (App Router) |
| 言語・型安全 | **TypeScript strict** / `any` 禁止 |
| スタイル | **Tailwind CSS v4** |
| 地図 | **Leaflet 1.9** / **react-leaflet 5** |
| グラフ | **Recharts** (スペクトラム・波形) |
| HTTP クライアント | **axios** (`lib/api.ts` で snake_case→camelCase 一度だけ変換) |
| テスト | **Vitest** + **Testing Library** (**カバレッジ 80%**) |
| Lint | **ESLint 9** (flat config) + `eslint-config-next` |

### インフラ

| 項目 | 内容 |
|---|---|
| クラウド | **AWS** (東京リージョン ap-northeast-1) |
| コンテナ | **Docker** / **ECS Fargate** |
| レジストリ | **ECR** (Elastic Container Registry) |
| ロードバランサー | **ALB** (Application Load Balancer) |
| Infrastructure as Code | **CloudFormation** (YAML) |
| CI/CD | **GitHub Actions** + **OIDC** |
| 監視 | **CloudWatch Logs** / **Alarms** / **SNS** |

### LLM 連携

| 項目 | 内容 |
|---|---|
| API プロバイダ | **Orcarouter API** (補修部材選定・見積自動起票) |
| リトライ戦略 | 429 → exponential backoff / 502-503 → fallback 分類 |
| キャッシング | Redis / in-memory LRU (デモは in-memory) |
| 原価計測 | トークン→円換算 (FR-6 / docs/llm-cost.md) |

---

## リポジトリ構成

```
smartwater-guardian/
├── backend/                              # FastAPI アプリケーション
│   ├── app/
│   │   ├── store.py                     # インメモリストア（シングルトン）
│   │   ├── main.py                      # FastAPI アプリ本体
│   │   ├── schemas/                     # Pydantic v2 モデル（API 契約）
│   │   ├── services/                    # ビジネスロジック集約
│   │   │   ├── audio.py                 # FFT 解析 + SVM リーク判定
│   │   │   ├── ledger.py                # 疑似 GIS 配管台帳照合
│   │   │   ├── orcarouter.py            # LLM 自動起票・リトライ・キャッシング
│   │   │   ├── llm_cost.py              # LLM 原価計測
│   │   │   ├── kpi.py                   # KPI 推定削減コスト算定
│   │   │   ├── demo_seed.py             # デモ一括投入（DEMO-2）
│   │   │   ├── disaster_signal.py       # 合成 Level3 波形生成（DEMO-2）
│   │   │   └── dataset_sync.py          # AWS向けS3データセット同期（DEMO-2）
│   │   ├── routers/                     # API エンドポイント（薄く保つ）
│   │   │   ├── telemetry.py             # POST /api/v1/telemetry
│   │   │   ├── alerts.py                # GET /api/v1/alerts 系
│   │   │   ├── sensors.py               # GET /api/v1/sensors
│   │   │   ├── kpi.py                   # GET /api/v1/kpi/summary
│   │   │   ├── disaster.py              # 防災モード API（DEMO-2で実在センサー書換え方式に再設計）
│   │   │   └── demo.py                  # POST /api/v1/demo/seed(-batch) / DELETE /demo/clear
│   │   ├── data/
│   │   │   ├── hydrants.json            # 消火栓マスタ（20 台）
│   │   │   ├── pipes.json               # 疑似 GIS 配管台帳（10 路線）
│   │   │   └── repair_parts.json        # 補修部材フォールバック
│   │   └── models/
│   │       ├── leak_svm_v1.joblib       # 学習済み SVM モデル
│   │       └── leak_svm_v1.metadata.json # モデルメタ（SHA-256）
│   ├── dataset/                          # 実音響WAV（Zenodo由来・git管理外・シード投入用）
│   ├── tests/                            # pytest テスト（334 件・カバレッジ 95%）
│   ├── scripts/                          # 手動検証・シード投入(seed_demo.py)・クリア(clear_demo.py)スクリプト
│   ├── requirements.txt                  # 依存パッケージ（pip freeze）
│   ├── requirements-dev.txt              # 開発用（pytest-cov / ruff / mypy）
│   ├── pyproject.toml                    # ruff / mypy 設定
│   ├── main.py                           # アプリケーションエントリポイント
│   ├── Dockerfile                        # Docker イメージ
│   ├── .env.example                      # 環境変数テンプレート
│   └── README.md                         # バックエンド詳細
│
├── frontend/                             # Next.js ダッシュボード
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx                 # ダッシュボード（Server Component）
│   │   │   ├── layout.tsx               # ルートレイアウト
│   │   │   └── api/docs/business-model/ # Route Handler（docs 配信）
│   │   ├── components/
│   │   │   ├── dashboard/               # KPI・ダッシュボード本体
│   │   │   ├── alert/                   # アラート一覧・詳細・ドロワー
│   │   │   ├── map/                     # Leaflet センサー地図
│   │   │   ├── chart/                   # スペクトラム・波形チャート
│   │   │   ├── workorder/               # AI 自動起票モーダル
│   │   │   └── common/                  # 深刻度バッジ等
│   │   ├── hooks/
│   │   │   ├── useAlertPolling.ts       # アラート 5 秒ポーリング
│   │   │   ├── useKpiPolling.ts         # KPI 5 秒ポーリング
│   │   │   ├── useSensorPolling.ts      # センサー GeoJSON ポーリング
│   │   │   └── useDisasterSummary.ts    # 防災サマリポーリング
│   │   ├── lib/
│   │   │   ├── api.ts                   # axios + snake_case→camelCase 変換
│   │   │   ├── severity.ts              # 深刻度メタ情報（単一ソース）
│   │   │   └── alertSort.ts             # アラート並び替え
│   │   └── types/
│   │       ├── api.ts                   # API 契約型
│   │       ├── sensor.ts                # GeoJSON 型
│   │       └── disaster.ts              # 防災クラスタ型
│   ├── tests/e2e/                       # Playwright E2E（global-setup・8 spec）
│   ├── package.json                     # npm 依存
│   ├── vitest.config.mts                # Vitest + coverage 80%
│   ├── playwright.config.ts             # E2E テスト設定
│   ├── next.config.ts
│   ├── eslint.config.mjs
│   ├── .env.local.example               # NEXT_PUBLIC_API_BASE_URL
│   └── README.md                         # フロントエンド詳細
│
├── infra/                                # AWS CloudFormation + デプロイ
│   ├── cloudformation/
│   │   ├── 00-github-oidc.yaml          # GitHub Actions OIDC + IAM ロール
│   │   ├── 01-network.yaml              # VPC / Subnet / NAT
│   │   ├── 02-security.yaml             # Security Group / IAM ロール
│   │   ├── 03-ecr.yaml                  # ECR リポジトリ ×2
│   │   ├── 04-alb.yaml                  # ALB / TargetGroup / Listener
│   │   ├── 06-ecs.yaml                  # ECS Fargate タスク定義・サービス
│   │   └── 07-monitoring.yaml           # CloudWatch Alarms
│   ├── scripts/
│   │   └── deploy.ps1                   # PowerShell デプロイ オーケストレーション
│   └── README.md                         # AWS 詳細・デプロイ手順
│
├── docs/                                 # 設計・要件・運用ドキュメント
│   ├── PRD.md                            # 要件定義
│   ├── business-model.md                 # 事業モデル・KPI 算定根拠
│   ├── llm-cost.md                       # LLM 原価計測・可視化
│   ├── demo-runbook.md                   # デモ実演手順
│   ├── aws-demo-runbook.md               # AWS デプロイ・実演
│   ├── architecture.md                   # システムアーキテクチャ
│   └── spec_doc/                         # 各 Issue の技術仕様書
│
├── .github/
│   └── workflows/
│       ├── ci.yml                        # テスト・カバレッジ・lint ゲート
│       └── deploy.yml                    # GitHub Actions CD（ECR push・ECS 更新）
│
├── aidlc/                                # AI-DLC ワークフロー記録
│   └── spaces/default/                   # プロジェクトワークスペース
│       ├── memory/
│       │   ├── org.md                    # 組織レベル規約
│       │   ├── team.md                   # チーム実践・確定判断
│       │   ├── project.md                # プロジェクト特化・学習記録
│       │   └── phases/                   # 各フェーズ方針
│       ├── codekb/                       # Reverse Engineering スナップショット
│       └── intents/                      # 各イニシアティブ記録
│
├── .claude/                              # Claude Code / AI-DLC ツール
│   ├── rules/
│   │   └── aidlc.md                     # aidlc 方針の import stub
│   ├── settings.json                     # Claude Code 設定（ツール許可・モデル）
│   ├── agents/                           # AI-DLC エージェントペルソナ
│   ├── knowledge/                        # メソドロジー参考資料
│   ├── sensors/                          # 自動チェック（コードスタイル等）
│   └── tools/
│       ├── aidlc-orchestrate.ts          # ワークフロー進行管理
│       ├── aidlc-runtime.ts              # コスト計算・進捗表示
│       └── aidlc-*.ts                    # 自動ツール群
│
├── CLAUDE.md                             # **プロジェクト規約（必読）**
├── README.md                             # **本ファイル**
└── .gitignore                            # Git 管理外（venv / .env / など）
```

---

## 実装状況

### バックエンド（BE-1 ～ BE-8 + DEMO-1）

| Issue | 機能 | 状態 | 詳細 |
|---|---|---|---|
| **BE-1** | テレメトリ受信・Pydantic v2 検証 | ✅ 完了 | `POST /api/v1/telemetry` → 深刻度分類 |
| **BE-2** | 消火栓マスタ・疑似センサーシミュレータ | ✅ 完了 | `hydrants.json` / `simulate_sensor.py` |
| **BE-3** | FFT 解析 + SVM リーク判定 | ✅ 完了 | 周波数スペクトル → 14 次元特徴量 → Level 0-3 |
| **BE-4** | 疑似 GIS 配管台帳・Haversine 位置照合 | ✅ 完了 | `ledger.py` find_nearest_pipe |
| **BE-5** | LLM 自動起票・キャッシング・フォールバック | ✅ 完了 | Orcarouter API リトライ分類・fallback 分類 |
| **BE-6** | インメモリストア・API（アラート・センサー） | ✅ 完了 | GeoJSON / JSON 応答 |
| **BE-7** | 防災モード・被害エリアクラスタリング | ✅ 完了（DEMO-2 で再設計） | 実在20消火栓のうち無作為6件をLevel3化・Haversine距離クラスタリング |
| **BE-8** | KPI サマリ「推定削減コスト」算定 | ✅ 完了 | 算定定数は `docs/business-model.md` 準拠 |
| **FR-6** | LLM 原価計測・可視化 | ✅ 完了 | トークン→円換算・UI 表示 |
| **DEMO-1** | デモ初期状態投入 | ✅ 完了 | 実スペクトル + 意図レベル上書き |
| **DEMO-2** | センサーデータ構成再設計（初期状態/シード投入/防災シミュレーション） | ✅ 完了 | 初期表示20件Lv0・一括シード投入API・実センサー書換え型防災シミュレーション |

### フロントエンド（FE-2 ～ FE-7）

| Issue | 機能 | 状態 | 詳細 |
|---|---|---|---|
| **FE-2** | 深刻度共通ユーティリティ | ✅ 完了 | `lib/severity.ts` 型+メタ情報 |
| **FE-3** | Leaflet センサー地図 | ✅ 完了 | GeoJSON マーカー・深刻度色分け |
| **FE-4** | 音響スペクトル・波形チャート | ✅ 完了 | Recharts・漏水帯域ハイライト |
| **FE-5** | アラート一覧・詳細ドロワー | ✅ 完了 | 5 秒ポーリング・詳細表示 |
| **FE-6** | AI 自動起票 UI・WorkOrderModal | ✅ 完了 | `POST /alerts/{id}/work-order` 連携 |
| **FE-7** | KPI サマリ実データ連携・「試算値」注記 | ✅ 完了 | `docs/business-model.md` リンク |

### 防災モード（BE-7・DEMO-2 で再設計）

| 機能 | 状態 | 詳細 |
|---|---|---|
| Level 3 アラートシミュレーション投入 | ✅ 完了 | `POST /disaster/simulate?count=1-20`。実在20消火栓のうち無作為 `count` 件（既定6）を、合成波形で信号データごとLevel3へ変化させる（架空センサーの新規追加はしない。監視センサー数は常に20） |
| 被災エリアクラスタリング（距離ベース） | ✅ 完了 | Haversine距離 + 貪欲法でクラスタリング（DBSCAN・scikit-learnは不使用）。シミュレーションで選出されたセンサーのみが対象（通常検知のLevel3は対象外） |
| 被災エリア地図描画（DisasterOverlay） | ✅ 完了 | `components/map/DisasterOverlay.tsx` |
| 想定断水世帯数表示 | ✅ 完了 | 消火栓密度ベース概算 |

### テスト・品質

| 項目 | 現状 | ゲート |
|---|---|---|
| **バックエンド** | 334 テスト・カバレッジ 95% | 行+branch 各 **80%** |
| **フロントエンド** | Vitest + Testing Library | lines / functions / branches / statements 各 **80%** |
| **E2E テスト** | Playwright 8 spec | global-setup / CI 前提 |
| **静的チェック** | ruff (lint) + mypy (型検査) | CI ゲート必須 |

---

## 開発ワークフロー

### AI-DLC（AI-Driven Development Life Cycle）

このプロジェクトは **AI-DLC v2** に準拠した構造化開発ワークフローを採用。詳細は [CLAUDE.md](./CLAUDE.md) §1-6 を参照。

```
Ideation (企画)
  ↓
Inception (立案・設計)
  ↓
Construction (開発・TDD)
  ↓
Operation (本番運用・最適化)
```

### TDD（Test-Driven Development）の厳格順守

**必ず Red → Green → Refactor サイクル：**

1. **Red**: 失敗するテストを書く
2. **Green**: テストをパスさせる最小実装
3. **Refactor**: テスト成功を維持したまま改善

**バックエンド:**
```powershell
cd backend
# ターミナル1: サーバー起動
venv\Scripts\uvicorn.exe main:app --reload --port 8000

# ターミナル2: テスト実行
venv\Scripts\python.exe -m pytest tests/ -v --cov=app --cov-branch --cov-fail-under=80
```

**フロントエンド:**
```powershell
cd frontend
npm run test
```

### ブランチ戦略（Trunk-Based）

- **main**: 常に CI テスト成功・デプロイ可能な状態
- **短命フィーチャーブランチ**: 大規模変更・レビュー必要時のみ使用
- **コミット粒度**: 1 Issue = 1 コミット（`feat: BE-8: KPI 推定削減コスト算定` など）

### GitHub Issues

各機能は GitHub Issues で追跡：
- **ラベル**: `BE-x`（バックエンド）/ `FE-x`（フロントエンド）/ `INFRA-x`（インフラ）
- **受入条件**: 各 Issue に記載された「何が完成と見なすか」
- **テスト**: 受入条件 = テスト仕様書

---

## テスト実行

### バックエンド（pytest）

```powershell
cd backend

# テスト実行（カバレッジなし）
venv\Scripts\python.exe -m pytest tests/ -v

# カバレッジ計測（行・branch 各 80% ゲート）
venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80
```

### フロントエンド（Vitest）

```powershell
cd frontend

# テスト実行＋カバレッジ
npm run test
```

### 静的チェック

**バックエンド:**
```powershell
cd backend
venv\Scripts\python.exe -m ruff check app main.py
venv\Scripts\python.exe -m mypy app main.py --ignore-missing-imports
```

**フロントエンド:**
```powershell
cd frontend
npm run lint
```

### E2E テスト（Playwright）

```powershell
cd frontend
# バックエンド・フロントエンドが起動している前提
npm run test:e2e
```

---

## 本番デプロイ

### 前提条件

- AWS アカウント（東京リージョン ap-northeast-1）
- AWS CLI v2
- Docker Desktop
- GitHub リポジトリの OIDC 統合

### クイックデプロイ（Phase 1 ～ 5）

詳細は [infra/README.md](./infra/README.md) を参照。簡潔版：

#### Phase 1: インフラ構築（00 ～ 04）

```powershell
cd infra/scripts
.\deploy.ps1 -Phase Infra -Environment dev -Region ap-northeast-1
```

#### Phase 2: ALB DNS 名の取得

```powershell
aws elbv2 describe-load-balancers --names smartwater-guardian-alb `
  --query 'LoadBalancers[0].DNSName' --output text --region ap-northeast-1
```

#### Phase 3-4: Docker イメージビルド・ECR プッシュ

```bash
# backend
docker build -f backend/Dockerfile -t smartwater-guardian-backend:latest backend/
# frontend（ALB DNS をビルド時指定）
docker build -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://<ALB-DNS-NAME> \
  -t smartwater-guardian-frontend:latest .

# ECR ログイン・プッシュ（AWS Account ID 等を設定）
...
```

#### Phase 5: アプリスタック デプロイ（06 ～ 07）

```powershell
cd infra/scripts
.\deploy.ps1 -Phase App -Environment dev -Region ap-northeast-1 `
  -BackendImageTag latest -FrontendImageTag latest `
  -OrcaRouterApiKey '<API_KEY>'
```

### デモコスト目安

デモ（1 日）向けに WAF・Secrets Manager・複数タスク を廃止：

| 項目 | 日額（USD） |
|---|---|
| Fargate（backend 1T） | $0.3 |
| Fargate（frontend 1T） | $0.6 |
| ALB 固定費 | $0.6 |
| NAT Gateway 1 台 | $1.5 |
| その他（ECR / CloudWatch） | $0.3 |
| **合計** | **$3.5 ～ 4.5** |

### 本番への道筋（To-Be）

WAF・Secrets Manager・HA（タスク数 2）・Auto Scaling を復元：

- 月額コスト: ~$125-155（デモ 31 倍）
- 詳細は [infra/README.md](./infra/README.md#to-be-構成本番向け将来設計) を参照

---

## 関連ドキュメント

### 設計・要件

- [**CLAUDE.md**](./CLAUDE.md) — **プロジェクト規約・AI-DLC ガイドラインの必読文書**
- [PRD.md](./docs/PRD.md) — 要件定義・ユーザーストーリー
- [business-model.md](./docs/business-model.md) — 事業モデル・KPI 算定根拠（**試算値の根拠**）
- [llm-cost.md](./docs/llm-cost.md) — LLM 原価計測・可視化（FR-6）
- [architecture.md](./docs/architecture.md) — システムアーキテクチャ

### 実行・デプロイ

- [backend/README.md](./backend/README.md) — バックエンド セットアップ・API エンドポイント・テスト実行
- [frontend/README.md](./frontend/README.md) — フロントエンド セットアップ・コンポーネント一覧
- [infra/README.md](./infra/README.md) — AWS デプロイ手順・CloudFormation パラメータ

### デモ実演

- [docs/demo-runbook.md](./docs/demo-runbook.md) — ローカルデモ実演手順
- [docs/aws-demo-runbook.md](./docs/aws-demo-runbook.md) — AWS デプロイ後のデモ実演

### AI-DLC ワークフロー

- [.claude/CLAUDE.md](./.claude/CLAUDE.md) — AI-DLC 環境セットアップ・フレームワーク概要
- [aidlc/spaces/default/memory/](./aidlc/spaces/default/memory/) — チーム実践・プロジェクト学習記録

---

## 開発規約

### 言語規定

- **ドキュメント・コメント・docstring・コミットメッセージ**: **日本語**
- **コード**: 言語標準に従う（`snake_case` in Python、`camelCase` in TypeScript）

### TDD 必須

1. テスト（失敗）を書く
2. 最小実装でテスト成功
3. テスト成功を維持したまま改善

### カバレッジ基準

- **バックエンド**: **行・branch 各 80%** （`--cov-fail-under=80`）
- **フロントエンド**: **lines / functions / branches / statements 各 80%** （`vitest.config.mts` で設定）

### コード品質

**バックエンド:**
- Pydantic v2 で入力検証（`strict=True` / `extra="forbid"`）
- 例外は具体的に（FileNotFoundError / ValueError など明示）
- `any` 禁止
- ruff + mypy で CI ゲート必須

**フロントエンド:**
- TypeScript strict で `any` 禁止
- `lib/api.ts` **のみ** で snake_case→camelCase 変換（他レイヤーでは変換しない）
- ESLint 9 で CI ゲート必須

### 明示的な根拠

- **KPI 金額**: 根拠なく断定的に表示しない（`is_estimate: true` / `assumption_doc` で明示）
- **デフォルト値**: 根拠のない既定値でごまかさない（明確に例外を上げる）
- **API キー**: 環境変数で注入・**コミットしない**（`.env` は `.gitignore`）

### セキュリティ

- 依存関係: **Dependabot** で監視
- シークレット検知: **GitHub secret scanning** を有効化
- API キー・機密情報: **環境変数** で管理（`.env` gitignore）

### 既知の制約（デモスコープ）

- ❌ 認証・権限管理
- ❌ 物理 IoT 通信プロトコル
- ❌ リアルタイム通知（WebSocket 等）
- ❌ 本番用大型 GIS DB
- ❌ WAF・Secrets Manager（コスト削減）

---

## よくある質問（FAQ）

### Q: サーバーが起動しない

**A:** ターミナル出力と `backend` の `.env` 設定を確認。`ORCAROUTER_API_KEY` が未設定でもバックエンドは動作します（フォールバック）。

### Q: フロントが「接続エラー」と出る

**A:** バックエンド（http://localhost:8000）が起動していることを確認。未応答時はフォールバック表示（スケルトン or マスタデータ）が出ます。

### Q: E2E テストが失敗する

**A:** `tests/e2e/global-setup.ts` でバックエンド起動確認とシード投入を実行。バックエンドが立ち上がり完全に応答するまで待つ必要があります。

### Q: テスト・カバレッジゲートが失敗した

**A:** `npm run test` / `python -m pytest --cov=...` を確認。各 **80%** 以上が必須。該当ファイル・行番号が表示されます。

### Q: AWS デプロイに失敗した

**A:** [infra/README.md](./infra/README.md#サポートトラブルシューティング) のトラブルシューティングセクションを参照。CloudWatch Logs を確認。

---

## サポート・フィードバック

- **バグ報告**: GitHub Issues（ラベル: `bug`）
- **機能提案**: GitHub Issues（ラベル: `enhancement`）
- **セキュリティインシデント**: 非公開で報告（プロジェクトメンテナーに連絡）

---

## ライセンス

このプロジェクトはデモ・研究用です。詳細なライセンスは [LICENSE](./LICENSE) を参照してください。

---

## 貢献者

- **Project Owner**: taka0928eye
- **開発チーム**: SmartWater Guardian デモチーム
- **AI-DLC Framework**: Anthropic AI-DLC v2

---

## ソースコード規模（ステップ数）

| レイヤ | 本体コード | テストコード | 合計 |
|---|---|---|---|
| バックエンド（Python） | 3,832 行 | 3,717 行 | 7,549 行 |
| フロントエンド（TypeScript） | 2,357 行 | 3,404 行 | 5,761 行 |
| **合計** | **6,189 行** | **7,121 行** | **13,310 行** |

計測方法: 各ファイルの物理行数（空行・コメント含む）を合算。vendor / generated / cache
（`venv`, `node_modules`, `.next`, `__pycache__`, `.pytest_cache`, `coverage` 等）は対象外。
バックエンドは `backend/app` + `backend/scripts` + `backend/main.py`（本体）/
`backend/tests` + `backend/test_llm_integration.py`（テスト）。フロントエンドは
`frontend/src/{app,components,hooks,lib,types}` の `__tests__` 除く（本体）/
`__tests__` + `frontend/src/test` + `frontend/tests/e2e`（テスト）。
計測日: 2026-08-14 時点。

---

**最終更新**: 2026-08-13  
**プロジェクト段階**: Construction（デモ準備中）  
**デモ予定**: 2026-08-10 ～ 08-15
