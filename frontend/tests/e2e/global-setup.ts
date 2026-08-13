/**
 * FE-8: E2E テストのグローバルセットアップ。
 *
 * バックエンドのヘルスチェックをポーリングした後、デモ初期状態（決定論的な内訳）を
 * `POST /api/v1/demo/seed` で投入する。Playwright は webServer の起動後に本ファイルを
 * 実行するため、起動済みバックエンドへシードを投入できる。
 *
 * シード内訳（docs/business-model.md §3.4 のデモ既定値に倣う最小構成）:
 *   Level 0（正常）×1 / Level 1 ×2 / Level 2 ×1 / Level 3 ×1
 *
 * 実音響WAV（backend/dataset）は Git 管理外のため使用せず、E2E 専用の合成音
 * （8000Hz / 1.0秒 / 8000サンプルの PCM16）で投入する。深刻度はシード API が
 * `level` に確定するため、スペクトル値の分類には依存しない（DEMO-1 と同じ確定方式）。
 */
import { request } from "@playwright/test";
import { API_BASE_URL, SEED_HYDRANTS, makePcm16Base64, sensorIdOf } from "./helpers";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** バックエンドのヘルスチェック（最大 30 秒ポーリング）。 */
async function waitForBackend(
  context: Awaited<ReturnType<typeof request.newContext>>,
): Promise<void> {
  for (let i = 0; i < 30; i++) {
    try {
      const response = await context.get("/api/v1/sensors");
      if (response.ok()) return;
    } catch {
      // 起動中は失敗するため再試行する
    }
    await sleep(1000);
  }
  throw new Error(
    `E2E 前提のバックエンド (${API_BASE_URL}) に接続できませんでした。` +
      "uvicorn の起動に失敗していないか確認してください（backend/ の依存・ポート 8000）。",
  );
}

/** デモシード 1 件を投入する。 */
async function seedOne(
  context: Awaited<ReturnType<typeof request.newContext>>,
  level: number,
  hydrantId: string,
  recordedAt: string,
): Promise<void> {
  const hydrant = SEED_HYDRANTS[hydrantId];
  if (!hydrant) {
    throw new Error(`シード未定義の消火栓です: ${hydrantId}`);
  }
  const response = await context.post("/api/v1/demo/seed", {
    data: {
      sensor_id: sensorIdOf(hydrantId),
      hydrant_id: hydrantId,
      recorded_at: recordedAt,
      location: { latitude: hydrant.latitude, longitude: hydrant.longitude },
      sample_rate_hz: 8000,
      duration_sec: 1.0,
      audio_base64: makePcm16Base64(level),
      level,
    },
  });
  if (!response.ok()) {
    throw new Error(
      `シード投入に失敗しました: ${hydrantId} level=${level} ` +
        `${response.status()} ${await response.text()}`,
    );
  }
}

/** グローバルセットアップ（テスト実行前に一度だけ実行される）。 */
export default async function globalSetup(): Promise<void> {
  const context = await request.newContext({ baseURL: API_BASE_URL });
  try {
    await waitForBackend(context);

    // 1 分前を起点にした録音日時（深刻度降順ソートが主なので時刻は表示順に影響しない）。
    const base = Date.now() - 60_000;
    // Level 0（正常）ベースライン → 既定では一覧非表示（「正常も表示」トグルの検証用）。
    await seedOne(context, 0, "HYD-006", new Date(base - 20_000).toISOString());
    // Level 1（微小漏水）×2
    await seedOne(context, 1, "HYD-001", new Date(base - 10_000).toISOString());
    await seedOne(context, 1, "HYD-002", new Date(base - 6_000).toISOString());
    // Level 2（進行性漏水）×1
    await seedOne(context, 2, "HYD-004", new Date(base - 4_000).toISOString());
    // Level 3（管路破裂）×1 → アラート一覧の最上位に表示される
    await seedOne(context, 3, "HYD-003", new Date(base - 2_000).toISOString());
  } finally {
    await context.dispose();
  }
}
