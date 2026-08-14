/**
 * FE-8: アラート一覧・詳細ドロワー E2E テスト（シナリオ 3・4）。
 *
 * シナリオ 3（一覧のフィルタ・ソート）: 深刻度降順ソート、Level 0 トグル。
 * シナリオ 4（詳細ドロワー）: 選択行の詳細（分析結果・スペクトル・波形・配管情報）表示。
 *
 * 前提: `tests/e2e/global-setup.ts` が実在マスタ（HYD-001〜010）へ投入する。
 * - L3: HYD-003 / HYD-004 / HYD-007（管路破裂・最上位 3 件）
 * - L2: HYD-005 / HYD-006 / HYD-008
 * - L1: HYD-009 / HYD-010 / HYD-001
 * - L0: HYD-002（正常・トグル検証用。既定で非表示）
 * ストアは並列テストで追加されないため、上位 3 件（L3）の順序は常に確定する。
 */
import { test, expect } from "./fixtures";
import { DashboardPage } from "./pages/DashboardPage";

test.describe("アラート一覧のソート・フィルタ（シナリオ 3）", () => {
  test("深刻度降順でソートされ、Level 0（正常）は既定で非表示", async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    // 最上位 3 件: Level 3 管路破裂（HYD-003 / HYD-004 / HYD-007）
    await expect(dashboard.alertRows.nth(0)).toContainText("HYD-003");
    await expect(dashboard.alertRows.nth(0)).toContainText("Level 3 管路破裂");
    await expect(dashboard.alertRows.nth(1)).toContainText("HYD-004");
    await expect(dashboard.alertRows.nth(1)).toContainText("Level 3 管路破裂");
    await expect(dashboard.alertRows.nth(2)).toContainText("HYD-007");
    await expect(dashboard.alertRows.nth(2)).toContainText("Level 3 管路破裂");

    // 4 番目: Level 2 進行性漏水（HYD-005）
    await expect(dashboard.alertRows.nth(3)).toContainText("HYD-005");
    await expect(dashboard.alertRows.nth(3)).toContainText("Level 2 進行性漏水");

    // 7 番目以降は Level 1（HYD-009 / HYD-010 / HYD-001）
    await expect(dashboard.alertRows.nth(6)).toContainText(/Level 1/);

    // 正常（Level 0・HYD-002）は既定で一覧に表示されない
    await expect(dashboard.alertRow("HYD-002")).not.toBeVisible();
  });

  test('「正常も表示」トグルで Level 0 の表示を切り替えられる', async ({ page }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.waitForAlertList();

    const toggle = page.getByTestId("show-level0-toggle");
    await expect(dashboard.alertRow("HYD-002")).not.toBeVisible();

    // チェックで正常（Level 0）も表示される
    await toggle.check();
    await expect(dashboard.alertRow("HYD-002")).toBeVisible();

    // チェックを外すと非表示へ戻る
    await toggle.uncheck();
    await expect(dashboard.alertRow("HYD-002")).not.toBeVisible();
  });
});

test.describe("詳細ドロワー表示（シナリオ 4）", () => {
  test("アラート選択でドロワーが開き、解析結果・スペクトル・波形・配管情報が表示される", async ({
    page,
  }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openAlert("HYD-003");

    // ドロワーが開く（見出し・アラート識別情報）
    await expect(dashboard.drawer).toBeVisible();
    await expect(dashboard.drawer.getByRole("heading", { name: "アラート詳細" })).toBeVisible();
    await expect(dashboard.drawer).toContainText("HYD-003");
    await expect(dashboard.drawer).toContainText("SNS-003");
    await expect(dashboard.drawer).toContainText("Level 3 管路破裂");
    await expect(dashboard.drawer).toContainText("センサーID");

    // FE-4: 解析結果（卓越周波数）・周波数スペクトル・時間軸波形
    await expect(
      dashboard.drawer.getByRole("heading", { name: "解析結果" }),
    ).toBeVisible();
    await expect(dashboard.drawer).toContainText("卓越周波数");
    await expect(
      dashboard.drawer.getByRole("heading", { name: /周波数スペクトル/ }),
    ).toBeVisible();
    await expect(
      dashboard.drawer.getByRole("heading", { name: "時間軸波形" }),
    ).toBeVisible();

    // 配管情報（BE-6 管台帳参照: HYD-003 → P-003）
    await expect(
      dashboard.drawer.getByRole("heading", { name: "配管情報" }),
    ).toBeVisible();
    await expect(dashboard.drawer).toContainText("管ID");
    await expect(dashboard.drawer).toContainText("P-003");

    // FE-6: AI 自動起票ボタンが表示される
    await expect(
      dashboard.drawer.getByRole("button", { name: /AI自動起票/ }),
    ).toBeVisible();

    // 閉じるボタンでドロワーが閉じる
    await dashboard.drawer.getByTestId("drawer-close").click();
    await expect(dashboard.drawer).not.toBeVisible();
  });

  test("選択したアラートの受信音響をWAVとして読み込める", async ({
    page,
    request,
    apiBaseUrl,
  }) => {
    const sampleRateHz = 8_000;
    const pcm = Buffer.alloc(sampleRateHz * 2);
    for (let index = 0; index < sampleRateHz; index += 1) {
      const sample = Math.round(
        Math.sin((2 * Math.PI * 900 * index) / sampleRateHz) * 12_000,
      );
      pcm.writeInt16LE(sample, index * 2);
    }

    const seedResponse = await request.post(`${apiBaseUrl}/api/v1/demo/seed`, {
      data: {
        level: 1,
        sensor_id: "SNS-AUDIO",
        hydrant_id: "HYD-AUDIO",
        recorded_at: "2026-08-14T10:00:00+09:00",
        location: { latitude: 35.7019, longitude: 139.7444 },
        sample_rate_hz: sampleRateHz,
        duration_sec: 1.0,
        audio_base64: pcm.toString("base64"),
        battery_pct: 90,
      },
    });
    expect(seedResponse.ok()).toBeTruthy();
    const seeded = (await seedResponse.json()) as { telemetry_id: string };

    const detailResponse = await request.get(
      `${apiBaseUrl}/api/v1/alerts/${seeded.telemetry_id}`,
    );
    expect(detailResponse.ok()).toBeTruthy();
    const detail = (await detailResponse.json()) as {
      analysis: { spectrum: unknown[] };
      waveform: unknown[];
    };
    expect(detail.analysis.spectrum).toHaveLength(128);
    expect(detail.waveform).toHaveLength(256);

    const dashboard = new DashboardPage(page);
    await dashboard.goto();
    await dashboard.openAlert("HYD-AUDIO");

    const player = dashboard.drawer.getByTestId("alert-audio-player");
    await expect(player).toBeVisible();
    const expectedUrl = `${apiBaseUrl}/api/v1/alerts/${seeded.telemetry_id}/audio`;
    await expect(player).toHaveAttribute("src", expectedUrl);

    const audioResponse = await request.get(expectedUrl);
    expect(audioResponse.ok()).toBeTruthy();
    expect(audioResponse.headers()["content-type"]).toBe("audio/wav");
    expect((await audioResponse.body()).subarray(0, 4).toString("ascii")).toBe(
      "RIFF",
    );
  });
});
