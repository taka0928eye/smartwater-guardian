# Approval & Handoff 質問 — BE-4 配管台帳照合サービス

## Q1: 配管ID（pipe_id）の形式はどちらにしますか？

消火栓マスタ `hydrants.json` は HYD-001〜HYD-010 の各行が `"pipe_id": "P-001"〜"P-010"` を参照しています。一方、GitHub Issue の配管台帳仕様では pipe_id の例示が `PIPE-001` 形式です。

A. `hydrants.json` と整合する `P-001` 形式（推奨）
- `find_pipe_by_hydrant()` がマスタの参照をそのまま解決でき、両ファイルの突合が不要。

B. Issue 例示どおり `PIPE-001` 形式
- Issue の文言に忠実だが、`hydrants.json` 側の参照値との変換（マッピング）が必要になる。

X. Other (please specify)

[Answer]: A. P-001 形式

## Q2: 経過年数（age）の算出基準日はどうしますか？

`get_pipe_age(installed_year)` の「現在」の基準をどこに置くかです。

A. 現在年（2026年）基準: `2026 - installed_year`（推奨）
- 8/15 デモ時点の実年齢が表示され、保守的な部材選定の入力になります。

X. Other (please specify)

[Answer]: A. 2026年基準

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
