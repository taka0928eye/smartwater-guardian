# Build Instructions — BU-1（FE-7: KPIサマリの実データ連携と「試算値」注記）

> 本指示書は `code-generation-plan.md` / `code-summary.md`（BU-1、フロントエンドのみ）の
> ビルド工程を実行・検証するための手順書。GitHub Issue #19（FE-7）を一次ソースとする。
> 対象は **frontend/**（Next.js 16.3.0 / TypeScript strict / Tailwind v4）。
> バックエンド（backend/）は本件の変更対象外。

## 1. 前提条件

- **Node.js / npm**: `frontend/package.json` が使用する npm ワークフロー（`next` / `vitest` / `eslint`）が実行可能であること。Node 20 以降を推奨（Next.js 16 の要件）。
- **作業ディレクトリ**: リポジトリルート `C:\workspace\smartwater-guardian`。フロントのコマンドはすべて `frontend/` 内で実行する。

## 2. 依存関係のインストール

初回・依存変更時のみ。`package-lock.json` があるため `npm ci` を推奨。

```powershell
cd frontend
npm ci
# （または開発中の再現性重視で npm ci、軽微な更新時は npm install）
```

## 3. 環境設定

- **環境変数**: フロントのビルド・テストに必須の環境変数はない（API ベース URL は `lib/api.ts` 内の `apiClient` でデフォルト値を使用。デモスコープのためローカルバックエンド `http://localhost:8000` を想定）。
- **ローカルサービス**: ビルド・単体テスト・コンポーネントテストはモック境界（`vi.mock("@/lib/api")`）で完結するため、バックエンド起動は不要。
  - 実データ表示の手動確認（`npm run dev` + バックエンド `uvicorn`）はビルド検証とは別の任意手順。

## 4. ビルドコマンド

| 工程 | コマンド | 説明 |
|------|----------|------|
| 型チェック + プロダクションビルド | `npm run build` | `next build`（Turbopack）。TS strict 型検査を実行し、最適化済みプロダクション生成物を作成 |
| 開発サーバー（任意） | `npm run dev` | `next dev`。ホットリロード付きローカル起動 |
| プロダクション起動（任意） | `npm run start` | `next start`。ビルド済み生成物を起動 |

## 5. ビルド検証手順

1. `npm run build` を実行し、**終了コード 0** を確認する。
2. 出力に `✓ Compiled successfully` と `✓ Generating static pages` が含まれることを確認する。
3. TypeScript 型検査（`Running TypeScript ... Finished TypeScript`）がエラー 0 で完了することを確認する。
4. 生成ルートが期待どおりであることを確認する（`/` が Server Component として生成される。FE-7 では `page.tsx` を Server Component のまま維持する方針のため `ƒ (Dynamic)` あるいは `○ (Static)` のどちらでも可）。

### 期待される出力例（Next.js 16.3.0 / Turbopack）

```
▲ Next.js 16.3.0 (Turbopack)
✓ Compiled successfully in ~1.6s
✓ Generating static pages using 5 workers (3/3) in ~1s

Route (app)
┌ ƒ /
└ ○ /_not-found
```

## 6. よくあるビルド問題と対処

| 症状 | 原因 | 対処 |
|------|------|------|
| `Cannot find module '@/...'` | tsconfig paths と vitest.config.mts の alias 不整合 | `tsconfig.json` の `paths`（`@/*` → `./src/*`）と `vitest.config.mts` の `resolve.alias` を一致させる |
| 型エラー `Type 'X' is not assignable to type 'Y'` | 型の二重定義・再エクスポートの不整合 | FE-7 では `SeverityLevel` を `lib/severity.ts` 単一ソース化。`types/api.ts` は再エクスポートに統一する |
| `MOCK_KPI_DATA` の残存 | FE-2 の固定モック | `grep -rn "MOCK_KPI_DATA" frontend/src` が 0 件であること。残存時は `page.tsx` から削除 |
| ビルドキャッシュ不整合 | Turbopack キャッシュ | `frontend/.next/` を削除して再ビルド |
| npm 依存解決エラー | lockfile 不整合 | `npm ci` で lockfile 準拠のクリーンインストール |
