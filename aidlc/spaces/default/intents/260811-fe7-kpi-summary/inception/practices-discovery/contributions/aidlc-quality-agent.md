**Collaborator:** aidlc-quality-agent

## Contribution

Testing Posture・カバレッジツール・CI 品質ゲート・テスト/コードパターンの観点で、リードドラフト3点（`team-practices.md` / `discovered-rules.md` / `evidence.md`）を独立検証した。実リポジトリ（`conftest.py` / `test_kpi.py` / `api.test.ts` / `DashboardClient.test.tsx` / `vitest.config.mts` / `.github/workflows/ci.yml` / `package.json` / `requirements.txt` / `.gitignore` / `git ls-files`）と突き合わせた結果、ドラフトの主要な主張は裏付けられたが、カバレッジゲートの「ローカル/CI 乖離」と「指標の非対称性」という品質上重要なギャップが未検出だった。以下、統合可能な形で所見を示す。

### 1. 確認（ドラフトの正確性を裏付け）

- **TDD 厳守・`python -m pytest` 実行・80% ゲート・テスト分離** は実証済み。`conftest.py` の autouse `_reset_store`（function スコープで `reset_store()` を前後実行）により、session スコープの `client`（TestClient）を再利用してもテスト間隔離が担保される。
- **`test_kpi.py` の 4 クラス構成**（単価計算 → サマリ集計 → エンドポイント → スキーマ型制約）は確認。`TestKpiSummarySchema` が Pydantic の `ge=0` / strict / extra=forbid を ValidationError 送出で検証するのは、mypy 非導入下で型安全性を受入検証する project.md 学習（asc-c4）と整合する。
- **FE-7 ギャップ**: `page.tsx` の `MOCK_KPI_DATA` 硬コード、`api.ts` に `fetchKpiSummary` 未実装、`KpiData`（5 項目）とバックエンド `KpiSummary`（7 項目・`level1Count` 有・`today_detections` 無）の契約乖離をそれぞれ確認。`discovered-rules.md` の `NEVER: 実データで埋められる KPI カードにモック値（MOCK_KPI_DATA）を残すこと` は妥当。

### 2. 追加・訂正（Testing Posture へ反映が必要）

1. **カバレッジ指標の非対称性を明記する**。backend は行カバレッジのみ（`--cov-fail-under=80`）、frontend は lines / functions / branches / statements の 4 指標各 80%（ci.yml で確認）。ドラフトの「カバレッジ 80% 以上」は一様すぎる。branch は行より有意義な指標であり、バックエンドで branch を追加要求するかはインタビューで解消すべき（下記ギャップ 1）。
2. **frontend のカバレッジ閾値が `vitest.config.mts` に無く CI インラインのみ**。`package.json` の `test` は `vitest run` のため、ローカル `npm run test` は 80% ゲートを強制しない（CI のみ `--coverage.thresholds.*` を付与）。ローカルと CI で品質ゲートが乖離する。`vitest.config.mts` の `coverage.thresholds`（4 指標 80%）へ移し、ローカル実行と CI を一致させることを推奨。
3. **`pytest-cov` が `requirements.txt` に未ピン**。CI は `pip install pytest pytest-cov httpx` を別途実行しており、ローカルに pytest-cov が無い環境では `--cov=app` が動かずゲートを再現できない。dev 用 `requirements-dev.txt` 等でピン追加を推奨（スコープ外提案に当たるため承認を要する）。
4. **`backend/.coverage` が git 追跡されている**（`git ls-files` で確認）。カバレッジ実行のたびに diff ノイズを生む生成物。`.gitignore` へ `backend/.coverage`・`backend/coverage.xml`（CI 生成物）を追加することを推奨。なお `frontend/coverage/` は frontend/.gitignore の `/coverage` で既に除外済み（codekb の懸念 #10 は一部解消済み）。
5. **テストピラミッドの明示**: E2E レイヤーは存在しない（Playwright/Cypress 等なし）。TestClient エンドポイントテスト（test_kpi.py / test_alerts.py）+ フロント component テストが統合境界を実質カバーしており、project.md 学習 c1（Minimal 戦略で統合/性能/セキュリティ指示書スキップ）と整合する。デモスコープでは意図的な選択として Testing Posture に明記し、E2E を導入しないことをインタビューで確認（下記ギャップ 3）。
6. **CI スモークテストの追記**: ci.yml は `scripts/check_telemetry.py`（uvicorn 起動 → 検証）も実行している。Testing Posture の CI 記述に「起動スモークテスト（check_telemetry.py）」を一行追加すると網羅的になる。

### 3. FE-7 に紐づく将来テスト義務（quality voice）

ドラフトは後方視的（現状の実証）に留まっており、FE-7 で新設されるテスト面を前方視的に補う。

- **`fetchKpiSummary()` 新設時の単体テスト**: 7 フィールド（`total_sensors` / `level1_count` / `level2_count` / `level3_count` / `estimated_cost_saved_yen` / `is_estimate` / `assumption_doc`）の snake_case→camelCase 変換・ApiError 変換・非 axios エラー透過。`api.test.ts` の既存パターン（`vi.spyOn(apiClient, "get")` + `MOCK_*`）を踏襲する。
- **`KpiData` 型の契約整合**: バックエンド契約（7 項目・`level1Count` 追加・`todayDetections` 撤去）へ揃える型変更と、それに伴う `KpiSummary.test.tsx` の更新（level1Count カードの testId/label 追加・`todayDetections` カード撤去）。型二重定義の単一ソース化方針（feasibility c2）とも整合。
- **`MOCK_KPI_DATA` 撤去後の `page.test.tsx` 更新**: KPI 取得成功時（実値描画）と失敗時（スケルトン/空状態表示・架空数値を表示しない）の 2 経路を必須化。現在の page.test.tsx は `MOCK_KPI_DATA` 依存のため、撤去と同時に必ず書き換わる。
- **DashboardClient ポーリング拡張**: intent-capture c4 の「DashboardClient で fetchKpiSummary をポーリング」を採用する場合、既存 `DashboardClient.test.tsx` のフェイクタイマー + アンマウント時 clearInterval パターンを KPI 取得にも適用する（タイマー/クリーンアップの独立性検証は既存パターンがそのまま使える）。
- **受入条件の検証可能性**: Minimal 戦略に従い、FE-7 の各受け入れ条件（S 番号）にテスト 1 本を当てる。既存 `test_kpi.py` が S-1〜S-5 を 4 クラスで検証している前例に倣う。

### 4. インタビューで解消すべきギャップ

1. バックエンドに branch カバレッジを追加要求するか（現状は行のみ。KPI 集計に分岐があるため有意義だが、Minimal 戦略との兼ね合い）。
2. カバレッジ 80% 閾値を team/project ルールとして固定するか（evidence.md 未確定 #5 と一致）。
3. デモまで E2E 層を導入しない方針でよいか（TestClient + component テストを統合境界の上限とする）。
4. Python リント（ruff/mypy）導入意向。導入するなら CI ゲート追加を Testing Posture へ反映し、現状の「Pydantic ランタイムテストで型安全性を代替」を維持するかを確認。
5. `pytest-cov` のピン追加・`backend/.coverage` の .gitignore 追加を承認するか（いずれもスコープ外提案の可能性）。

## Positions

- AGREE: TDD 厳守・`python -m pytest` 実行・80% ゲート・`_reset_store` によるテスト分離の記述 — リポジトリ実証（conftest.py / ci.yml / test_kpi.py）で裏付けられている。
- AGREE: `MOCK_KPI_DATA` 撤去と NEVER ルール（モック値非表示）— feasibility c5 と整合し、受け入れ条件として検証可能。
- OBJECT: 「カバレッジ 80% 以上」の一様な記述 — backend は行のみ・frontend は 4 指標で非対称。Testing Posture の正確化が必要。
- OBJECT: Mandated の「バックエンド停止時はフォールバックを用意」の文言 — 架空数値（モック値）の表示を許容すると NEVER（モック値非表示）と矛盾する。フォールバックは「スケルトン/空状態」に限定する旨を明記すべき。
- OBJECT: カバレッジゲートのローカル/CI 乖離（vitest.config.mts 未設定・pytest-cov 未ピン・backend/.coverage 追跡）が未検出 — 品質ゲートの再現性とリポジトリ衛生に影響するため統合してほしい。
