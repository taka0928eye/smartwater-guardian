import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // AWS ECS Fargate へのコンテナデプロイ用に standalone 出力を追加する（INFRA-1）。
  // .next/standalone に依存関係込みの最小サーバーが出力される。npm run dev には影響しない。
  output: "standalone",
};

export default nextConfig;
