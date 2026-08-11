# Refined Mockups — ステージ日誌

> ステージ進行中の観察記録。ステージ開始時に自動生成され、ステージ実行中に自動更新される。
> 手編集はしない。

## Interpretations

- 2026-08-11T11:00:00Z — Q1（試算値注記の表示構造）を承認ゲートで人間確認し **A（2段構成）** に確定した。User Stories レビュー Major 指摘（FR-6 結合リテラル vs US-2 AC3 2段構成の乖離）を本ステージで解消する。表示文字列は「試算値」（見出しラベル）と「前提: docs/business-model.md」（カード本文）に固定し、テストは 2 文字列の完全一致 + 連結文字列の部分一致で FR-6 要件（両文字列が常に画面にある）を満たす設計とした。Q2〜Q4 は上流確定事項のためリード導出（モック値は旧 MOCK と異なる値・レスポンシブは現状維持・スケルトンは animate-pulse + prefers-reduced-motion）。
- 2026-08-11T11:05:00Z — Refined Mockups 成果物（mockups.md / interaction-spec.md / design-system-mapping.md / accessibility-checklist.md）を生成。KPI カード5枚の降順（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）、h2 見出し「KPI サマリ」+ aria-labelledby、Level 1 は lime（getSeverityMeta(1) 再利用）、コストカード 2 段構成の試算値注記、スケルトンは DashboardClient が data-testid="kpi-skeleton" で描画・KpiSummary は表示専用維持、を仕様化。
- 2026-08-11T11:10:00Z — Q1=A（試算値注記 2 段構成）を質問ファイル・全成果物に反映。User Stories レビュー Major 指摘（FR-6 結合リテラル vs US-2 AC3 2段構成の乖離）を本ステージで解消し、「実装・QA は 2 段構成を正とし、FR-6 の『結合リテラル』表記は 2 段構成の表示内容を言い表したものと解釈する」と mockups.md / interaction-spec.md に明記した（approval-handoff:c6 学習）。テストは 2 文字列の完全一致 + 連結文字列の部分一致で FR-6 要件を満たす設計とした。
- 2026-08-11T11:30:00Z — §12a レビュー（aidlc-product-lead-agent / advisory・単一パス・iteration 1）が **READY** を返却。REVIEW_COMPLETED（READY）を記録済み。指摘: Major 2 件 — (1) `section`/`h2`/`aria-labelledby`/`aria-busy` の所有が interaction-spec（KpiSummary 所有）と mockups スケルトン図（h2 がスケルトン中も常時表示）で不一致。Application Design で DashboardClient が section（h2 + aria-labelledby + aria-busy）を常時描画し配下でスケルトン/カードグリッドを切替える構成へ一元確定する。(2) モックアップ表示例（204.8万円・counts 8/3/1）とテストフィクスチャ（estimatedCostSavedYen: 800_000→80万円）のコスト値が不一致。functional-design で fixture を 2_048_400 に揃えるか設計参照専用と明記する。Minor 3 件 — (3) `[interaction-design-patterns]` タグの Sources 未登録（mockups.md / accessibility-checklist.md）。(4) 連結文字列「試算値（前提: docs/business-model.md）」の部分一致アサートは 2 段構成の実レンダリング（金額を挟み全角括弧なし）ではマッチしない。正規表現 `/試算値[\s\S]*前提: docs\/business-model\.md/` か完全一致のみに一本化。(5) SEVERITY_META の label（Level 2 進行性漏水 / Level 3 管路破裂）とカード実ラベル（Level 2 警告 / Level 3 破裂リスク）の不一致。Q9=A 単一ソース宣言との整合を明記。advisory のため修正ループなし・指摘は承認ゲートで人間確認に供する。

## Deviations

## Tradeoffs

## Open questions
