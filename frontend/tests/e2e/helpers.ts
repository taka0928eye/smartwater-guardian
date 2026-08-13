/**
 * FE-8: E2E テスト共通ヘルパー。
 *
 * - PCM16LE mono 音声（8000Hz / 1.0秒 / 8000サンプル = BE-3 MVP 契約）を Base64 生成し、
 *   実音響WAVなしで `POST /api/v1/demo/seed` へ投入する（深刻度は API が意図レベルに確定）。
 * - バックエンド URL の単一ソース（`E2E_API_BASE_URL` / 既定 `http://localhost:8000`）。
 * - バックエンド未応答シミュレーション用のネットワーク遮断ヘルパー。
 */
import type { APIRequestContext, Page } from "@playwright/test";

/** バックエンド API の接続先（playwright.config.ts と同じ解決）。 */
export const API_BASE_URL =
  process.env.E2E_API_BASE_URL ?? "http://localhost:8000";

/** BE-3 MVP 契約のサンプリング仕様（audio.py と一致させる）。 */
const SAMPLE_RATE_HZ = 8000;
const SAMPLE_COUNT = 8000;
const DURATION_SEC = 1.0;

/** シードに利用する消火栓（backend/app/data/hydrants.json に実在するIDと座標）。 */
export const SEED_HYDRANTS: Record<string, { latitude: number; longitude: number }> = {
  "HYD-001": { latitude: 35.7019, longitude: 139.7444 },
  "HYD-002": { latitude: 35.6917, longitude: 139.7703 },
  "HYD-003": { latitude: 35.6812, longitude: 139.7744 },
  "HYD-004": { latitude: 35.6667, longitude: 139.7583 },
  "HYD-005": { latitude: 35.6896, longitude: 139.7006 },
  "HYD-006": { latitude: 35.6595, longitude: 139.7005 },
  "HYD-007": { latitude: 35.7121, longitude: 139.777 },
};

/** hydrant_id から sensor_id を導出する（例: HYD-001 -> SNS-001）。 */
export function sensorIdOf(hydrantId: string): string {
  const seq = hydrantId.replace("HYD-", "");
  return `SNS-${seq}`;
}

/**
 * 8000Hz / 1.0秒 / 8000サンプルの PCM16LE mono raw bytes を Base64 で生成する。
 * `POST /api/v1/demo/seed` の `audio_base64` は WAV コンテナを含まないため、
 * 生バイト列をそのままエンコードする。正弦波はスペクトル描画用の実信号であって、
 * 深刻度はシード API が `level` に確定する（実 SVM の分類結果には依存しない）。
 */
export function makePcm16Base64(level: number): string {
  const samples = new Int16Array(SAMPLE_COUNT);
  // Level 0 は低周波（正常）、Level 1〜3 は漏水帯域（500〜1500Hz）寄りの周波数。
  const freqHz = level === 0 ? 200 : 800 + level * 120;
  for (let i = 0; i < SAMPLE_COUNT; i++) {
    samples[i] = Math.round(
      Math.sin((2 * Math.PI * freqHz * i) / SAMPLE_RATE_HZ) * 6000,
    );
  }
  const bytes = Buffer.alloc(SAMPLE_COUNT * 2);
  for (let i = 0; i < SAMPLE_COUNT; i++) {
    bytes.writeInt16LE(samples[i]!, i * 2);
  }
  return bytes.toString("base64");
}

export interface SeedAlertOptions {
  /** 投入する深刻度（0〜3）。デフォルト 1。 */
  level?: number;
  /** 録音日時の相対オフセット（ミリ秒）。デフォルト 0（現在時刻）。 */
  offsetMs?: number;
}

/**
 * `POST /api/v1/demo/seed` でデモシード 1 件を投入し、生成された telemetry_id を返す。
 * ポーリング検証（新着アラートの自動反映）などテスト中にデータを追加する場合に使う。
 */
export async function seedAlert(
  request: APIRequestContext,
  hydrantId: string,
  options: SeedAlertOptions = {},
): Promise<string> {
  const level = options.level ?? 1;
  const offsetMs = options.offsetMs ?? 0;
  const hydrant = SEED_HYDRANTS[hydrantId];
  if (!hydrant) {
    throw new Error(`シード未定義の消火栓です: ${hydrantId}`);
  }
  const response = await request.post(`${API_BASE_URL}/api/v1/demo/seed`, {
    data: {
      sensor_id: sensorIdOf(hydrantId),
      hydrant_id: hydrantId,
      recorded_at: new Date(Date.now() - offsetMs).toISOString(),
      location: { latitude: hydrant.latitude, longitude: hydrant.longitude },
      sample_rate_hz: SAMPLE_RATE_HZ,
      duration_sec: DURATION_SEC,
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
  const body = (await response.json()) as { telemetry_id?: string };
  return body.telemetry_id ?? "";
}

/**
 * ブラウザから `/api/v1/**` への要求をすべて遮断し、バックエンド未応答を再現する。
 * SSR（サーバー側取得）は遮断されないため、クライアント側のフォールバック
 * （KPI 再スケルトン / アラートエラー表示）を検証できる。
 */
export async function interceptBackendFailure(page: Page): Promise<void> {
  await page.route("**/api/v1/**", (route) => route.abort());
}
