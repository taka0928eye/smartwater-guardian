# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

- Minimal テスト戦略では統合・性能・セキュリティのテスト指示書はスキップする（produces リストは最大集合で戦略により絞られる）。 (learned 2026-08-11) <!-- cid:build-and-test:c1 -->
- pytest は `venv/Scripts/pytest.exe` でなく `venv/Scripts/python.exe -m pytest` で実行する（pytest.exe は cwd を sys.path に挿入せず `app` を import できないため）。 (learned 2026-08-11) <!-- cid:build-and-test:c3 -->
- Minimal 戦略で統合テスト指示書を生成しない判断は、TestClient のエンドポイントテスト（test_alerts.py）が統合境界を実質カバーしていることを根拠にする。 (learned 2026-08-11) <!-- cid:build-and-test:c4 -->
## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

## Decided

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- スコープ境界（対象ファイル・配線範囲）はユーザー確認で確定する。 (learned 2026-08-10) <!-- cid:intent-capture:c1 -->
- 最小スコープで scope-document / intent-backlog が存在しなくても、イニシアティブ・ブリーフは既存成果物とリポジトリ実態で整合を担保できる。 (learned 2026-08-11) <!-- cid:approval-handoff:c1 -->
- ステージの質問群のうちスコープに該当しない質問（市場検証・モックアップ・モブ編成等）は省略し、実決定に必要な質問のみ提示する。 (learned 2026-08-11) <!-- cid:approval-handoff:c2 -->
- pipe_id 等の識別子は Issue 例示よりマスタ（hydrants.json）と整合する形式を優先する（変換不要で照合信頼性が高い）。 (learned 2026-08-11) <!-- cid:approval-handoff:c3 -->
- 単一イテレーションのダイレクティブで unit-of-work が存在しないため、`{unit-name}` を `be4-ledger` に解決して記録パスを決定。 (learned 2026-08-11) <!-- cid:code-generation:c1 -->
- 「モジュールロード時のキャッシュ」は store.py の `@lru_cache(maxsize=1)` 先例に合わせ、初回呼び出し時に読み込んで以後キャッシュする設計と解釈（「リクエスト毎の再読み込みをしない」要件を満たし、テスト分離も壊さない）。 (learned 2026-08-11) <!-- cid:code-generation:c2 -->
- store.py は欠損を RuntimeError で包むが、受け入れ条件が FileNotFoundError / ValueError の明示指定の場合は、ledger.py のようにそのまま伝播・変換する。 (learned 2026-08-11) <!-- cid:code-generation:c3 -->
- find_nearest_pipe は路線の LineString 頂点との Haversine 最小距離で判定する（路線全体の中心点方式より、消火栓位置に近い頂点を考慮でき直感的）。 (learned 2026-08-11) <!-- cid:code-generation:c4 -->
- バックエンド Python のビルドは「依存導入の確認 + アプリ import スモークテスト + 検証スクリプト実行」で定義する（コンパイル工程がないため）。フロントエンドは変更対象外なら対象外と明記する。 (learned 2026-08-11) <!-- cid:build-and-test:c2 -->
