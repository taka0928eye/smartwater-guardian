/**
 * E2E テスト グローバルセットアップ
 *
 * バックエンドサーバー起動後、デモシード（アラート）をインメモリストアに投入する。
 * このセットアップ完了後に全テストが並列・直列で実行される。
 */
import { FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig) {
  const apiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://localhost:8000";

  // バックエンド起動を HTTP ポーリングで確認（最大 30 秒）
  console.log(`[global-setup] バックエンド接続確認: ${apiBaseUrl}/health`);
  const maxRetries = 30;
  let connected = false;

  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`${apiBaseUrl}/health`, {
        method: "GET",
        timeout: 3000,
      });
      if (response.ok) {
        console.log("[global-setup] バックエンド起動確認");
        connected = true;
        break;
      }
    } catch {
      // 接続失敗 → 1 秒待機して再試行
      if (i < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
  }

  if (!connected) {
    throw new Error(
      `[global-setup] バックエンド接続失敗（${maxRetries * 1000}ms タイムアウト）`
    );
  }

  // デモシード投入: Level 3, 2, 1 をそれぞれ投入
  console.log("[global-setup] デモシード投入開始");
  try {
    const seedResponse = await fetch(`${apiBaseUrl}/api/v1/alerts/seed`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        count: 9, // Level 3, 2, 1 をそれぞれ 3 件ずつ（合計 9 件）
      }),
    });

    if (!seedResponse.ok) {
      const text = await seedResponse.text();
      console.warn(
        `[global-setup] シード投入失敗 (${seedResponse.status}): ${text}`
      );
    } else {
      const data = (await seedResponse.json()) as {
        inserted_count: number;
        message: string;
      };
      console.log(`[global-setup] ${data.message}`);
    }
  } catch (err) {
    console.warn(`[global-setup] シード投入エラー (続行): ${err}`);
  }
}

export default globalSetup;
