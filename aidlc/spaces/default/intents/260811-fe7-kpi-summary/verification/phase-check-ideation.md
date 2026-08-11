# Phase Check — Ideation → Inception（境界検証）

> イデアーションからインセプションへのハンドオフ前に、全イデアーション成果物の整合性を検証する。 [approval-handoff]

## 1. Intent → Scope → Intent Backlog の整合性

| 検証項目 | 結果 | 根拠 |
|---|---|---|
| Intent Statement の対象（6ファイル）が Scope Document と一致 | ✅ 一致 | intent-statement「Initial Scope Signal」/ scope-document「In Scope（対象）」のファイル列挙が同一 |
| Scope Document の In Scope が Intent Backlog の BU-1 に反映 | ✅ 反映 | BU-1「対象ファイル」が6ファイルを列挙、変更内容①〜⑥が scope-document の In Scope と1対1対応 |
| Out of Scope が Intent Statement / Constraint Register と整合 | ✅ 整合 | `today_detections` 対象外・バックエンド変更なし・外部BI・AWS は各成果物で一貫 |
| 配線方式（DashboardClient ポーリング・page.tsx Server Component 維持）が全成果物で一貫 | ✅ 一貫 | intent-statement / scope-document / feasibility / constraint-register TC-5 |
| 単一 proto-Unit（BU-1）・依存先順の決定が反映 | ✅ 反映 | intent-backlog「バックログ方針」・scope-document Assumptions |

## 2. 全スコープ項目に実現性（Feasibility）の裏付けがあるか

| スコープ項目 | Feasibility の裏付け | 結果 |
|---|---|---|
| `fetchKpiSummary()` 追加（BE-8 配線） | 「BE-8 との配線」= 成立（既存 `unwrap` / `toCamelCase` パターン） | ✅ |
| `MOCK_KPI_DATA` 削除（実データ化） | 「KPI 表示の実データ化」= 成立 | ✅ |
| カード構成変更（本日の検知数削除・Level 1 追加） | 「本日の検知数カード」対象外 /「レベル1カードの追加」= 成立（BE-8 が `level1_count` を返す） | ✅ |
| `SeverityLevel` 単一ソース化 | 「SeverityLevel 単一ソース化」= 成立（`0 \| 1 \| 2 \| 3` に統一） | ✅ |
| スケルトン表示（白画面回避） | 「バックエンド停止時の動作」= 成立 | ✅ |
| `page.tsx` Server Component 維持 | 「Server Component 維持」= 成立（DashboardClient 側で取得） | ✅ |
| 試算値注記の常時表示 | 「スキーマ差分」= `is_estimate` に依存せず定常表示で充足 | ✅ |

## 3. ハンドオフ時の残課題（Inception への引き継ぎ）

- 上流レビュー（rough-mockups product-lead）の Major 2件は、イニシアティブ・ブリーフで解決済み（intent-backlog を明示参照 / 試算値注記を「カード内の常時表示インライン短文」に確定）。実装時の受入条件として「試算値」注記は常時表示で判定する。
- Inception は Reverse Engineering から開始。codekb スナップショットは reverse-engineering 時点で固定されるため、実装前に grep 等で現状を再確認する（project.md 学習 asc-c2 準拠）。

## 総合判定

**✅ パス（Inception への進行を許可）。** Intent → Scope → Intent Backlog の整合、全スコープ項目の実現性裏付けとも満たしている。実装ブロッカー（Critical）なし。

## Sources

- [approval-handoff] `ideation/approval-handoff/initiative-brief.md`（スコープ境界・リスク・ビルド順序）
- [intent] `ideation/intent-capture/intent-statement.md`（成功指標・対象6ファイル・配線方式）
- [scope-document] `ideation/scope-definition/scope-document.md`（In Scope / Out of Scope）
- [intent-backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit BU-1）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術成立性・リスク）
- [constraint-register] `ideation/feasibility/constraint-register.md`（TC-1〜TC-9）
- [review] `ideation/rough-mockups/wireframes.md` の Review 節（Major 2件）
