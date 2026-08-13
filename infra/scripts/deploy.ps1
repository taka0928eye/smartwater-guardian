# INFRA-1: AWS CloudFormation デプロイオーケストレーション（PowerShell）
# ローカルまたは CI/CD パイプラインからスタックを依存順にデプロイする
#
# 使用方法:
#   .\deploy.ps1 -Environment prod -Region ap-northeast-1 -BackendImageTag latest
#
# パラメータ:
#   -Environment: デプロイ環境（dev/staging/prod、既定: dev）
#   -Region: AWS リージョン（既定: ap-northeast-1）
#   -BackendImageTag: backend ECR イメージタグ（既定: latest）
#   -FrontendImageTag: frontend ECR イメージタグ（既定: latest）

param(
    [string]$Environment = "dev",
    [string]$Region = "ap-northeast-1",
    [string]$BackendImageTag = "latest",
    [string]$FrontendImageTag = "latest",
    [string]$GitHubOrg = "taka0928eye",
    [string]$GitHubRepo = "smartwater-guardian",
    [string]$VpcCidr = "10.0.0.0/16",
    [int]$NatGatewayCount = 1,
    [string]$OrcaRouterBaseUrl = "",
    [string]$OrcaRouterModel = "gpt-4",
    [string]$OrcaRouterEnabled = "false",
    [string]$AllowedOrigins = "http://localhost:3000"
)

$ErrorActionPreference = "Stop"

# ローカル設定
$TemplateDir = Join-Path $PSScriptRoot ".." "cloudformation"
$ProjectName = "smartwater-guardian"
$StackPrefix = "${ProjectName}-${Environment}"

Write-Host "Deploying SmartWater Guardian infrastructure..." -ForegroundColor Green
Write-Host "Environment: $Environment"
Write-Host "Region: $Region"
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

    # パラメータ文字列を構築
    $ParameterArgs = @()
    foreach ($key in $Parameters.Keys) {
        $ParameterArgs += "ParameterKey=$key,ParameterValue=$($Parameters[$key])"
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

    & aws @params

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Stack deployment failed: $FullStackName" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Deployed: $FullStackName" -ForegroundColor Green
}

# 00: GitHub OIDC
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

# 04: ALB
Deploy-Stack -StackName "alb" -TemplateFile "$TemplateDir/04-alb.yaml" -Parameters @{
    NetworkStackName = "${StackPrefix}-network"
    SecurityStackName = "${StackPrefix}-security"
}

# 05: WAF
Deploy-Stack -StackName "waf" -TemplateFile "$TemplateDir/05-waf.yaml" -Parameters @{
    AlbStackName = "${StackPrefix}-alb"
}

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
    AllowedOrigins = $AllowedOrigins
}

# 07: Monitoring
Deploy-Stack -StackName "monitoring" -TemplateFile "$TemplateDir/07-monitoring.yaml" -Parameters @{
    EcsStackName = "${StackPrefix}-ecs"
    AlbStackName = "${StackPrefix}-alb"
}

Write-Host ""
Write-Host "✓ All stacks deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Set Orcarouter API key: aws secretsmanager put-secret-value --secret-id smartwater-guardian-orcarouter-key --secret-string '<API_KEY>'"
Write-Host "2. Verify ALB: aws elbv2 describe-load-balancers --region $Region"
Write-Host "3. Monitor ECS: aws ecs describe-services --cluster smartwater-guardian-$Environment --services smartwater-guardian-backend smartwater-guardian-frontend --region $Region"
