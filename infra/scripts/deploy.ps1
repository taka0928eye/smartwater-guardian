# INFRA-1: AWS CloudFormation デプロイオーケストレーション（PowerShell）
# ローカルまたは CI/CD パイプラインからスタックを依存順にデプロイする
#
# 使用方法:
#   .\deploy.ps1 -Environment prod -Region ap-northeast-1 -BackendImageTag latest
#   .\deploy.ps1 -Phase Infra -Environment dev            # 初回: 00〜04（ALB まで）
#   .\deploy.ps1 -Phase App  -Environment dev             # 初回: 06〜07（イメージ準備後）
#
# パラメータ:
#   -Environment: デプロイ環境（dev/staging/prod、既定: dev）
#   -Region: AWS リージョン（既定: ap-northeast-1）
#   -BackendImageTag: backend ECR イメージタグ（既定: latest）
#   -FrontendImageTag: frontend ECR イメージタグ（既定: latest）
#   -Phase: デプロイ対象（All=00〜07 全部 / Infra=00〜04（ALB まで）/ App=06〜07（ECS・監視）、既定: All）
#     初回デプロイは frontend の NEXT_PUBLIC_API_BASE_URL（ALB DNS 名）をビルド時固定するため、
#     「Infra → ALB DNS 名取得 → イメージビルド/ECR プッシュ → App」の順で実行する。

param(
    [string]$Environment = "dev",
    [string]$Region = "ap-northeast-1",
    [ValidateSet("All", "Infra", "App")]
    [string]$Phase = "All",
    [string]$BackendImageTag = "latest",
    [string]$FrontendImageTag = "latest",
    [string]$GitHubOrg = "taka0928eye",
    [string]$GitHubRepo = "smartwater-guardian",
    [string]$VpcCidr = "10.0.0.0/16",
    [int]$NatGatewayCount = 1,
    [string]$OrcaRouterBaseUrl = "",
    [string]$OrcaRouterModel = "gpt-4",
    [string]$OrcaRouterEnabled = "false",
    [string]$OrcaRouterApiKey = "",
    [string]$AllowedOrigins = "http://localhost:3000"
)

$ErrorActionPreference = "Stop"

# 文字エンコーディング設定（日本語テキスト対応）
# PowerShell: UTF-8 出力を強制
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# Python: UTF-8 を強制（cp932 での decode エラーを回避）
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
# AWS CLI: ページャー無効化（エンコーディング問題を回避）
$env:AWS_PAGER = ""

# ローカル設定（PowerShell 5.1 / 7+ の両方に対応したマルチプラットフォーム用パス結合）
$TemplateDir = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($PSScriptRoot, "..", "cloudformation"))
$ProjectName = "smartwater-guardian"
$StackPrefix = "${ProjectName}-${Environment}"

# Phase 判定（All=00〜07 / Infra=00〜04 / App=06〜07）
# frontend イメージは NEXT_PUBLIC_API_BASE_URL（ALB DNS 名）をビルド時固定するため、
# 初回デプロイは「Infra（ALB まで）→ ALB DNS 名取得 → イメージビルド/ECR プッシュ → App」の順で行う。
$RunInfra = $Phase -in @("All", "Infra")
$RunApp   = $Phase -in @("All", "App")

Write-Host "Deploying SmartWater Guardian infrastructure..." -ForegroundColor Green
Write-Host "Environment: $Environment"
Write-Host "Region: $Region"
Write-Host "Phase: $Phase"
Write-Host "Template Directory: $TemplateDir"
Write-Host ""

# AWS CLI が利用可能か確認
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: AWS CLI not found. Please install it and configure credentials." -ForegroundColor Red
    exit 1
}

# AWS 認証確認
try {
    $identity = aws sts get-caller-identity --region $Region 2>$null | ConvertFrom-Json
    Write-Host "AWS Account: $($identity.Account)" -ForegroundColor Cyan
} catch {
    Write-Host "ERROR: AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE." -ForegroundColor Red
    exit 1
}

# =========================================================
# スタック デプロイ（依存順）
# =========================================================

function Deploy-Stack {
    param(
        [string]$StackName,
        [string]$TemplateFile,
        [hashtable]$Parameters
    )

    $FullStackName = "${StackPrefix}-${StackName}"
    Write-Host ""
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] Deploying: $FullStackName" -ForegroundColor Yellow

    # パラメータ文字列を構築（cloudformation deploy は Key=Value 形式を使用）
    $ParameterArgs = @()
    foreach ($key in $Parameters.Keys) {
        $ParameterArgs += "$key=$($Parameters[$key])"
    }

    # スタックデプロイ（既存なら更新、なければ作成）
    $params = @(
        "cloudformation", "deploy",
        "--template-file", $TemplateFile,
        "--stack-name", $FullStackName,
        "--region", $Region,
        "--no-fail-on-empty-changeset",
        "--capabilities", "CAPABILITY_NAMED_IAM"
    )

    if ($ParameterArgs.Count -gt 0) {
        $params += "--parameter-overrides"
        $params += $ParameterArgs
    }

    # AWS CLI 実行
    & aws @params

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Stack deployment failed: $FullStackName" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Deployed: $FullStackName" -ForegroundColor Green
}

# 00: GitHub OIDC
if ($RunInfra) {
    Deploy-Stack -StackName "github-oidc" -TemplateFile "$TemplateDir/00-github-oidc.yaml" -Parameters @{
        GitHubOrg = $GitHubOrg
        GitHubRepo = $GitHubRepo
    }

    # 01: Network
    Deploy-Stack -StackName "network" -TemplateFile "$TemplateDir/01-network.yaml" -Parameters @{
        VpcCidr = $VpcCidr
        NatGatewayCount = $NatGatewayCount.ToString()
    }

    # 02: Security
    Deploy-Stack -StackName "security" -TemplateFile "$TemplateDir/02-security.yaml" -Parameters @{
        NetworkStackName = "${StackPrefix}-network"
    }

    # 03: ECR
    Deploy-Stack -StackName "ecr" -TemplateFile "$TemplateDir/03-ecr.yaml" -Parameters @{}

    # 04: ALB（frontend ビルドに必要な ALB DNS 名はこのスタックで生成される）
    Deploy-Stack -StackName "alb" -TemplateFile "$TemplateDir/04-alb.yaml" -Parameters @{
        NetworkStackName = "${StackPrefix}-network"
        SecurityStackName = "${StackPrefix}-security"
    }

    # 05: WAF（コスト削減のため削除。デモ向け最小構成では不要）
}

if ($RunApp) {
    # 06: ECS
    Deploy-Stack -StackName "ecs" -TemplateFile "$TemplateDir/06-ecs.yaml" -Parameters @{
        NetworkStackName = "${StackPrefix}-network"
        SecurityStackName = "${StackPrefix}-security"
        EcrStackName = "${StackPrefix}-ecr"
        AlbStackName = "${StackPrefix}-alb"
        BackendImageTag = $BackendImageTag
        FrontendImageTag = $FrontendImageTag
        OrcaRouterBaseUrl = $OrcaRouterBaseUrl
        OrcaRouterModel = $OrcaRouterModel
        OrcaRouterEnabled = $OrcaRouterEnabled
        OrcaRouterApiKey = $OrcaRouterApiKey
        AllowedOrigins = $AllowedOrigins
    }

    # 07: Monitoring
    Deploy-Stack -StackName "monitoring" -TemplateFile "$TemplateDir/07-monitoring.yaml" -Parameters @{
        EcsStackName = "${StackPrefix}-ecs"
        AlbStackName = "${StackPrefix}-alb"
    }
}

if ($RunInfra -and -not $RunApp) {
    Write-Host ""
    Write-Host "✓ インフラスタック（00〜04、ALB まで）のデプロイが完了しました。" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. ALB DNS 名を取得し、frontend イメージの NEXT_PUBLIC_API_BASE_URL に指定してください:"
    Write-Host "   aws elbv2 describe-load-balancers --names smartwater-guardian-alb --query 'LoadBalancers[0].DNSName' --output text --region $Region"
    Write-Host "2. イメージをビルド・ECR へプッシュ後、-Phase App で ECS・監視スタックをデプロイしてください:"
    Write-Host "   .\deploy.ps1 -Phase App -Environment $Environment -Region $Region -BackendImageTag latest -FrontendImageTag latest"
} elseif (-not $RunInfra -and $RunApp) {
    Write-Host ""
    Write-Host "✓ アプリスタック（06〜07、ECS・監視）のデプロイが完了しました。" -ForegroundColor Green
    Write-Host "Verify ALB: aws elbv2 describe-load-balancers --names smartwater-guardian-alb --region $Region"
    Write-Host "Monitor ECS: aws ecs describe-services --cluster smartwater-guardian-$Environment --services smartwater-guardian-backend smartwater-guardian-frontend --region $Region"
} else {
    Write-Host ""
    Write-Host "✓ All stacks deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Orcarouter API key: ECS スタック（ecs）の OrcaRouterApiKey パラメータに注入（secretsmanager はコスト削減のため不使用）"
    Write-Host "2. Verify ALB: aws elbv2 describe-load-balancers --region $Region"
    Write-Host "3. Monitor ECS: aws ecs describe-services --cluster smartwater-guardian-$Environment --services smartwater-guardian-backend smartwater-guardian-frontend --region $Region"
}