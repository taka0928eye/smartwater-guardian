# セキュリティ要件 — KPI サマリ（BU-1）

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）のセキュリティ要件。
> フロントエンドのみ（C-1）。デモ評価者向け内部機能・PII なし・認証スコープ外（feasibility:c3）。
> **Conversation language: 日本語**

## 1. 認証・認可

- 本スコープは **認証・権限管理を実装しない**（project.md Forbidden / CLAUDE.md Out of Scope）。
- デモ（8/10〜8/15）はローカル実行を主とし、アクセス制御はバックエンドの既存方針（未実装）に従う。

## 2. データ保護

| # | 要件 | 内容 |
|---|---|---|
| S-1 | シークレット・API キーのコミット禁止 | 本スコープで新規キー・資格情報を導入しない。`.env` は gitignore 管理（team-practices / project.md Forbidden） |
| S-2 | PII 非保持 | KPI サマリ（センサー数・コスト・レベル別件数）は PII を含まない。扱いは内部機能レベル |
| S-3 | 攻撃面の拡大なし | フロントのみの変更。新規外部通信・新規依存・新規ライブラリを追加しない（C-5） |

## 3. 脅威考察

| 脅威 | 対応 |
|---|---|
| バックエンド不正応答 | `lib/api.ts` 境界で `unwrap<T>` / `ApiError` により検証（4xx/5xx を例外化） |
| 表示 XSS | KPI 数値は `formatManYen` 等の数値フォーマットのみ。`assumptionDoc` は表示に使わない（FR-6 / frontend-components §3.4） |
| ポーリング DoS | 5 秒固定ポーリングのみ。レート制御・認証は対象外（上記 §1） |

## 4. 準拠

- PCI / HIPAA / SOC2 / データレジデンシー等の規制要件は **N/A**（デモ内部機能・PII なし・認証スコープ外。feasibility:c3）。
- Dependabot（依存脆弱性スキャン）・GitHub secret scanning はプロジェクト既定で有効（変更なし）。

## Sources

- [functional-design] `construction/BU-1/functional-design/business-logic-model.md`（エラーハンドリング方針 §5）
- [requirements] `inception/requirements-analysis/requirements.md`（NFR-3 / Constraints C-1〜C-5 / Out of Scope）
- [project.md] Forbidden（認証実装禁止・シークレットコミット禁止）

## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-08-11T09:52:23Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Resolution |
|---|---|---|---|---|
| 3 | Minor | §3（表示 XSS の行） | `assumptionDoc` 表示未使用の根拠引用が ADR-004 と不正確 | 引用を「FR-6 / frontend-components §3.4」へ修正済み |

### Summary

本成果物は Finding 3（ADR 誤引用の連鎖）のみ。引用修正で解消。Critical 0・Major 0 → **READY**。
