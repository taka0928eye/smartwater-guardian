# Quality Gates — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> ステージ: ci-pipeline（Construction）| リード: aidlc-pipeline-deploy-agent | 日時: 2026-08-11
> 上流成果物: build-and-test-summary（build-and-test）、team.md（Q3/Q4/Q6 確定）、project.md（Mandated 学習）

## 1. ゲート一覧

CI（`.github/workflows/ci.yml`）が main への push / PR で強制する品質ゲート。ローカル実行と CI でゲートを一致させる。

| # | ゲート | 対象 | 閾値 | ローカルコマンド | CI ジョブ |
|---|--------|------|------|------------------|-----------|
| G1 | **ESLint** | frontend | エラー 0・警告 0 | `npm run lint` | frontend-test |
| G2 | **フロントカバレッジ** | frontend | lines / functions / branches / statements **各 80%**（`vitest.config.mts` 単一ソース） | `npm run test` | frontend-test |
| G3 | **Next.js ビルド** | frontend | `npm run build` 成功（コンパイル + TS 型検査 + 静的生成） | `npm run build` | frontend-test |
| G4 | **Ruff Lint** | backend（`app/` `main.py` `scripts/`） | 違反 0 | `ruff check app main.py scripts` | backend-test |
| G5 | **Mypy 型検査** | backend（`app/` `main.py`） | エラー 0（`--ignore-missing-imports`） | `mypy app main.py --ignore-missing-imports` | backend-test |
| G6 | **バックエンドカバレッジ** | backend（`app/`） | 行 + branch **各 80%**（`--cov-branch --cov-fail-under=80`） | `python -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80` | backend-test |
| G7 | **バックエンドテスト** | backend | 全テスト Green（132 テスト） | 同上 | backend-test |
| G8 | **起動スモーク** | backend | `import main` ルート一覧 + `scripts/check_telemetry.py` 成功 | 手動実行 | backend-test |

## 2. カバレッジゲートの根拠（Q3 / Q4 確定）

- **Q3: A** — カバレッジゲート（80% 以上）はローカル実行と CI で一致させる。
- **Q4: B** — backend は「行 + branch の各 80%」（`--cov=app --cov-branch --cov-fail-under=80`）。
  `pytest-cov` は `requirements-dev.txt` でピン固定（7.1.0）。
- frontend は `vitest.config.mts` の `coverage.thresholds`（4 指標各 80）を単一ソースとする（NFR-1）。

## 3. 静的チェックの根拠（Q6: C 確定）

- backend に **ruff + mypy を導入し、CI ゲートに追加**（本ステージで実装）。
  - ruff: lint（`ruff check`）。format は既存 8 ファイルの再整形を避けるため導入保留（backend 別 Issue で検討）。
  - mypy: 実稼働コード `app/` + `main.py` を対象。`scripts/`（検証・デモ用スクリプト）は型チェック対象外。
- 型安全性は ruff / mypy の静的チェックと、Pydantic v2（strict / extra=forbid）のランタイムテスト（ValidationError 送出）の両輪で担保。

## 4. 品質ゲートでブロックされるもの

- テスト・カバレッジ・lint・build が成功していないコードの main へのマージ（NEVER 確定 / project.md）
- `any` の使用（NEVER 確定 / TypeScript・Python 双方）
- 認証・権限管理 / 物理 IoT 通信 / リアルタイム通知 / 本番用大型 GIS DB の実装（NEVER 確定）
- 実データで埋められる KPI カードへのモック値（`MOCK_KPI_DATA`）残存（NEVER 確定）
- シークレット・API キーのリポジトリコミット（NEVER 確定。`.env` は gitignore）

## 5. 実測検証（2026-08-11）

| ゲート | 実測結果 |
|--------|----------|
| G4 Ruff | `All checks passed`（15 件自動修正後） |
| G5 Mypy | `Success: no issues found in 18 source files`（sensors.py Literal 型修正後） |
| G6 バックエンドカバレッジ | branch 込み **99.60%**（行 + branch 各 80% 超過） |
| G7 バックエンドテスト | **132 passed** |
| G2 フロントカバレッジ | Statements 93.15% / Branches 84.15% / Functions 90.12% / Lines 94.05%（build-and-test 実測） |
| G3 Next.js ビルド | `Compiled successfully`（build-and-test 実測） |
| G1 ESLint | PASS（build-and-test 実測） |

## 6. 本スコープ外（backend 側で対応予定）

- `ruff format` の導入（既存コード再整形）
- backend の型チェック対象拡張（`scripts/` を含めるか検討）
