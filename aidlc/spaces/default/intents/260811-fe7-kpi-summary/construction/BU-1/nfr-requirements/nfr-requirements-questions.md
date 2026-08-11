# NFR Requirements — BU-1 質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」BU-1（kind: `ui`）の NFR 要件質問。
> NFR-1〜5 は `requirements.md` で全て数量化済み・矛盾なしのため、**質問はゼロ件**（Construction では質問は例外的。
> requirements-analysis が NFR ターゲットを取得済みのため re-ask しない。approval-handoff:c2 / requirements-analysis:c1 学習と整合）。
>
> **Conversation language: 日本語**

## NFR ターゲット（上流確定・再確認の必要なし）

| NFR | ターゲット | 出典 |
|---|---|---|
| NFR-1（カバレッジ） | frontend 4 指標（lines/functions/branches/statements）各 80%。`vitest.config.mts` thresholds | requirements.md |
| NFR-2（品質ゲート） | `npm run build` / `lint` / `test` 成功。TS strict・`any` 禁止 | requirements.md |
| NFR-3（エラーハンドリング） | `lib/api.ts` 境界で `ApiError` 変換。`clearInterval` + `cancelled` フラグ | requirements.md / team-practices |
| NFR-4（可読性） | コメント・docstring は日本語・Issue 参照（FE-7） | requirements.md |
| NFR-5（UI 一貫性） | Tailwind v4 トーン・`lg:grid-cols-5` 等の既存クラス踏襲 | requirements.md |

- 実現手段のうち NFR-1 カバレッジゲート恒久化（`vitest.config.mts` 設定）は functional-design レビュアー
  Minor 3 の引継ぎどおり **build-and-test で確定・実装**する。
- 既存テストへの `fetchKpiSummary` モック追加（functional-design レビュー Minor 5）は **code-generation で実施**。

## 保留中の質問

- なし（None.）

---

## Consolidated Summary Confirmation

NFR ターゲットは上流（requirements.md NFR-1〜5 / functional-design）で全て確定済みであり、本ステージで追加の
人間判断を要する質問はない。上記の解釈（質問ゼロ件・NFR-1 は build-and-test へ引継ぎ）で成果物を生成してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct
