**Collaborator:** aidlc-developer-agent

## Contribution

リードドラフト（team-practices.md / discovered-rules.md / evidence.md）を、実リポジトリ（`backend/app/**`・`frontend/src/**`・`.github/workflows/ci.yml`）と codekb 証拠で突合し、Developer Agent の焦点（命名・レイヤー境界・エラーハンドリング・ファイル構成・コードスタイル）の観点で検証した。ドラフトの命名規約・Pydantic v2 strict・ESLint 9 flat config・`lib/api.ts` 境界変換・`components/<domain>/` 配置は実コードと一致しており妥当。以下は統合時に検討いただきたい追加・訂正。

### 1. エラーハンドリング規約が Code Style に未記載（追加提案）

既存コードに一貫したエラーハンドリングパターンがあるが、ドラフトには未反映。

- **バックエンド**: 入力は Pydantic v2 境界（`STRICT_INPUT_CONFIG`）で検証し、ハンドラは HTTPException に依存せず状態コードを整理する（`kpi.py` docstring: 「空ストア・例外時にも HTTPException を上げず 200 を返す（500 にしない）」）。エラーはサイレントにせず例外を上げる（store は `RuntimeError`、ledger は `FileNotFoundError` / `ValueError` を伝播）。
- **フロント**: `lib/api.ts` の `unwrap()` が axios エラーを `ApiError` へ変換し（axios 以外は透過）、`useAlertPolling` は取得失敗時も最終状態を据え置いて控えめにエラー表示する（画面を壊さない）。ポーリングは `useEffect` クリーンアップで `clearInterval` + `cancelled` フラグによるアンマウント後 setState 防止を徹底。

→ team-practices.md `## Code Style` に以下を追記することを提案:

```markdown
- **エラーハンドリング（バックエンド）**: 入力は Pydantic v2 境界で検証し、ハンドラは HTTPException に依存せず状態コードを整理する（200 / 404 / 422 / 501。意図的に 500 にしない）。欠損・算出不能はサイレントな既定値で誤魔化さず、例外を明確に上げる。
- **エラーハンドリング（フロント）**: API エラーは `lib/api.ts` 境界で `ApiError` に変換する（axios 以外は透過）。取得失敗時は最終状態を据え置いて控えめにエラー表示し、画面を白紙にしない。ポーリングはクリーンアップで `clearInterval` と `cancelled` フラグを徹底する。
```

### 2. バックエンドのレイヤー境界が未記載（追加提案）

ドラフトの Code Style はフロント中心。バックエンドの責務分離は codekb（コード構造）に明記された主要規約なので、追記を提案:

```markdown
- **バックエンドのレイヤー境界**: `routers`（薄く保ち、リクエスト→サービスの呼び出しとレスポンス組み立てのみ）→ `services`（ビジネスルール集約）→ `schemas`（外部契約境界・Pydantic v2）→ `store`（データ保持・シングルトン）の責務分離を維持する。ビジネスロジックをルーターに書かない。
- **マスタローダー**: `@lru_cache(maxsize=1)` で JSON マスタを初回呼び出し時に読み込み以後キャッシュする（リクエスト毎再読込なし）。欠損・破損はサイレントな空台帳にせず例外を上げる。テスト隔離のためシングルトンは `reset_store()` で破棄可能にする。
```

### 3. `SeverityLevel` 単一ソースは「現行規約」ではなく「FE-7 で実施する確定方針」と明記すべき（訂正）

team-practices.md `## Code Style` に「表示メタ（`SEVERITY_META` / `getSeverityColor` 等）は型と同居するユーティリティ層（`lib/severity.ts`）を単一ソースとし、契約層（`types/api.ts`）から re-export する」とあるが、**これは現状ではなく FE-7 の実施対象**。現状 `SeverityLevel` は `types/api.ts`（`0|1|2|3`）と `lib/severity.ts`（`0|1|2|3`）に二重定義され、`types/api.ts` からの re-export は未実施（code-quality-assessment の技術負債 #4）。promotion 後に読む開発者が「既に単一ソース化済み」と誤解すると、コード生成時に重複を再発させうる。以下への訂正を提案:

```markdown
- **表示メタの単一ソース（FE-7 で実施予定）**: 表示メタ（`SEVERITY_META` / `getSeverityColor` 等）は型と同居するユーティリティ層（`lib/severity.ts`）を本拠とする。現状 `SeverityLevel` は `types/api.ts` と `lib/severity.ts` に二重定義されているため、FE-7 で `lib/severity.ts` に集約し、契約層（`types/api.ts`）から re-export する。
```

### 4. discovered-rules.md: 「フォールバック」と「モック非残置」の境界を明文化すべき（訂正）

「ALWAYS: バックエンド停止中でも画面を白紙にせず、スケルトン表示等のフォールバック」と「NEVER: 実データで埋められる KPI カードにモック値（`MOCK_KPI_DATA`）を残す」が併存する。この 2 つは矛盾しないが、読み手によっては「フォールバック = モック値表示の許可」と誤読しうる。フォールバックは「表示崩れ防止」（スケルトン or 実マスタ `hydrants.json` 由来データ）を目的とし、**固定の KPI 数値モックを実データの代わりに表示する用途には使わない**旨を ALWAYS 側に明記することを提案:

```markdown
- ALWAYS: バックエンド停止中でも画面を白紙にせず、スケルトン表示（または実マスタ由来データ）にフォールバックすること。フォールバックは表示崩れ防止を目的とし、固定の KPI 数値モック（`MOCK_KPI_DATA` 等）を実データの代わりに表示する用途には使わないこと。
```

### 5. evidence.md の補足（誤りではないが整合確認）

- エラーハンドリング・レイヤー境界の「確定」項目に、上記 1・2 の根拠（`kpi.py` の 500 にしない docstring、`unwrap()` の `ApiError` 変換、`useAlertPolling` の据え置き表示、store 3層分離）を追加すると、Step 4 インタビューの確認材料として一貫する。
- 現行の `page.tsx` フォールバックは `FALLBACK_SENSOR_FEATURES`（地図用・`hydrants.json` 由来の実マスタ + モック状態）であり、KPI 側の `MOCK_KPI_DATA`（固定数値）とは種別が異なる。この区別を evidence に明記すると項目 4 の訂正と整合する。

### 6. インタビュー（Step 4）への申し送り候補

上記 1・2 のエラーハンドリング / レイヤー境界はコード実態からの「推測」であり、discovered-rules の Mandated/Forbidden は「人間が明示したハード制約のみ」を promote する原則に照らし、インタビューで確認する項目として提示することを提案する。

## Positions

- AGREE: 命名規約（snake_case / PascalCase / UPPER_SNAKE_CASE、TS camelCase / PascalCase）・Pydantic v2 strict / extra=forbid・ESLint 9 flat config + TS strict・`lib/api.ts` 境界変換・`components/<domain>/` 配置の記述は実コードと一致している。
- AGREE: discovered-rules.md の Mandated/Forbidden の大半（日本語・TDD・Pydantic v2・カバレッジ80%・`python -m pytest`・Conventional Commits・`any` 禁止・認証/IoT/リアルタイム/GIS DB スコープ外）は CLAUDE.md / git / CI で裏付けられている。
- OBJECT: エラーハンドリング規約が Code Style に未記載 — 実コードに一貫した「500 にしない」「`ApiError` 変換」「最終状態据え置き」パターンがあり、チーム規約として明文化すべき。
- OBJECT: バックエンドのレイヤー境界（routers / services / schemas / store の責務分離）がチームプラクティス未記載 — フロント中心の記述に偏っている。
- OBJECT: `SeverityLevel` 単一ソースを「既存規約」として記述しているが現状は二重定義 — 現状と FE-7 の実施方針を区別しないとコード生成時に誤読を招く。
- OBJECT: 「フォールバック」と「モック非残置」の境界が曖昧 — フォールバックはスケルトン / 実マスタ由来に限定し、固定 KPI 数値モックは実データの代わりに使わない旨を明文化すべき。
