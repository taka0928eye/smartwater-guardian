# Mob Composition — FE-7 KPIサマリの実データ連携と「試算値」注記

## モブ編成の扱い

Q2=A により **モブ編成は適用しない** ことを確定。ソロ開発のため、複数人による同時開発（ドライバー / ナビゲーター / リサーチャー）は行わない。 [Q2]

## 代替の役割分担

モブ編成の代わりに、AI-DLC のステージ構成が各専門役割を時系列で担います。 [Q2]

```
[Ideation]       [Inception]        [Construction]        [Operation]
product ------>  architect -------> developer -------->  quality / operations
delivery         delivery           quality (レビュー)     (デモ評価フィードバック)
design (モック)   design
```

<!-- テキストフォールバック: Ideation(PM・デリバリー・デザイン) → Inception(アーキテクト・デリバリー・デザイン) → Construction(開発者・品質) → Operation(品質・運用) -->

## 品質ゲートの役割

- 各ステージの承認ゲートでユーザーが最終承認（人間レビュー）。 [intent] [scope]
- レビューエージェント（product-lead / architecture-reviewer）が設計・成果物の妥当性を検証。 [Q2]
- テスト戦略（カバレッジ80%以上）と CI が品質を担保。 [intent] [org]

## Assumptions & Open Questions

- その他の未確定項目はなし（None.）

## Sources

- [desc] Initial description: "GitHub内のISSUESを確認し、ISSUE#19「FE-7: KPIサマリの実データ連携と「試算値」注記の実装」を実装してください。"
- [scope] Workflow-selected scope: `feature`.
- [intent] `ideation/intent-capture/intent-statement.md`（成功指標: build・lint・test 成功、カバレッジ80%）
- [org] `aidlc/spaces/default/memory/org.md`（テストポスチャ・承認ゲート）
- [Q2] Team Formation 質問ファイル `ideation/team-formation/team-formation-questions.md` の回答 A（モブ編成は適用しない）
- [scope] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit）
