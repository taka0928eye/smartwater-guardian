/**
 * DEMO-2: デモ操作 API（POST /api/v1/demo/seed-batch / DELETE /api/v1/demo/clear）の
 * レスポンス型。
 *
 * バックエンドは snake_case（Pydantic v2）、フロントは camelCase で統一する。
 * snake_case -> camelCase 変換は src/lib/api.ts の境界で一度だけ行うため、
 * 本ファイルの型は camelCase 側のみを公開する（FE-1 規約）。
 */

/** POST /api/v1/demo/seed-batch のレスポンス。 */
export interface DemoSeedBatchResponse {
  /** 投入結果ステータス。 */
  status: string;
  /** 投入件数（常に23件）。 */
  insertedCount: number;
  /** 深刻度別の件数内訳（キーは "0"〜"3"）。 */
  levelCounts: Record<string, number>;
  /** ステータスメッセージ。 */
  message: string;
}

/** DELETE /api/v1/demo/clear のレスポンス。 */
export interface DemoClearResponse {
  /** クリア結果ステータス。 */
  status: string;
  /** クリア前の件数（実績値）。 */
  clearedCount: number;
  /** ステータスメッセージ。 */
  message: string;
}
