**Collaborator:** aidlc-developer-agent

## Contribution

実装可能性・ストーリーサイズの観点で `stories.md`（US-1〜4）をレビューした。現状コード
（`types/api.ts`・`lib/api.ts`・`lib/severity.ts`・`page.tsx`・`KpiSummary.tsx`・
`DashboardClient.tsx`・各テスト・`vitest.config.mts`）およびバックエンド
`backend/app/schemas/kpi.py`・`backend/app/routers/kpi.py` と突き合わせた結果、
**全ストーリーは概ね実装可能**で、単一 proto-Unit BU-1 での完結も妥当。ただし
**Critical #2 が部分的にしか解決されていない**（`page.test.tsx` がスコープ外）点と、
**Minor #7**（`vitest.config.mts` の coverage 設定）が未解決のままである点を修正として挙げる。

### ストーリー別検証

#### US-1: `KpiSummary` 型定義と `fetchKpiSummary` — 承認

- 型契約は `backend/app/schemas/kpi.py` の `KpiSummary`（`total_sensors` / `level1_count` /
  `level2_count` / `level3_count` / `estimated_cost_saved_yen` / `is_estimate` / `assumption_doc`）
  と 1:1 一致しており、AC1 の camelCase フィールド名（`totalSensors` / `level1Count` /
  `level2Count` / `level3Count` / `estimatedCostSavedYen` / `isEstimate` / `assumptionDoc`）は妥当。
- `fetchKpiSummary()` は既存 `fetchAlerts`（`frontend/src/lib/api.ts` L123-125）と同じ
  `apiClient.get` + `unwrap<T>` パターンで実装可能。エンドポイント `GET /api/v1/kpi/summary`
  は `backend/app/routers/kpi.py:18-19` に実在する。変換境界（C-3）・`ApiError` 変換（NFR-3）も
  既存実装の再利用で満たせる。
- 実装対象 3 ファイル（`types/api.ts` / `lib/api.ts` / `lib/__tests__/api.test.ts`）は妥当。
  api.test.ts は既存の `vi.spyOn(apiClient, "get")` パターンを踏襲し、snake_case→camelCase 変換と
  エラー変換を検証できる。
- 補足: `isEstimate` / `assumptionDoc` は FR-6 が固定リテラル表示のため UI からは使わないが、
  FR-1 の「1:1 対応」要件で型には含める。妥当。

#### US-2: KPI サマリ実データ表示と「試算値」注記 — 承認（注記1点・Minor #6 是正を推奨）

- カード順（監視センサー数 / Level 3 / Level 2 / Level 1 / 推定削減コスト）は承認済みワイヤーフレーム
  降順と一致し、Major #3 を解消する（Q3=A）。現状 `KpiSummary.tsx` は「本日の検知数」
  （`kpi-card-today` / L104-108）を Level 1 カードへ置換すれば 5 カード構成に一致する。
- 全面幅セクションとして DashboardClient 配下に描画（Major #4 解消、AC5）は、実際の配置変更コードが
  **US-3 の `DashboardClient.tsx`** に含まれる。US-2 の実装対象（`page.tsx` / `KpiSummary.tsx` /
  `KpiSummary.test.tsx`）だけでは配置移動は完了しないため、「KPI の描画位置が DashboardClient 配下へ
  移るのは US-3 完了時」である旨を AC5 に注記することを推奨（依存 US-2 → US-3 の順序自体は正しい）。
- Minor #6（型 `KpiSummary` とコンポーネント `KpiSummary` の同名）が未対応。TS は type と value の
  名前空間分離により `import type { KpiSummary }` + `function KpiSummary()` はコンパイル可能だが、
  レビュー指摘の「混乱」を避けるため、`KpiSummary.tsx` 内で
  `import type { KpiSummary as KpiSummaryData }` のエイリアスを採用するか、同名共存を明示的に許容する
  旨をストーリーに明記することを推奨。
- テストフィクスチャ注意: `KpiSummary.test.tsx` の `BASE_KPI`（`KpiData`・5 フィールド）は
  `KpiSummary`（7 フィールド、`isEstimate` / `assumptionDoc` 追加）へ変わるため、フィクスチャに
  2 フィールドの追加が必要。同ファイルは実装対象に含まれており対応可能。

#### US-3: 取得失敗時のスケルトン表示フォールバック — 修正必要（`page.test.tsx` を追加）

- **Critical #1 は解消**: `DashboardClient.tsx` を実装対象に含めている。✓
- **Critical #2 は部分解消**: `DashboardClient.test.tsx` のみスコープに含まれ、要件レビューが
  明記した **`page.test.tsx`（L17-20）が含まれていない**。`page.test.tsx` の `vi.mock("@/lib/api")`
  は `fetchSensorsGeoJson` / `fetchAlerts` のみを返し、US-3 後に DashboardClient（page.tsx が描画する
  実物）が `fetchKpiSummary` を呼ぶとモックに存在せず `undefined` 参照になる。ポーリング実装が
  try/catch を備えれば「クラッシュ」ではなく「スケルトン表示」に落ちるため既存アサーションが通る
  可能性は高いが、モック不完全のままでは挙動が未定義で、テストが壊れた際の切り分けも困難。
  **`page.test.tsx` を US-3 の実装対象に追加**し、`fetchKpiSummary` のモック追加と
  スケルトン表示アサーションを明示することを推奨する。
- Minor #5（スケルトン testId `kpi-skeleton`）は AC5 で解消。✓
- ポーリング実装は `DashboardClient.tsx` 内に `useEffect` + `setInterval` + `cancelled` フラグ +
  `clearInterval` をインラインで実装するのが、実装対象（2〜3 ファイル）に収まりデモ期限優先（C-5）に
  合う。`useKpiPolling` フックを抽出する場合は新ファイル追加になるため、インライン採用かフック抽出かを
  明記することを推奨（推奨はインライン）。
- FR-8 の「取得失敗時はカード群をすべてスケルトンへ切替え、取得成功まで更新しない」は、アラートの
  「最終状態据え置き」（`useAlertPolling` の挙動）と異なる点を AC1 が正しく表現している。実装時にこの
  差異を意識する必要がある。
- `DashboardClient.tsx` のルート構造変更（3 列グリッドを包む親要素の追加と KPI 全面幅セクションの先頭
  描画）が必要。AC5 で要件化済み。

#### US-4: `SeverityLevel` 型の単一ソース化 — 承認

- Minor #8 の対象である陳腐コメント（`lib/severity.ts:12-13` の「API 型の SeverityLevel(1|2|3) とは
  別に」）を実装対象に含め、解消。✓ re-export 化後は「別に」ではなく「単一ソースから re-export」の
  旨への書換えが必要。
- re-export 化（`types/api.ts` が `lib/severity.ts` から `import type`）は、`lib/severity.ts` が
  `types/api.ts` を import しないため循環依存なし。✓ 参照元（`lib/api.ts` / `SeverityBadge.tsx`）は
  どちらも同一型へ到達し、契約は壊れない。
- AC2 の「定義 1 箇所」は `SeverityLevel = 0 | 1 | 2 | 3` の定義パターンを grep する**静的確認**であり
  ユニットテストではない点を注記。`npm run build`（tsc）+ grep で検証するのが現実的。
- US-1 と同じ `types/api.ts` を編集するため、US-1 と同時実装（同一イテレーション）が妥当。✓

### 要件レビュー指摘の解決状況サマリ

| # | Severity | 解決状況 |
|---|---|---|
| 1 | Critical | US-3 で `DashboardClient.tsx` を実装対象に含め **解消** ✓ |
| 2 | Critical | **部分解消** — `DashboardClient.test.tsx` は含むが `page.test.tsx` が未含（追加を推奨） |
| 3 | Major | US-2 AC1 で降順採用（Q3=A）**解消** ✓ |
| 4 | Major | US-2 AC5 で全面幅・DashboardClient 配下を明記 **解消** ✓ |
| 5 | Minor | US-3 AC5 で `kpi-skeleton` testId 付与 **解消** ✓ |
| 6 | Minor | **未対応** — 型・コンポーネント同名の扱いを明記推奨 |
| 7 | Minor | **未解決** — `vitest.config.mts` の coverage 設定の扱いを明記推奨 |
| 8 | Minor | US-4 で `lib/severity.ts` を含め **解消** ✓ |
| 9 | Minor | US-2 AC3 でコストカード見出しに注記を明記 **解消** ✓ |

### ストーリーサイズ / スコープ整合

- 各ストーリーは 1〜3 ファイルに収まる。US-3 は `page.test.tsx` 追加後も 3 ファイル
  （`DashboardClient.tsx` / `DashboardClient.test.tsx` / `page.test.tsx`）で収まり、「1〜3 ファイル」
  のサイズ目安を満たす。✓
- 依存順 US-1 → US-2 → US-3、US-4 を US-1 と同順で実装する方針は scope-definition:c2 学習
  （型 → API クライアント → 表示）と整合。✓
- スコープは元の 6 ファイル → 9 ファイル（+ 推奨 `page.test.tsx` = 10）へ拡大する。この拡大は
  Q2=A（配線方式）とレビュー指摘（Critical #1/#2・Minor #8）で正当化されるが、**対象ファイルの
  全一覧をストーリーの 1 箇所（例: 「依存関係と関係性」節）に明示**することを推奨する（現状は
  ストーリー毎に散在しており、スコープ拡大の全体像が見えにくい）。

## Positions

- AGREE: US-1 の型契約（`backend/app/schemas/kpi.py` と 1:1）と `fetchKpiSummary` の実装方針
  （`unwrap<T>` 再利用・camelCase 変換境界）は現状コードと整合し実装可能である。
- AGREE: US-2 のカード順（降順）・全面幅配置・試算値注記は承認済みワイヤーフレーム（Q3=A）と整合し、
  Major #3 / #4・Minor #9 を解消する。
- AGREE: US-4 の `SeverityLevel` 単一ソース化（`lib/severity.ts` 本拠・`types/api.ts` から re-export・
  陳腐コメント更新）は循環依存なく実装可能で、Minor #8 を解消する。
- AGREE: 実装順 US-1 → US-2 → US-3、US-4 を US-1 と同順とする依存順は scope-definition:c2 学習と整合
  する。
- OBJECT: Critical #2 の解決が不十分 — `DashboardClient.test.tsx` のみスコープに含まれ、
  `page.test.tsx`（L17-20 の `vi.mock` が `fetchKpiSummary` 未定義）が含まれない。`page.test.tsx` を
  US-3 実装対象に追加し、`fetchKpiSummary` モックとスケルトン表示アサーションを明示すべき。
- OBJECT: Minor #7 が未解決のまま — `vitest.config.mts`（L6-14）に coverage 設定が無く、NFR-1 の
  「`coverage.thresholds` に設定」と実態が乖離する。`vitest.config.mts` をスコープに含めて
  `coverage.thresholds` を設定するか、build-and-test 段階への委譲を明記するかをストーリーで決定すべき
  （無言のままにしない）。
- OBJECT: Minor #6 が未明示 — 型 `KpiSummary` とコンポーネント `KpiSummary` の同名は TS 上コンパイル
  可能だが、レビュー指摘の混乱を回避するため import 時エイリアス
  （`import type { KpiSummary as KpiSummaryData }`）の採用または同名許容をストーリーに明記すべき。
- OBJECT: US-2 AC5 の「DashboardClient 配下に描画」は実際のコード変更が US-3 の
  `DashboardClient.tsx` に含まれる点を注記すべき — US-2 の実装対象だけでは配置移動は完了しない。
