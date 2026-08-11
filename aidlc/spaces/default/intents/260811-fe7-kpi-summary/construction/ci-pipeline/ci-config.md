# CI Config — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> ステージ: ci-pipeline（Construction）| リード: aidlc-pipeline-deploy-agent | 日時: 2026-08-11
> 上流成果物: code-summary（BU-1/code-generation）、build-and-test-summary / build-test-results（build-and-test）

## 1. CI ツール

- **GitHub Actions**（`.github/workflows/ci.yml`）を採用。既存 CI を本スコープの品質ゲート（Q3/Q4/Q6）に整合させて拡張した。
- 代替案（CodePipeline / CodeBuild / Jenkins）は本プロジェクトで未使用・導入対象外（ローカル実行主体のデモスコープ）。

## 2. トリガーとブランチ戦略

- **トリガー**: `main` への push / pull_request（既存のまま維持）
- **ブランチ戦略**: main 直コミット中心（trunk-based、team.md Q1: A 確定）。短命フィーチャーブランチ + PR は大規模変更・他者レビュー時のみ。CI は push / PR の両トリガーで品質ゲートを強制する。

## 3. ジョブ構成

### 3.1 backend-test（Ubuntu / Python 3.12）

| ステップ | 内容 | ゲート根拠 |
|----------|------|------------|
| Checkout | `actions/checkout@v4` | — |
| Set up Python | `actions/setup-python@v5`（3.12, pip キャッシュ） | — |
| Install Dependencies | `requirements.txt` + `requirements-dev.txt` | Q4: B（pytest-cov ピン固定） |
| Verify Backend Routes & Imports | `import main` でルート一覧確認 | 起動スモーク |
| **Run Ruff Lint** | `ruff check app main.py scripts` | **Q6: C 追加** |
| **Run Mypy Type Check** | `mypy app main.py --ignore-missing-imports` | **Q6: C 追加** |
| Run Telemetry Verification | サーバー起動 + `scripts/check_telemetry.py` | 起動スモーク |
| **Run Pytest with Coverage** | `pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=80` | **Q4: B（行+branch 各 80%）** |
| Upload Backend Coverage Artifact | `backend/coverage.xml` | レポート保管 |

### 3.2 frontend-test（Ubuntu / Node.js 22）

| ステップ | 内容 | ゲート根拠 |
|----------|------|------------|
| Checkout | `actions/checkout@v4` | — |
| Set up Node.js | `actions/setup-node@v4`（22, npm キャッシュ） | — |
| Install Dependencies | `npm ci` | lockfile 固定 |
| Run ESLint | `npm run lint` | lint ゲート |
| **Run Vitest Tests with Coverage** | `npm run test`（thresholds 単一ソース化） | **NFR-1 / Q3: A（4 指標 80%）** |
| Upload Frontend Coverage Artifact | `frontend/coverage/` | レポート保管 |
| Build Next.js App | `npm run build`（`NEXT_PUBLIC_API_BASE_URL` 付与） | build ゲート |

## 4. カバレッジゲートの単一ソース化

- **frontend**: `vitest.config.mts` の `coverage.thresholds`（lines / functions / branches / statements 各 80）を
  単一ソースとし、ローカル `npm run test` と CI `npm run test` が同一ゲートを強制（NFR-1 / code-summary 逸脱 1）。
  CI 側の冗長 CLI フラグ（`--coverage.thresholds.*`）は撤去済み。
- **backend**: `--cov-branch --cov-fail-under=80` を CI とローカル実行で同一指定（Q4: B）。
  ローカル実測 99.60%（行+branch）を確認。

## 5. セキュリティ統制（補足）

- **Dependabot**（Q11: A）: 依存関係の脆弱性スキャン。GitHub ネイティブ機能として監視。
- **secret scanning**（Q12: B）: GitHub secret scanning でシークレット検知を自動化。
- シークレットは環境変数で注入し、`.env` は gitignore 管理（NEVER: シークレットコミット）。

## 6. 既知の制約

- **`ruff format` は今回導入しない**: 既存 8 ファイルの再整形（diff 大量発生）を避けるため、lint（`ruff check`）のみを
  CI ゲート化。format 導入は backend 側の別 Issue で検討する（memory.md Tradeoffs 参照）。
- **`scripts/` は mypy 対象外**: 検証・デモ用スクリプトのため、型チェックは実稼働コード（`app/` + `main.py`）に限定。
- **backend カバレッジは branch 80% を新規に要求**: ローカル実測で充足済み（99.60%）。今後 branch カバレッジが
  80% を下回る変更は CI でブロックされる。
