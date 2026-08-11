# Phase Check — Construction → Operation（境界検証）

> Construction フェーズから Operation フェーズへのハンドオフ前に、Architecture → Code → Tests の整合と
> CI 品質ゲートの充足を検証する。検証時点: 2026-08-11（ci-pipeline ステージ完了）。
> 参照: `ci-config.md` / `quality-gates.md` / `build-test-results.md` / `code-summary.md` / `requirements.md`。

## 1. Architecture → Code → Tests の整合

| 検証項目 | 結果 | 根拠 |
|---|---|---|
| 全コードが設計（functional-design / application-design）にトレース | ✅ トレース | `code-summary.md` の生成・変更 14 ファイルが functional-design（business-logic-model / frontend-components）と application-design の ADR（C-1〜C-6 等）に対応 |
| FE-7 の FR がすべて実装済み | ✅ 充足 | FR-1（KpiSummary 型）〜 FR-8（スケルトン表示）を `code-summary.md` のファイル・実装決定と1対1で確認 |
| NFR-1（カバレッジ）が CI ゲートで強制 | ✅ 強制 | `vitest.config.mts` thresholds（4 指標各 80）を単一ソースとし、CI `npm run test` とローカル実行が一致（NFR-1 / Q3: A） |
| NFR-2（build / lint / test）が CI で強制 | ✅ 強制 | frontend-test ジョブ: `npm run lint` / `npm run test` / `npm run build`（ci-config.md §3.2） |
| テストカバレッジが受入条件を充足 | ✅ 充足 | frontend 4 指標（93.15 / 84.15 / 90.12 / 94.05%）・backend branch 込み 99.60%（build-test-results.md / 本ステージ実測） |
| C-1〜C-5（スコープ・Server Component・変換境界・モック非残置・デモ期限）が順守 | ✅ 順守 | code-summary.md「逸脱」で承認済みの vitest.config.mts / ci.yml スコープ追加のみ。`MOCK_KPI_DATA` は page.tsx から撤去済み |

## 2. テストの統合境界（フロント内部）

| 検証項目 | 結果 | 根拠 |
|---|---|---|
| 統合境界の定義 | ✅ フロント内部 | page.tsx → DashboardClient → KpiSummary / useKpiPolling → lib/api の連携（build-and-test:c4 学習） |
| 実ネットワーク統合の代替 | ✅ component テスト | DashboardClient.test.tsx / page.test.tsx が `vi.mock("@/lib/api")` で統合境界をカバー |
| バックエンド統合の担保 | ✅ 既存で充足 | backend `test_alerts.py` が BE-8 で TestClient 統合を実質カバー（132 テスト Green） |

## 3. CI 品質ゲートと確定プラクティスの整合（本ステージの主検証）

| 品質ゲート | 確定プラクティス | CI 反映 | 実測 |
|---|---|---|---|
| フロントカバレッジ 4 指標 80% | Q3: A / NFR-1 | ✅ `npm run test`（thresholds 単一ソース） | 93.15 / 84.15 / 90.12 / 94.05% |
| backend 行 + branch 各 80% | Q4: B | ✅ `--cov-branch --cov-fail-under=80` 追加（本ステージ） | 99.60%（行+branch） |
| ruff + mypy 導入・CI ゲート | Q6: C | ✅ `ruff check` / `mypy` ステップ追加（本ステージ） | ruff: All checks passed / mypy: no issues |
| pytest 実行方式 | python -m pytest（pytest.exe 不使用） | ✅ CI は `python -m pytest` で実行 | 132 passed |
| pytest-cov ピン固定 | Q4: B | ✅ `requirements-dev.txt` に `pytest-cov==7.1.0` | 導入済み |
| backend/.coverage を gitignore | Q4: B | ✅ `.gitignore` に追加（本ステージ） | — |
| 依存スキャン（Dependabot） | Q11: A | ✅ GitHub ネイティブ | — |
| secret scanning | Q12: B | ✅ GitHub ネイティブ | — |

## 4. Operation フェーズへの引き継ぎ

- **デモの受け渡しはローカル実行を主**（team.md Deployment / Q7）。`uvicorn` 起動（backend）と `npm run dev`（frontend）の手順は
  `build-instructions.md` に記録済み。AWS デプロイは余裕があれば検討（本スコープ外）。
- **本番 CD パイプラインは未整備**。Operation フェーズの deployment-pipeline ステージで、ローカル実行・デモ受け渡しの
  方針を踏襲したデプロイ手順の設計を期待。
- **CI は main への push / PR で全ゲートを強制**。デモ期間中の回帰（MOCK_KPI_DATA 再混入・カバレッジ低下・lint/type 違反）を
  CI がブロックする。

## 総合判定

**✅ パス（Operation フェーズへの進行を許可）。** Architecture → Code → Tests の整合、FE-7 の FR/NFR 充足、
CI 品質ゲートの確定プラクティス（Q3/Q4/Q6）反映とも満たしている。本ステージで backend の ruff+mypy 導入と
branch カバレッジを CI ゲートに追加し、ローカル実測で全ゲートの通過を確認した。実装ブロッカー（Critical）なし。

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜FR-8 / NFR-1〜NFR-5 / C-1〜C-5）
- [code-summary] `construction/BU-1/code-generation/code-summary.md`（生成・変更 14 ファイル / 逸脱）
- [build-and-test-summary] `construction/build-and-test/build-and-test-summary.md`（レディネス評価）
- [build-test-results] `construction/build-and-test/build-test-results.md`（frontend 実測 4 指標）
- [ci-config] `construction/ci-pipeline/ci-config.md`（ジョブ構成 / ゲート単一ソース化）
- [quality-gates] `construction/ci-pipeline/quality-gates.md`（G1〜G8 / 実測）
- [team-practices] `inception/practices-discovery/team-practices.md`（Q1〜Q12）
- [questions] `construction/ci-pipeline/ci-pipeline-questions.md`（Q1〜Q3 リード導出 / Q4 ユーザー回答 C）
