# Intent Statement — BE-4 配管台帳照合サービス

## Problem Statement

FR-3 の前段として、センサー位置（消火栓）から該当する水道管路（材質・口径・布設年等）を引き当て、BE-5（補修部材選定）に必要な入力を揃える必要がある。現在は消火栓マスタ（`hydrants.json`）しかなく、対象管路の属性を照合する手段が存在しない。軽量な JSON ファイルで配管台帳を代替し、照合ロジックを提供する。 [desc] [Q2]

## Target Customer

- **BE-5（補修部材選定・見積自動起票）**: 配管の材質・口径・布設年・経過年数を渡して部材選定の入力を揃える直接の消費者。 [Q2]
- **監視UIの利用者**: アラート詳細画面で対象管路の情報（材質・口径・布設年・経過年数）を確認したい。 [Q2]

## Success Metrics

- Issue の受け入れ条件の通過:
  - `hydrants.json` の全10件の消火栓が `find_pipe_by_hydrant()` で正しく配管データに解決される（`None` が返らない）。 [desc]
  - 未知の `hydrant_id` を渡した場合、エラーにならず `None` が返る。 [desc]
  - `find_nearest_pipe()` が与えられた座標の最近傍にある配管を正しく返す。 [desc]
  - `pipes.json` が欠損または破損している場合、起動/読み込み時に明確な例外が発生しサイレント失敗しない。 [desc]
  - `GET /api/v1/alerts/{id}` のレスポンスに「材質・口径・布設年・経過年数」が含まれている。 [desc]
  - JSON ファイルがリクエストごとに再読み込みされず、モジュールキャッシュされている。 [desc]
  - `python scripts/check_ledger.py` を実行してエラーなく全検証が成功する。 [desc]
- 上記の受け入れ条件の通過で十分であり、追加の成功指標は設けない（8/15 デモ完了を最優先）。 [Q3]

## Initiative Trigger

- GitHub Issue「BE-4: 配管台帳照合サービス（ledger.py）」として、FR-3 の前段実装を指示されている。 [desc]
- アラート詳細 API（BE-6）の `pipe_info` プレースホルダが BE-4 実装を待っており、現在は常に `None` を返している。 [Q4]

## Initial Scope Signal

- **Workflow-selected scope:** `be4-ledger-reconciliation`（workflow-selected） [scope]
- **User-confirmed product boundary:** 配管台帳データ（`app/data/pipes.json`）・スキーマ（`app/schemas/pipe.py`）・照合サービス（`app/services/ledger.py`）・検証スクリプト（`scripts/check_ledger.py`）の4ファイル新規作成と、`GET /api/v1/alerts/{id}` への配管情報（`pipe_info`）配線。 [Q1]
- BE-6 配線はこの BE-4 タスク内で実施する（ledger.py 実装後に alerts.py を接続）。 [Q4]

## Assumptions & Open Questions

None.

## Review

**Verdict: NOT-READY**（実質スコープ・成果物の骨格は健全。下記の接地契約上の逸脱を承認ゲートで判断材料としてください。いずれも小さく、そのまま許容する選択も合理的です。）

### 中程度の指摘（承認判断の要否）

1. **ステークホルダーマップの「決定者」行にソース非支持の役割・権限を創出している。** 「BE-4 / BE-5 / BE-6 実装担当」を Decision-maker とし `[desc] [Q4]` をタグ付けするが、いずれのソースも「実装担当が決定者である」「その権限を持つ」ことを示していない。Q4 が確定するのは「配線タイミングの選択」のみ。ステージ指示は「stakeholder role / interest / authority を invent しない」と明記しており、また Q&A には「誰がスコープ・優先度を決めるか（決定者 vs 影響力者）」を問う質問自体が存在しない（Q2 は消費者のみ）。→ 契約上は `Unknown (open question) [assumption]` とするか、追質問で決定者を確認すべき。

2. **Problem Statement にソース非支持の「現状欠如」主張を確定事実として記載している。** 「現在は消火栓マスタ（`hydrants.json`）しかなく、対象管路の属性を照合する手段が存在しない」は `[desc] [Q2]` タグだが、どちらのソースにもこの文言・含意は無い。リポジトリ実態（`app/services/` が空、`alerts.py` の `pipe_info=None`）とは一致しており事実としては正しいが、接地契約の「確認済みソースのみ」には反する。→ `## Assumptions & Open Questions` に `[assumption]` として移すか、追質問で確認するのが契約準拠。

3. **Communication Requirements 欄の唯一の行が「コミュニケーション要件」ではなく成果物/成功指標になっている。** 「受け入れ条件の通過を `python scripts/check_ledger.py` で検証できること」は検証手段の提供であり、報告頻度・誰に何を報告するか等のコミュニケーション要件ではない。ステージは同欄を要求するが、ユーザー確認済みのコミュニケーション要件は無い。→ 実質は `Unknown (open question) [assumption]` とすべき。

### 低程度の指摘（参考情報）

4. **成功指標（受け入れ条件）の出典が間接的である。** 各成功指標は `[desc]` タグだが、`[desc]` レジスタには「詳細は以下のIssue内容を参照」のみで、`find_pipe_by_hydrant()` / `find_nearest_pipe()` / 全10件 / `None` / キャッシュ等の文言は含まれない。実体は外部 GitHub Issue と Q3 の質問文要約の確認に由来する。リポジトリ実態（`hydrants.json` の10件、`alerts.py` の `pipe_info=None`、`alert.py` の `PipeInfo` スキーマ）とは一致しており事実は正しいが、定義完了（Definition of Done）のトレーサビリティが弱い。

### 適合確認（問題なし）

- 両アーティファクトとも `## Assumptions & Open Questions` を保持（`None.`）。
- 未選択オプションを除外条件に転化していない（Q3 の B/C を「やらない」と確定していない点も適切）。
- Initial Scope Signal で workflow-selected scope と user-confirmed 境界を分離し、`[scope]` を workflow-selected と明記（接地契約 3 に準拠）。
- Q&A のソースレジスタ（`[desc]` / `[scope]`）は解決可能。`alerts.py`・`PipeInfo`・`hydrants.json` の現状記述はコードベースと一致。
