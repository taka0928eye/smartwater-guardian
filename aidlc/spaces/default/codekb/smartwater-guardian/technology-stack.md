# SmartWater Guardian - テクノロジースタック

## バックエンド（backend/）

| カテゴリ | 技術 | バージョン | 用途 |
|----------|------|------------|------|
| 言語 | Python | 3.12（CI 実測）／3.11+（CLAUDE.md 記載） | アプリ言語 |
| Web フレームワーク | FastAPI | 0.141.1 | ASGI API フレームワーク（同期 def + スレッドプール） |
| データ検証 | Pydantic | 2.13.4（pydantic_core 2.46.4） | v2 strict / extra=forbid |
| 数値解析 | NumPy | 2.5.2 | rfft / hanning / interp による FFT モック解析 |
| 科学計算 | SciPy | 1.18.0 | **未使用**（BE-3 本実装で導入予定） |
| HTTP クライアント | httpx | 0.28.1 | `HttpClientDep`（BE-5/Orcarouter 用・現状未使用） |
| ASGI サーバー | uvicorn | 0.52.1 | 開発・デプロイ |
| テスト | pytest | 9.1.1 | 単体・統合テスト（`python -m pytest`） |
| カバレッジ | pytest-cov | CI 導入 | `--cov=app --cov-fail-under=80` |
| 設定 | python-dotenv | 1.2.2 | `.env` 読込 |
| リント | （無し） | - | ruff / mypy / pyproject.toml は未導入 |

依存は `backend/requirements.txt` にピン固定（==）。

## フロントエンド（frontend/）

| カテゴリ | 技術 | バージョン | 用途 |
|----------|------|------------|------|
| フレームワーク | Next.js | 16.3.0（ピン） | App Router / Server・Client 分離 |
| UI ライブラリ | React / react-dom | 19.2.8 | コンポーネント |
| 言語 | TypeScript | ^5（strict） | 型安全 |
| スタイリング | Tailwind CSS | ^4（@tailwindcss/postcss ^4） | Utility-first CSS |
| 地図 | Leaflet | ^1.9.4 | 地図コア |
| 地図 React 連携 | react-leaflet | ^5.0.0 | MapContainer / GeoJSON |
| 地図型定義 | @types/leaflet | ^1.9.22 | TS 型 |
| チャート | Recharts | ^3.10.1 | **import 未使用**（FE-4 スペクトル描画で利用予定） |
| アイコン | lucide-react | ^1.31.0 | アイコン |
| HTTP クライアント | axios | ^1.19.0 | API 呼び出し |
| テスト | Vitest | ^4.1.10 | 単体テスト（`vitest run`） |
| テストカバレッジ | @vitest/coverage-v8 | ^4.1.10 | 80% thresholds |
| テストライブラリ | @testing-library/react | ^16.3.2 | コンポーネントテスト |
| DOM | jsdom | ^30.0.1 | テスト環境 |
| テストマッチャ | @testing-library/jest-dom | ^7.0.1 | 拡張アサーション |
| テスト DOM | @testing-library/dom | ^10.4.1 | DOM クエリ |
| リント | ESLint | ^9（flat config）＋ eslint-config-next 16.3.0 | CI ゲート（`npm run lint`） |
| Node | Node.js | 22（CI） | ランタイム |

## CI / CD

- **GitHub Actions** `.github/workflows/ci.yml`
  - `backend-test`: Python 3.12 / pip install / ルート確認 / `check_telemetry.py` / `pytest --cov=app --cov-fail-under=80` / coverage.xml アップロード
  - `frontend-test`: Node 22 / `npm ci` / `npm run lint` / `vitest run --coverage`（lines/functions/branches/statements 各 80%）/ `npm run build`
- main push / PR で実行

## 設計上の技術選定（代替案との比較）

| 判断 | 選択 | 代替案 | 理由 |
|------|------|--------|------|
| API フレームワーク | FastAPI | Django / Flask | Pydantic v2 統合・自動 OpenAPI・非同期対応 |
| 入力検証 | Pydantic v2 strict | 手動バリデーション | IoT 外部入力の型厳密化・未知フィールド拒否 |
| 地図 | Leaflet + react-leaflet | Mapbox GL | 軽量・GeoJSON ネイティブ・デモ規模に十分 |
| 可視化 | Recharts | Chart.js / D3 | 軽量 React 向き（現状 import 未使用） |
| 状態管理 | ローカル useState + フック | Redux / Zustand | 単一画面・選択状態のみで十分（最小実装） |
| 外部 LLM | Orcarouter API | 自前実装 | 補修部材選定・見積自動起票（BE-5 で利用予定） |
