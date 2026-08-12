# Scope Definition & Prioritization — BE-5: Orcarouter による LLM 自動起票

> このファイルはステージ実行中に自動的に最新化されます。レビュー段階で観察を追記します。

## Interpretations

- 2026-08-12T00:00:00Z — スコープは単一 Issue（BE-5）完結とし、`scope-definition:c1` 学習（相互依存する複数ファイルの1 Issue 完結変更は単一 proto-Unit として扱う）に従い、バックログは単一 proto-Unit で表現する。

## Deviations

- 2026-08-12T00:00:00Z — `approval-handoff:c2` 学習（スコープに該当しない質問は省略し実決定に必要な質問のみ提示）に従い、ステージ本文の定型質問（市場検証・モックアップ・モブ編成等）は省略し、スコープ境界とバックログ表現の2点のみ実決定質問として提示する。

## Tradeoffs

- 2026-08-12T00:00:00Z — バックログ表現は「単一 proto-Unit」（1 Issue 完結・依存が密）と「機能別複数 proto-Unit」（分割管理）を比較。実装順序は依存先順（型 → APIクライアント → 表示 / サービス → ルーター）で決まるため、`scope-definition:c1` に従い単一 proto-Unit を選択した。

## Open questions

- 2026-08-12T00:00:00Z — なし（None.）。スコープ境界・優先度・依存・納期は上流（intent-statement / feasibility / 制約レジスタ）とチーム実践で確定済み。
