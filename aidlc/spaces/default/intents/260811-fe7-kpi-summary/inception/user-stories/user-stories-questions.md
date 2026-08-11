# User Stories — ストーリープランと明確化質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」のユーザーストーリー計画。
> 上流成果物（requirements.md / business-overview / component-inventory / team-practices /
> initiative-brief / wireframes）で確定済みの事項は省略し、実決定が必要な事項のみ質問する
> （project.md 学習 requirements-analysis:c1 と整合）。
>
> **一次ソースの確定（ユーザー指示）**: ユーザーストーリーは **GitHub Issue #19** に既に定義されている
> （受入条件・検証方法・実装方針）。本ステージでは Issue #19 を一次ソースとし、その受入条件を
> INVEST 準拠のユーザーストーリーとして整理・形式化する。Issue #19 の内容と矛盾する新規ストーリーは
> 生成しない。

## 計画概要（ベースライン）

- **ペルソナ開発方針**: 一次顧客「水道事業者オペレータ（監視担当）」を中心に、最終確認者
  「デモ評価者」の関心事を参照。詳細は Q1 で確定。
- **ストーリーフォーマット**: INVEST 準拠。「As a [ペルソナ], I want [ゴール], so that [価値]」+
  Given/When/Then の受入条件（3〜6 件、悲観パス含む）。
- **優先度**: MoSCoW。単一 proto-Unit（BU-1）完結のため全 Must-have を基本とし、分割粒度を Q2 で確定。
- **分割アプローチ**: 依存先順（型 → APIクライアント → 表示）で機能領域別に分割する案を推奨
  （scope-definition:c2 学習と整合）。
- **上流レビュー指摘の引き継ぎ**: requirements レビューで残った Major（カード表示順・KPI 配置）と
  Critical（DashboardClient テストファイルのスコープ）を本ステージで解消・明記する（approval-handoff:c6）。

## 明確化質問

### 前提確認

1. **ペルソナの範囲** — 本スコープのユーザーストーリーを書くペルソナの範囲は？

- A. 「水道事業者オペレータ（監視担当）」を一次、最終確認者「デモ評価者」を二次として 2 ペルソナ
  （デモ評価者はレビュアー視点として参照のみ）
- B. 「水道事業者オペレータ（監視担当）」の 1 ペルソナのみ
- C. その他
- X. Other (please specify)

[Answer]: A

> **導出根拠**: ユーザー指示「ユーザーストーリーは GitHub Issue #19 に作成されている」を受け、Issue #19 の
> 目的・作業内容・受け入れ条件をストーリーの実体として扱う。ペルソナは一次顧客（水道事業者オペレータ）と
> 最終確認者（デモ評価者）の 2 ペルソナ（business-overview と整合）。デモ評価者はレビュアー視点として参照のみ。

## 分割と優先度

2. **ストーリー分割の粒度** — FE-7（単一 proto-Unit BU-1）をどう分割するか？

- A. 機能領域別に 3〜4 ストーリーへ分割（型・APIクライアント / KPI表示・試算値注記 / スケルトンフォールバック。
  依存先順で独立にテスト可能）
- B. ユーザー価値スライスで分割（実データで KPI が見られる / 試算値と分かる / 停止中も崩れない）
- C. FE-7 全体を 1 ストーリーとして扱う（スコープが小さく分割不要）
- X. Other (please specify)

[Answer]: A

> **導出根拠**: Issue #19 の作業内容は「型・APIクライアント（FR-1〜3）→ 表示（FR-4〜6）→ ポーリング・
> フォールバック（FR-7〜8）」の依存先順で整理されており、機能領域別の 3 ストーリー＋内部品質 1 ストーリー
> （SeverityLevel 単一ソース）に分割する（scope-definition:c2 学習と整合）。各ストーリーは受入条件
> （Given/When/Then）で独立に検証可能。

## 表示仕様の解消（上流レビュー指摘の引き継ぎ）

3. **KPI カードの表示順と配置** — requirements レビューで指摘された「FR-5 のカード順（昇順）と承認済み
   ワイヤーフレーム（降順）の矛盾」をどう解消するか？承認済みワイヤーフレーム
   （`ideation/rough-mockups/wireframes.md`・initiative-brief §5、approval-handoff Q4=A）は
   **「監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト」の降順**で、KPI サマリは
   全面幅セクションとして DashboardClient 配下に描画し、コストカード見出しに「試算値」注記を
   常時表示するとしている。

- A. 承認済みワイヤーフレームに合わせる（降順・全面幅セクション・コストカード見出しに試算値注記。
  レビュー指摘 #3/#4/#9 を解消して引き継ぐ）
- B. requirements.md FR-5 の昇順を維持する（ワイヤーフレームの降順は採用しない）
- C. その他
- X. Other (please specify)

[Answer]: A

> **導出根拠**: 承認済みワイヤーフレーム（approval-handoff Q4=A / initiative-brief §5）を優先し、
> requirements レビュー指摘 #3/#4/#9 を解消する。カード順は降順（監視センサー数 / Level 3 / Level 2 /
> Level 1 / 推定削減コスト）、KPI サマリは全面幅セクション、コストカード見出しに「試算値」注記を常時表示する。

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: ペルソナの範囲は **A（オペレータ一次＋デモ評価者二次）**。デモ評価者はレビュアー視点として参照のみ。
- Q2: ストーリー分割は **A（機能領域別 4 ストーリー）**。型・API / KPI表示・試算値 / スケルトン / 内部品質。
- Q3: KPI カード表示順・配置は **A（承認済みワイヤーフレーム降順・全面幅・コストカード見出しに試算値注記）**。

ストーリーは **GitHub Issue #19** を一次ソースとし、その受入条件・検証方法・実装方針を INVEST 準拠の
ストーリーへ整理・形式化する。Issue #19 と矛盾する新規ストーリーは生成しない。

この内容でユーザーストーリーを生成してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct

## モブ編成トリアージ（Round 1 contribution 統合）

3 サポート（design / developer / quality）の contribution から、人間判断が必要な 2 点を提示する。

4. **Level 1 カードの色** — ラフモック `wireframes.md:16` は「Level 1=青」と注記するが、権威ソース
   `docs/ui-wireframe.md:16,21` は Level 1 を **lime 黄緑 `#84cc16`** と定義し、
   `frontend/src/lib/severity.ts:42,44` も `color: "#84cc16"` を持つ（design agent OBJECT）。

- A. 権威ソース（docs/ui-wireframe.md / lib/severity.ts）に合わせ **lime 黄緑**を採用し、
  `getSeverityMeta(1)` を再利用する（ラフモックの「青」はラフ段階の近似として採用しない。
  US-4 の深刻度単一ソース化と一貫）
- B. ラフモックの「青」を採用する（wireframes.md の注記を維持）
- C. その他
- X. Other (please specify)

[Answer]: A

5. **NFR-1 カバレッジゲートのローカル/CI 一致（Minor #7）** — 現状 `frontend/package.json` の `test` は
   `vitest run`（coverage なし）・`vitest.config.mts` に coverage 設定なし・CI のみ CLI フラグで 80% 強制。
   team.md Mandated「ローカル `npm run test` でも CI と同じゲートを強制」を満たす実現手段は？

- A. **`vitest.config.mts` に coverage 設定（provider: v8・thresholds で lines/functions/branches/statements 各 80%）を追加し、`package.json` の `test` を `vitest run --coverage` に変更、CI の CLI フラグを設定と一致させる**。FE-7 のスコープに vitest.config.mts / package.json を含める（品質ゲートの恒久化）
- B. CI は現行 CLI フラグのまま、ローカルは `npm run test -- --coverage`（同じしきい値）を NFR-1 に明記する（スコープ追加なし・ドキュメント解決）
- C. その他
- X. Other (please specify)

[Answer]: A
