# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

- Minimal テスト戦略では統合・性能・セキュリティのテスト指示書はスキップする（produces リストは最大集合で戦略により絞られる）。 (learned 2026-08-11) <!-- cid:build-and-test:c1 -->
- pytest は `venv/Scripts/pytest.exe` でなく `venv/Scripts/python.exe -m pytest` で実行する（pytest.exe は cwd を sys.path に挿入せず `app` を import できないため）。 (learned 2026-08-11) <!-- cid:build-and-test:c3 -->
- Minimal 戦略で統合テスト指示書を生成しない判断は、TestClient のエンドポイントテスト（test_alerts.py）が統合境界を実質カバーしていることを根拠にする。 (learned 2026-08-11) <!-- cid:build-and-test:c4 -->
- プロジェクトに mypy 等の静的型チェッカーが存在しない場合、型安全性の受入条件は Pydantic の型制約（Literal等）が実際に ValidationError を送出することを検証するランタイムテストで代替する。 (learned 2026-08-11) (learned 2026-08-11) <!-- cid:code-generation:asc-c4 -->
- 2 段構成の表示（見出しラベル + 本文注記、例: 試算値）のテストは、連結文字列の部分一致でなくカード内スコープの順序検証（正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/`）で検証する。 (learned 2026-08-11) <!-- cid:application-design:c2 -->
- テスト戦略は aidlc-state.md の `**Test Strategy**` に従う。Standard 戦略では performance / security テスト指示書を生成しない（Comprehensive 戦略限定。build-and-test.md Step 4-8。produces は最大集合で戦略により絞られる）。 (learned 2026-08-11) <!-- cid:build-and-test:bt-standard-strategy -->
- フロントは外部 API（axios）を `vi.mock` で境界モックするため実ネットワーク統合を持たない。既存の component テスト（DashboardClient.test.tsx / page.test.tsx）が事実上の統合境界テストを担うため、integration テスト指示書はそれらを再利用・整理して記載する。 (learned 2026-08-11) <!-- cid:build-and-test:bt-component-integration -->
- フロントエンドのみの変更では、integration テスト指示書の統合境界を「バックエンド TestClient に対する統合」でなくフロント内部境界（page.tsx → DashboardClient → KpiSummary / useKpiPolling → lib/api の連携）として定義する。バックエンド統合は既存 test_alerts.py が BE-8 で実質カバー済み。 (learned 2026-08-11) <!-- cid:build-and-test:bt-frontend-integration -->
## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

## Decided

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

- NEVER: TypeScript / Python コードで `any` を使用すること。 (affirmed 2026-08-11)
- NEVER: 認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB を実装すること。 (affirmed 2026-08-11)
- NEVER: デモスコープで本番用 DB やクラウドインフラを導入すること (affirmed 2026-08-11)
（インメモリストア + JSON マスタでデモを成立させる）。 (affirmed 2026-08-11)
- NEVER: テスト・カバレッジ・lint・build が成功していない状態のコードを main へマージすること。 (affirmed 2026-08-11)
- NEVER: 実データで埋められる KPI カードにモック値（`MOCK_KPI_DATA`）を残すこと。 (affirmed 2026-08-11)
- NEVER: 本番または共有リポジトリへシークレット・API キーをコミットすること (affirmed 2026-08-11)
（実キーは環境変数/シークレット管理で注入し、`.env` は gitignore で管理する）。 (affirmed 2026-08-11)
## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

- ALWAYS: ドキュメント・会話・コメント・docstring・コミットメッセージは**日本語**で書くこと。 (affirmed 2026-08-11)
- ALWAYS: コード作成前に必ず失敗テストを書き、TDD（Red → Green → Refactor）のサイクルを順守すること。 (affirmed 2026-08-11)
- ALWAYS: バックエンドの入力検証は **Pydantic v2（strict / extra=forbid）** を使用すること。 (affirmed 2026-08-11)
- ALWAYS: テストカバレッジ **80% 以上**を維持し、**カバレッジゲートをローカル実行と CI で一致させる**こと (affirmed 2026-08-11)
（Q3: A 承認済み）。backend は **行 + branch の各 80%**（`--cov=app --cov-branch --cov-fail-under=80`、 (affirmed 2026-08-11)
Q4: B 確定）、frontend は lines / functions / branches / statements の各 80% (affirmed 2026-08-11)
（`vitest.config.mts` の `coverage.thresholds` で設定）。`pytest-cov` は `requirements-dev.txt` で (affirmed 2026-08-11)
ピン固定し、`backend/.coverage` は `.gitignore` に追加すること。 (affirmed 2026-08-11)
- ALWAYS: バックエンドのテストは `python -m pytest` で実行すること（pytest.exe 不使用）。 (affirmed 2026-08-11)
- ALWAYS: バックエンドに **ruff + mypy を導入し、CI ゲートに追加**して静的チェックを実施すること (affirmed 2026-08-11)
（Q6: C 確定）。 (affirmed 2026-08-11)
- ALWAYS: コミットメッセージは Conventional Commits 形式（`feat:` / `fix:` / `docs:` / `ci:`）で (affirmed 2026-08-11)
Issue/ステージ参照（BE-x / FE-x）を添えること。 (affirmed 2026-08-11)
- ALWAYS: ブランチ戦略は **main 直コミット中心（trunk-based）**とし、短命フィーチャーブランチ + PR は (affirmed 2026-08-11)
**大規模変更・他者レビュー・共同作業が必要な場合のみ**使用すること（Q1: A 確定）。 (affirmed 2026-08-11)
- ALWAYS: フロント↔バックエンドの `snake_case`→`camelCase` 変換は `lib/api.ts` 境界で 1 回だけ行うこと。 (affirmed 2026-08-11)
- ALWAYS: バックエンド停止中でも画面を白紙にせず、**スケルトン表示（または実マスタ由来データ）に (affirmed 2026-08-11)
フォールバック**すること。フォールバックは表示崩れ防止を目的とし、**固定の KPI 数値モック (affirmed 2026-08-11)
（`MOCK_KPI_DATA` 等）を実データの代わりに表示する用途には使わない**こと（Q10: A 確定）。 (affirmed 2026-08-11)
- ALWAYS: 依存関係の脆弱性スキャンとして **Dependabot を有効化**すること（Q11: A 確定）。 (affirmed 2026-08-11)
- ALWAYS: **GitHub secret scanning を有効化**し、シークレット検知を自動化すること（Q12: B 確定）。 (affirmed 2026-08-11)
## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->
- 最小スコープで scope-document / intent-backlog が存在しなくても、イニシアティブ・ブリーフは既存成果物とリポジトリ実態で整合を担保できる。 (learned 2026-08-11) <!-- cid:approval-handoff:c1 -->
- ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->
- pipe_id 等の識別子は Issue 例示よりマスタ（hydrants.json）と整合する形式を優先する（変換不要で照合信頼性が高い）。 (learned 2026-08-11) <!-- cid:approval-handoff:c3 -->
- 単一イテレーションのダイレクティブで unit-of-work が存在しないため、`{unit-name}` を `be4-ledger` に解決して記録パスを決定。 (learned 2026-08-11) <!-- cid:code-generation:c1 -->
- 「モジュールロード時のキャッシュ」は store.py の `@lru_cache(maxsize=1)` 先例に合わせ、初回呼び出し時に読み込んで以後キャッシュする設計と解釈（「リクエスト毎の再読み込みをしない」要件を満たし、テスト分離も壊さない）。 (learned 2026-08-11) <!-- cid:code-generation:c2 -->
- store.py は欠損を RuntimeError で包むが、受け入れ条件が FileNotFoundError / ValueError の明示指定の場合は、ledger.py のようにそのまま伝播・変換する。 (learned 2026-08-11) <!-- cid:code-generation:c3 -->
- find_nearest_pipe は路線の LineString 頂点との Haversine 最小距離で判定する（路線全体の中心点方式より、消火栓位置に近い頂点を考慮でき直感的）。 (learned 2026-08-11) <!-- cid:code-generation:c4 -->
- バックエンド Python のビルドは「依存導入の確認 + アプリ import スモークテスト + 検証スクリプト実行」で定義する（コンパイル工程がないため）。フロントエンドは変更対象外なら対象外と明記する。 (learned 2026-08-11) <!-- cid:build-and-test:c2 -->
- unit-of-work が存在しない単一イテレーションのディレクティブでは、`{unit-name}` を intent slug に解決して記録パスを決定する（be4-ledger 案件の先例を踏襲）。 (learned 2026-08-11) (learned 2026-08-11) <!-- cid:code-generation:asc-c1 -->
- codekb のスナップショットは reverse-engineering 時点で固定されるため古くなりうる。Code Generation で「重複解消」等の既存コード状態に依存するプラン項目は、実装前に grep 等で現状を再確認してから着手する。 (learned 2026-08-11) (learned 2026-08-11) <!-- cid:code-generation:asc-c2 -->
- docstring/コメント陳腐化の修正依頼は、requirements.md の FR が明示する対象クラス・箇所のみに限定して実装し、同種の陳腐化が他に見つかった場合はスコープ外として承認ゲートの確認事項に明記する（無断で拡大も無視もしない）。 (learned 2026-08-11) (learned 2026-08-11) <!-- cid:code-generation:asc-c3 -->
- KPI配線は Issue 推奨の「DashboardClient で fetchKpiSummary をポーリングし KpiSummary を配下に描画」を Q2 で確認。page.tsx は Server Component のまま維持。 (learned 2026-08-11) <!-- cid:intent-capture:c2 -->
- `today_detections` はバックエンドスキーマ上 FE-7 以降の対応とされているため本件対象外と明記。 (learned 2026-08-11) <!-- cid:intent-capture:c3 -->
- Q2 の配線方式は A（DashboardClient ポーリング）を採用。B（Server 側1回 fetch）の方が実装は単純だが、アラートと KPI の更新タイミングを揃える Issue 推奨を優先した。 (learned 2026-08-11) <!-- cid:intent-capture:c4 -->
- 外部 BI・可視化ツールの導入は build-vs-buy の評価対象外（既存 Next.js/Recharts スタックとの一貫性を優先）。将来、ダッシュボードの可視化要求が高度化した場合に再評価する。 (learned 2026-08-11) <!-- cid:market-research:c3 -->
- 型の二重定義の単一ソース化は、表示メタ（SEVERITY_META 等）と同居するユーティリティ層を本拠とし、契約層から re-export する方針で進める（Issue 指定・intent-statement 成功指標の根拠を優先）。 (learned 2026-08-11) <!-- cid:feasibility:c2 -->
- デモ評価者向け内部機能・PIIなし・認証スコープ外の実装では、規制・コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー）は N/A として扱い、質問も省略する。 (learned 2026-08-11) <!-- cid:feasibility:c3 -->
- 実データ不在のカードは削除し、実データで埋められるカード（例: BE-8 が返す level1_count）を追加する構成に揃える。モック値の表示を残さない。 (learned 2026-08-11) <!-- cid:feasibility:c5 -->
- 共通型の単一ソース化は、型とその表示メタ（SEVERITY_META / getSeverityColor 等）が同居するユーティリティ層を本拠にする。 (learned 2026-08-11) <!-- cid:feasibility:c6 -->
- 相互依存する複数ファイルの変更（1 Issue 完結）は、分割せず単一 proto-Unit として扱う。スコープ管理・受入条件検証が容易になる。 (learned 2026-08-11) <!-- cid:scope-definition:c1 -->
- 実装順序は依存先順（型 → APIクライアント → 表示）で進める。TDD（Red→Green）と整合し、テストも同順に追加できる。 (learned 2026-08-11) <!-- cid:scope-definition:c2 -->
- 単一 Issue 完結のスコープでは、バックログの優先度をすべて Must-have として扱う（Should-have 分離は不要）。 (learned 2026-08-11) <!-- cid:scope-definition:c5 -->
- 上流レビュー（advisory）で残った Major 指摘は修正ループに回さず、次段の成果物（例: イニシアティブ・ブリーフ）で解決・明記して引き継ぐ（無断で拡大も無視もしない）。 (learned 2026-08-11) <!-- cid:approval-handoff:c6 -->
- プロジェクト種別が Brownfield の Reverse Engineering は pipeline モード（developer スキャン → architect 合成の2リンクチェーン）で実行し、contribution ファイルは作成しない。 (learned 2026-08-11) <!-- cid:reverse-engineering:c1 -->
- codekb 既存ストアが CURRENT でも分析済みパスが本イニシアティブの対象外なら、reuse は選択肢に提示せず rescan vs focused のみ提示する（partial カバレッジのストア再利用はスコープ外知識の混入を招く）。 (learned 2026-08-11) <!-- cid:reverse-engineering:c2 -->
- プロジェクト種別は Brownfield（aidlc-state.md 確認）。Step 1 の再実行コンテキスト用 team.md は空のため、今回は既存 affirmation なしの初回として進める。証拠源は reverse-engineering の codekb（code-structure / technology-stack / dependencies / code-quality-assessment / architecture / business-overview の6点）と git 履歴・CI 設定。 (learned 2026-08-11) <!-- cid:practices-discovery:c1 -->
- Step 4 インタビュー完了。12問中、ブランチ戦略(A)・WS不実施(A)・カバレッジゲート固定(A)・branch80%(B)・E2E不導入(A)・ruff+mypy導入(C)・デモはローカル実行のままAWS余裕時(C)・規約化(A)・SeverityLevel FE-7実施予定表記(A)・フォールバック限定(A)・Dependabotのみ(A)・secret scanning有効化(B)と回答。特に Python リント導入（C: ruff+mypy）と backend branch カバレッジ（B）は、Minimal 戦略のデモスコープを超える追加投資の承認として有意。 (learned 2026-08-11) <!-- cid:practices-discovery:c2 -->
- Step 5 リード統合完了。3 contribution とインタビュー回答を統合し、4 宣言成果物を最終化。team-practices.md（5セクション最終版・Q1〜Q12 反映）、discovered-rules.md（Mandated 12件・Forbidden 6件）、evidence.md（確定/推測/未確定 をインタビュー結果で解決、CORS ハードコード等を既知負債として明記）、practices-discovery-timestamp.md（`Discovered: 2026-08-11T07:17:07Z at commit 78303016...`）。`PRACTICES_DISCOVERED` イベント発行済み。 (learned 2026-08-11) <!-- cid:practices-discovery:c3 -->
- リード（aidlc-pipeline-deploy-agent）のディスパッチがモデル解決で失敗（セッション開始時に `model: sonnet` としてキャッシュされ、`claude-sonnet-5` への解決が続くため 503。ファイル編集は次のセッションで反映される）。一般用途エージェント（general-purpose、セッションモデル継承）に `.claude/agents/aidlc-pipeline-deploy-agent.md` のペルソナを自己ロードさせてリード作業を代行した。support 3 名は開始時点で `inherit` のため影響なし。 (learned 2026-08-11) <!-- cid:practices-discovery:c4 -->
- モデル解決は harness のコンパイル済みレジストリではなく Claude Code ネイティブの Agent ツールが行い、エージェント定義をセッション開始時にキャッシュすることを確認（`.claude/tools/data/harness.json` にモデルマッピングなし）。 (learned 2026-08-11) <!-- cid:practices-discovery:c5 -->
- 上流成果物（intent-statement / scope-document / practices-discovery）で要件が高度に確定済みのスコープでは、要件分析の質問を実決定が必要な事項に絞って提示する（approval-handoff:c2 学習と整合）。 (learned 2026-08-11) <!-- cid:requirements-analysis:c1 -->
- Issue の記述前提（例: FE-7 の SeverityLevel「1|2|3」）が陳腐化している場合、現状コードを検証してから要件化し、前提ズレを要件に注記する（code-generation:asc-c2 と同系）。 (learned 2026-08-11) <!-- cid:requirements-analysis:c2 -->
- ユーザーストーリーが GitHub Issue に既に定義されている場合、Issue を一次ソースとし、その受入条件・検証方法・実装方針を INVEST 準拠のストーリーへ整理・形式化する。Issue の内容と矛盾する新規ストーリーは生成しない。 (learned 2026-08-11) <!-- cid:user-stories:c1 -->
- ユーザーが質問ファイル編集モードを選択せず、上流成果物（Issue・要件・ワイヤーフレーム）で既に確定済みの質問は、リード導出で回答を確定する（AskUserQuestion で集約確認を取得）。 (learned 2026-08-11) <!-- cid:user-stories:c2 -->
- モブ編成で複数サポートが独立に同一指摘（例: page.test.tsx スコープ漏れ）した場合は知識合意として是正統合し、ゲートで報告する。上流ソース間の矛盾（Level1 色）や品質ゲート実現手段（coverage 恒久化）等の判断要は構造化質問として人間に提示する。 (learned 2026-08-11) <!-- cid:user-stories:c5 -->
- モブトリアージで判断が必要な指摘（表示色の権威ソース vs ラフモックの矛盾、カバレッジゲートの恒久化手段）は質問ファイルへ追加し人間に構造化提示して確定する。 (learned 2026-08-11) <!-- cid:user-stories:c6 -->
- 次回以降はユーザーストーリーステージを省略する（ユーザー指示 2026-08-11。Issue 等でストーリーが既定義・上流成果物が確定済みの場合は直接次ステージへ進む）。 (learned 2026-08-11) <!-- cid:user-stories:c12 -->
- 「試算値」注記の表示構造は 2 段構成（コストカード見出しラベル「試算値」+ カード本文「前提: docs/business-model.md」のインライン短文）で確定し、テストは 2 文字列の完全一致 + 連結文字列の部分一致で検証する（FE-7 の User Stories Major 指摘の解消）。 (learned 2026-08-11) <!-- cid:refined-mockups:c1 -->
- KPI サマリの表示仕様（カード5枚の降順: 監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト、Level 1 は lime 黄緑 getSeverityMeta(1) 再利用、スケルトンは DashboardClient が data-testid="kpi-skeleton" で描画し KpiSummary は表示専用維持、h2 見出し + aria-labelledby）を refined-mockups 成果物として仕様化した。 (learned 2026-08-11) <!-- cid:refined-mockups:c2 -->
- 表示仕様の文言が上流成果物間で乖離する場合（例: requirements.md FR-6 の結合リテラル「試算値（前提: docs/business-model.md）」 vs 詳細化した 2 段構成）、詳細化ステージ（refined-mockups）で表示文字列とテストアサート方針を固定し、「FR 表記は詳細化した表示内容を言い表したものと解釈する」と明記して引き継ぐ（approval-handoff:c6 と整合）。 (learned 2026-08-11) <!-- cid:refined-mockups:c3 -->
- 表示専用コンポーネントが成功時のみ描画される場合、section / h2 / aria-labelledby / aria-busy は常時描画されるラッパー側（例: DashboardClient）に一元所有させ、配下でスケルトン（kpi-skeleton）かカードグリッドを切替える構成とする（スケルトン中も h2 とランドマークを維持）。 (learned 2026-08-11) <!-- cid:refined-mockups:c4 -->
- KPI セクション等のランドマーク（section/h2/aria-labelledby/aria-busy）は常時描画されるラッパー側（例: DashboardClient）が一元所有し、配下でスケルトンかカードグリッドを切替える。上流の「KpiSummary に h2」等の文言はラッパー側所有に読み替えて実装する。 (learned 2026-08-11) <!-- cid:application-design:c1 -->
- ADR はステージの decisions.md 内にインライン記載し、リポジトリルート /docs/adr/ は設けない（インテント単位で決定履歴を完結させる）。 (learned 2026-08-11) <!-- cid:application-design:c4 -->
- 失敗時挙動が異なる複数のポーリング対象（例: KPI 再スケルトン vs アラート据え置き）は共通フックに統合せず、対象ごとに専用フックを新設して分離する（共通化より責務分離・テスト分離を優先）。 (learned 2026-08-11) <!-- cid:application-design:c5 -->
- 表示ラベルは承認済み表示文言を固定値とし、表示メタ（SEVERITY_META 等）の label とは分離する（色・accentClass のみ単一ソースを利用）。 (learned 2026-08-11) <!-- cid:application-design:c6 -->
- 作業タスクはGitHubのISSUESを正とし、Unit Generationステージは実施しない（ユーザー指示 2026-08-11。Issue 単位でタスク分解が確定している場合は Units Generation を省略し、直接 Delivery Planning へ進む）。 (learned 2026-08-11) <!-- cid:units-generation:c1 -->
- Delivery Planning ステージも実施しない（ユーザー指示 2026-08-11。GitHub Issue を参照し、タスク分解が Issue 単位で確定している場合は Units Generation に続き Delivery Planning も省略し、直接 Construction（Functional Design）へ進む）。 (learned 2026-08-11) <!-- cid:delivery-planning:c1 -->
