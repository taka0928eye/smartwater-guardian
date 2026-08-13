# INFRA-1: AWS ECS Fargate デプロイ用 frontend イメージ（マルチステージビルド）
# ビルドコマンド: docker build -f frontend/Dockerfile --build-arg NEXT_PUBLIC_API_BASE_URL=<ALB-DNS> -t smartwater-guardian-frontend:latest .
# （context = リポジトリルート = "." である点に注意）

# --- deps stage: node_modules インストール
FROM node:22-slim AS deps

WORKDIR /app

# package*.json（dependencies インストール用）
COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

# --- builder stage: Next.js ビルド
FROM node:22-slim AS builder

WORKDIR /app

# build-arg で ALB DNS 名またはカスタムドメインを受け取る（ビルド時埋め込み）
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

# deps stage からコピー
COPY --from=deps /app/node_modules ./node_modules

# frontend ソースコード
COPY frontend/ .

# ビルド実行（output: standalone → .next/standalone が生成される）
RUN npm run build

# --- runtime stage: standalone server
FROM node:22-slim

WORKDIR /app

# ユーザー作成（Next.js 公式 standalone サンプルに倣う）
RUN groupadd -r nodejs && useradd -r -g nodejs nextjs

# builder からコピー: .next/standalone（依存関係込みサーバー）
COPY --from=builder /app/.next/standalone ./

# builder からコピー: .next/static（クライアント JS・CSS）
COPY --from=builder /app/.next/static ./.next/static

# builder からコピー: public ディレクトリ
COPY --from=builder /app/public ./public

# INFRA-1: route.ts が process.cwd()/../docs/business-model.md を参照するため、
# リポジトリルート context でここに docs/business-model.md を relative path で配置
# → WORKDIR /app/frontend で cwdが合わせられるため、
#   process.cwd() + ".." + "docs/business-model.md" = /app/docs/business-model.md に解決される
COPY docs/business-model.md ./docs/business-model.md

# ユーザー切り替え
USER nextjs

# expose port
EXPOSE 3000

# 環境変数設定
ENV PORT=3000 HOSTNAME=0.0.0.0

# standalone サーバー起動（ビルド済みの server.js で起動）
CMD ["node", "server.js"]
