# INFRA-1: AWS ECS Fargate デプロイ用 backend イメージ（マルチステージビルド）
# ビルドコマンド: docker build -f backend/Dockerfile -t smartwater-guardian-backend:latest backend/
# （context = backend/ ディレクトリ）

FROM python:3.12-slim AS builder

WORKDIR /build

# requirements.txt のみ先にコピーしてキャッシュを効かせる
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- runtime stage ---
FROM python:3.12-slim

WORKDIR /app

# ユーザー作成（本番で root 実行を避ける）
RUN useradd -r -s /sbin/nologin appuser

# builder からの依存関係をコピー
COPY --from=builder /root/.local /home/appuser/.local

# アプリケーション本体（app/ + main.py）
# app/ 配下には data/*.json（hydrants.json 等）と models/*.joblib（ML モデル）が自動的に含まれる
COPY app ./app
COPY main.py .

# アプリケーションディレクトリの所有権を appuser に変更
RUN chown -R appuser:appuser /app

# デモ音源ディレクトリを事前作成（S3同期時に書き込み権限が必要）
RUN mkdir -p /app/dataset && chown -R appuser:appuser /app/dataset

# ユーザー切り替え
USER appuser

# PATH に入れないと python -m pip の警告が出るため設定
ENV PATH=/home/appuser/.local/bin:$PATH

# ヘルスチェック（軽量: python スタンドアライブアリでは -c で呼び出し）
# healthcheck コマンドが実行できない環境もあるため optional
# HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
#     CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/')" || exit 1

EXPOSE 8000

# 本番では reload なし
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
