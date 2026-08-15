import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // AWS ECS Fargate へのコンテナデプロイ用に standalone 出力を追加する（INFRA-1）。
  // .next/standalone に依存関係込みの最小サーバーが出力される。npm run dev には影響しない。
  // Docker ビルド時（frontend/Dockerfile が BUILD_STANDALONE=true を設定）のみ有効化する。
  // "next start" は standalone 出力と非互換（Next.js が起動時に警告し、E2E の
  // webServer（npm run start）実行中にクラッシュする）なため、ローカル
  // ビルド・E2E（npm run e2e）・CI の npm run build では通常出力のままにする。
  output: process.env.BUILD_STANDALONE === "true" ? "standalone" : undefined,
};

export default nextConfig;
