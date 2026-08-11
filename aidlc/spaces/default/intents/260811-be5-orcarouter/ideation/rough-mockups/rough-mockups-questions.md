# Rough Mockups Questions — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Sources

- [desc] Initial description: "GitHub内のISUUESを確認し、ISSUE#13「BE-5: services/orcarouter.py によるLLM自動起票の実装」を実装してください。短期開発で時間が限られているので、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。手が離せないので自動承認でOKです。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル）。
- [scope-doc] 前段スコープ定義書 `ideation/scope-definition/scope-document.md`（イン/アウト境界・依存関係 D-1〜D-7・実装順序・アウトオブスコープ: フロントエンド変更なし）。
- [backlog] 前段インテント・バックログ `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・価値連鎖図・受入条件11件）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"

## Q1. 非UIイニシアティブとしてのラフモック扱いの確定

本スコープ（BE-5）はフロントエンド変更なしの API バックエンドのみ（スコープ定義書アウトオブスコープ: フロントエンド変更なし）のため、本ステージはステージ本文 Step 5 の非UIパス（システムコンテキスト図・主要相互作用フロースケッチ）で実行します。UI 向けワイヤーフレーム・アクセシビリティ注記は生成しません。この扱いで確定しますか？ [intent] [scope-doc] [backlog]

- A. 確定する — 非UIパス（システムコンテキスト図 + API 相互作用フロー）でラフモックを作成。UI ワイヤーフレーム・アクセシビリティ注記は生成しない
- B. 調整する — 扱いに変更がある（Other で指定）
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- BE-5 は API バックエンドのみの非UIイニシアティブのため、ラフモックはシステムコンテキスト図（`POST /alerts/{id}/work-order` → `orcarouter.py` → Orcarouter API / フォールバック部材マスタ → `WorkOrder`）と API 相互作用フロー（成功・5xx/ネットワーク1回リトライ後フォールバック・4xx/パース失敗即フォールバック・キャッシュヒット）で作成する。 [Q1] [scope-doc] [backlog]
- 主要なシステム相互作用・データフロー（D-1〜D-7・価値連鎖図）は上流成果物で確定済みのため、本ステージで新たに追加する実決定はない。 [scope-doc] [backlog]
- UI ワイヤーフレーム・情報階層・ブランドガイドライン・デバイス/フォームファクタ・アクセシビリティ要件は非UIスコープのため対象外とする。 [scope-doc]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- BE-5 は非UI（API バックエンドのみ）イニシアティブとし、ラフモックはシステム相互作用図として作成すると仮定する。 [assumption]
- 主要システム相互作用・データフローはスコープ定義書 D-1〜D-7 とインテント・バックログの価値連鎖図で確定済みであり、本ステージで新たな追加決定は発生しないと仮定する。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
