# SmartWater Guardian - テクノロジースタック

## バックエンド（backend/）

| カテゴリ | 技術 | バージョン | 用途 |
|----------|------|------------|------|
| 言語 | Python | 3.12（CI 実測）／3.11+（CLAUDE.md 記載） | アプリ言語 |
| Web フレームワーク | FastAPI | 0.141.1 | ASGI API フレームワーク（同期 def + スレッドプール） |
| データ検証 | Pydantic | 2.13.4（pydantic_core 2.46.4） | v2 strict / extra=forbid |
| 数値解析 | NumPy | 2.5.2 | FFT・特徴量抽出（services/audio.py） |
| 科学計算 | SciPy | 1.18.0 | DSP（フィルタ・窓関数等。services/audio.py） |
| 機械学習 | scikit-learn | 1.9.0 | SVM 漏水判定（services/audio.py） |
| モデル読込 | joblib | 1.5.3 | leak_svm_v1.joblib の読込・SHA-256 検証 |
| HTTP クライアント | httpx | 0.28.1 | `HttpClientDep` → orcarouter（LLM API 呼び出し） |
| AWS SDK | boto3 / botocore | 1.43.72 | `services/dataset_sync.py`（DEMO-2・AWS環境向けS3データセット同期） |
| ASGI サーバー | uvicorn | 0.52.1 | 開発・デプロイ |
| テスト | pytest | 9.1.1 | 単体・統合テスト（`python -m pytest`） |
| カバレッジ | pytest-cov | CI 導入 | `--cov=app --cov-branch --cov-fail-under=80`（行+branch 各 80%） |
| 設定 | python-dotenv | 1.2.2 | `.env` 読込 |
| リント | ruff | pyproject.toml | `select = E/W/F/I + E501`・line-length 100（Q6: C 実装済み） |
| 型検査 | mypy | pyproject.toml | `strict=true`（Q6: C 実装済み） |

依存は `backend/requirements.txt` にピン固定（==）。静的検査設定は `backend/pyproject.toml`。

## フロントエンド（frontend/）

| カテゴリ | 技術 | バージョン | 用途 |
|----------|------|------------|------|
| フレームワーク | Next.js | 16.3.0（ピン） | App Router / Server・Client 分離 / Route Handler |
| UI ライブラリ | React / react-dom | 19.2.8 | コンポーネント |
| 言語 | TypeScript | ^5（strict） | 型安全（`any` 禁止） |
| スタイリング | Tailwind CSS | ^4（@tailwindcss/postcss ^4） | Utility-first CSS |
| 地図 | Leaflet | ^1.9.4 | 地図コア |
| 地図 React 連携 | react-leaflet | ^5.0.0 | MapContainer / GeoJSON / 防災クラスタ描画 |
| 地図型定義 | @types/leaflet | ^1.9.22 | TS 型 |
| チャート | Recharts | ^3.10.1 | SpectrumChart / WaveformChart（FE-4・実使用） |
| アイコン | lucide-react | ^1.31.0 | アイコン |
| HTTP クライアント | axios | ^1.19.0 | API 呼び出し（lib/api.ts） |
| テスト | Vitest | ^4.1.10 | 単体テスト（`vitest run`） |
| テストカバレッジ | @vitest/coverage-v8 | ^4.1.10 | 4 指標 80% thresholds |
| E2E | Playwright | ^1.62.1 | E2E テスト（webServer + global-setup・8 spec） |
| テストライブラリ | @testing-library/react | ^16.3.2 | コンポーネントテスト |
| DOM | jsdom | ^30.0.1 | テスト環境 |
| テストマッチャ | @testing-library/jest-dom | ^7.0.1 | 拡張アサーション |
| テスト DOM | @testing-library/dom | ^10.4.1 | DOM クエリ |
| リント | ESLint | ^9（flat config）＋ eslint-config-next 16.3.0 | CI ゲート（`npm run lint`） |
| Node | Node.js | 22（CI） | ランタイム |

## インフラ（infra/・INFRA-1）

| カテゴリ | 技術 | 用途 |
|----------|------|------|
| IaC | AWS CloudFormation | スタック 00-github-oidc 〜 07-monitoring（VPC / ECR / ALB / ECS / CloudWatch） |
| コンテナ | Docker + ECS Fargate | backend 0.25vCPU/0.5GB・frontend 0.5vCPU/1GB（各 1 タスク） |
| ロードバランサ | ALB（公開サブネット ×2） | `/api/v1/*` → backend TG / その他 → frontend TG |
| 外部接続 | NAT Gateway ×1 | ECR プル・Orcarouter へのアウトバウンド |
| 監視 | CloudWatch Logs / Alarms / SNS | ALB 5xx・ECS CPU/Memory・UnHealthy Host |
| CI/CD | GitHub Actions OIDC | ECR push・ECS タスク定義更新（deploy.yml） |
| セキュリティ | （コスト削減で廃止） | WAF / Secrets Manager 不使用。API キーは環境変数注入。To-Be 構成に記録 |
| ストレージ | S3（プライベートバケット） | `DemoDatasetBucket`（DEMO-2）。Zenodoライセンスの実音響を手動アップロードし、`DemoDatasetEnabled=true` で backend タスクが起動時に同期（`infra/README.md`） |

デモ 1 日コスト目安は約 **$3.5-4.5**（NAT Gateway 1 台・タスク各 1・WAF 廃止）。

## CI / CD

- **GitHub Actions** `.github/workflows/ci.yml`
  - `backend-test`: Python 3.12 / pip install / ルート確認 / `ruff check` / `mypy` / `check_telemetry.py` / `check_kpi.py` / `check_disaster.py` / `pytest --cov=app --cov-branch --cov-fail-under=80` / coverage.xml アップロード
  - `frontend-test`: Node 22 / `npm ci` / `npm run lint` / `npm run test`（vitest + coverage 4 指標 80%）/ `npm run build`
  - `e2e-test`（needs: backend + frontend）: `npx playwright install --with-deps chromium` / `npm run e2e` / playwright-report アップロード
- main push / PR で実行
- **GitHub Actions** `.github/workflows/deploy.yml`（INFRA-1）
  - `workflow_dispatch`（environment: dev / staging / prod）。OIDC → ECR → ECS

## 設計上の技術選定（代替案との比較）

| 判断 | 選択 | 代替案 | 理由 |
|------|------|--------|------|
| API フレームワーク | FastAPI | Django / Flask | Pydantic v2 統合・自動 OpenAPI・非同期対応 |
| 入力検証 | Pydantic v2 strict | 手動バリデーション | IoT 外部入力の型厳密化・未知フィールド拒否 |
| 音響解析 | scikit-learn SVM + SciPy DSP | 深層学習 / ルールベース | MVP 契約（8000Hz/1.0s）に十分な精度を最小構成で実現（BE-3）。SHA-256 でモデル改ざん検知 |
| 地図 | Leaflet + react-leaflet | Mapbox GL | 軽量・GeoJSON ネイティブ・デモ規模に十分 |
| 可視化 | Recharts | Chart.js / D3 | 軽量 React 向き（スペクトル/波形チャートを実装済み） |
| 状態管理 | ローカル useState + フック | Redux / Zustand | 単一画面・選択状態のみで十分（最小実装） |
| 外部 LLM | Orcarouter API（プロキシ経由・キー環境変数） | 自前 LLM 実装 | 補修部材選定・見積自動起票（BE-5 実装済み）。フォールバックで可用性担保 |
| クラウド | AWS（CloudFormation + Fargate） | オンプレ / 自宅サーバー | デモ受け渡しはローカル主体・余裕があれば AWS へ（INFRA-1）。コスト最適化 |
