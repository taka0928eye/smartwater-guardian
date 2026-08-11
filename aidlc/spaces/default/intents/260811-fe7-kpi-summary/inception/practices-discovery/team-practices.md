# チームプラクティス（Step 5 統合版）— FE-7 KPIサマリ実データ連携

> Practices Discovery（Step 5 Lead Integration）の最終版。Step 2 のリードドラフトに
> Step 3 の 3 盲検レビュー（quality / developer / devsecops）と Step 4 のインタビュー回答
> （Q1〜Q12）を統合し、チームの声で確定した内容を記述している。各項目の根拠・確定/推測/未確定の
> 分類は `evidence.md` を参照。affirmation ゲート（Step 6）での承認後に
> `memory/team.md` へ promote される。

## Way of Working

- 単一リポジトリ（モノレポ）で開発する。`backend/`（FastAPI）・`frontend/`（Next.js）・`docs/`・
  `.github/workflows/` が同一リポジトリに共存し、機能追加は Issue（BE-x / FE-x）単位で進める。
- ブランチ戦略は **main 直コミット中心（trunk-based）** を明文化する。短命フィーチャーブランチ + PR は
  **大規模変更・他者レビュー・共同作業が必要な場合のみ**使用する（Q1: A 確定）。git 履歴は
  `feat: BE-8: ...` のように 1 コミット＝ 1 Issue/機能の粒度で main に積む。
- コミットメッセージは Conventional Commits 形式（`feat:` / `fix:` / `docs:` / `ci:`）＋
  Issue/ステージ参照（BE-8 / FE-7 等）で書く。メッセージ本文は日本語。
- 開発プロセスは AI-DLC ワークフローに従い、インテント（`aidlc/` 配下）でステージを進行する。

## Walking Skeleton

- 本スコープ（`feature` / Brownfield）ではスケルトン・セレモニーは実施しない（Q2: A 確定）。
  アクティブスコープは `skeleton: on` を宣言しておらず、アプリは既に end-to-end
  （BE-8 KPI サマリ API 実装済み・フロントは FE-7 のみ未着手）で動作しているため、
  薄い縦スライス検証の追加は不要。
- 新規の縦スライスが必要になるのは、新プロジェクト（Greenfield）や大規模機能追加時のみ。

## Testing Posture

- TDD（Red → Green → Refactor）を厳格に順守する。コード作成前に必ず失敗テストを書き、
  最小実装で Green にした後、リファクタリングする。
- バックエンドは pytest。`python -m pytest` で実行する（pytest.exe は cwd を sys.path に
  挿入せず `app` を import できないため使用しない）。
- カバレッジは **80% 以上**を CI ゲートとし、**ローカル実行と CI でゲートを一致させる**（Q3: A 承認済み）。
  - backend: **行 + branch の各 80%**（`--cov=app --cov-branch --cov-fail-under=80`）を要求する（Q4: B 確定）。
    `pytest-cov` は `requirements-dev.txt` でピン固定し、`backend/.coverage` は `.gitignore` に追加する。
  - frontend: lines / functions / branches / statements の各 80%。`vitest.config.mts` の
    `coverage.thresholds` に設定し、ローカル `npm run test` でも CI と同じゲートを強制する。
- E2E テスト（Playwright / Cypress）はデモまで導入しない（Q5: A 確定）。TestClient エンドポイント
  テスト + フロント component テストを統合境界の上限とする（project.md 学習 c1 と整合）。
- バックエンドに **ruff + mypy を導入し、CI ゲートに追加する**（Q6: C 確定）。型安全性は
  ruff / mypy の静的チェックと、Pydantic ランタイムテスト（ValidationError 送出）の両輪で担保する。
- テスト分離は `conftest.py` の autouse フィクスチャ（`_reset_store`）で担保する。session スコープの
  `client`（TestClient）を再利用してもテスト間隔離を維持する。
- CI（GitHub Actions）は main への push / PR でテスト・カバレッジ・lint・build を強制し、
  起動スモークテスト（`scripts/check_telemetry.py`）も実行する。

## Deployment

- 本番向け CD パイプラインは存在しない。`.github/workflows/` は CI ゲート（`ci.yml`）のみで、
  デプロイワークフローは未整備。
- デモ（8/10〜8/15）の受け渡しは **ローカル実行を主とする**（バックエンド `uvicorn`・
  フロント `npm run dev` / 本番ビルドは `npm run build`）。**余裕があれば AWS へデプロイする**
  （Q7: X 回答で確定）。
- 対象はデモスコープ。クラウドインフラ・本番用 DB は持たず、インメモリストア + JSON マスタで
  デモを成立させる。
- デプロイは手動・ローカル実行に限定され、本番環境の明示的なロールバック手順は未定義。

## Code Style

- **Python**: ファイル・関数は `snake_case`、クラスは `PascalCase`、定数は `UPPER_SNAKE_CASE`。
  入力検証は **Pydantic v2（strict / extra=forbid）** を徹底。`any` は禁止。
- **Python 静的チェック**: **ruff + mypy を導入し、CI ゲートに追加する**（Q6: C 確定）。
- **TypeScript**: ファイルは `camelCase`、型・コンポーネントは `PascalCase`。
  ESLint 9 flat config + `eslint-config-next` を CI ゲートに組み込み、TS strict を維持。`any` は禁止。
- フロント↔バックエンドの `snake_case`→`camelCase` 変換は `lib/api.ts` 境界で **1 回だけ**行う。
- **エラーハンドリング（バックエンド）**: 入力は Pydantic v2 境界で検証し、ハンドラは HTTPException に
  依存せず状態コードを整理する（200 / 404 / 422 / 501。**意図的に 500 にしない**）。欠損・算出不能は
  サイレントな既定値で誤魔化さず、例外を明確に上げる（store は `RuntimeError`、ledger は
  `FileNotFoundError` / `ValueError` を伝播）。
- **エラーハンドリング（フロント）**: API エラーは `lib/api.ts` 境界で `ApiError` に変換する
  （axios 以外は透過）。取得失敗時は最終状態を据え置いて控えめにエラー表示し、画面を白紙にしない。
  ポーリングはクリーンアップで `clearInterval` と `cancelled` フラグを徹底する。
- **バックエンドのレイヤー境界**: `routers`（薄く保ち、リクエスト→サービスの呼び出しとレスポンス組み立てのみ）
  → `services`（ビジネスルール集約）→ `schemas`（外部契約境界・Pydantic v2）→ `store`
  （データ保持・シングルトン）の責務分離を維持する。ビジネスロジックをルーターに書かない。
- **マスタローダー**: `@lru_cache(maxsize=1)` で JSON マスタを初回呼び出し時に読み込み以後キャッシュする
  （リクエスト毎再読込なし）。欠損・破損はサイレントな空台帳にせず例外を上げる。テスト隔離のため
  シングルトンは `reset_store()` で破棄可能にする。
- **表示メタの単一ソース（FE-7 で実施予定）**: 表示メタ（`SEVERITY_META` / `getSeverityColor` 等）は
  型と同居するユーティリティ層（`lib/severity.ts`）を本拠とする。**現状 `SeverityLevel` は
  `types/api.ts` と `lib/severity.ts` に二重定義**されているため、FE-7 で `lib/severity.ts` に集約し、
  契約層（`types/api.ts`）から re-export する（Q9: A 確定）。
- **フォールバック**: バックエンド停止中でも画面を白紙にせず、**スケルトン表示（または実マスタ
  `hydrants.json` 由来データ）にフォールバック**する。フォールバックは表示崩れ防止を目的とし、
  **固定の KPI 数値モック（`MOCK_KPI_DATA`）を実データの代わりに表示する用途には使わない**
  （Q10: A 確定）。
- **セキュリティ統制**: 依存関係の脆弱性スキャンは **GitHub ネイティブの Dependabot** を有効化して
  監視する（Q11: A 確定）。シークレット検知は **GitHub secret scanning** に委ねる（Q12: B 確定）。
  シークレット・API キーは環境変数で注入し、`.env` は gitignore で管理する。
- コメント・docstring・コミットメッセージは **日本語** で書く。docstring には Issue 参照を明記する。
- コンポーネントは責務単位で `components/<domain>/` に配置し、ページは Server Component を
  基本とし、状態を持つ部分のみ Client Component に分離する。
