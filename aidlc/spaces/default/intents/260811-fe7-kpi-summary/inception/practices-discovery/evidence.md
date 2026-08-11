# 調査・推測の記録（evidence）— FE-7 KPIサマリ実データ連携

> Practices Discovery の調査記録。Step 2（リードドラフト）の時点で git / CI / codekb から
> 「確定・推測・未確定」を整理し、Step 5（Lead Integration）で Step 3 の盲検レビュー
> （quality / developer / devsecops）と Step 4 のインタビュー回答（Q1〜Q12）を統合して
> 最終化した。「確定」は証拠またはインタビュー回答で裏付け、「推測」は証拠から導いた解釈、
> 「未確定」は解決に至っていない事項を示す。

## 調査日時

- 初回調査: 2026-08-11T07:03:45Z
- 最終統合: 2026-08-11T07:17:07Z（HEAD: `78303016d5734789d5e0d5be251376f28ec0ec30`）

## 調査したソース

| # | ソース | パス |
|---|--------|------|
| 1 | codekb: コード構造 | `aidlc/spaces/default/codekb/smartwater-guardian/code-structure.md` |
| 2 | codekb: テクノロジースタック | `aidlc/spaces/default/codekb/smartwater-guardian/technology-stack.md` |
| 3 | codekb: 依存関係 | `aidlc/spaces/default/codekb/smartwater-guardian/dependencies.md` |
| 4 | codekb: コード品質評価 | `aidlc/spaces/default/codekb/smartwater-guardian/code-quality-assessment.md` |
| 5 | codekb: アーキテクチャ | `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md` |
| 6 | codekb: ビジネス概要 | `aidlc/spaces/default/codekb/smartwater-guardian/business-overview.md` |
| 7 | git 履歴 | `git log --oneline -30` / `git log --merges` / `git branch -a` |
| 8 | CI 設定 | `.github/workflows/ci.yml` |
| 9 | プロジェクト状態 | `aidlc/spaces/default/intents/260811-fe7-kpi-summary/aidlc-state.md` |
| 10 | スコープ成果物 | `ideation/scope-definition/scope-document.md`・`intent-backlog.md` |
| 11 | quality contribution | `contributions/aidlc-quality-agent.md` |
| 12 | developer contribution | `contributions/aidlc-developer-agent.md` |
| 13 | devsecops contribution | `contributions/aidlc-devsecops-agent.md` |
| 14 | インタビュー回答 | `practices-discovery-questions.md`（`## 回答`） |

## 確定（証拠で裏付け）

- **プロジェクト種別**: Brownfield（`aidlc-state.md` の `Project Type: Brownfield`）。スコープは `feature`。
- **モノレポ構成**: `backend/`（FastAPI・Pydantic v2 strict）・`frontend/`（Next.js App Router / TS strict）・
  `docs/`・`.github/workflows/ci.yml` が同一リポジトリ。
- **CI ゲート**: `.github/workflows/ci.yml` は main への push / PR で実行。
  - backend: Python 3.12 / `python -m pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-fail-under=80`。
  - frontend: Node 22 / `npm ci` / `npm run lint` / `npx vitest run --coverage`（各 80%）/ `npm run build`。
  - 起動スモークテスト `scripts/check_telemetry.py` も実行（quality contribution #6）。
- **デプロイパイプラインは不在**: `.github/workflows/` は `ci.yml` のみ。CD ワークフローなし。
- **ブランチ戦略**: git 履歴は main への直接コミットが主体。`Merge pull request #24 from
  taka0928eye/feature/be-2-sensor-simulator-pr` のマージコミットと、ローカルに
  `feat/FE-3-sensor-map`・`feature/be-2-sensor-simulator-pr`・`feature/fe-5-alert-list` の短命
  フィーチャーブランチを確認（trunk-based + 時折のフィーチャーブランチ/PR）。
- **コミットメッセージ規約**: `feat:` / `fix:` / `docs:` / `ci:` の Conventional Commits 形式で、
  BE-x / FE-x の Issue 参照付き（例: `feat: BE-8: KPI「推定削減コスト」...`）。
- **Python リント未導入（統合時点）**: codekb に ruff / mypy / pyproject.toml は未導入と明記。
  → **Q6: C で ruff + mypy 導入・CI ゲート追加を決定**（下記「インタビューで確定した事項」参照）。
- **フロントのカバレッジ閾値**: `vitest run --coverage` で lines / functions / branches / statements 各 80%
  （ci.yml にインラインのみ。`vitest.config.mts` には未設定）。
- **`any` 使用なし**: code-quality-assessment に「`any` 使用なし」と明記。
- **テスト分離**: `conftest.py` の autouse `_reset_store`（function スコープ）でテスト間隔離を担保
  （quality contribution #1）。
- **FE-7 ギャップ**: `page.tsx` の `MOCK_KPI_DATA` 硬コード、`api.ts` に `fetchKpiSummary` 未実装、
  `KpiData`（5 項目）とバックエンド `KpiSummary`（7 項目・`level1Count` 有・`today_detections` 無）の
  契約乖離（quality contribution #1・developer contribution #3）。

## 推測（証拠から導いた解釈）

- **Walking Skeleton は対象外**: アクティブスコープの `scope-document.md` は `skeleton: on` を宣言しておらず、
  Brownfield かつアプリが end-to-end で動作済み（BE-8 実装済み）のため、薄い縦スライスの追加検証は不要。
  → **Q2: A で確定**（下記参照）。
- **デプロイ方式は手動・ローカル**: CD 不在・`uvicorn`/`npm run dev`・`npm run build` の使用から、
  デモスコープ（8/10〜8/15）の手動デプロイと判断。本番ロールバック手順は未定義。
  → **Q7: X で「ローカル実行のまま、余裕があれば AWS へデプロイ」と確定**（下記参照）。
- **TDD の実践**: CLAUDE.md §1 の TDD 徹底方針に加え、`test_kpi.py` が
  「単価計算 → サマリ集計 → エンドポイント（TestClient）→ スキーマ型制約」を 4 クラスで検証する
  構成から、テストファースト開発が実践されていると判断。
- **エラーハンドリング / レイヤー境界の暗黙規約**: `kpi.py` の「HTTPException を上げず 500 にしない」、
  `lib/api.ts` の `unwrap()` による `ApiError` 変換、`useAlertPolling` の最終状態据え置き、
  store 3 層分離・`@lru_cache(maxsize=1)` マスタローダーが実コードに一貫して存在
  （developer contribution #1・#2）。
  → **Q8: A で Code Style への明文化を確定**（下記参照）。

## インタビューで確定した事項（Step 4 回答による未確定→確定）

1. **ブランチ戦略（Q1: A）**: main 直コミット中心を明文化。短命フィーチャーブランチ + PR は
   大規模変更・共同作業時のみ。
2. **Walking Skeleton（Q2: A）**: 本スコープでは実施しない（ドラフトのまま確定）。
3. **カバレッジゲートのローカル/CI 一致（Q3: A）**: `vitest.config.mts` の `coverage.thresholds` 設定・
   `pytest-cov` の `requirements-dev.txt` ピン・`backend/.coverage` の `.gitignore` 追加を承認。
4. **バックエンド branch カバレッジ（Q4: B）**: backend にも branch カバレッジ 80% を要求。
5. **E2E（Q5: A）**: デモまで導入しない。TestClient + component テストを統合境界の上限とする。
6. **Python リント（Q6: C）**: ruff + mypy を導入し CI ゲートに追加。
7. **デモ受け渡し（Q7: X）**: ひとまずローカル実行のまま、余裕があれば AWS にデプロイ。
8. **エラーハンドリング / レイヤー境界の規約化（Q8: A）**: Code Style に明文化（developer 提案を統合）。
9. **`SeverityLevel` 単一ソース表記（Q9: A）**: 「FE-7 で実施予定」と明記し、現状の二重定義と区別。
10. **フォールバック限定（Q10: A）**: スケルトン / 実マスタ由来に限定し、固定 KPI 数値モック
    （`MOCK_KPI_DATA`）は実データの代わりに使わない。
11. **依存脆弱性スキャン（Q11: A）**: Dependabot のみ有効化（最小導入）。
12. **シークレット検知（Q12: B）**: GitHub secret scanning を有効化。

## 既知のセキュリティ負債（devsecops contribution より）

- **CORS ハードコード**（`backend/main.py:10`）: `allow_origins=["http://localhost:3000"]`・
  `allow_credentials=True`・`allow_methods=["*"]`・`allow_headers=["*"]`。固定オリジンなのでデモでは
  機能上安全だが、`allow_credentials=True` と組み合わせて `*` にしてはならない。ホスティング時に
  環境変数化（`ALLOWED_ORIGINS`）する方針で既知負債として記録（codekb code-quality-assessment #9 と整合）。
- **CI 内の unpinned install**（`ci.yml` の `pip install pytest pytest-cov httpx`）: バージョン未指定で
  サプライチェーンの再現性がやや劣る。**Q3: A で `pytest-cov` の `requirements-dev.txt` ピンが承認されたため**
  部分的に解消に向かうが、`pytest` / `httpx` を含む全体の `requirements-dev.txt` 化は将来提案として残る。
- **依存脆弱性・シークレット・SAST は統合時点で未整備**（Dependabot / secret scanning / bandit 等なし）。
  → Q11: A（Dependabot 有効化）・Q12: B（GitHub secret scanning 有効化）で最小導入を決定。

## 未確定・未解決（Step 5 統合後も残る事項）

1. **AWS デプロイの具体的サービス**: Q7 で「余裕があれば AWS へデプロイ」は確定したが、具体的な
   サービス（ECS / Elastic Beanstalk / Amplify 等）と手順は未定。デモ完成後に再評価する。
2. **DAST**: デプロイ環境（staging）が存在せずローカル実行のみのため現状 N/A。将来ホスティング環境が
   できた時点で OWASP ZAP 等を再評価する（devsecops contribution #4）。
3. **Python SAST（bandit 等）**: Q6 で ruff + mypy は決定したが、セキュリティ SAST はデモスコープでは
   導入しない方針（非ブロッキング警告としての導入か、スコープ外として明記するかは未決）。
4. **`MOCK_KPI_DATA` 撤去の実装タイミング**: 撤去と実データ（BE-8）への置換は FE-7 スコープで確定済み
   （Q10: A・モック非残置の NEVER）だが、具体的なコミットは実装依存（推測のまま）。

## 参照

- org.md 既定（`aidlc/spaces/default/memory/org.md`）: trunk-based / squash-merge、Walking Skeleton は
  `skeleton: on` 時のみ、テストは 80% 以上、デプロイは merge 時 staging。本ドラフトはこれを参照しつつ、
  あくまで実リポジトリの証拠（git/CI/codekb）とインタビュー回答から書いた。
- 既存ルール: `memory/team.md` は空（既存 affirmation なし）。`memory/project.md` に learning 由来の
  プラクティスあり（pytest 実行方法・KPI 配線方式等）。これらは本ドラフトの Testing Posture に反映済み。
