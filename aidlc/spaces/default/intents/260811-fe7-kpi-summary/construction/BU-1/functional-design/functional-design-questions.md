# Functional Design — BU-1 質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）の機能設計質問。
> 上流成果物（`requirements.md` FR-1〜8 / `stories.md` US-1〜4 / application-design 5 成果物 /
> `unit-of-work.md` §2.2・`unit-of-work-story-map.md`）で確定済みの事項は質問を省略し、
> **実決定が必要な事項のみ提示**する（approval-handoff:c2 / requirements-analysis:c1 学習と整合）。
>
> **Conversation language: 日本語** — 成果物はすべて日本語で記述する。

## Q1: `useKpiPolling` のシグネチャ（循環依存解消の引き継ぎ）

上流にシグネチャの乖離がある。`component-methods.md` §2.1 は `useKpiPolling()`（入力なし・内部で
`ALERT_POLL_INTERVAL_MS` を参照）と記載するが、Application Design レビュアー Major 1 の指摘を受け
`unit-of-work.md` §2.2 は **`useKpiPolling(intervalMs: number)`** と引数化し `DashboardClient` 側から
`ALERT_POLL_INTERVAL_MS`（5000）を渡すことを権威としている（`DashboardClient ↔ useKpiPolling` の
モジュール循環を回避）。機能設計の正はどちらか？

- A. `useKpiPolling(intervalMs: number)`（推奨）— unit-of-work §2.2 を権威とし、既存 `useAlertPolling(intervalMs)`
  と対称。循環依存を解消し、component-methods.md は陳腐化注記に留める
- B. `useKpiPolling()`（component-methods.md のまま）— 内部で定数を参照。lint で import/no-cycle 違反になる恐れ
- X. Other (please specify)

[Answer]: A. useKpiPolling(intervalMs: number)

## Q2: ポーリング失敗時〜再成功時の状態遷移の厳密化

FR-8 は「取得成功前・取得失敗後・再取得成功まではスケルトン表示」を要求する。`useKpiPolling` の
失敗→再成功の遷移で、具体的な状態遷移は？

- A. 失敗時点で即 `isLoading: true`（再スケルトン）に遷移し、次回ポーリング成功時に `kpiData` 更新 + カード復帰
  （推奨）— stale 値を一切見せない FR-8 を厳密に満たす
- B. 失敗しても直前の成功値を表示し続け、成功時に更新（`useAlertPolling` の据え置きと同挙動）— FR-8 違反
- X. Other (please specify)

[Answer]: A. 失敗時点で即 `isLoading: true`（再スケルトン）に遷移し、次回ポーリング成功時に `kpiData` 更新 + カード復帰

## Q3: 機能設計に文書化するビジネスシナリオの網羅範囲

kind `ui` のためビジネスルール・ドメインエンティティの設計判断は発生しない（produces は
`business-logic-model.md` + `frontend-components.md`）。データフロー・シナリオの文書化範囲は？

- A. データフロー（BE-8 → useKpiPolling → DashboardClient → KpiSummary）＋ ハッピーパス / 失敗パス /
  アンマウント時クリーンアップ の 3 シナリオ（推奨）— Minimal 戦略で要件 FR-7/FR-8 の検証に必要な最小網羅
- B. 上記 + エッジケース（初回ポーリング前・連続失敗・成功直後アンマウント）まで詳細化
- X. Other (please specify)

[Answer]: A. データフロー（BE-8 → useKpiPolling → DashboardClient → KpiSummary）＋ ハッピーパス / 失敗パス / アンマウント時クリーンアップ の 3 シナリオ

---

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: `useKpiPolling(intervalMs: number)` を権威とする（unit-of-work §2.2 準拠・循環依存解消。component-methods.md は陳腐化注記に留める）
- Q2: 失敗時点で即 `isLoading: true`（再スケルトン）へ遷移し、次回成功時に `kpiData` 更新 + カード復帰（FR-8 厳密充足）
- Q3: データフロー（BE-8 → useKpiPolling → DashboardClient → KpiSummary）＋ ハッピーパス / 失敗パス / アンマウント時クリーンアップ の 3 シナリオを文書化（Minimal 戦略）

上記の内容で機能設計成果物（business-logic-model.md / frontend-components.md）を生成してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct
