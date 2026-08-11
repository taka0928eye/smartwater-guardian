**Collaborator:** aidlc-design-agent

## Contribution

リード草稿（`personas.md` / `stories.md`）を、承認済みワイヤーフレーム（`ideation/rough-mockups/wireframes.md`・`initiative-brief.md` §5）・権威ある深刻度カラーソース（`docs/ui-wireframe.md` / `frontend/src/lib/severity.ts`）・現行フロント実装（`KpiSummary.tsx` / `page.tsx` / `DashboardClient.tsx` / `Header.tsx`）と突合し、UX・ペルソナ忠実度の観点で検証した。

**総評**: ストーリー構成・カード順（降順）・全面幅・試算値注記・スケルトンフォールバックの大枠は承認済みコンセプトと整合しており **承認**に値する。ただし表示仕様のうち (1) Level 1 カードの色が権威ソースと衝突、(2) KPI サマリの可視 `h2` 見出しが現状存在せずワイヤーフレームの見出し階層と不整合、(3) 試算値注記の配置がストーリーとワイヤーフレームで揺れる、の 3 点と、スケルトンのアクセシビリティ要件（`aria-busy` / `aria-live` 方針）の不足を指摘する。以下、該当ストーリー ID とファイル位置を明示する。

### 1. ペルソナ忠実度（personas.md）— 概ね適切、1 点だけ整合補足

- **AGREE**: P1 オペレータ一次 / P2 デモ評価者二次の位置づけは `business-overview.md`・Issue #19 と整合。P2 を「レビュアー視点として参照のみ」としストーリーの主語にしない判断は、デモ成功（MOCK 撤去・試算値注記・スケルトン）を受入条件として検証する視点として正しい。
- **補足提案（軽微）**: `personas.md` は P1 / P2 の 2 ペルソナのみだが、`stories.md:14` の US-4 はペルソナ列が「開発者」となっている。内部品質ストーリーのアクターである「開発者」はエンドユーザーのペルソナではないため、`personas.md` の「ペルソナ関係と優先順位」節に「開発者はペルソナ外のアクター（内部品質ストーリーの主語）」と 1 行追記すると、2 ペルソナ構成との整合が明示される。

### 2. US-2「Level 1 カードの色は『青』でなく既存の深刻度シングルソース（lime 黄緑）を再利用すべき」【修正】

- **根拠**: `ideation/rough-mockups/wireframes.md:16` は「Level 1=青」と注記するが、権威ある深刻度カラーソース `docs/ui-wireframe.md:21` は Level 1 を `#84cc16`（黄緑 / `text-lime-500` / `bg-lime-500`）と定義し、`:16` で「Level 1 を緑＝正常系の色に置いてはならない。この区別がデモの訴求の核心」と明記している。`frontend/src/lib/severity.ts:42` も `color: "#84cc16"`・`:44` で `accentClass: "border-lime-200 text-lime-700"` を持ち、地図マーカー（FE-3）・アラートバッジ（FE-5）はこの lime を共通利用している。
- **影響**: ラフモックの「青」を採用すると、同一深刻度（Level 1）が画面内で KPI カードのみ別色になり、監視オペレータの認知一貫性（Nielsen: 一貫性と標準）を損なう。FE-7 自身が US-4 で「深刻度メタの単一ソース化」を行う以上、表示も単一ソースに揃えるべき。
- **提案**: US-2 の受入条件に「Level 1 カードのアクセント・ラベルは `getSeverityMeta(1)` を再利用する（lime 黄緑。ワイヤーフレーム注記の『青』はラフ段階の近似として採用しない）」を追加。カードラベルは現行の L3/L2 の短縮ラベル（「Level 3 破裂リスク」「Level 2 警告」）のパターンに合わせ、UI-1 の核心である「微小漏水（AI検知）」を含む文言（例: 「Level 1 微小漏水（AI検知）」）を US-2 で確定する。ラベル・色の決定は次の `refined-mockups` で視覚仕様化する際の起点にする。

### 3. US-2「KPI サマリの可視 `h2` 見出しが現状なく、見出し階層（h1→h2→p）と不整合」【追加提案】

- **根拠**: `ideation/rough-mockups/wireframes.md:65` は「ページ `h1` → KPI サマリ `h2` → 各カードは見出しを使わず `p`（label）」と規定。現状 `frontend/src/components/dashboard/KpiSummary.tsx:80` は `<section aria-label="KPI サマリ">` のみで可視見出しがなく、`Header.tsx:79` の `h1` → 地図・一覧の `h2`（`DashboardClient.tsx:51`）という階層に KPI が並ばない（見出しレベルが飛ぶ）。
- **提案**: US-2 の受入条件に「KPI サマリセクションに見出し `h2`「KPI サマリ」を追加し、セクションを `aria-labelledby` で見出しに紐付ける。各カードは引き続き `p`（ラベル）のまま」を追加。グリッド構成（`lg:grid-cols-5`）は NFR-5 の通り維持する。

### 4. US-2「試算値注記の配置をワイヤーフレームの 2 段構成（見出しラベル + 本文前提注記）に確定」【修正】

- **根拠**: `ideation/rough-mockups/wireframes.md:32` は「見出しに『試算値』ラベルを併記」、`:34` は「カード下部に『前提: docs/business-model.md』注記」の 2 段構成。一方 `stories.md:45`（US-2 AC3）は「コストカード見出しに固定リテラル『試算値（前提: `docs/business-model.md`）』」と 1 行で記述しており、実装時に「見出しに全量」か「見出し + 本文に分割」かで揺れうる（requirements レビュー Major #9 の再発リスク）。
- **提案**: 承認済みコンセプトに合わせ、AC3 を「コストカード見出しに『試算値』ラベルを併記し、カード本文に『前提: `docs/business-model.md`』を常時表示インライン短文として表示する」に確定する。固定リテラル（「試算値」「前提: `docs/business-model.md`」）は維持し、配置のみ 2 段構成にする。ラベル・前提注記はいずれも可視テキストのためスクリーンリーダーでも読まれ、WCAG 1.3.1 / 1.4.1 の観点で望ましい。

### 5. US-2「KPI セクションの DOM 配置を『DashboardClient 先頭・grid 外・全面幅』に明確化」【追加提案】

- **根拠**: `stories.md:47`（US-2 AC5）は「全面幅セクションとして DashboardClient 配下に描画」とあるが、現状 `frontend/src/app/page.tsx:164` は `<KpiSummary kpiData={MOCK_KPI_DATA} />` を `<main>` 直下（DashboardClient の外・上）に描画している。DashboardClient に移す際、`DashboardClient.tsx:47` の `lg:grid-cols-3` グリッドのどの位置に置くかが未規定だと、実装時に 3 列グリッドの 1 セルへ誤配置するリスクがある（requirements レビュー Major #4 の再発）。
- **提案**: AC5 を「KPI サマリを DashboardClient の返却 JSX 先頭に、`lg:grid-cols-3` グリッドの外側の全面幅ブロックとして配置し、その下に地図 / アラート一覧のグリッドを描画する」に明確化する。

### 6. US-3「スケルトン中のアクセシビリティ要件（`aria-busy` / `aria-live` 方針）を AC に追加」【追加提案】

- **根拠**: `ideation/rough-mockups/wireframes.md:67` は「スケルトン中は `aria-busy="true"`」と規定するが、`stories.md:67`（US-3 AC5）は testId（`kpi-skeleton`）のみ言及で、`aria-busy` に触れていない。
- **提案**: AC5 に「スケルトン中は KPI セクションコンテナに `aria-busy="true"` を付与し、取得成功時に解除する」を追加。あわせて **`aria-live` は KPI セクション全体に付与しない**方針を明記する（5 秒ポーリングで値が更新されるたびにスクリーンリーダーが読上げ、ノイズになる）。値の自動更新は監視運用上必須のため WCAG 2.2.2（Pause, Stop, Hide）の「essential」例外に該当するが、その判断をストーリーの注記として残す。
- **補足**: スケルトン→実データの状態遷移を伝えたい場合は、`aria-live="polite"` を KPI セクションではなくステータス 1 行（例: 「KPI データを読み込み中」→「最新値を表示中」）に限定して付与する方式が低ノイズで望ましい。これは実装詳細として `refined-mockups` に引き継ぐ。

### 7. US-3「価値記述『監視を継続でき』は過剰表現」【修正（軽微）】

- **根拠**: `stories.md:59` の so that「監視を継続でき、古い値を最新として誤解しない」のうち、「監視を継続でき」はスケルトン表示中は KPI 値が見えない実態とやや過剰。実際の価値は「障害時も白画面にならず、データ取得中であることが視認できる」「古い値を最新と誤認しない」。
- **提案**: so that を「障害時も白画面にならず、データ取得中であることが分かる。古い値を最新として誤認しない」等に微修正する（受入条件の実質は不変）。

### 8. US-4（SeverityLevel 単一ソース化）— AGREE

UX 観点でも、表示メタを `lib/severity.ts` に集約することで Level 1 カードの色・ラベルが地図・アラートと揃い、監視オペレータの認知一貫性に寄与する。上記 2 の「Level 1 カードは `getSeverityMeta(1)` を再利用」と相互補完の関係にある。ストーリーとしての妥当性に異論なし。

## Positions

- AGREE: ペルソナ構成（P1 オペレータ一次 / P2 デモ評価者二次・参照のみ）と、P1 をストーリー主語にする方針。
- AGREE: カード順（監視センサー数 → Level 3 → Level 2 → Level 1 → 推定削減コスト）の降順・全面幅セクション・コストカード見出しへの試算値注記（Q3=A）は承認済みワイヤーフレームと一致。
- AGREE: スケルトンフォールバック（US-3）と「`MOCK_KPI_DATA` を実データの代わりに表示しない」（Q10: A）の設計。
- OBJECT: ラフモックの「Level 1=青」（`wireframes.md:16`）を表示仕様に残すと、権威ソース（`docs/ui-wireframe.md:16,21` / `lib/severity.ts:42,44`）の lime 黄緑と衝突し、画面内で同一深刻度の色が分裂する。`getSeverityMeta(1)`（lime）を再利用すべき。
- OBJECT: KPI サマリに可視 `h2` 見出しがない現状（`KpiSummary.tsx:80`）を US-2 で維持すると、ワイヤーフレームの見出し階層（h1→h2→p、`wireframes.md:65`）に反する。`h2`「KPI サマリ」を追加すべき。
- OBJECT: 試算値注記を「コストカード見出し 1 行」（`stories.md:45`）にすると、ワイヤーフレームの 2 段構成（見出しラベル `wireframes.md:32` + 本文前提注記 `:34`）と実装が揺れる。「見出し: 『試算値』ラベル併記 / 本文: 『前提: `docs/business-model.md`』」に確定すべき。
- OBJECT: US-3 の「so that 監視を継続でき」（`stories.md:59`）はスケルトン表示中の実態と過剰。障害検知・誤認防止の価値記述に修正すべき。
- OBJECT: US-3 に `aria-busy` と `aria-live` 方針の AC が無い。スケルトン中 `aria-busy="true"`（`wireframes.md:67`）を追加し、セクション全体の `aria-live` は不採用（5 秒自動更新の読上げノイズ回避）と明記すべき。
