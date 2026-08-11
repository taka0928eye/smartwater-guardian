# 発見されたルール（Step 5 統合版）— FE-7 KPIサマリ実データ連携

> Practices Discovery（Step 5 Lead Integration）で確定したハード制約。Step 4 インタビュー
> （Q1〜Q12）で人間が明示的に承認・決定した事項と、CLAUDE.md（プロジェクト指示）で既に
> 確定しているハード制約のみを `## Mandated`（ALWAYS）・`## Forbidden`（NEVER）に整理している。
> 各ルールの根拠・決定プロセスは `evidence.md` を参照。affirmation ゲート（Step 6）での承認後に
> `memory/team.md` / `memory/project.md` へ promote される。
>
> **確定/候補の区分**: 以下のうち、日本語・TDD・Pydantic v2・`python -m pytest`・Conventional
> Commits・`any` 禁止・スコープ外・モック非残置は CLAUDE.md / git / CI で既に裏付けられた
> ハード制約。ブランチ戦略（Q1）・カバレッジ一致（Q3）・branch カバレッジ（Q4）・ruff + mypy
> 導入（Q6）・フォールバック限定（Q10）・Dependabot（Q11）・secret scanning（Q12）は
> インタビューで新たに確定・更新された事項。

## Mandated

- ALWAYS: ドキュメント・会話・コメント・docstring・コミットメッセージは**日本語**で書くこと。
- ALWAYS: コード作成前に必ず失敗テストを書き、TDD（Red → Green → Refactor）のサイクルを順守すること。
- ALWAYS: バックエンドの入力検証は **Pydantic v2（strict / extra=forbid）** を使用すること。
- ALWAYS: テストカバレッジ **80% 以上**を維持し、**カバレッジゲートをローカル実行と CI で一致させる**こと
  （Q3: A 承認済み）。backend は **行 + branch の各 80%**（`--cov=app --cov-branch --cov-fail-under=80`、
  Q4: B 確定）、frontend は lines / functions / branches / statements の各 80%
  （`vitest.config.mts` の `coverage.thresholds` で設定）。`pytest-cov` は `requirements-dev.txt` で
  ピン固定し、`backend/.coverage` は `.gitignore` に追加すること。
- ALWAYS: バックエンドのテストは `python -m pytest` で実行すること（pytest.exe 不使用）。
- ALWAYS: バックエンドに **ruff + mypy を導入し、CI ゲートに追加**して静的チェックを実施すること
  （Q6: C 確定）。
- ALWAYS: コミットメッセージは Conventional Commits 形式（`feat:` / `fix:` / `docs:` / `ci:`）で
  Issue/ステージ参照（BE-x / FE-x）を添えること。
- ALWAYS: ブランチ戦略は **main 直コミット中心（trunk-based）**とし、短命フィーチャーブランチ + PR は
  **大規模変更・他者レビュー・共同作業が必要な場合のみ**使用すること（Q1: A 確定）。
- ALWAYS: フロント↔バックエンドの `snake_case`→`camelCase` 変換は `lib/api.ts` 境界で 1 回だけ行うこと。
- ALWAYS: バックエンド停止中でも画面を白紙にせず、**スケルトン表示（または実マスタ由来データ）に
  フォールバック**すること。フォールバックは表示崩れ防止を目的とし、**固定の KPI 数値モック
  （`MOCK_KPI_DATA` 等）を実データの代わりに表示する用途には使わない**こと（Q10: A 確定）。
- ALWAYS: 依存関係の脆弱性スキャンとして **Dependabot を有効化**すること（Q11: A 確定）。
- ALWAYS: **GitHub secret scanning を有効化**し、シークレット検知を自動化すること（Q12: B 確定）。

## Forbidden

- NEVER: TypeScript / Python コードで `any` を使用すること。
- NEVER: 認証・権限管理 / 物理 IoT 通信プロトコル / リアルタイム通知 / 本番用大型 GIS DB を実装すること。
- NEVER: デモスコープで本番用 DB やクラウドインフラを導入すること
  （インメモリストア + JSON マスタでデモを成立させる）。
- NEVER: テスト・カバレッジ・lint・build が成功していない状態のコードを main へマージすること。
- NEVER: 実データで埋められる KPI カードにモック値（`MOCK_KPI_DATA`）を残すこと。
- NEVER: 本番または共有リポジトリへシークレット・API キーをコミットすること
  （実キーは環境変数/シークレット管理で注入し、`.env` は gitignore で管理する）。
