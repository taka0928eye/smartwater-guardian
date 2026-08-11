# Intent Statement — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Problem Statement

漏水監視のアラート発生後、補修部材の選定・概算見積・作業指示書の起票は運用スタッフの手作業に依存しており、判断・入力に時間がかかる。本イニシアティブは解析結果と配管台帳から Orcarouter 経由で LLM を呼び、補修部材選定・概算見積・作業指示書を自動起票することで、アラート発生から補修起票までの一連の作業を自動化し、運用スタッフの省力化を図る（FR-3 / FR-4 の中核機能、本プロダクトの目玉）。 [Q3]

## Target Customer

水道事業者の運用スタッフ（オペレータ・管理者）が主たる受益者。漏水アラートを受けた際に、補修部材の選定・概算見積・作業指示書の起票作業を自動化・省力化する。加えて、8/15 デモのレビュー評価者が機能の完成度を確認する対象でもある。 [Q4]

## Success Metrics

Issue の受け入れ条件の通過を成功指標とする。主要な受入条件は以下のとおり。 [Q5]

- 有効な API キー設定下で `POST /api/v1/alerts/{id}/work-order` が `WorkOrder` を返し `source == "llm"` になる [Q5]
- 部材リスト・概算見積合計・作業手順・通知文面がすべて日本語で埋まる [Q5]
- `usage` からトークン数が取り込まれ、実モデル名と `latency_ms` が記録される（FR-6） [Q5]
- 起票のたびに 1 行 JSON の構造化ログが出力される（`telemetry_id` / `model` / トークン数 / `cost_yen` / `source` / `latency_ms`） [Q5]
- API キー未設定時に 500 ではなくフォールバック応答（`source == "fallback"`）が返る [Q5]
- タイムアウト時に 1 回リトライし、それでも失敗ならフォールバックする [Q5]
- 4xx ではリトライせず即フォールバックする [Q5]
- ログ・例外メッセージ・HTTP レスポンスのいずれにも API キーが出力されない（NFR-4） [Q5]
- 同一アラートへの 2 回目の呼び出しがキャッシュを返す（LLM を再度呼ばない） [Q5]
- キャッシュヒット時に原価が二重計上されない [Q5]
- `pytest --cov=app` のカバレッジが 80% 以上 [Q5]

## Initiative Trigger

本イニシアティブは、PRD FR-3 / FR-4（LLM 自動起票）が本プロダクトの中核機能であることに加え、PRD 更新で FR-6（LLM 原価の計測・可視化）が追加され、`docs/llm-cost.md` §2 が「BE-5 実装時に必ず入れる」と規定していること、および 8/15 デモ完了のマイルストーン（P1・想定日 8/13）がトリガーである。 [Q6]

## Initial Scope Signal

- **Workflow-selected scope**: `feature`（ワークフロー選択） [scope]
- **User-confirmed product boundary**: 変更対象は Issue 記載の 4 ファイル（`backend/app/services/orcarouter.py` 新規・`backend/app/routers/alerts.py` 修正・`backend/.env.example` 修正・`backend/tests/test_orcarouter.py` 新規）に限定し、フロントエンドは変更しない。 [Q1]
- **実装方針**: `httpx.AsyncClient` + `HttpClientDep`、API キーは環境変数、タイムアウト 30 秒、5xx/ネットワークのみ 1 回リトライ、4xx・パース失敗は即フォールバック。 [Q2]
- **開発プロセス**: TDD（Red → Green → Refactor）を厳格に順守する。 [memory:M2]
- **スコープ境界**: 対象ファイル・配線範囲はユーザー確認で確定する。 [memory:M1]

## Assumptions & Open Questions

None.

## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-08-11T21:20:26Z
**Iteration:** 1

### Findings

| # | Severity | Location | Finding | Recommendation |
|---|---|---|---|---|
| 1 | Minor | Target Customer | 「加えて、8/15 デモのレビュー評価者が機能の完成度を確認する対象でもある。」は [Q4] でタグ付けされているが、Q4 の確定回答（A）にデモ評価者は登場しない。デモ評価者が最終確認を行うという主張は Q7（A）に根拠がある。また Q4 の不採用オプション B（デモ評価者を主対象とする）を採用したと誤読させる恐れがある。 | ソースタグを [Q4][Q7]（または [Q7]）に修正する |
| 2 | Minor | Success Metrics | 成功指標 11 件はすべてエンジニアリング受入条件であり、ビジネス成果指標（アラート当たりの所要時間削減、手作業入力の削減等）は含まれない。これは Q5 A（「追加指標なし」、Q5 B の実キー検証も不採用）でユーザーが明示的に選択した決定であり誤りではないが、デモ優先の方針が許容するかを承認ゲートで確認しておく価値がある。 | 承認時にビジネス指標を持たない方針を意図的に確認する（変更不要） |
| 3 | Minor | Initial Scope Signal | 実装方針（httpx.AsyncClient / HttpClientDep / タイムアウト30秒 / リトライ方針）が ideation 成果物に含まれており、ideation フェーズのガードレール「ideation アーティファクトに実装詳細を含めない」と緊張関係にある。Q2 でユーザー確定済みのため無根拠な挿入ではないが、後段（inception 以降）で要件レベルへ読み替えて引き継ぐ想定を明示しておくと齟齬がない。 | 次段への引き継ぎ時に「受入条件として確定済み」と明記する（変更不要） |

### Summary

全要求セクション（Problem / Customer / Metrics / Trigger / Scope Signal）とステークホルダーマップの必須構成が揃い、実質的な主張はすべて許可ソース（Q1-Q8 / scope / memory）にトレース可能、メモリソース M1/M2 は原文一致、成功指標は QA で検証可能な受入条件である。指摘は Minor 3 件のみで実装着手を妨げない。READY とする。
