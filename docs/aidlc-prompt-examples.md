# AI-DLC (AI-Driven Lifecycle) プロンプト集

本ドキュメントは、SmartWater Guardian の開発において各担当者（フロントエンド、バックエンド、AI/データ処理）がAIツール（ChatGPT / Claude / GitHub Copilot 等）を活用するための標準プロンプト定義です。

---

## 1. バックエンド（Spring Boot / API）開発用プロンプト

### 1.1 センサーデータ受信API＆モック生成
```text
Spring Boot (Java 17) を使用して、IoT音響センサーからのデータを受信するREST APIコントローラーを作成してください。
エンドポイント: POST /api/v1/sensor-data
リクエストボディ (JSON):
{
  "sensorId": "SN-001",
  "latitude": 35.681236,
  "longitude": 139.767125,
  "timestamp": "2026-08-10T03:00:00Z",
  "audioBase64": "..." 
}
レスポンス (JSON):
{
  "status": "success",
  "leakDetected": true,
  "confidence": 0.88,
  "severityLevel": 1,
  "recommendedPart": "鋳鉄管150mm用 補修クランプA型"
}
Swagger注記と、処理の骨組みを含めてください。
