# Feasibility Questions — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Sources

- [desc] Initial description: "GitHub内のISUUESを確認し、ISSUE#13「BE-5: services/orcarouter.py によるLLM自動起票の実装」を実装してください。短期開発で時間が限られているので、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。手が離せないので自動承認でOKです。"
- [scope] Workflow-selected scope: `feature`.
- [intent] 前段イニシアティブ・ステートメント `ideation/intent-capture/intent-statement.md`（対象: Issue #13 記載の4ファイル、実装方針: httpx.AsyncClient + HttpClientDep、成功指標: Issue 受入条件11件）。
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->"
- [memory:M2] `aidlc/spaces/default/memory/project.md#Corrections`: "デモ評価者向け内部機能・PIIなし・認証スコープ外の実装では、規制・コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー）は N/A として扱い、質問も省略する。 (learned 2026-08-11) <!-- cid:feasibility:c3 -->"

## Q1. Orcarouter 実API の接続検証方法（デモ時点での実キー有無）

BE-5 の受入条件は「有効な API キー設定下で `POST /api/v1/alerts/{id}/work-order` が `WorkOrder` を返し `source == "llm"`」です。実装方針は `httpx.AsyncClient` + `HttpClientDep`（既存 `backend/app/dependencies.py` に OR-1 で実装済み・タイムアウト30秒）で、テストは Issue Step 1 のとおり `httpx.MockTransport` で LLM をモックします。デモ（8/13）時点で Orcarouter の実キーを入手できる見込みは不確定です。接続検証の方法はどれにしますか？ [intent]

- A. モック中心で検証 — TDD・CI は `httpx.MockTransport` のモックで完結させ、実キーはデモ直前に環境変数（`ORCAROUTER_API_KEY`）で注入する。キーが入手できない場合もフォールバック（`source == "fallback"`）でデモを成立させる
- B. 実キー必須 — 実キー入手を前提に検証方法と成果物（`scripts/check_orcarouter.py` の実接続確認）を組み立てる
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. 未実装の上流依存成果物（フォールバック実装・フォールバック用部材マスタ）のスコープ内対処

Issue #13 は OR-2 の `WorkOrder` スキーマ・OR-3 のフォールバック・OR-4 の原価算出を前提としています。`main` の実態確認（2026-08-11 ユーザー指摘で修正）により、**OR-2（`schemas/work_order.py` / `services/prompts.py`）と OR-4（`services/llm_cost.py`）は実装済み**でそのまま再利用できます。一方、**OR-3（#14）のフォールバックは未実装**で、フォールバック用の補修部材マスタ **`data/repair_parts.json` も存在しません**。BE-5 の受入条件（`source == "fallback"` のフォールバック応答・FR-6 の原価5フィールド記録・`WorkOrder` 型の返却）を満たすには、不足分の対処が必要です。どのように対処しますか？ [intent]

- A. 既存サービスを再利用し不足分のみ BE-5 内で内包 — OR-2 / OR-4 の実装（`WorkOrder` スキーマ・`prompts.py`・`llm_cost.py`）を再利用し、`data/repair_parts.json`（フォールバック用・材質×口径の最小版）のみを本イニシアティブの対象ファイルに追加して新規作成する。フォールバック応答（`source == "fallback"`）は BE-5 の `orcarouter.py` 内で実装する（OR-3 未実装のスコープ内対処・後続 OR-3 マージ時に委譲へ切替可能に保つ）
- B. 4ファイルスコープ厳守 — フォールバック用部材マスタの作成やフォールバック実装を OR-3 に委ね、BE-5 の受入条件（特に `source == "fallback"`）は OR-3 マージ待ちの条件付きとして調整する
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A（2026-08-11 ユーザー指摘「OR-2 / OR-4 は実装済み、OR-3 は未実装」に基づき前提修正・回答再確認済み）

## Q3. 実装完了タイムライン（8/13 想定日）の成立性

BE-5 は P1・想定日 8/13（デモ 8/15）。変更範囲はバックエンドのみ（`orcarouter.py` 新規 + `alerts.py` 修正 + テスト + 設定）。上流の OR-1（`HttpClientDep`）は実装済みで、OR-2 のプロンプト・スキーマ仕様は Issue #12 本文に詳細に記述済みです。フロントの FE-6（起票モーダル）は並行開発中ですが、BE-5 の完了をブロックしません。8/13 実装完了は成立する見込みですか？ [intent]

- A. 成立する — 単一サービス + 既存ルーターの差し替え + モックテストで構成され、上流仕様（Issue #12 / #20 本文）が詳細に確定しているため、TDD で1日〜2日以内に実装・カバレッジ80%到達は現実的
- B. リスクあり — 上流成果物（WorkOrder スキーマ等）の不在と OR-3 の未実装が追加作業を生み、8/13 には間に合わない可能性がある
- C. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- 接続検証はモック中心（`httpx.MockTransport`）で実施し、実キーはデモ直前に環境変数で注入。キー未入手でもフォールバックでデモ成立。 [Q1]
- 未実装の上流依存の対処は、OR-2（WorkOrder スキーマ・prompts.py）と OR-4（llm_cost.py）が**実装済みのため再利用**し、フォールバック用の `repair_parts.json` のみ BE-5 内で新規作成、フォールバック応答は `orcarouter.py` 内で実装する（OR-3 未実装のスコープ内対処・後続 OR-3 マージ時に委譲へ切替可能）。 [Q2]
- 8/13 実装完了は成立見込み。単一サービス + 既存ルーター差し替え + モックテストで、上流仕様が詳細確定済みのため TDD で現実的に到達可能。 [Q3]
- 規制・コンプライアンス要件（PCI / HIPAA / SOC2 / データレジデンシー）は N/A — デモ評価者向け内部機能・PIIなし・認証スコープ外（feasibility:c3 学習に整合）。 [memory:M2]
- 前提2件は承諾済み（実キーはデモ時点で不確定・上流成果物の不在は BE-5 内包で対処）。 [assumption]

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

- Orcarouter の実 API キーはデモ（8/13）時点で入手できるか不確定であり、モック（`httpx.MockTransport`）中心で検証し、実キーは環境変数で注入する。 [assumption]
- OR-2（`WorkOrder` スキーマ / `prompts.py`）と OR-4（`llm_cost.py`）は `main` に実装済みであり再利用する。OR-3（#14）のフォールバックは未実装のため、フォールバック応答とフォールバック用部材マスタ（`data/repair_parts.json`）は BE-5 の実装内で必要最小限を内包して作成し、後続 OR-3 のマージ時に委譲・強化へ切替可能な設計に保つ。 [assumption]

- A. Accept assumptions
- B. Convert to follow-up questions

[Answer]: A. Accept assumptions
