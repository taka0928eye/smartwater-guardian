/**
 * FE-7: docs/business-model.md の内容を配信する API ルート。
 *
 * KPI コストカードの「前提: docs/business-model.md」リンクボタンが、このルートから
 * マークダウン本文を取得してモーダル表示する。取得失敗時は 500 にせず 404 と error を
 * 返す（バックエンドのエラーハンドリング方針に合わせ、画面を壊さない）。
 * コメント・docstring は日本語（NFR-4 / FE-7）。
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

/** リポジトリルート直下の docs/business-model.md。
 *  Next.js 実行時の cwd は frontend/（npm run dev / build の起点）なので、その親
 *  （リポジトリルート）+ docs/ で解決する。動的生成により Turbopack のビルド時
 *  解決（プロジェクト外パス）を避ける。 */
const BUSINESS_MODEL_PATH = path.join(
  process.cwd(),
  "..",
  "docs",
  "business-model.md",
);

export async function GET(): Promise<Response> {
  try {
    const content = await readFile(BUSINESS_MODEL_PATH, "utf-8");
    return Response.json({ content });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "docs/business-model.md を読み込めません";
    return Response.json({ content: null, error: message }, { status: 404 });
  }
}
