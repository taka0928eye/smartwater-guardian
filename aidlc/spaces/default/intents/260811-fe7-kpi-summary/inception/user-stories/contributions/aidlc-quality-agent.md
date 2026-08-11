**Collaborator:** aidlc-quality-agent

## Contribution

QA リードとして、リード草稿 `stories.md`（FE-7 ユーザーストーリー）を受入条件の**検証可能性（テスト可能性）**の観点でレビューした。総評は**承認方向**だが、テストが確実に赤→緑へ落ちるための具体化・スコープ補完が複数必要。特に **`page.test.tsx` のスコープ漏れ**と **NFR-1 のローカル/CI カバレッジゲート一致（Minor #7）の未解決**の 2 点は、このまま実装に入ると既存テストが壊れる／品質ゲートが守れないため、修正を求める。

### 全体所見

- 4 ストーリーすべて Given/When/Then で、正常系＋悲観パスの両方が記述されている点は妥当。US-3 で `DashboardClient.test.tsx` をスコープに含めた判断（Critical #2 の一部解消）と、US-4 で `lib/severity.ts` をスコープに含めた判断（Minor #8 解消）は正しい。
- 一方、requirements レビュー指摘 **Critical #2** は `DashboardClient.test.tsx` だけでなく **`page.test.tsx` にも波及する**が、stories.md のどこにも `page.test.tsx` が言及されていない。**Minor #7**（coverage 設定の実態整合）はどのストーリーの受入条件・実装対象にも含まれていない。この 2 点はテスト可能性の欠落として最優先で是正する。

### ストーリー別検証

#### US-1（`KpiSummary` 型定義と `fetchKpiSummary` API クライアント）— 概ね可、2 点を具体化

- AC#1 は可。ただし新しい変換経路（`isEstimate` / `assumptionDoc` を含む 7 フィールド）の snake→camel 変換を**全フィールド**アサートする fixture を `api.test.ts` に用意すること。`totalSensors` だけの検証では返り値契約の完全性を担保できない。
- AC#2 は既存 `api.test.ts` の `fetchSensors` 異常系テスト（`axiosError` ヘルパー＋`ApiError` 変換）と同じパターンで実装可能。`4xx/5xx` 両方の変換を確認するケースを推奨する。
- **AC#3「変換は `lib/api.ts` 境界で 1 回だけ」はランタイムテスト単体では検証不能**。テストで検証できるのは「返り値が camelCase であること」までで、「他レイヤーで変換していない」ことはテストからは観測できない。検証手段を「出力の camelCase アサート + コンポーネント側に `toCamelCase`／snake_case キー直参照が無いことの grep 静的確認」と AC に明記することを推奨する。
- AC#4（`any` 不使用）は `npm run build` / `tsc --noEmit` で担保される。AC に「検証は type-check / build で行う」と書くと実体が明確になる。

#### US-2（実データ表示と「試算値」注記）— 3 点を具体化・1 点はスコープ修正

- **AC#1「降順で表示する」の観測点が未規定**。現在の `KpiSummary.test.tsx` はラベルの存在（`getByText`）しか検証しておらず、DOM 上の出現順を検証していない。「testId が `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2` → `kpi-card-level1` → `kpi-card-cost` の順に出現すること」を AC に明記する（例: `container.querySelectorAll('[data-testid^="kpi-card-"]')` の順序アサート）。
- **AC#2（Level 1 カード追加）のカードラベルと testId が未確定**。表示文言（例: 「Level 1 微小漏水」。`lib/severity.ts` の `getSeverityMeta(1).label` と整合させる）と testId（`kpi-card-level1`）を固定し、`getByText` の完全一致を決定的にする。あわせて既存テストの `kpi-card-today` / `todayDetections` の撤去・`BASE_KPI` データの作り替え（`todayDetections` → `level1Count`）を TDD の Red 工程として明示する。
- **AC#3 の「試算値（前提: `docs/business-model.md`）」は表示文字列を確定**。要件 FR-6 のバッククォートは Markdown 表記であり表示文字列に含まれるのか、含まれないのか（`試算値（前提: docs/business-model.md）`）を確定し、テストの完全一致アサート（`screen.getByText("試算値（前提: docs/business-model.md）")`）を決定的にする。
- **【要スコープ修正】AC#4（`page.tsx` から `MOCK_KPI_DATA` 撤去）の検証に `page.test.tsx` の変更が必須だが、実装対象に含まれていない**。後述の Position P1。

#### US-3（スケルトンフォールバック）— Critical #2 の半分は解消、残りと細部を修正

- Critical #2 のうち `DashboardClient.test.tsx` をスコープに含めたのは正しい。ただし **`page.test.tsx` も同じ理由で壊れる**。現状 `page.test.tsx` の `@/lib/api` モックは `fetchSensorsGeoJson` / `fetchAlerts` のみで、`DashboardClient` が `fetchKpiSummary` を呼ぶと `undefined` 参照で失敗する（FR-7 で KPI ポーリングを足した時点で発症）。→ Position P1。
- **AC#1 の状態遷移のテストケースを 3 状態に明示**。FR-8 は「失敗後に最終成功値を据え置かない（再スケルトン）」を要求するため、(a) 初回ローディング中＝スケルトン、(b) 取得成功＝カード値表示、(c) **成功後に失敗＝再スケルトン（stale 値を表示しない）** の 3 ケースを網羅する。現行 AC は (a)(b) が主で (c) が明示されていない。分岐カバレッジ 80% のためにも必要。
- **AC#2（モック非表示）は AC#1 と同一テスト内で `queryByText("1,240")` / `queryByText("142万円")` の非存在アサートとして統合できる**旨を明記すると良い。
- **AC#3（クリーンアップ）は既存 `DashboardClient.test.tsx` のアンマウントテスト（L164-181）と同じフェイクタイマー手法で実装可能**。アンマウント後 `advanceTimersByTime` で `fetchKpiSummary` が再呼び出しされないことを検証する。
- **AC#4（5 秒統一）は `ALERT_POLL_INTERVAL_MS` を単一の間隔定数として共用し、`advanceTimersByTime(5000)` で `fetchKpiSummary` が再呼び出しされることを検証**する。同じ定数を使うことで「KPI とアラートで周期が一致」をコード上も保証できる。
- **AC#5 の testId「例: `kpi-skeleton`」は「例」を外して `kpi-skeleton` に固定**し、単一コンテナかカード毎かも決める（全カード一括でスケルトンに切り替わるため、コンテナ単一 testId で十分と考える。観測点を 1 つに絞れるためテストが単純になる）。
- **スケルトン描画の所在が未確定**。KpiSummary 自身が `kpiData` を受ける契約を `KpiSummary | null` に変えてスケルトンを内包するのか、DashboardClient がスケルトン用要素を別途描画するのかで、テストファイルの責務分割が変わる。US-2/US-3 の境界として確定させること（例: KpiSummary は表示専用のまま、DashboardClient が null 時に `data-testid="kpi-skeleton"` を描画、とすれば US-2=表示単位・US-3=状態遷移単位の分割が綺麗に保てる）。→ Position P4。

#### US-4（`SeverityLevel` 単一ソース化）— 検証手段の確定が必要

- AC#1/AC#2 の「単一ソースであること」「定義が 1 箇所のみ」は、**vitest のランタイムテストでは検出できない**（vitest は esbuild で型を除去するため、型の二重定義があっても実行時に気付かない）。検証は (a) ソース文字列の grep／静的アサート（`types/api.ts` に `export type { SeverityLevel } from "@/lib/severity"` が在り、`export type SeverityLevel =` が無いことを確認）、(b) `npm run build` / `tsc --noEmit` の型チェック成功、で行う旨を AC に明記する。`api.test.ts` のランタイムテストは「re-export 後の `SeverityLevel` が値として使用可能（既存コードの型参照が壊れない）」ことの確認に留める。
- AC#3（陳腐化コメント更新）は実行時の検証対象でなくレビュー/grep で確認するものであり、`lib/severity.ts` を実装対象に含めた判断（Minor #8 解消）は妥当。コメント文言の確認はソース静的確認として AC に添える。

### NFR-1 / レビュー指摘 Minor #7（カバレッジゲートのローカル/CI 一致）— 未解決

現状の実態を確認した。

- `frontend/package.json` の `test` スクリプトは `vitest run`（**coverage なし**）。
- `frontend/vitest.config.mts` には `coverage` 設定が**無い**。
- CI（`.github/workflows/ci.yml` L85）は `npx vitest run --coverage --coverage.thresholds.lines=80 ...` の **CLI フラグ**で 80% を強制。
- team.md の Mandated は「`vitest.config.mts` の `coverage.thresholds` に設定し、**ローカル `npm run test` でも CI と同じゲートを強制**」を要求している。

このままでは「ローカル実行と CI でゲートが一致しない」（ローカル `npm run test` は 80% 未満でも成功する）ため、**NFR-1 を満たす実装手段がどのストーリーにも含まれていない**。→ Position P2。

### カバレッジ 80% への影響（実装時の分岐網羅）

FE-7 で新規に生まれる分岐を列挙する。下記をテストで網羅しないと lines/functions/branches の 80% を割り込むリスクがある。

- `fetchKpiSummary` の正常系／異常系（4xx/5xx）分岐 — US-1 で対応。
- スケルトン→成功→再スケルトンの状態分岐 — US-3 で 3 状態をテスト（Position P4）。
- ポーリングの初回実行／interval 再実行／クリーンアップ分岐 — US-3 のフェイクタイマー 3 ケースで対応。
- `page.tsx` から `MOCK_KPI_DATA` を撤去した後の「モック数値が描画されない」検証 — page.test.tsx のスコープ追加時に `queryByText("1,240")` 非存在を追加（Position P1）。

## Positions

- **AGREE: US-3 の実装対象に `DashboardClient.test.tsx` を含めた判断（Critical #2 の解消）** — `fetchKpiSummary` 未モックによる既存テスト破壊を防ぐ正しい処置。
- **AGREE: US-4 の実装対象に `lib/severity.ts` を含めた判断（Minor #8 解消）** — 陳腐化コメント（`lib/severity.ts` L12-13 の「(1|2|3)」）の更新先が確定し、スコープが曖昧でなくなる。
- **OBJECT: `page.test.tsx` がスコープ外のまま** — FR-7 で DashboardClient が `fetchKpiSummary` を呼ぶと `page.test.tsx` の `@/lib/api` モックが `fetchKpiSummary` を提供せず TypeError で壊れる。Critical #2 は DashboardClient.test.tsx と page.test.tsx の**両方**に波及する。
- **OBJECT: NFR-1（Minor #7）が未解決** — 「ローカル `npm run test` と CI でカバレッジゲートを一致させる」実現手段がどのストーリーにも含まれない。team.md の Mandated に反し、品質ゲートが実効性を持たない。
- **修正提案（P1）**: `page.test.tsx` を US-3（または US-2）の実装対象に追加し、(1) `@/lib/api` モックへ `fetchKpiSummary: vi.fn().mockResolvedValue(...)` を追加、(2) `MOCK_KPI_DATA` 撤去の検証として `queryByText("1,240")` / `queryByText("142万円")` の非存在アサートを追加、を受入条件に明記する。
- **修正提案（P2）**: NFR-1 の実現手段を確定する。推奨は「`vitest.config.mts` に `coverage` 設定（provider: 'v8'、`thresholds` で lines/functions/branches/statements 各 80%）を追加し、`package.json` の `test` スクリプトを `vitest run --coverage` に変更、CI の CLI フラグを設定と一致させる」案。スコープ外の設定変更を避けたい場合は「CI は現行 CLI フラグ、ローカルは `npm run test -- --coverage`（同じしきい値）」を NFR-1 に明記するか、どちらかを人間に諮る。
- **修正提案（P3）**: US-2 AC#1 の「降順」に DOM 出現順の検証（testId `kpi-card-sensors` → `kpi-card-level3` → `kpi-card-level2` → `kpi-card-level1` → `kpi-card-cost` の順）を明記する。
- **修正提案（P4）**: スケルトン描画の所在を確定し、testId を `kpi-skeleton` に固定、US-3 AC#1 に「成功後失敗で再スケルトン（stale 値非表示）」のテストケースを追加する。
- **修正提案（P5）**: US-1 AC#3 と US-4 の検証手段を「ランタイムアサート + grep/ソース静的確認 + `npm run build`/`tsc`」と AC に明記する（vitest は型を検査しないため、型の単一ソースは静的確認で担保）。
- **修正提案（P6）**: US-2 の Level 1 カードラベル（`lib/severity.ts` と整合）と testId `kpi-card-level1`、試算値注記の表示文字列を確定し、テストの完全一致アサートを決定的にする。
