/** 手動配置WAVを使うシード投入のE2E。実音源・外部通信には依存しない。 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { test, expect } from "./fixtures";

const REQUIRED_WAV_FILES = [
  "BE3_demo_no-leak_level0.wav",
  "BE3_demo_leak_level1.wav",
  "BE3_demo_leak_level2.wav",
  "BE3_demo_leak_level3.wav",
] as const;
const datasetDir = path.resolve(process.cwd(), "../backend/dataset");
let backupDir = "";
const backedUpFiles: string[] = [];

function createTestWav(filePath: string, frequencyHz: number): void {
  const sampleRate = 8_000;
  const sampleCount = 8_000;
  const pcm = Buffer.alloc(sampleCount * 2);
  for (let index = 0; index < sampleCount; index += 1) {
    const value = Math.round(
      Math.sin((2 * Math.PI * frequencyHz * index) / sampleRate) * 12_000,
    );
    pcm.writeInt16LE(value, index * 2);
  }

  const wav = Buffer.alloc(44 + pcm.length);
  wav.write("RIFF", 0, "ascii");
  wav.writeUInt32LE(36 + pcm.length, 4);
  wav.write("WAVE", 8, "ascii");
  wav.write("fmt ", 12, "ascii");
  wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20);
  wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(sampleRate, 24);
  wav.writeUInt32LE(sampleRate * 2, 28);
  wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34);
  wav.write("data", 36, "ascii");
  wav.writeUInt32LE(pcm.length, 40);
  pcm.copy(wav, 44);
  fs.writeFileSync(filePath, wav);
}

test.describe.configure({ mode: "serial" });

test.beforeAll(() => {
  fs.mkdirSync(datasetDir, { recursive: true });
  backupDir = fs.mkdtempSync(path.join(os.tmpdir(), "smartwater-e2e-wav-"));
  for (const filename of REQUIRED_WAV_FILES) {
    const source = path.join(datasetDir, filename);
    if (fs.existsSync(source)) {
      fs.renameSync(source, path.join(backupDir, filename));
      backedUpFiles.push(filename);
    }
  }
});

test.afterAll(() => {
  for (const filename of REQUIRED_WAV_FILES) {
    const generated = path.join(datasetDir, filename);
    if (fs.existsSync(generated)) fs.unlinkSync(generated);
  }
  for (const filename of backedUpFiles) {
    fs.renameSync(path.join(backupDir, filename), path.join(datasetDir, filename));
  }
  fs.rmSync(backupDir, { recursive: true, force: true });
});

test("音声未配置時も画面を壊さず全ファイルの配置案内を表示する", async ({ page }) => {
  await page.goto("/");

  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) =>
        candidate.url().includes("/api/v1/demo/seed-batch") &&
        candidate.request().method() === "POST",
    ),
    page.getByTestId("seed-demo-button").click(),
  ]);

  expect(response.status()).toBe(404);
  const error = page.getByTestId("seed-demo-error");
  await expect(error).toContainText("WAVが不足しています");
  for (const filename of REQUIRED_WAV_FILES) {
    await expect(error).toContainText(filename);
  }
  await expect(
    page.getByRole("heading", { name: /SmartWater Guardian/ }),
  ).toBeVisible();
  await expect(page.locator(".leaflet-container")).toBeVisible();
});

test("テスト用WAV 4本を配置すると画面のボタンだけで23件投入できる", async ({ page }) => {
  REQUIRED_WAV_FILES.forEach((filename, index) => {
    createTestWav(path.join(datasetDir, filename), 400 + index * 300);
  });
  await page.goto("/");

  const [response] = await Promise.all([
    page.waitForResponse(
      (candidate) =>
        candidate.url().includes("/api/v1/demo/seed-batch") &&
        candidate.request().method() === "POST",
    ),
    page.getByTestId("seed-demo-button").click(),
  ]);

  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as {
    inserted_count: number;
    level_counts: Record<string, number>;
  };
  expect(body.inserted_count).toBe(23);
  expect(body.level_counts).toEqual({ "0": 11, "1": 8, "2": 3, "3": 1 });
  await expect(page.getByTestId("seed-demo-message")).toContainText("23 件投入しました");
  await expect(page.getByTestId("kpi-card-sensors")).toContainText("23台");
});
