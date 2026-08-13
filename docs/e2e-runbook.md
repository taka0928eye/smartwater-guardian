# E2E テスト実行手順書（Playwright）

> Issue #29（FE-8）: Playwright による E2E テストの実装。
> デモ 8 シナリオのうち、現状 UI が存在する 7 シナリオをブラウザ E2E で検証する。
> シナリオ 7（防災モード）はフロント UI 未実装のため対象外（Issue #29 の対象外区分に合致）。

---

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| フレームワーク | `@playwright/test`（Chromium） |
| 実行ディレクトリ | `frontend/` |
| 起動コマンド | `npm run e2e` |
| 対象シナリオ | 初期表示 / 地図操作 / 一覧ソート・フィルタ / 詳細ドロワー / バックエンド停止フォールバック / ポーリング / AI自動起票 |
| 対象外 | ユニットテスト / ビジュアルリグレッション / 性能テスト / 防災モード（UI 未実装） |

テストは `webServer`（playwright.config.ts）が **バックエンド（uvicorn:8000）とフロント（next start:3000）を自動起動**するため、
`npm run e2e` 1 コマンドで完結する（3 ターミナルを手動起動する必要はない）。

> `npm run e2e` は `next build && playwright test` を実行する。
> next dev はコールドコンパイル待ちでテストがタイムアウトしやすいため、**本番ビルド
> （`next build` → `next start`）**で実行する。これにより起動が高速・決定論的になり、
> team.md のデモ受け渡し（`npm run build` / `npm run dev`）とも整合する。

---

## 2. 前提条件

- Node.js 20 以上 / npm
- Python 3.11 以上 + `backend/venv`（FastAPI の依存が入っていること）
- バックエンドの依存（`backend/requirements.txt`）が venv に導入済みであること

```powershell
# backend 依存（初回のみ）
cd C:\workspace\smartwater-guardian\backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 3. セットアップ（初回のみ）

```powershell
cd C:\workspace\smartwater-guardian\frontend

# 1) @playwright/test とブラウザの導入
npm install
npm run e2e:install      # npx playwright install chromium（キャッシュ済みなら短時間で完了）

# 2) 環境変数ファイル
#    .env.e2e.example をコピーして .env.e2e を作成する
#    （既定値のままでよい: PLAYWRIGHT_BASE_URL=http://localhost:3000
#      E2E_API_BASE_URL=http://localhost:8000）
Copy-Item .env.e2e.example .env.e2e
```

> `.env.e2e` はシークレットを含む可能性があるため `.gitignore`（`.env*`）対象。
> テンプレートは `.env.e2e.example` をコミット済み。

---

## 4. 実行

### 4.1 一括実行（推奨）

```powershell
cd C:\workspace\smartwater-guardian\frontend
npm run e2e
```

`playwright.config.ts` の `webServer` がバックエンドとフロント（本番ビルド）を自動起動し、
`global-setup.ts` がデモシード（L3×1 / L2×1 / L1×2 / L0×1）を投入してからテストを実行する。

### 4.2 ヘッド付き・デバッグ・レポート

```powershell
npm run e2e:headed    # ブラウザを表示しながら実行
npm run e2e:debug     # Playwright Inspector（ステップごとに確認）
npm run e2e:report    # HTML レポートをブラウザで表示（実行後に）
```

### 4.3 手動 3 ターミナル構成（任意）

Playwright の自動起動ではなく、既存のバックエンド/フロントを使う場合:

```powershell
# ターミナル 1: バックエンド（E2E と同設定で起動）
cd C:\workspace\smartwater-guardian\backend
$env:ORCAROUTER_ENABLED = "false"
.\venv\Scripts\uvicorn.exe main:app --port 8000

# ターミナル 2: フロント
cd C:\workspace\smartwater-guardian\frontend
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm run dev

# ターミナル 3: テスト（自動起動を無効化するため reuseExistingServer に依存）
npm run e2e
```

> 手動構成ではテスト前に `POST /api/v1/demo/seed` でシードを投入しておく必要がある。
> 通常は 4.1 の自動構成（webServer 起動 + global-setup シード）を使うのが確実。

---

## 5. テスト構成

| ファイル | 検証シナリオ |
| --- | --- |
| `tests/e2e/dashboard.spec.ts` | 1（初期表示: KPI・地図・一覧） / 6（ポーリング自動反映） |
| `tests/e2e/map.spec.ts` | 2（マーカー描画・選択→ドロワー・ズーム） |
| `tests/e2e/alerts.spec.ts` | 3（深刻度降順ソート・Level 0 トグル） / 4（詳細ドロワー: 解析結果・スペクトル・波形・配管情報） |
| `tests/e2e/workorder.spec.ts` | 8（AI 自動起票 → 作業指示書モーダル） |
| `tests/e2e/offline.spec.ts` | 5（バックエンド停止時フォールバック: 白紙にしない） |

| サポートファイル | 役割 |
| --- | --- |
| `tests/e2e/helpers.ts` | シード投入ヘルパー・PCM16 合成音・ネットワーク遮断 |
| `tests/e2e/global-setup.ts` | バックエンドヘルスチェック + デモシード投入 |
| `tests/e2e/fixtures.ts` | `apiBaseUrl` テストオプション |
| `tests/e2e/pages/DashboardPage.ts` | ページオブジェクトモデル（POM） |
| `playwright.config.ts` | webServer 自動起動（バックエンド + フロント本番ビルド）・レポーター・タイムアウト設定 |

---

## 6. 決定論の確保（シード・LLM コスト）

- **実装のモック・スタブはしない**（Issue #29 の「backend mock 禁止」に準拠）。
  実バックエンド（FE-5/FE-7/BE-6 実装）へ `POST /api/v1/demo/seed` でシードを投入する。
- 実音響 WAV は Git 管理外のため、**E2E 専用の合成音**（8000Hz / 1.0秒 / 8000サンプルの PCM16 =
  BE-3 MVP 契約準拠）を Base64 生成して投入する。深刻度はシード API が `level` に確定する。
- バックエンドは `ORCAROUTER_ENABLED=false` で起動するため、AI 自動起票は **LLM を呼ばず**
  規定ルール（fallback）で Work Order を生成する。実 LLM コストは発生せず、結果も一定になる。
  （詳細: `docs/llm-cost.md` FR-6、プロキシ無効時 fallback 経路）
- 並列実行（`workers: 4`）によるストア干渉を考慮し、件数の厳密検証は
  他スペックが追加しない深刻度（L3/L2）に限定し、L1 は「2 件以上」で検証する。

---

## 7. 受入条件との対応

| 受入条件 | 実現方法 |
| --- | --- |
| インストールが成功する | `npm install` + `npm run e2e:install` |
| 全テスト GREEN | `npm run e2e` で全パス確認 |
| 網羅的カバレッジ | 上表のシナリオ 1〜6・8（7 は UI 未実装のため対象外と明記） |
| バックエンド起動/停止両方の検証 | 起動時（全スペック）/ 停止時（offline.spec.ts: `page.route` abort で再現） |
| 失敗時のスクリーンショット/ビデオ | config で `screenshot: only-on-failure` / `video: retain-on-failure` 設定済み |
| POM による保守性 | `pages/DashboardPage.ts` にセレクタを集約 |
| トラブルシューティング | 本ドキュメント §8 |
| ローカル/CI で同一コマンド・同一結果 | `npm run e2e` を共通ゲートとし、CI 時は `retries: 1`・`workers` 調整のみ |
| 実行時間 < 2 分（4 workers） | `workers: 4`・`fullyParallel: false`（ファイル内直列）で短縮 |

---

## 8. トラブルシューティング

| 症状 | 原因・対処 |
| --- | --- |
| `browserType.launch: Executable doesn't exist` | `npm run e2e:install` で Chromium を導入する |
| ポート 8000/3000 が使用中 | webServer の自動起動が失敗する。該当プロセスを終了するか、手動 3 ターミナル構成（§4.3）を使う |
| global-setup が `接続できませんでした` | バックエンド起動に失敗。`backend/venv` の依存導入・ポート競合を確認 |
| 作業指示書の脚註が「LLM未使用」以外 | 既存サーバーを再利用（`reuseExistingServer`）した場合、`ORCAROUTER_ENABLED=false` の前提が外れる。手動構成（§4.3）を参照し E2E と同じ環境変数で起動する |
| 地図タイルがグレー | OSM タイルはネットワーク必須。マーカー・ズーム操作の検証には影響しない（SVG 描画のため） |
| 地図マーカーをクリックできない | 既定ビューでは実描画マーカーが地図端に位置し、Playwright の実クリックはヒットテストでコンテナに遮られる。map.spec.ts はマーカー中心の実座標を `dispatchEvent`（MouseEvent）で渡し、Leaflet 本来のクリック処理経路（点検出 → レイヤー click → ドロワー）を通す。テスト自体の修正不要 |
| `npm run e2e` の実行時間が長い | `next build`（初回数分）とサーバー起動待ちが含まれる。2 回目以降も `next build` は毎回実行される。テストだけを再実行したい場合は `npx playwright test`（`.next` が既にビルド済みの前提）を使う |

---

## 9. CI での実行

`.github/workflows/ci.yml` に E2E を追加する場合は、`npm run e2e` を共通コマンドとして利用する。

```yaml
# 抜粋（playwright ステップ）
- run: npm ci
- run: npx playwright install chromium
- run: npm run e2e
```

CI では `reuseExistingServer: !IS_CI` のため、毎回 webServer を新規起動する
（`CI=true npm run e2e`）。`retries: 1`・`workers: 4` で安定性と速度を両立する。
