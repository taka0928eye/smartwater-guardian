# 技術スタック決定 — KPI サマリ（BU-1）

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）の技術スタック。
> 既存スタック（reverse-engineering の `technology-stack.md`）を踏襲し、**新規ライブラリ・依存を追加しない**（C-5）。
> **Conversation language: 日本語**

## 1. 技術スタック（決定）

| レイヤー | 採用 | 変更 | 根拠 |
|---|---|---|---|
| フレームワーク | Next.js（App Router / TS / Tailwind） | なし | 既存。`page.tsx` は Server Component 維持（C-2） |
| UI 表示 | Tailwind v4（`lg:grid-cols-5` 等の既存トークン） | なし | NFR-5。デザインを崩さない |
| API クライアント | axios + `lib/api.ts`（`unwrap<T>` / `ApiError`） | `fetchKpiSummary` を追加のみ | 既存パターン踏襲（C-3 変換境界 1 回） |
| 状態管理 | React Hooks（`useKpiPolling` 新設） | 新規フックのみ | 専用フックで責務分離（application-design:c5） |
| テスト | Vitest + Testing Library | 追加テストのみ | 既存。カバレッジ 4 指標 80%（NFR-1） |
| バックエンド | FastAPI（BE-8 実装済み） | **なし** | C-1。本スコープで変更しない |
| LLM / 外部サービス | 利用しない | なし | KPI サマリに LLM は不要 |

## 2. 決定理由（要約）

- **新規ライブラリを追加しない**: デモ期限（C-5）優先。既存スタックで KPI ポーリング・表示は完全に実現できる。
- **`useKpiPolling` は新規フックとして新設**: 既存 `useAlertPolling`（失敗時据え置き）と KPI（失敗時再スケルトン）の
  挙動差があるため、共通フックに統合しない（application-design:c5）。循環依存は `intervalMs` 引数化で回避（Q1=A）。
- **`getSeverityMeta(1)` を Level 1 カードに再利用**: 新規色トークンを追加せず、既存 `lib/severity.ts` を単一ソースとする（FR-2 / Q9）。

## 3. リスクと緩和

| リスク | 緩和 |
|---|---|
| `types/api.ts` の `KpiSummary` 型と `KpiSummary.tsx` コンポーネントの同名衝突 | 表示層は `KpiSummaryData` 別名（component-methods §4） |
| 既存テストの `vi.mock("@/lib/api")` が `fetchKpiSummary` 未モック | テスト追加時にモックを更新（functional-design レビュー Minor 5 引継ぎ） |
| ポーリング out-of-order（応答 5 秒超） | 既存 `useAlertPolling` と同型の既知制約。デモスコープでは許容し、注記に留める |

## Sources

- [technology-stack] `aidlc/spaces/default/codekb/smartwater-guardian/technology-stack.md`（reverse-engineering 成果物）
- [requirements] `inception/requirements-analysis/requirements.md`（NFR-2 / NFR-5 / C-1〜C-5）
- [functional-design] `construction/BU-1/functional-design/frontend-components.md`（型設計 §2・コンポーネント仕様 §3）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:52:23Z
**Iteration:** 1

### Findings

nfr-requirements レビューの 3 Minor（P-1 引用・C-1 スコープ持ち越し明示・ADR 引用）は performance-requirements.md / security-requirements.md に帰属し、本成果物への指摘はなし。

### Summary

技術スタック（新規依存なし・既存パターン踏襲・`useKpiPolling` 新設・`getSeverityMeta(1)` 再利用）は既存実装と整合。Critical 0・Major 0 → **READY**。
