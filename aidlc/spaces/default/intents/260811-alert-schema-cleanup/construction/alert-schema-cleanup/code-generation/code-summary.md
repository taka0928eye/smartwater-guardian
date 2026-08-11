# Code Summary — alert-schema-cleanup

## 変更ファイル

| ファイル | 変更内容 | 対応FR |
|---------|---------|--------|
| `backend/app/schemas/pipe.py` | `MIN_INSTALL_YEAR = 1965` / `MAX_INSTALL_YEAR = 2015` の named constant を追加し、`PipeRecord.installed_year` の `Field(ge=..., le=...)` で参照 | FR-4 |
| `backend/app/schemas/alert.py` | `PipeMaterial` を `pipe.py` からインポートし `PipeInfo.material: str` → `PipeInfo.material: PipeMaterial` に変更。`PipeInfo` クラス docstring を BE-4 実装済みの実態に更新 | FR-1, FR-2 |
| `backend/tests/test_alerts.py` | `TestPipeInfoSchema` クラスを追加し、`PipeInfo(material="invalid_material", ...)` が `ValidationError` を送出することを検証する単体テストを1件追加 | FR-1, FR-3 |
| `backend/tests/test_pipes.py` | `_valid_pipe_record_payload()` ヘルパーと `test_installed_year_boundary_rejects_below_min_accepts_min_and_max` を追加し、`installed_year` の境界値検証（`MIN_INSTALL_YEAR - 1` は拒否、`MIN_INSTALL_YEAR`/`MAX_INSTALL_YEAR` 自体は受理）を検証 | FR-4 |

## 主要な実装判断

- **FR-5（`STRICT_INPUT_CONFIG` 重複解消）は変更不要と判明**: 実装時点のコードベースを確認したところ、`pipe.py`・`alert.py` は既に `telemetry.py` から `STRICT_INPUT_CONFIG` をインポートしており、重複定義は存在しなかった。codekb のスナップショット（reverse-engineering 時点）がやや古く、BE-4 の先行コミットで既に解消されていたと推測される。`grep` で単一定義であることを確認済み。
- **TDDのRed→Green検証**: 2つの新規テストは、スキーマ変更前（stash）→失敗（Red）→スキーマ変更後（unstash）→成功（Green）の手順で実際に検証した（メンタル検証ではなく実行による確認）。詳細は memory.md参照。
- **FR-1の受入条件の実現方法**: requirements.md の「型チェッカーがエラーを出さないこと」という受入条件は、プロジェクトに mypy 等の静的型チェッカーが存在しないため（product-lead レビューの Minor指摘で既知）、実行可能なテスト（`PipeInfo(material="invalid_material")` が `ValidationError` を送出する）で代替検証した。

## テストカバレッジ

- **pytest 結果**: 109 passed, 1 warning（warning は本修正と無関係の既存の `httpx`/`starlette` 非推奨警告）
- **カバレッジ**: 100%（375 stmts, 0 miss）— CLAUDE.md §4 の80%以上の要求を満たす
- **新規テスト**: 2件（`test_alerts.py` に1件、`test_pipes.py` に1件）
- 既存テスト（`test_returns_detail_with_spectrum_and_pipe_info`、`test_installed_year_within_range` 等）は変更せず、そのまま green を維持

## プランからの逸脱

1. **Step 2, Step 5（`STRICT_INPUT_CONFIG` 重複解消）**: 実装不要と判明（上記「主要な実装判断」参照）。コード変更なし。
2. **モジュールレベル docstring・`pipe_info` フィールドの description は未修正**: `alert.py` の冒頭 docstring（3-5行目）と `AlertDetail.pipe_info` フィールドの `description="BE-4 実装までは null"` に、`PipeInfo` クラス docstring と同種の陳腐化した記述が残っている。requirements.md FR-2 は `PipeInfo` クラスの docstring のみをスコープとしており、承認済みプランの Step 4 もそれに従ったため、これらは意図的に対象外とした。ユーザーへの確認事項として次項に記載。

## 確認事項（承認ゲートで判断）

上記逸脱2点目について、`alert.py` の以下2箇所にも同種の陳腐化した記述が残っています（今回のスコープ外として意図的に未修正）:

- モジュール docstring（3-5行目）: 「``pipe_info`` は BE-4（疑似GIS配管台帳）実装までは常に ``None`` を返す」
- `AlertDetail.pipe_info` フィールドの `description`: 「BE-4 実装までは null」

これらは元のユーザー依頼「docstring陳腐化の解消」の趣旨には合致しますが、requirements.md の FR-2 は `PipeInfo` クラスの docstring のみを明示的にスコープとしていたため、今回は含めていません。承認ゲートで、これらも含めるか（Request Changes）、次の別対応に回すか（Approve のまま）をご判断ください。

## Review

**Verdict**: READY
**Reviewer**: aidlc-architecture-reviewer-agent（Advisory）
**Date**: 2026-08-11T01:44:25Z

このレビューはアドバイザリー1回パスであり、以下の指摘は承認ゲートで人間が取捨選択するための入力です。修正・再レビューのループは発生しません。

### Findings

- **Moderate — FR-2 が未完了のまま「docstring 陳腐化の解消」を名乗っている（確認事項として提起済みだが実質的なギャップ）**: `alert.py` のモジュール冒頭 docstring（3-5行目「``pipe_info`` は BE-4 実装までは常に ``None`` を返す」）と `AlertDetail.pipe_info` フィールドの `description="BE-4 実装までは null"` は、`PipeInfo` クラス docstring と全く同じ種類の陳腐化（BE-4 実装済みという実態と矛盾）を抱えたまま残っている。requirements.md の [desc] は「docstring陳腐化の解消」を目的として明記しており、FR-2 の対象を `PipeInfo` クラスのみに限定したのは Code Generation 段階の解釈（プランの Step 4）であって、requirements.md 自体が「これ以外は対象外」と明示しているわけではない。結果として、モジュールを開いた開発者は冒頭の docstring と `pipe_info` フィールドの description という、最も目に入りやすい2箇所で依然として誤った情報（「実装までは常に null」）を読むことになり、FR-2 が解消しようとした「将来の開発者の誤解を防ぐ」という目的の一部が達成されないまま残る。既に確認事項として承認ゲートに提起されている点は妥当な対応だが、スコープ限定の妥当性そのものについては、アーキテクチャレビューとしても「同一ファイル内に新旧の説明が混在する」状態は半端な修正であり、フォローアップに回すとしても Issue 化を明示すべきという評価を付言する。
  - 推奨: 人間が Approve する場合でも、この2箇所を追跡する GitHub Issue を必ず起票し、code-summary.md に Issue 番号を残す。

- **Minor — FR-1 の受入条件「型チェッカーがエラーを出さない」の代替検証はテストの性質上ではなく静的検証の欠如を隠すのみ**: `test_material_outside_pipe_material_literal_raises_validation_error` はランタイムの `ValidationError` 送出を検証しており、これは FR-3（値レベルの回帰）としては適切だが、FR-1 の受入条件が本来意図していた「型アノテーションの静的な正しさ（mypy/pyright 相当）」は依然として未検証のまま。プロジェクトに型チェッカーがない以上、コードレビュー（本レビュー含む）による目視確認が唯一の担保であり、実装判断としては妥当（product-lead レビューの Minor指摘と整合）。将来 `PipeInfo.material` の型を誤って `str` に戻すような回帰があっても、静的解析なしでは検出できないのは変わらないため、そのリスクは今回のスコープでは許容とする。

- **Minor — テストの重複が軽微に残る**: `test_pipes.py` の新規テスト `test_installed_year_boundary_rejects_below_min_accepts_min_and_max` は境界値（`MIN_INSTALL_YEAR`, `MAX_INSTALL_YEAR`, `MIN_INSTALL_YEAR - 1`）を検証するが、`MAX_INSTALL_YEAR + 1`（上限超過の拒否）は検証していない。既存の `Field(ge=..., le=...)` は対称的な制約であり、下限側の拒否が確認できていれば実装上の対称性からリスクは低いが、境界値テストとしては上限超過ケースも1アサーション追加するだけで完全になる点は指摘しておく。ブロッキングではない。

### 検証結果

- **型合成の健全性**: `_build_pipe_info()`（`routers/alerts.py`）は `PipeRecord.material`（既に `PipeMaterial` 型として `pipe.py` でバリデーション済み）をそのまま `PipeInfo(material=pipe.material, ...)` に渡しており、型の合成は健全。`pipes.json` の実データ（10件）は全件 `PipeMaterial` の許容値集合（`ductile_iron`, `cast_iron`, `pvc`, `steel`）に収まっており、`PipeRecord.model_validate()` 時点で境界検証が完了しているため、`PipeInfo` 構築時に `ValidationError` が発生するリスクはない。
- **他箇所への影響**: `PipeInfo` を参照するのは `alert.py`（定義）、`routers/alerts.py`（構築）、`test_alerts.py`（テスト）の3ファイルのみ（`grep` で確認）。`material` を `str` として型付けている他の箇所は見当たらない。
- **FR-5 の「変更不要」判断の裏付け**: `grep -rn "STRICT_INPUT_CONFIG\s*="` で `telemetry.py` の1箇所のみが定義元であることを確認した。code-summary.md の記述は事実と一致する。
- **テスト・カバレッジの数値検証**: `venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing` を実際に実行し、`109 passed, 1 warning`・カバレッジ `375 stmts, 0 miss, 100%` を確認した。code-summary.md の記載と完全に一致し、誇張・不整合はない。
- **テストの非タウトロジー性**: 2件の新規テストはいずれも実際のスキーマ制約（`PipeMaterial` Literal、`installed_year` の `ge`/`le`）に依存した `pytest.raises(ValidationError)` を使っており、実装を無視して常に成立するアサーションではない。`test_pipes.py` のテストは境界値の受理（`MIN_INSTALL_YEAR`/`MAX_INSTALL_YEAR` 自体は通る）も確認しており、拒否のみを検証する片側テストではない点も良い。

### 総評

`PipeInfo.material` の型統一（FR-1）は `PipeRecord` との合成、実データ、テストのいずれの面でも健全であり、本番運用でのバリデーションエラーのリスクは確認できなかった。FR-3〜FR-5・NFR-1〜NFR-3 も実装・テストで裏付けが取れている。唯一の実質的な懸念は、確認事項として既に承認ゲートに提起されている「モジュール docstring と `pipe_info` フィールド description の陳腐化未解消」で、Moderate 1件として記録した。Critical な欠陥・循環依存・破損した参照は見当たらず、Moderate 1件・Minor 2件はいずれも実装着手や本番投入を妨げるものではない。
