/**
 * FE-7: docs/business-model.md の内容を配信する API ルート。
 *
 * KPI コストカードの「前提: docs/business-model.md」リンクボタンが、このルートから
 * マークダウン本文を取得してモーダル表示する。内容は環境変数 BUSINESS_MODEL_CONTENT
 * から読み込み、ファイル I/O を避ける（ECS 環境での動作を考慮）。
 * 環境変数が未設定の場合は 404 を返す。
 * コメント・docstring は日本語（NFR-4 / FE-7）。
 */

export async function GET(): Promise<Response> {
  const content = process.env.BUSINESS_MODEL_CONTENT;
  if (!content) {
    return Response.json(
      { content: null, error: "docs/business-model.md が設定されていません" },
      { status: 404 }
    );
  }
  return Response.json({ content });
}
