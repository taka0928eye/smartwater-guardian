# Requirements — alert-schema-cleanup

## Sources

- [desc] Initial description: 「レビュー指摘に従ってコード品質を改善：PipeInfo.materialの型統一、docstring陳腐化の解消」
- [memory:M1] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md` — アラート詳細取得フロー、PipeInfo組み立てパス
- [memory:M2] `aidlc/spaces/default/codekb/smartwater-guardian/code-structure.md` — スキーマ・ルーター・サービスのモジュール構造
- [memory:M3] `aidlc/spaces/default/codekb/smartwater-guardian/code-quality-assessment.md` — 技術的債務の識別（型不整合、陳腐化docstring、マジックナンバー、STRICT_INPUT_CONFIG重複）
- [Q1]-[Q4], [Q4-follow] `requirements-analysis-questions.md` — ユーザー回答

## Intent Analysis

ユーザーの目的は、コードレビューで指摘された技術的債務を解消し、SmartWater Guardian バックエンドのコード品質を向上させることです。具体的には：

1. **型の一貫性確保** — `PipeInfo.material` と `PipeRecord.material` の型不整合を解消し、Pydantic の型安全性を保管台帳データ全体で一貫させる
2. **ドキュメントの正確性維持** — 実装状況の変化（BE-4完了）に追随していない docstring を更新し、将来の開発者の誤解を防ぐ
3. **周辺の軽微な技術的債務の同時解消** — 同一修正サイクルで関連する軽微な改善（マジックナンバー、設定重複）も片付け、再訪コストを避ける

この修正は CLAUDE.md の TDD 徹底原則（Red → Green → Refactor）に従い、既存テストスイートを壊さずに実施します。 [desc]

## Functional Requirements

### FR-1: PipeInfo.material の型統一

- **対象ファイル**: `backend/app/schemas/alert.py`
- **変更内容**: `PipeInfo.material: str` を `PipeInfo.material: PipeMaterial` に変更する
- **実装詳細**: `app.schemas.pipe` から `PipeMaterial` をインポートする
- **受入条件**:
  - `PipeInfo.material` の型アノテーションが `PipeMaterial`（`Literal["ductile_iron", "cast_iron", "pvc", "steel"]`）であること
  - `routers/alerts.py::_build_pipe_info()` が `PipeRecord.material`（既に `PipeMaterial` 型）をそのまま `PipeInfo.material` に代入でき、型チェッカーがエラーを出さないこと
  - 既存の `GET /api/v1/alerts/{telemetry_id}` エンドポイントのレスポンス形式（JSON構造）が変わらないこと（値の集合は元々 `PipeMaterial` の許容値と一致していたため、後方互換性に影響なし）

[Q1]

### FR-2: PipeInfo docstring の更新

- **対象ファイル**: `backend/app/schemas/alert.py`
- **変更内容**: `PipeInfo` クラスの docstring を、BE-4（`app/services/ledger.py`）が実装済みである実態に合わせて更新する
- **実装詳細**: 現在の「BE-6 では常に ``None`` を返す」という記述を、「配管台帳に該当する消火栓であれば実データが入る。該当しない場合は `AlertDetail.pipe_info` 自体が `None` になる」という内容に書き換える
- **受入条件**:
  - docstring が BE-6 の実装状況（常に null）ではなく、現在の実際の挙動（条件付きで実データ、非該当時は `pipe_info` 全体が `None`）を正しく説明していること
  - docstring 内のステージ番号への言及（BE-4/BE-6）は、実装状況の説明として引き続き有用なため維持してよい

[Q2]

### FR-3: リグレッションテストの追加

- **対象ファイル**: `backend/tests/test_alerts.py`（または該当のテストファイル）
- **変更内容**: `PipeInfo.material` が正しい `PipeMaterial` の値を保持することを検証するテストケースを追加する
- **実装詳細**: `GET /api/v1/alerts/{telemetry_id}` エンドポイントを配管台帳に該当する `hydrant_id` で呼び出し、レスポンスの `pipe_info.material` が期待される `PipeMaterial` 値（例: `"ductile_iron"`）と一致することを検証する
- **受入条件**:
  - 新規テストケースが `pytest` で実行され、パスすること
  - テストは型の値そのもの（文字列値の一致）を検証し、型システムの静的チェックだけに依存しないこと

[Q3]

### FR-4: マジックナンバーの named constant 化

- **対象ファイル**: `backend/app/schemas/pipe.py`
- **変更内容**: `PipeRecord.installed_year` の範囲制約（`ge=1965, le=2015`）を、named constant `MIN_INSTALL_YEAR` / `MAX_INSTALL_YEAR` に置き換える
- **実装詳細**: モジュールレベルで `MIN_INSTALL_YEAR = 1965`、`MAX_INSTALL_YEAR = 2015` を定義し、`Field(ge=MIN_INSTALL_YEAR, le=MAX_INSTALL_YEAR, ...)` として参照する
- **受入条件**:
  - `installed_year` のバリデーション範囲（1965〜2015）が変更前と同一であること（既存の `pipes.json` データが全件パスし続けること）
  - 定数名がモジュール内で一意で、他の定数（`services/ledger.py` の `REFERENCE_YEAR` など）と衝突しないこと

[Q4] [Q4-follow]

### FR-5: STRICT_INPUT_CONFIG の重複解消

- **対象ファイル**: `backend/app/schemas/telemetry.py`（定義元）、`backend/app/schemas/alert.py`、`backend/app/schemas/pipe.py`（利用側）
- **変更内容**: `STRICT_INPUT_CONFIG = ConfigDict(strict=True, extra="forbid")` の重複定義を解消する
- **実装詳細**: `telemetry.py` に既存の定義を正とし、`alert.py` と `pipe.py` はそれぞれ独自定義を持たず `from app.schemas.telemetry import STRICT_INPUT_CONFIG` でインポートする（新規モジュールを作らず、既存の定義元に一本化する — 最もシンプルな実装を優先する CLAUDE.md の MVP 原則に従う）
- **受入条件**:
  - `STRICT_INPUT_CONFIG` の定義が `telemetry.py` の1箇所のみに存在すること
  - `alert.py`・`pipe.py` の該当モデル（`AlertSummary`, `PipeInfo`, `AlertDetail`, `PipeRecord`, `GeoJSONLineString` など `STRICT_INPUT_CONFIG` を使用するクラス）が、インポートした共通定義を `model_config` に設定していること
  - 既存の strict バリデーション挙動（未知フィールド拒否、型強制なし）が変わらないこと

[Q4] [Q4-follow]

## Non-Functional Requirements

### NFR-1: 後方互換性

- API のレスポンス JSON 構造・フィールド名・既存の許容値集合は変更しない。`PipeInfo.material` の型変更は Python 側の型アノテーションのみに影響し、シリアライズされる JSON 値（文字列）は変わらない。

### NFR-2: テストカバレッジ

- CLAUDE.md §4 の要求（カバレッジ80%以上）を維持する。新規追加コード（FR-3のテスト、FR-4/FR-5の定数・インポート変更）がカバレッジを低下させないこと。

### NFR-3: 静的解析・Lint 準拠

- Ruff によるリンティングでエラー・警告が増加しないこと。`any` 型を新規に導入しないこと（CLAUDE.md §4）。

## Constraints

- **CLAUDE.md §3 適用**: 認証・権限管理、物理IoT通信プロトコル、リアルタイム通知、本番用大型GIS DB の実装は本修正のスコープ外
- **TDD 徹底**: CLAUDE.md §1 に従い、Red（失敗するテスト）→ Green（最小実装）→ Refactor のサイクルを厳格に順守する。FR-3 のテストケースは実装前に失敗する状態で作成する
- **Pydantic v2 徹底使用**: すべてのスキーマ変更は Pydantic v2 の記法（`ConfigDict`, `Field`, `Literal`）に従う
- **既存テストスイートの維持**: `org.md` Testing Posture の bugfix 方針（既存テストスイートは green を維持）に従い、本修正で既存テストを壊さないこと

## Assumptions

- `PipeMaterial` の許容値集合（`ductile_iron`, `cast_iron`, `pvc`, `steel`）は今回の修正範囲では変更しない。既存の `pipes.json` データはすべてこの集合内の値を持つと仮定する
- `test_alerts.py` に既存のテストフィクスチャ（配管台帳に該当する `hydrant_id` を持つテレメトリデータ）が存在するか、新規に追加可能であると仮定する。存在しない場合は Code Generation 段階でテストフィクスチャも合わせて追加する
- `STRICT_INPUT_CONFIG` の一本化は `telemetry.py` を正とする方針とし、循環インポートは発生しないと仮定する（`alert.py`・`pipe.py` は既に `telemetry.py` の他のシンボルを利用していないため、新規依存関係の追加はリスクが低いと判断）

## Out of Scope

- GeoJSON シリアライズのテスト未整備（`code-quality-assessment.md` で識別されたテストギャップ）— 別の対応とする [Q4-follow: D は選択されず、A・Bのみが対象]
- エラーメッセージの日本語ローカライズ統一 — 別の対応とする
- BE-3（FFT音響解析）の未実装スタブ — 本修正の対象外
- BE-5（工事発注自動起票）の未実装 — 本修正の対象外
- 認証・権限管理、本番用GIS DB — CLAUDE.md §3 により恒久的に対象外

## Open Questions

なし。すべての要件確認事項はコンソリデーテッドサマリーで確認済み。

## Review

**Verdict**: READY
**Reviewer**: aidlc-product-lead-agent（Advisory）
**Date**: 2026-08-11T01:27:45Z

このレビューはアドバイザリー1回パスであり、以下の指摘は承認ゲートで人間が取捨選択するための入力です。修正・再レビューのループは発生しません。

### Findings

- **Moderate — 上流カバレッジの欠落（`business-overview.md` 未参照）**: `## Sources` は `architecture.md`（M1）、`code-structure.md`（M2）、`code-quality-assessment.md`（M3）を引用しているが、本ステージの `consumes`（`conditional_on: brownfield`）に含まれる `business-overview.md` への参照が本文中どこにも存在しない。本プロジェクトは brownfield と明記されており（business-overview.md「プロジェクト特性」）、Inception フェーズガードレールの Traceability 原則（「Every requirement must trace back to an ideation artifact」）に照らすと、なぜこの型修正が水道局の資産管理という事業目的にとって重要か（例: `PipeInfo.material` の型不整合が下流の資産管理判断・地図連携表示にどう影響しうるか）という事業文脈の紐付けが requirements.md に一切書かれていない。技術的完全性は高いが、ビジネス価値の説明が [desc] の一文（「コード品質を向上させる」）だけに留まっている点は、プロダクトオーナーへの説明責任として弱い。
  - 推奨: `## Intent Analysis` に、business-overview.md の該当箇所（BE-4 配管台帳参照・資産管理自動化という事業目的）へのタグ付き参照を1〜2文追加する。

- **Minor — FR-1 受入条件が現行ツールチェーンで検証不能**: FR-1 の受入条件に「型チェッカーがエラーを出さないこと」とあるが、CLAUDE.md §4 が規定する品質コマンドは Ruff（lint）と pytest（カバレッジ）のみで、mypy/pyright 等の静的型チェッカーの実行はプロジェクトのビルド定義（team-practices の `code-generation:c1〜c4` 学習事項含む）に一切登場しない。このままでは QA がこの受入条件をどのコマンドで確認すればよいか特定できない。
  - 推奨: 「型チェッカー」を具体的な検証手段（例: FR-3 のランタイムテストで代替検証する、またはコードレビュー時の目視確認とする）に書き換えるか、mypy 導入を別途明記する。

- **Minor — FR-4 の「定数の衝突」記述が不正確**: 受入条件「定数名がモジュール内で一意で、他の定数（`services/ledger.py` の `REFERENCE_YEAR` など）と衝突しないこと」は、`MIN_INSTALL_YEAR`/`MAX_INSTALL_YEAR` を定義するのは `pipe.py` であり、`REFERENCE_YEAR` は別モジュール `ledger.py` にある。Python のモジュール名前空間上、別モジュールの定数と名前が衝突することはない（`import` 経由で明示的に同名で持ち込まない限り）。この書き方は実装者に不要な確認作業（別モジュールとの突合）を求めかねない。
  - 推奨: 「`pipe.py` モジュール内の既存の定数・識別子と衝突しないこと」に限定して書き換える。

- **Minor — FR-2 の受入条件が定性的判断に依存**: FR-2 の受入条件（「docstring が…正しく説明していること」）は自動化不能な人手レビュー基準であり、それ自体は docstring 更新というタスクの性質上妥当だが、他の FR（FR-1/FR-3/FR-4/FR-5）が機械的に検証可能な基準であるのに対し、FR-2 だけが「誰が・どう確認するか」を明記していない。
  - 推奨: 「Code Generation 段階の完了時に diff レビューで確認する」等、検証主体を一文添える。

### 総評

Q1〜Q4-follow の全回答が FR-1〜FR-5 に過不足なくトレースされており、Consolidated Summary との整合、CLAUDE.md §3 のスコープ外事項の遵守、org.md Testing Posture（bugfix: リグレッションテスト + 既存スイート green 維持）への準拠は確認できた。Critical な欠落・矛盾は見当たらず、指摘はいずれも Moderate 1件・Minor 3件で、実装着手を妨げるものではない。上記は人間の承認判断のための参考情報として提示する。

