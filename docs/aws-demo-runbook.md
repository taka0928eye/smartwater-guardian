# AWS デモ実行ガイド

> **前提**: AWS 上にデモアプリケーション（ECS / ALB）が既にデプロイされていること
> **想定実行環境**: Windows PowerShell 5.1+ / AWS CLI v2 / 有効な AWS 認証
> **対象リージョン**: ap-northeast-1（東京リージョン）

---

## 1. 目的

AWS 上（ECS / ALB）で稼働するデモアプリケーションに対し、
デモ検証・シード投入・当日実演を行う。

- **ローカル実行を主とし、AWS はフェイルオーバー・予備用**
- **8/15 デモ当日の朝に環境確認・シード投入を実施**
- **同一シード（`--seed 42`）で同一の視覚的結果を確認**

---

## 2. 前提条件

- [ ] AWS アカウントにアクセス可能、東京リージョン（ap-northeast-1）で確認できる
- [ ] `aws configure` または `AWS_PROFILE` 環境変数で認証済み
- [ ] PowerShell 5.1+（`Get-Command aws` で AWS CLI が見つかる）
- [ ] ローカルで `scripts/seed_demo.py` / `scripts/clear_demo.py` が実行可能（venv 構成済み）

---

## 3. 初期環境確認

AWS デモ環境が稼働しているか確認します。

```powershell
# 1. ALB DNS 名を取得
$ALB_DNS = aws elbv2 describe-load-balancers `
  --names smartwater-guardian-alb `
  --region ap-northeast-1 `
  --query 'LoadBalancers[0].DNSName' `
  --output text

Write-Host "ALB DNS: $ALB_DNS"
```

```powershell
# 2. AWS 上のタスクが running か確認
aws ecs describe-services `
  --cluster smartwater-guardian-demo `
  --services smartwater-guardian-backend smartwater-guardian-frontend `
  --region ap-northeast-1 `
  --query 'services[*].[serviceName,status,desiredCount,runningCount]' `
  --output table

# => desiredCount == runningCount を確認
```

```powershell
# 3. ALB ターゲットが healthy か確認
aws elbv2 describe-target-health `
  --target-group-arn "arn:aws:elasticloadbalancing:ap-northeast-1:ACCOUNT:targetgroup/smartwater-guardian-backend/*" `
  --region ap-northeast-1

# => HealthyCount > 0 を確認
```

---

## 4. デモシード投入・検証

### 4.1 ALB の動作確認

```powershell
# ブラウザで以下 URL を開く
Write-Host "Open in browser: http://$ALB_DNS"
```

**期待される画面**:
- 地図が表示される（マーカー無し・初期状態）
- コンソール に API エラーが無い（CORS 等）

### 4.2 シード投入

```powershell
# AWS 上のバックエンド にシード投入
cd backend

$BACKEND_URL = "http://$ALB_DNS:8000"

venv/Scripts/python.exe scripts/seed_demo.py `
  --seed 42 `
  --url "$BACKEND_URL/api/v1/demo/seed"

# 出力例:
# [OK] 13 件を http://ALB_DNS:8000/api/v1/demo/seed へ投入しました
```

### 4.3 デモ動作確認

ブラウザを更新してシード後の状態を確認：

1. **地図**: Level 1〜3 のマーカーが表示される（色分け: 黄緑・オレンジ・赤）
2. **アラート一覧**: Level 1 が上位に並ぶ
3. **KPI**: 「推定削減コスト」が **204.8万円** と表示される
4. **詳細ドロワー**: アラートをクリック → スペクトルグラフが表示される
5. **起票モーダル**: 「AI自動起票」ボタン → フォールバック応答（`source: fallback`）が表示される

---

## 5. 当日デモ当番の流れ

### 朝のチェック（8:00〜8:30）

```powershell
# 1. ALB DNS 名を再度確認
$ALB_DNS = aws elbv2 describe-load-balancers `
  --names smartwater-guardian-alb `
  --region ap-northeast-1 `
  --query 'LoadBalancers[0].DNSName' `
  --output text

# 2. AWS 上のタスクが running か確認
aws ecs describe-services `
  --cluster smartwater-guardian-demo `
  --services smartwater-guardian-backend smartwater-guardian-frontend `
  --region ap-northeast-1 `
  --query 'services[*].[serviceName,status,desiredCount,runningCount]' `
  --output table

# => desiredCount == runningCount を確認
```

```powershell
# 3. シード状態の復旧（必要に応じて）
cd backend
venv/Scripts/python.exe scripts/seed_demo.py --seed 42 --url "http://$ALB_DNS:8000/api/v1/demo/seed"
```

### デモ中のシード状態リセット

「正常状態 → Level 1 検知」を何度も実演したい場合、バックエンド再起動不要でストアをリセット：

```powershell
cd backend

$BACKEND_URL = "http://$ALB_DNS:8000"

# シード状態をクリア
venv/Scripts/python.exe scripts/clear_demo.py `
  --url "$BACKEND_URL/api/v1/demo/clear"

# 同じシード 42 で再度投入
venv/Scripts/python.exe scripts/seed_demo.py `
  --seed 42 `
  --url "$BACKEND_URL/api/v1/demo/seed"
```

### ローカル ↔ AWS の切り替え

```powershell
# AWS から ローカルに戻す場合（安定性重視）
# ブラウザ URL を localhost:3000 に変更
# ブラウザキャッシュをクリア（Ctrl+Shift+Delete）

npm run dev       # frontend
# 別ターミナル
cd backend
venv/Scripts/uvicorn.exe main:app --reload --port 8000
```

---

## 6. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| ALB が 503 Bad Gateway | タスクが起動していない | `aws ecs describe-services` で確認 → CloudWatch ログ確認 |
| frontend が読み込めない | イメージの `NEXT_PUBLIC_API_BASE_URL` が誤り | Step 2 で ALB DNS を正しく設定したか確認 |
| シード API が 404 | バックエンド容器がクラッシュ | CloudWatch Logs でエラーメッセージ確認 |
| CORS エラー が出る | ALB 背後の backend の CORS 設定が誤り | `deploy.ps1` の `-AllowedOrigins` に ALB DNS を指定 |
| スペクトルが表示されない | localStorage キャッシュが古い | ブラウザキャッシュクリア（Ctrl+Shift+Delete） |

### CloudWatch ログ確認

```powershell
# backend ログ
aws logs tail /ecs/smartwater-guardian-demo-backend --follow --region ap-northeast-1

# frontend ログ
aws logs tail /ecs/smartwater-guardian-demo-frontend --follow --region ap-northeast-1
```

---

## 7. 参考リンク

- `docs/demo-runbook.md` — ローカルデモ検証ガイド
- `backend/scripts/seed_demo.py` — シード投入スクリプト
- `backend/scripts/clear_demo.py` — シード状態リセットスクリプト
