# Initiative Brief — BE-5: services/orcarouter.py によるLLM自動起票の実装

> イニシアティブの全体像を1ページにまとめた承認用ブリーフ。イデエーション段階の成果物（intent-statement.md・scope-document.md・feasibility-assessment.md・constraint-register.md・competitive-analysis.md・team-assessment.md・rough-mockups 成果物）と一次ソース（GitHub Issue #13）に基づいて編纂する。 [intent] [scope-doc] [feasibility] [constraint] [competition] [team] [wireframes] [issue]

## 1. 意図と問題定義

漏水監視のアラート発生後、補修部材の選定・概算見積・作業指示書の起票は運用スタッフの手作業に依存しており、判断・入力に時間がかかる。本イニシアティブは解析結果と配管台帳から Orcarouter 経由で LLM を呼び、補修部材選定・概算見積・作業指示書を自動起票することで、アラート発生から補修起票までの一連の作業を自動化し、運用スタッフの省力化を図る（FR-3 / FR-4 の中核機能、本プロダクトの目玉）。 [intent]

- 契機: GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」の実装指示（8/15 デモ完了・実装完了 8/13 想定）。 [issue] [feasibility]

## 2. スコープ境界

| 項目 | 決定内容 |
|------|----------|
| 対象ファイル | バックエンドのみ。`backend/app/services/orcarouter.py`（新規）・`backend/app/routers/alerts.py`（501 スタブ差替）・`backend/tests/test_orcarouter.py`（新規）・`backend/.env.example`（`ORCAROUTER_API_KEY` 追記）+ フォールバック用 `backend/app/data/repair_parts.json`（新規） |
| 変更対象外 | フロントエンド（FE-6 起票モーダルは並行開発中・BE-5 をブロックしない）・認証/権限管理・物理 IoT 通信・リアルタイム通知・本番用大型 GIS DB・本番用 DB / クラウドインフラ |
| 実装方針 | `httpx.AsyncClient` + `HttpClientDep`（OR-1 再利用）・API キーは環境変数 `ORCAROUTER_API_KEY`・タイムアウト30秒・5xx/ネットワークのみ1回リトライ・4xx/パース失敗は即フォールバック・同一アラート2回目はキャッシュ返却 |
| 受入条件 | **一次ソース（Issue #13）の13件**に統一（rough-mockups レビュー Major 指摘の是正。上流成果物の「11件」表記は13件に読み替え） |
| 再利用資産 | OR-1 `HttpClientDep`・OR-2 `WorkOrder` / `prompts.py`・OR-4 `llm_cost.py`（すべて実装済み）。OR-3（#14）フォールバックは未実装のため BE-5 内包で最小実装 |

- 出典: [scope-doc]（イン/アウト境界・依存 D-1〜D-7）、[intent]（対象ファイル・実装方針）、[constraint]（TC-1〜TC-9）

## 3. 市場検証サマリ

- `build-vs-buy` で **buy（Orcarouter API 採用）** が確定。 [competition]
- BE-5 の LLM 自動起票は「検知後の運用自動化（アラート発生から補修起票までの自動化）」として差別化。実測原価の可視化（FR-6）とフォールバックによる継続性（NFR-5）が評価軸。 [competition] [intent]
- 主要ステークホルダーは運用スタッフ（受益者）・PRD / GitHub Issue（要件決定権者）・デモ評価者（最終確認）。決定権者は要件が決定済みの PRD / Issue であり、開発チームが実装判断を行う。 [stakeholder]

## 4. フィージビリティとリスク

### 実現性

- 呼び出し基盤（`HttpClientDep`・タイムアウト30秒）と OR-2（`WorkOrder` / `prompts.py`）・OR-4（`llm_cost.py`）が実装済みのため、`orcarouter.py` は LLM 呼び出し・リトライ・フォールバック・キャッシュ・原価記録の編成に集中できる。 [feasibility]
- テストは `httpx.MockTransport` で LLM をモックするため、実 API キーなしで TDD・CI が完結。 [feasibility]
- 8/13 実装完了は成立見込み（Q3: A）。 [feasibility]

### 主要リスクと対策

| リスク | 対策 |
|--------|------|
| **実 API キーがデモ時点で未入手**（R-1・高/中） | モック中心検証で TDD・CI 完結。実キーはデモ直前に環境変数で注入。未入手時はフォールバック（`source == "fallback"`）でデモ成立 |
| **OR-3 フォールバック未実装**（R-2・確定/中） | フォールバック応答は BE-5 の `orcarouter.py` 内で実装し、`repair_parts.json` を BE-5 で新規作成。後続 OR-3 マージ時に委譲へ切替 |
| **フォールバック部材選定の過渡実装**（R-3・中/低） | `repair_parts.json` は材質×口径の最小版で実装し、OR-3 マージ時に強化・委譲 |
| **キャッシュ・リトライ境界の複雑度**（R-4・中/低） | 同一アラート2回目はキャッシュ・タイムアウト時1回リトライ・4xx は即フォールバックを関数境界で分離 |
| **実装タイムライン超過**（R-5・低/高） | 単一サービス + 既存ルーター差し替え + モックテストで TDD 1〜2日以内の実装・カバレッジ80%到達は現実的 |

- 出典: [feasibility]（リスク分析）、[constraint]（TC-5 シークレット管理・TC-6 障害処理・TC-7 FR-6 原価計測）

## 5. コンセプト

UI モックアップはスコープ外（フロント変更なし・API バックエンドのみ）のため、非UIパス（システムコンテキスト図 + API 相互作用フロー）で確定した。 [wireframes]

```mermaid
flowchart LR
  A[POST /api/v1/alerts/{telemetry_id}/work-order] --> B[routers/alerts.py]
  B --> C[services/orcarouter.py<br/>LLM 自動起票サービス]
  C --> D[services/prompts.py<br/>プロンプト編成 OR-2]
  C --> E[(キャッシュ<br/>同一ID 2回目は再呼び出しなし)]
  C --> F[Orcarouter API<br/>LLM]
  C --> G[data/repair_parts.json<br/>フォールバック部材マスタ]
  C --> H[services/llm_cost.py<br/>FR-6 原価記録 OR-4]
  H --> I[schemas/work_order.py<br/>WorkOrder 型 OR-2]
  I --> J[WorkOrder 返却<br/>+ 1行 JSON 構造化ログ]
```

（テキスト代替）`POST /alerts/{telemetry_id}/work-order` → `alerts.py` → `orcarouter.py`。`prompts.py` でプロンプト編成し、キャッシュ未達なら Orcarouter API へ呼び出し。成功時 `WorkOrder(source="llm")`、4xx/パース失敗・5xx/ネットワークの1回リトライ後は `repair_parts.json` 由来フォールバック（`source="fallback"`）。いずれも `llm_cost.py` で FR-6 原価5フィールドを記録し、`WorkOrder` と 1 行 JSON 構造化ログを返却。 [wireframes]

## 6. チームプラン

- 実装担当: 単独開発者（ユーザー）+ AI-DLC エージェント群。モブ編成は不成立（人間1名）のため省略。 [team]
- 進め方: AI-DLC ワークフローに沿って Requirements Analysis → Application Design → Code Generation（TDD: Red → Green → Refactor）→ Build and Test を順次実施し、各段階で人間が承認（今回は自動承認指示）。 [scope-doc] [constraint]
- 完了期限: 8/13 実装完了・8/15 デモ完了。品質基準は pytest カバレッジ80%以上（行 + branch 各80%）・ruff + mypy・起動スモークテスト。 [constraint]

## 7. Go/No-Go 推奨

**推奨: GO**

- 意図とスコープが確定（バックエンドのみ・単一 proto-Unit PU-1・依存先順）。 [scope-doc]
- 主要リスク（実キー不確定・OR-3 未実装）はモック中心検証と BE-5 内包で対処可能。 [feasibility]
- 受入条件は一次ソース（Issue #13）の13件に統一し、欠落2件を DoD / テスト対象に明記して引き継ぐ（rough-mockups レビュー Major 指摘の解消・Q1 承認済み）。 [issue] [memory:M1]
- 8/15 デモ完了（P1）までに実装完了（8/13 想定）が成立し、フェイルオーバーとしてフォールバック動作でもデモを成立させられる。 [feasibility]

## Assumptions & Open Questions

- 受入条件は一次ソース（GitHub Issue #13）の13件を正とし、上流成果物の「11件」表記は13件に読み替える（欠落2件を DoD / テスト対象に明記）。 [assumption]
- OR-1 / OR-2 / OR-4 は実装済みであり再利用する。OR-3 フォールバックは BE-5 内包で最小実装し、後続 OR-3 マージ時に委譲・強化へ切替可能な境界を保つ。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [desc] GitHub Issue #13「BE-5: services/orcarouter.py によるLLM自動起票の実装」— 実装指示・目的（FR-3 / FR-4 中核）
- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル・実装方針）
- [stakeholder] `ideation/intent-capture/stakeholder-map.md`（決定権者・影響力者）
- [scope-doc] `ideation/scope-definition/scope-document.md`（イン/アウト境界・依存関係・実装順序）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・価値連鎖図）
- [competition] `ideation/market-research/competitive-analysis.md`（LLM 自動起票の差別化位置づけ）
- [feasibility] `ideation/feasibility/feasibility-assessment.md`（技術的実現性・リスク R-1〜R-5・タイムライン）
- [constraint] `ideation/feasibility/constraint-register.md`（TC-1〜TC-9 / OC-1〜OC-6 / RC-1）
- [team] `ideation/team-formation/team-assessment.md`（単独開発者 + AI-DLC エージェント群）
- [wireframes] `ideation/rough-mockups/wireframes.md`・`user-flow.md`（非UI: システムコンテキスト図・API 相互作用フロー）
- [issue] GitHub Issue #13（受入条件13件・変更予定ファイル・実装方針・検証方法 — 一次ソース）
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections` 学習 `approval-handoff:c6`（上流レビュー Major 指摘の引き継ぎ方針）
