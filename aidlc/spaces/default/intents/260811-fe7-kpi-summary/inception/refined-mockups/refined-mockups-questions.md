# Refined Mockups — 明確化質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の Refined Mockups ステージ質問。
> 上流成果物（wireframes / user-flow / stories / requirements / team-practices）で高度に確定済みの
> 項目はリード導出で回答を確定し、実決定が必要な事項のみ人間に確認する
> （approval-handoff:c2 / requirements-analysis:c1 学習と整合）。

## Q1: 「試算値」注記の表示構造（実決定事項 — 承認ゲートで確認）

**背景:** User Stories レビュー（advisory）の **Major 指摘**により、試算値注記の文言が
上流で不一致のまま残っている。

| 出所 | 文言 |
|---|---|
| requirements.md FR-6 | 結合リテラル **「試算値（前提: `docs/business-model.md`）」** を常時表示 |
| stories.md US-2 AC3 | **2 段構成** — コストカード見出しにラベル「試算値」併記 + カード本文に
  インライン短文「前提: `docs/business-model.md`」を常時表示 |
| wireframes.md（承認済み Q2=A） | 見出し「推定削減コスト · 試算値」 + カード下部「前提: docs/business-model.md」 |

**リード導出の推奨（Q1=A）:** **2 段構成**で確定する。wireframes（承認済み）と US-2 AC3 が
いずれも 2 段構成を指示しており、カード見出し（視認性）と前提文書の注記（透明性）を分離する
ことで「根拠のない金額を断定的に見せない」（business-model.md §3.5）を満たす。表示文字列は
「試算値」と「前提: docs/business-model.md」に固定し、テストは 2 文字列の完全一致アサート
+ 連結文字列「試算値（前提: docs/business-model.md）」の部分一致アサートを併用して
FR-6 の文言要件（両文字列が常に画面にあること）を満たす。

- [x] A. **2 段構成（見出しラベル「試算値」+ カード本文「前提: docs/business-model.md」）を採用**（推奨）— 承認ゲートで人間確認済み（2026-08-11）
- [ ] B. 結合リテラル 1 行「試算値（前提: docs/business-model.md）」をそのまま表示

## Q2: モック・テストフィクスチャの数値（リード導出 — 確認のみ）

**背景:** User Stories レビュー **Minor 1** の指摘。fetchKpiSummary のテストフィクスチャを
旧 `MOCK_KPI_DATA` の値（totalSensors: 1240 / estimatedCostSavedYen: 1_420_000）と一致させると、
「モック数値が消えた」ことを確認する非存在アサート（`queryByText("1,240")` /
`queryByText("142万円")`）が偽陰性になる。

**リード導出の回答:** フィクスチャは旧値と異なる値に固定する。
例: `totalSensors: 999` / `level1Count: 8` / `level2Count: 3` / `level3Count: 1` /
`estimatedCostSavedYen: 800_000`。加えてモックアップの表示例は business-model.md §3.4 の
デモ算出例（Level 1×8 / Level 2×3 / Level 3×1 → **204.8万円**）を参照値として使用する
（Minor 4 の引き継ぎ）。

- [x] A. フィクスチャは旧 MOCK 値と異なる値に固定（推奨・確定済み）

## Q3: レスポンシブ挙動（リード導出 — 確認のみ）

**背景:** wireframes（承認済み）はデスクトップ / ラージグリッドのみを示す
（レビュー Minor 5）。現状コード `KpiSummary.tsx` は `grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`。
ダッシュボード中心の変更で、モバイル専用レイアウトはスコープ外。

**リード導出の回答:** 現状のレスポンシブ（1 列 → 2 列 → 5 列）を維持し、モバイル対応は
表示崩れ防止のスタックのみ（スコープ外として明記）。

- [x] A. 現状レスポンシブ維持・モバイル専用レイアウトはスコープ外（確定済み）

## Q4: スケルトンのアニメーション（リード導出 — 確認のみ）

**背景:** wireframes（承認済み Q3=A）は「カードと同じ形状のグレーアニメーション（スケルトン）5 枚」。
Tailwind v4 の `animate-pulse` が最もシンプルな実装で、インタラクションデザインパターン
（スケルトンローディング）と一致する。

**リード導出の回答:** `animate-pulse` を使用し、`prefers-reduced-motion` ではアニメーションを
無効化する。スケルトンは静的な形状のみ表示し、数値テキストは一切表示しない（stale 値非表示の担保）。

- [x] A. animate-pulse 使用 + prefers-reduced-motion 対応（確定済み）

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: 試算値注記の表示構造は **A（2 段構成）** — コストカード見出しにラベル「試算値」を併記し、
  カード本文に「前提: docs/business-model.md」のインライン短文を常時表示。テストは 2 文字列の完全一致
  + 連結文字列の部分一致で FR-6 要件（両文字列が常に画面にある）を満たす。
- Q2: テストフィクスチャは旧 MOCK 値（1240 / 142万円）と異なる値に固定（例: totalSensors: 999 /
  estimatedCostSavedYen: 800_000）。表示例は business-model.md §3.4 のデモ算出（204.8万円）を参照値とする。
- Q3: レスポンシブは現状維持（1 列 → 2 列 → 5 列）。モバイル専用レイアウトはスコープ外。
- Q4: スケルトンは animate-pulse + prefers-reduced-motion 対応。数値テキストは一切表示しない。

上記の内容で Refined Mockups 成果物（mockups.md / interaction-spec.md / design-system-mapping.md /
accessibility-checklist.md）を確定してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumptions & Open Questions

- 上記 Q2〜Q4 は上流で確定済みのため、人間確認は Q1 のみに絞る（質問数を実決定事項に絞る学習と整合）。
- その他の未確定項目はなし（None.）

## Sources

- [wireframes] `ideation/rough-mockups/wireframes.md`（カード構成・試算値注記配置・スケルトン・アクセシビリティ注記）
- [user-flow] `ideation/rough-mockups/user-flow.md`（ハッピーパス / エラーフロー / スケルトン切替）
- [stories] `inception/user-stories/stories.md`（US-1〜4・試算値注記 2 段構成・Minor 1/4 引き継ぎ）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-6 結合リテラル・FR-7 ポーリング・FR-8 スケルトン・NFR-5 UI 一貫性）
- [team-practices] `inception/practices-discovery/team-practices.md`（変換境界・フォールバック Q10 / 単一ソース Q9 / coverage ゲート）
