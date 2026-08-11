# Requirements Analysis — 確認事項

このステージでは、ユーザーの依頼「レビュー指摘に従ってコード品質を改善：PipeInfo.materialの型統一、docstring陳腐化の解消」を要件化します。リバースエンジニアリング（codekb）で特定した技術的債務は以下の通りです：

1. **型不整合**: `PipeInfo.material`（`backend/app/schemas/alert.py`）が `str` 型だが、`PipeRecord.material`（`backend/app/schemas/pipe.py`）は `PipeMaterial`（`Literal["ductile_iron", "cast_iron", "pvc", "steel"]`）型
2. **陳腐化した docstring**: `PipeInfo` クラスの docstring が「BE-6 では常に None を返す」と記載しているが、BE-4（ledger.py）実装により実際にはデータが挿入される

依頼内容は明確でスコープが狭いため、実装判断に必要な項目のみ質問します。

## Q1. 型統一の対象範囲

`PipeInfo.material` の型を `str` から `PipeMaterial`（`app/schemas/pipe.py` で定義済みの `Literal["ductile_iron", "cast_iron", "pvc", "steel"]`）に変更する方針でよいですか？

A. はい。`PipeInfo.material: str` → `PipeInfo.material: PipeMaterial` に変更し、`pipe.py` から `PipeMaterial` をインポートする
B. 型を統一する代わりに、新しい共有型（例: `alert.py` と `pipe.py` の両方が参照する共通モジュール）を作る
C. 型は変更せず、docstring・コメントで不整合を明記するだけに留める
X. Other (please specify)

[Answer]: A

## Q2. docstring 更新の内容

`PipeInfo` クラスの docstring（現在: 「BE-6 では常に ``None`` を返す。BE-4（app/services/ledger.py）が実装されたらここに配管情報が入る。」）をどう更新しますか？

A. BE-4 実装済みである旨を反映し、「配管台帳に該当する消火栓であれば実データが入る。該当しない場合は AlertDetail.pipe_info 自体が None になる」のように更新する
B. BE-6/BE-4 のようなステージ番号への言及自体を削除し、純粋にフィールドの意味だけを説明する記述にする
C. 現状の docstring 構成（実装状況の言及付き）を維持しつつ、日付・状態だけ更新する
X. Other (please specify)

[Answer]: A

## Q3. リグレッションテストの追加

`org.md` の Testing Posture では bugfix スコープに対して「regression test for the specific bug/vulnerability」を求めています。この修正に対して追加すべきテストの範囲は？

A. `PipeInfo.material` が正しい `PipeMaterial` の値を持つことを検証するテストケースを `test_alerts.py`（または該当のテストファイル）に追加する
B. 型チェック（mypy等の静的解析）で担保し、ランタイムテストの追加は不要とする
C. テスト追加は不要（既存の `test_alerts.py` が pipe_info 生成パスを暗黙的にカバーしているため）
X. Other (please specify)

[Answer]: A

## Q4. スコープ境界の確認

リバースエンジニアリングで、上記2点以外にも軽微な技術的債務（例: `STRICT_INPUT_CONFIG` の重複定義、`installed_year` の範囲がマジックナンバー、GeoJSON シリアライズのテスト未整備）が見つかりました。今回の修正範囲は？

A. 依頼された2点（型統一・docstring更新）のみに限定する。他の債務は対象外とし、将来の別対応とする
B. 型統一・docstring更新に加えて、関連する軽微な改善（マジックナンバーの定数化など）も同一修正に含める
X. Other (please specify)

[Answer]: B

## Q4-follow. 「関連する軽微な改善」の具体的範囲

Q4でBを選択いただきました。「軽微な改善」の範囲を確定させてください。code-quality-assessment.md で識別した軽微な技術的債務のうち、対象に含めるものを選んでください（複数選択可）。

A. `installed_year` の範囲（`ge=1965, le=2015`）をマジックナンバーから named constant（`MIN_INSTALL_YEAR` / `MAX_INSTALL_YEAR`）に変更する（pipe.py）
B. `STRICT_INPUT_CONFIG` の重複定義（telemetry.py, alert.py, pipe.py の3箇所）を共通モジュールに集約する
C. 上記A・B両方を含める
D. 上記以外は含めず、Q1・Q2（型統一・docstring更新）のみに戻す
X. Other (please specify)

[Answer]: C

## Consolidated Summary Confirmation

- `PipeInfo.material` の型を `str` から `PipeMaterial`（`app/schemas/pipe.py` の既存 Literal 型）に変更し、`alert.py` に `PipeMaterial` をインポートする
- `PipeInfo` の docstring を BE-4 実装済みの実態に合わせて更新する（該当消火栓があれば実データが入り、該当しなければ `AlertDetail.pipe_info` 自体が `None` になる旨を明記）
- `PipeInfo.material` が正しい `PipeMaterial` の値を持つことを検証するリグレッションテストケースを `test_alerts.py`（または該当のテストファイル）に追加する
- 修正範囲は型統一・docstring更新に加え、以下の軽微な改善を含める：
  - `installed_year` の範囲（`ge=1965, le=2015`）を `MIN_INSTALL_YEAR` / `MAX_INSTALL_YEAR` の named constant に変更する（`pipe.py`）
  - `STRICT_INPUT_CONFIG` の重複定義（`telemetry.py`, `alert.py`, `pipe.py` の3箇所）を共通モジュールに集約する

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
