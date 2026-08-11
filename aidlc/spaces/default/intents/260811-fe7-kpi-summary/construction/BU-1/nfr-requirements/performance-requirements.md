# 性能要件 — KPI サマリ（BU-1）

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）の性能要件。
> 本ユニットはフロントエンドのみ（C-1）。バックエンド BE-8 の `GET /api/v1/kpi/summary` をポーリングし、
> KPI カード 5 枚を描画する。既存 `useAlertPolling`（5 秒周期）と同一の取得頻度に統一する。
> **Conversation language: 日本語**

## 1. 応答時間・取得頻度

| # | 要件 | ターゲット | 根拠 |
|---|---|---|---|
| P-1 | KPI ポーリング周期 | 5 秒（`ALERT_POLL_INTERVAL_MS = 5000`） | FR-7（Q3=A）／intent-capture:c4。アラートと更新タイミングを揃える |
| P-2 | 初回データ表示までの猶予 | 初回ポーリング成功までスケルトン表示。実データ表示はバックエンド応答次第 | FR-8。白画面回避（フォールバック） |
| P-3 | 失敗時の復帰 | 次回 5 秒ポーリング成功時にカードへ復帰 | FR-8 / 状態遷移 T4 |

- バックエンド応答時間の SLO は本ユニットの責務外（BE-8 実装済み・インメモリ由来の高速応答を前提）。
  本ユニットでは**レイテンシ予算の配分は不要**（フロント単体は軽量表示処理のみ）。

## 2. リソース・負荷

| # | 要件 | ターゲット | 根拠 |
|---|---|---|---|
| P-4 | ポーリングの重複実行防止 | クリーンアップで `cancelled = true` + `clearInterval` を徹底 | NFR-3 / team-practices。メモリリーク・in-flight setState 防止 |
| P-5 | 描画負荷 | カード 5 枚・軽量 Tailwind レイアウト。再レンダリングはポーリング成功時のみ | デモスコープ（C-5）。最適化は不要 |
| P-6 | スケルトン表示 | スケルトン中も `h2` / ランドマークを維持し、レイアウトシフトを抑制 | refined-mockups:c4 / application-design:c1 |

## 3. 監視対象外（本ユニットの対象外）

- バックエンドのスループット・可用性（SLO / SLA）は BE-8 側の課題であり、本ユニットでは定義しない。
- スケーラビリティ要件（`produces_kinds` 上 `service` のみ適用）は本 `ui` ユニットでは非対象。

## Sources

- [functional-design] `construction/BU-1/functional-design/business-logic-model.md`（状態遷移 T1〜T4・ポーリング制御 §2.3）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-7 / FR-8 / NFR-1〜5 / C-1〜C-5）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:52:23Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| 1 | Minor | P-1（根拠列） | 「requirements NFR-1 相当」はカバレッジ NFR と不一致 | P-1 根拠列を「FR-7（Q3=A）／intent-capture:c4」へ修正済み |
| 2 | Minor | 付記（build-and-test 引継ぎ） | vitest.config.mts は C-1 対象外でスコープ判断が未確定 | 付記に「スコープ追加のユーザー確認が必要」を追記済み |
| 3 | Minor | security-requirements.md §3 | ADR-004 引用が不正確 | security-requirements.md の引用を「FR-6 / frontend-components §3.4」へ修正済み |

### Summary

Critical 0・Major 0 → **READY**。3 成果物は上流契約（requirements.md NFR-1〜5 / Constraints）と実コードの双方に整合し、NFR ターゲットはいずれも検証可能。Minor 3 件（引用の正確性 2・C-1 スコープ持ち越し明示 1）は反映済み。

## 付記（build-and-test への引継ぎ）

- NFR-1（frontend カバレッジ 4 指標 80%）の実現手段（`vitest.config.mts` の `coverage.thresholds` 設定）は
  functional-design レビュアー Minor 3 の指摘どおり **build-and-test で確定・実装**する。
- `vitest.config.mts` / `package.json` の変更は C-1（Issue #19 記載の 6 ファイルのみ）対象外のため、
  **スコープ追加（7 ファイル目以降）のユーザー確認が必要**である旨を build-and-test へ持ち越す
  （nfr-requirements レビュアー Minor 2）。現状 CI は CLI フラグ強制（`ci.yml` L85）・ローカル `npm run test`
  （=`vitest run`）はカバレッジ非計測のため、team-practices「ローカルと CI のゲート一致（Q3=A）」の
  実現手段（thresholds 設定 vs CLI フラグ統一）も build-and-test で確定する。
