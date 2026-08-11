# Feasibility & Constraint Analysis — BE-5: Orcarouter による LLM 自動起票

> このファイルはステージ実行中に自動的に最新化されます。レビュー段階で観察を追記します。

## Interpretations

- 2026-08-11T21:56:23Z — ステージ本文の対象は Issue 記載の4ファイルだが、Q2 回答 A に従い `schemas/work_order.py` と `data/repair_parts.json` を本イニシアティブの対象ファイルに追加して内包することとした（上流 OR-2 / OR-4 の実装不在を BE-5 内で解消）。後続 Issue マージ時の委譲・強化へ切替可能な境界を保つ。

## Deviations

- 2026-08-11T21:56:23Z — 規制・コンプライアンス質問（PCI / HIPAA / SOC2 / データレジデンシー）は、`feasibility:c3` 学習（デモ評価者向け内部機能・PIIなし・認証スコープ外は N/A）に基づき質問群から省略し、質問ファイルの Sources で N/A と明記した。
- 2026-08-11T21:57:30Z — 前提修正（ユーザー指摘）: 初期成果物では「OR-2 / OR-4 は CLOSED だがファイルが main に不在」としていたが、ユーザー指摘「OR-2, OR-4 は実装済み、OR-3 は未実装」とリポジトリ実態確認（`schemas/work_order.py` / `services/prompts.py` / `services/llm_cost.py` が存在）により、前提を「OR-1/OR-2/OR-4 実装済み・再利用、OR-3 未実装・BE-5 内包」へ修正した。Q2 の回答 A（内包方針）は維持しつつ、内包対象を `repair_parts.json` とフォールバック応答のみに縮小し、3成果物（feasibility-assessment / constraint-register / raid-log）を更新した。

## Tradeoffs

- 2026-08-11T21:56:23Z — 原価の円換算は OR-4 の `llm_cost.py` 不在のため、`orcarouter.py` 内の関数境界で切出し内包とする案を選択。上流実装マージ時の委譲を容易にする境界設計を維持しつつ、デモ期間内に FR-6 の原価5フィールド記録を成立させる。内包（スコープ拡大）と依存待ち（受入条件未達リスク）のトレードオフで内包先行を選択。
- 2026-08-11T21:57:30Z — 前提修正後、原価円換算の内包は不要となり `llm_cost.py` の `calculate_and_enrich_cost` を再利用する方針へ変更。実装済みサービス再利用（重複排除・短工期）と内包（独立性）のトレードオフで、再利用を選択した（実装済み資産が受入条件を満たしているため）。

## Open questions

- 2026-08-11T21:56:23Z — OR-3（#14）・OR-4（#20）のマージ時期が不確定。BE-5 内包実装から委譲・強化への切替タイミングを、後続 Issue の進行状況に応じて construction 以降で確認する。
- 2026-08-11T21:57:30Z — OR-3（#14）のマージ時期が不確定。BE-5 内包のフォールバック実装（`orcarouter.py` 内 + `repair_parts.json`）から OR-3 実装への委譲・強化の切替タイミングを、後続 Issue の進行状況に応じて construction 以降で確認する。
