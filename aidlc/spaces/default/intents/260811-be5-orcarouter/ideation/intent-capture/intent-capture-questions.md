# Intent Capture Questions — BE-5: services/orcarouter.py によるLLM自動起票の実装

## Sources

- [desc] Initial description: "GitHub内のISUUESを確認し、ISSUE#13「BE-5: services/orcarouter.py によるLLM自動起票の実装」を実装してください。短期開発で時間が限られているので、GitHub ISSUEに書かれている作業内容に沿ってコード生成を始めてください。手が離せないので自動承認でOKです。"
- [scope] Workflow-selected scope: `feature`.
- [memory:M1] `aidlc/spaces/default/memory/project.md#Corrections`: "- スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->"
- [memory:M2] `aidlc/spaces/default/memory/team.md#Testing Posture`: "- TDD（Red → Green → Refactor）を厳格に順守する。コード作成前に必ず失敗テストを書き、最小実装で Green にした後、リファクタリングする。"

## Q1. 製品境界（スコープ）の確認

このワークフローは **`feature`** スコープで進みます。GitHub Issue #13 の主旨は「解析結果と配管台帳から Orcarouter 経由で LLM を呼び、補修部材選定・概算見積・作業指示書を自動起票する（FR-3 / FR-4 中核）。処理は `backend/app/services/orcarouter.py` にカプセル化する（CLAUDE.md §5.3）」ことです。変更対象は Issue 記載の4ファイル（`backend/app/services/orcarouter.py` 新規・`backend/app/routers/alerts.py` 修正・`backend/.env.example` 修正・`backend/tests/test_orcarouter.py` 新規）です。この製品境界は想定どおりですか？

- A. はい、`feature` スコープで正しい — 対象は上記4ファイルのみ。フロントエンドは変更しない
- B. いいえ、バックエンド対象ファイルを増やす（範囲は自由記述で指定）
- C. いいえ、対象ファイルを減らす（範囲は自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q2. 実装方針（LLM 呼び出しの形態）

Issue の実装方針は「`async def create_work_order(client: httpx.AsyncClient, alert: AlertDetail, pipe: PipeRecord | None) -> WorkOrder` を `httpx.AsyncClient` + `HttpClientDep` で実装。APIキーは `os.environ["ORCAROUTER_API_KEY"]`、タイムアウト30秒・`response.raise_for_status()`・5xx/ネットワークのみ1回リトライ・4xx は即フォールバック・パース失敗はフォールバック」です。この実装方針で進めますか？

- A. はい、Issue 記載の実装方針どおり（httpx.AsyncClient + 失敗分類 + フォールバック）
- B. httpx ではなく他のHTTPクライアントを使用する
- C. 方針が違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q3. ビジネス課題と解決価値

Issue の目的は「FR-3 / FR-4 の中核であり本プロダクトの目玉。漏水検知アラートと配管台帳から LLM を呼び、補修部材選定・概算見積・作業指示書を自動起票して運用の省力化を図る」ことです。ビジネス課題の理解はこれで合っていますか？

- A. 合っている — アラート発生から補修起票までを自動化し、運用スタッフの判断・入力作業を省力化する
- B. LLM 原価の計測・可視化（FR-6）が主目的
- C. 課題の理解が違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q4. ターゲット顧客（誰の課題か）

この機能は消火栓センサーによる漏水監視システムで、水道事業者の運用スタッフ（オペレータ・管理者）が漏水アラートを受けた際に、補修部材選定・概算見積・作業指示書の起票作業を自動化するために使います。ターゲット顧客とペインの理解はこれで合っていますか？

- A. 水道事業者の運用スタッフ（オペレータ・管理者） — アラート対応時の起票作業を自動化・省力化
- B. デモ・レビュー評価者（8/15 デモのステークホルダー）が主対象
- C. 顧客像が違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q5. 成功指標

Issue の受け入れ条件がそのまま成功指標になり得ます（有効キーで `source == "llm"` / 部材・見積・手順・通知が日本語で埋まる / `usage` トークン数・実モデル名・`latency_ms` 記録 / 1行 JSON 構造化ログ / キー未設定時フォールバック / タイムアウト1回リトライ / 4xx 即フォールバック / ログ・例外・レスポンスにキー非露出 / キャッシュ / 二重計上なし / カバレッジ80%）。成功指標は受け入れ条件の通過で確定しますか？

- A. 受け入れ条件の通過を成功指標とする（8/15 デモ完了を最優先、追加指標なし）
- B. 実キーを使った実動作確認（`scripts/check_orcarouter.py` で `source == "llm"`）も成功指標に含める
- C. 別の成功指標がある（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q6. イニシアティブのトリガー

このイニシアティブのトリガーは「PRD FR-3 / FR-4（LLM自動起票）が本プロダクトの目玉であり、FR-6（LLM原価計測）が PRD 更新で追加された（`docs/llm-cost.md` §2 が BE-5 実装時必須と規定）」ことと「8/15 デモ完了のマイルストーン（想定日 8/13）」です。トリガーの理解はこれで合っていますか？

- A. 中核機能の実装完了とデモ期限（P1・想定日8/13）、および FR-6 の計測要件がトリガー
- B. 市場競争や規制対応が主トリガー
- C. トリガーが違う（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q7. ステークホルダーと決定権者

ステークホルダー候補は「開発チーム（FE/BE）」「PRD・Issue の要件定義者」「デモ評価者（8/15）」「運用スタッフ（エンドユーザー）」です。スコープ・優先度の決定権者と、影響力を持つ人は誰ですか？

- A. 開発チームが実装判断、要件は PRD / Issue が決定済み。デモ評価者が最終確認
- B. 要件定義者（PRD・docs の作成者）がスコープ決定の主権者
- C. 別のステークホルダーがいる（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Q8. コミュニケーション要件

報告頻度・報告対象・連絡体制に関する要件（例: 定例レビューの有無、進捗報告先）はありますか？

- A. 特になし（個別 Issue ベースで進捗管理、コミュニケーション要件なし）
- B. 進捗報告が必要（対象・頻度は自由記述で指定）
- C. 報告先や体制が決まっている（自由記述で指定）
- D. まだ特定されていない（Not identified）
- X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

- スコープは `feature` で正しい。対象は Issue 記載の4ファイルのみ（`backend/app/services/orcarouter.py` 新規・`backend/app/routers/alerts.py` 修正・`backend/.env.example` 修正・`backend/tests/test_orcarouter.py` 新規）。フロントエンドは変更しない。 [Q1]
- 実装方針は Issue 記載どおり。`httpx.AsyncClient` + `HttpClientDep`、APIキーは環境変数、タイムアウト30秒、5xx/ネットワークのみ1回リトライ、4xx・パース失敗は即フォールバック。 [Q2]
- ビジネス課題は「アラート発生から補修起票までを自動化し、運用スタッフの判断・入力作業を省力化する」ことで合っている。 [Q3]
- ターゲット顧客は水道事業者の運用スタッフ（オペレータ・管理者）。アラート対応時の起票作業を自動化・省力化。 [Q4]
- 成功指標は Issue 受け入れ条件の通過（`source=="llm"` / 部材・見積・手順・通知が埋まる / トークン数・実モデル名・`latency_ms` 記録 / 構造化ログ / フォールバック / キャッシュ / キー非露出 / カバレッジ80%）。 [Q5]
- トリガーは FR-3 / FR-4 中核機能の実装完了、FR-6 の計測要件、デモ期限（P1・想定日8/13）。 [Q6]
- ステークホルダーは開発チーム（実装判断）、PRD / Issue（要件決定済み）、デモ評価者（最終確認）、運用スタッフ（エンドユーザー）。 [Q7]
- コミュニケーション要件は特になし（個別 Issue ベースで進捗管理）。 [Q8]

- Looks correct
- Request changes

[Answer]: Looks correct
