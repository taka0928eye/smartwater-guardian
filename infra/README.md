# AWS 本番環境構築ガイド（INFRA-1）

SmartWater Guardian の AWS 本番環境を CloudFormation で構築・デプロイするためのドキュメント。

## アーキテクチャ概要

```
Internet (HTTP)
    ↓
[ALB (public subnet ×2, AZ-a/AZ-c)]
  ├─ /api/v1/* → backend TargetGroup
  └─ その他 → frontend TargetGroup
    ↓
[ECS Fargate Cluster (private subnet ×2)]
  ├─ backend Service (desiredCount=1, ALB Stickiness有効)
  │   ├─ TaskDef: 0.25vCPU/0.5GB
  │   ├─ Env: ALLOWED_ORIGINS, ORCAROUTER_*, ORCAROUTER_API_KEY
  │   └─ 注: WAF / Secrets Manager はコスト削減のため不使用（APIキーは環境変数注入）
  └─ frontend Service (desiredCount=1)
      ├─ TaskDef: 0.5vCPU/1GB
      ├─ Env: PORT=3000, HOSTNAME=0.0.0.0
      └─ ビルド時: NEXT_PUBLIC_API_BASE_URL (ALB DNS)

[VPC NAT Gateway] (1台 デフォルト / 2台オプション)
  └─ ECRプル、外部API(Orcarouter) へのアウトバウンド

[CloudWatch Logs / Alarms / SNS]
  └─ ALB 5xx率、ECS CPU/Memory、UnHealthy Host 監視

[GitHub Actions OIDC]
  └─ ロール引き受け、ECR push、ECS タスク定義更新
```

## 前提条件

- AWS アカウント（東京リージョン = ap-northeast-1 を想定）
- AWS CLI v2 以上
- Docker Desktop（ローカルイメージビルド用）
- GitHub リポジトリ（OIDC 統合用）
- 最小限の IAM 権限（CloudFormation, ECS, ECR, VPC, ALB）

## ファイル構成

```
infra/
├── cloudformation/
│   ├── 00-github-oidc.yaml       # GitHub Actions OIDC プロバイダ + IAM ロール
│   ├── 01-network.yaml            # VPC / Subnet / NAT Gateway
│   ├── 02-security.yaml           # SG（3個） / IAM ロール（3個）
│   ├── 03-ecr.yaml                # ECR リポジトリ ×2
│   ├── 04-alb.yaml                # ALB / TargetGroup ×2 / Listener / ルール
│   ├── 06-ecs.yaml                # ECS クラスタ / TaskDef ×2 / Service ×2（デモ向け最小構成）
│   └── 07-monitoring.yaml         # CloudWatch Alarms + SNS
├── scripts/
│   └── deploy.ps1                 # PowerShell デプロイオーケストレーション
└── README.md                      # このファイル

.github/workflows/
└── deploy.yml                     # GitHub Actions ワークフロー（OIDC + ECR push + ECS更新）
```

## CloudFormation パラメータ一覧

### 共通

- `ProjectName`: デフォルト = `smartwater-guardian`
- `Environment`: デフォルト = `dev`（パラメータにはスタック名に含まれる）

### 00-github-oidc.yaml

| パラメータ | 型 | 既定値 | 説明 |
|-----------|---|-------|------|
| `GitHubOrg` | String | `taka0928eye` | GitHub 組織名 |
| `GitHubRepo` | String | `smartwater-guardian` | リポジトリ名 |
| `GitHubBranch` | String | `main` | デプロイ対象ブランチ |

### 01-network.yaml

| パラメータ | 型 | 既定値 | 説明 |
|-----------|---|-------|------|
| `VpcCidr` | String | `10.0.0.0/16` | VPC CIDR |
| `NatGatewayCount` | Number | `1` | NAT Gateway 数（1=コスト最適、2=完全HA） |

### 04-alb.yaml

| パラメータ | 型 | 既定値 | 説明 |
|-----------|---|-------|------|
| `DomainName` | String | `` （空） | カスタムドメイン（未設定時は ALB DNS 使用） |
| `EnableHttps` | String | `false` | HTTPS 有効化（Route53 + ACM 前提） |

### 06-ecs.yaml

| パラメータ | 型 | 既定値 | 説明 |
|-----------|---|-------|------|
| `BackendImageTag` | String | `latest` | backend ECR イメージタグ |
| `FrontendImageTag` | String | `latest` | frontend ECR イメージタグ |
| `BackendDesiredCount` | Number | `1` | backend タスク数（デモ向け最小構成=1） |
| `FrontendDesiredCount` | Number | `1` | frontend タスク数（デモ向け最小構成=1） |
| `OrcaRouterBaseUrl` | String | `` | Orcarouter API ベース URL |
| `OrcaRouterModel` | String | `gpt-4` | Orcarouter モデル名 |
| `OrcaRouterEnabled` | String | `false` | Orcarouter 有効化 |
| `OrcaRouterApiKey` | String | `` | Orcarouter API キー（環境変数で直接注入。Secrets Manager はコスト削減のため不使用） |
| `AllowedOrigins` | String | `http://localhost:3000` | CORS 許可オリジン |

## デプロイ手順

### 初回デプロイ（ローカルまたは CI/CD）

#### 1. Docker イメージ準備

backend：
```bash
docker build -f backend/Dockerfile -t smartwater-guardian-backend:latest backend/
```

frontend（`NEXT_PUBLIC_API_BASE_URL` をビルド時指定）：
```bash
docker build -f frontend/Dockerfile \
  --build-arg NEXT_PUBLIC_API_BASE_URL=http://<ALB-DNS-or-domain> \
  -t smartwater-guardian-frontend:latest .
```

#### 2. ECR リポジトリ作成（03-ecr.yaml のみデプロイ）

```bash
aws cloudformation deploy \
  --template-file infra/cloudformation/03-ecr.yaml \
  --stack-name smartwater-guardian-ecr \
  --region ap-northeast-1
```

#### 3. イメージを ECR にプッシュ

```bash
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <AWS-ACCOUNT-ID>.dkr.ecr.ap-northeast-1.amazonaws.com

docker tag smartwater-guardian-backend:latest \
  <AWS-ACCOUNT-ID>.dkr.ecr.ap-northeast-1.amazonaws.com/smartwater-guardian-backend:latest

docker tag smartwater-guardian-frontend:latest \
  <AWS-ACCOUNT-ID>.dkr.ecr.ap-northeast-1.amazonaws.com/smartwater-guardian-frontend:latest

docker push <AWS-ACCOUNT-ID>.dkr.ecr.ap-northeast-1.amazonaws.com/smartwater-guardian-backend:latest
docker push <AWS-ACCOUNT-ID>.dkr.ecr.ap-northeast-1.amazonaws.com/smartwater-guardian-frontend:latest
```

#### 4. 全スタックをデプロイ（PowerShell）

```powershell
cd infra/scripts
.\deploy.ps1 -Environment dev -Region ap-northeast-1 `
  -BackendImageTag latest -FrontendImageTag latest `
  -OrcaRouterApiKey '<ACTUAL_ORCAROUTER_API_KEY>'
```

API キーは ECS タスク定義の環境変数 `ORCAROUTER_API_KEY` として直接注入される（Secrets Manager はコスト削減のため不使用。未設定時は backend が安全にフォールバック動作）。

または個別デプロイ：

```bash
# 依存順
aws cloudformation deploy --template-file infra/cloudformation/00-github-oidc.yaml --stack-name smartwater-guardian-github-oidc --region ap-northeast-1 --capabilities CAPABILITY_NAMED_IAM

aws cloudformation deploy --template-file infra/cloudformation/01-network.yaml --stack-name smartwater-guardian-network --region ap-northeast-1 --parameter-overrides VpcCidr=10.0.0.0/16 NatGatewayCount=1

# ... 以下同様
```

#### 5. デプロイ確認

ALB DNS 名取得：
```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[0].DNSName' \
  --region ap-northeast-1
```

ブラウザで `http://<ALB-DNS-NAME>` にアクセス。

ECS サービス状態確認：
```bash
aws ecs describe-services \
  --cluster smartwater-guardian-dev \
  --services smartwater-guardian-backend smartwater-guardian-frontend \
  --region ap-northeast-1
```

### 更新デプロイ（コード変更後）

1. 対象イメージをビルド・ECR にプッシュ
2. GitHub Actions ワークフロー実行（`workflow_dispatch`）またはローカルで `deploy.ps1` 実行
3. ECS がタスク定義を更新し、ローリングデプロイを開始

## 概算コスト（デモ向け最小構成、NAT Gateway 1台・東京リージョン）

デモ（1日）向けに **WAF・Secrets Manager・Auto Scaling・Container Insights・VPC Flow Logs を廃止**し、
タスク数を各 **1台** に削減した最小構成。1日デモの実コスト目安は **約 $3.5-4.5**。

| 項目 | 月額（USD） | デモ1日換算 |
|-----|-----------|-----------|
| Fargate（backend 1タスク 0.25vCPU/0.5GB） | ~$7-9 | ~$0.3 |
| Fargate（frontend 1タスク 0.5vCPU/1GB） | ~$15-18 | ~$0.6 |
| ALB（固定費） | ~$16-20 | ~$0.6 |
| ALB（LCU 従量） | ~$5-10 | ~$0.3 |
| NAT Gateway ×1（固定） | ~$45 | ~$1.5 |
| NAT Gateway（データ処理） | ~$1-5 | ~$0.1 |
| ECR（ストレージ） | <$1 | <$0.1 |
| CloudWatch Logs | ~$1-3 | ~$0.1 |
| Route53（ドメイン保有時） | ~$0.5 | ~$0.02 |
| **合計（目安）** | **~$85-115** | **~$3.5-4.5** |

**NAT Gateway 2台構成の場合: +$45/月（デモでは1台を推奨）**

## To-Be 構成（本番向け・従来設計）

デモ（1日）向けコスト最小化のため現行構成からは廃止した、**INFRA-1 当初の本番向け設計（To-Be）**。
デモ後の本番運用・HA・セキュリティ要件に備えて、設計内容とコスト目安をここに記録する。

> 現行（As-Is）は「[アーキテクチャ概要](#アーキテクチャ概要)」のデモ向け最小構成。To-Be は WAF 適用・API キーの Secrets Manager 管理・2タスクHA を求める本番移行時の目標構成。

### アーキテクチャ図（従来設計）

```
Internet (HTTP)
    ↓
[ALB (public subnet ×2, AZ-a/AZ-c)]
  ├─ /api/v1/* → backend TargetGroup
  └─ その他 → frontend TargetGroup
    ↓
[WAF WebACL]
  ├─ マネージドルール (AWS managed)
  ├─ レート制限 (2000 req/5min)
  └─ /api/v1/telemetry: OversizeHandling=CONTINUE
    ↓
[ECS Fargate Cluster (private subnet ×2)]
  ├─ backend Service (desiredCount=2, ALB Stickiness有効)
  │   ├─ TaskDef: 0.25vCPU/0.5GB
  │   ├─ Env: ALLOWED_ORIGINS, ORCAROUTER_*
  │   └─ Secrets: ORCAROUTER_API_KEY (Secrets Manager)
  └─ frontend Service (desiredCount=2)
      ├─ TaskDef: 0.5vCPU/1GB
      ├─ Env: PORT=3000, HOSTNAME=0.0.0.0
      └─ ビルド時: NEXT_PUBLIC_API_BASE_URL (ALB DNS)

[VPC NAT Gateway] (1台 デフォルト / 2台オプション)
  └─ ECRプル、外部API(Orcarouter) へのアウトバウンド

[CloudWatch Logs / Alarms / SNS]
  └─ ALB 5xx率、ECS CPU/Memory、UnHealthy Host 監視

[GitHub Actions OIDC]
  └─ ロール引き受け、ECR push、ECS タスク定義更新
```

### 構成要素（従来設計）

| 要素 | 内容 |
|-----|------|
| **WAF WebACL** | `05-waf.yaml`（AWS::WAFv2::WebACL + WebACLAssociation）。マネージドルール 3種（CommonRuleSet / KnownBadInputs / AmazonIpReputationList）+ レート制限 2000req/5min（IP 単位・429応答）。`/api/v1/telemetry` は `SizeRestrictions_BODY` を Allow 上書き（OversizeHandling=CONTINUE） |
| **Secrets Manager** | `02-security.yaml` の `OrcaRouterApiKeySecret`（`smartwater-guardian/orcarouter-api-key`）。実行ロールに `SecretsManagerAccess`、backend タスクロールに `SecretsManagerRead` を付与。キーは `aws secretsmanager put-secret-value` で投入 |
| **タスク数** | backend / frontend とも desiredCount=**2**（HA）。ALB スティッキーセッション（lb_cookie 86400s） |
| **Auto Scaling** | `06-ecs.yaml` の `ScalableTarget` + `TargetTrackingScalingPolicy`（CPU 70% ターゲット・Max 4・cooldown 300s） |
| **Container Insights** | ECS クラスタで `enabled`（タスク/サービス単位のメトリクス収集） |
| **VPC Flow Logs** | `01-network.yaml`（REJECT のみ・CloudWatch Logs へ・保持7日） |
| **ログ保持** | `/ecs/*` ロググループは **30日** |

### コスト目安（従来設計・月額・東京リージョン）

| 項目 | 月額（USD） |
|-----|-----------|
| Fargate（backend 2タスク 0.25vCPU/0.5GB） | ~$15-18 |
| Fargate（frontend 2タスク 0.5vCPU/1GB） | ~$30-36 |
| ALB（固定費） | ~$16-20 |
| ALB（LCU 従量） | ~$5-10 |
| NAT Gateway ×1（固定） | ~$45 |
| NAT Gateway（データ処理） | ~$1-5 |
| ECR（ストレージ） | <$1 |
| CloudWatch Logs | ~$1-3 |
| WAF（WebACL） | ~$5 |
| WAF（ルール） | ~$3-5 |
| Secrets Manager | ~$0.4 |
| Route53（ドメイン保有時） | ~$0.5 |
| **合計（目安）** | **~$125-155** |

NAT Gateway 2台構成の場合: +$45/月

### To-Be へ戻す手順（デモ構成 → 本番構成）

現行のデモ最小構成から To-Be 構成に戻すには、削除した要素を復元・再デプロイする。

1. **WAF**: `infra/cloudformation/05-waf.yaml` を復元し、`deploy.ps1` に WAF スタックのデプロイブロックを再追加
2. **Secrets Manager**: `02-security.yaml` に `OrcaRouterApiKeySecret`・`SecretsManagerAccess` / `SecretsManagerRead` ポリシー・`OrcaRouterSecretArn` 出力を再追加し、`06-ecs.yaml` の `ORCAROUTER_API_KEY` を `Secrets:`（`ValueFrom`）参照に戻す
3. **タスク数/HA**: `06-ecs.yaml` の `BackendDesiredCount` / `FrontendDesiredCount` を `2` に戻す
4. **Auto Scaling**: `06-ecs.yaml` に `ScalableTarget` + `ScalingPolicy` 4リソースを再追加
5. **Container Insights**: ECS クラスタの `containerInsights` を `enabled` に戻す
6. **VPC Flow Logs**: `01-network.yaml` に `VpcFlowLogsRole` / `VpcFlowLogsLogGroup` / `VpcFlowLogs` を再追加
7. **ログ保持**: `/ecs/*` ロググループの `RetentionInDays` を `30` に戻す
8. **デプロイ**: `deploy.ps1` を実行後、`aws secretsmanager put-secret-value --secret-id smartwater-guardian/orcarouter-api-key --secret-string '<API_KEY>'` でキー投入

## 既知の制約・リスク

### インメモリストア

- `backend/app/store.py` の `InMemoryStore` はプロセス内シングルトン
- **デモ向け最小構成はタスク数 1 のため、タスク間のデータ不整合は発生しない**（複数タスク化した場合はタスク間で共有されず、再起動で履歴が消失する点に注意）
- タスク再起動でテレメトリ/アラート履歴が消失（デモ1日で再構築するため実害なし）

### 認証・権限管理

- ALB 配下は認証なしで公開状態
- **WAF はデモコスト削減のため廃止**しており、レート制限・L7攻撃対策は未適用
- スコープ外（実装禁止）だが、将来は IP ホワイトリスト（WAF）や Cognito 検討推奨

### HTTP 暫定運用

- ドメイン未保有のため初期は HTTP のみ
- 通信は平文（中間者攻撃リスク）
- ドメイン取得後は HTTPS 化を最優先で実施する運用ルール必須

### ビルド時埋め込み

- `NEXT_PUBLIC_API_BASE_URL`（frontend）はビルド時に固定
- ALB DNS 名からカスタムドメインへ切り替える場合、frontend イメージ再ビルド必須
- ECS タスク定義の環境変数上書きだけでは対応不可

## サポート・トラブルシューティング

### ECS タスクが起動しない

CloudWatch Logs を確認：
```bash
aws logs tail /ecs/smartwater-guardian-dev/backend --follow --region ap-northeast-1
```

タスク定義や IAM ロールを確認：
```bash
aws ecs describe-task-definition \
  --task-definition smartwater-guardian-dev-backend \
  --region ap-northeast-1
```

### ALB がトラフィックをルーティングしない

TargetGroup ヘルスチェック確認：
```bash
aws elbv2 describe-target-health \
  --target-group-arn <TG-ARN> \
  --region ap-northeast-1
```

## 参考

- [計画書](../../.claude/plans/aws-aws-cloudformation-yml-wobbly-melody.md)
- [GitHub Issue #30](https://github.com/taka0928eye/smartwater-guardian/issues/30)
- AWS CloudFormation ベストプラクティス: https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/
