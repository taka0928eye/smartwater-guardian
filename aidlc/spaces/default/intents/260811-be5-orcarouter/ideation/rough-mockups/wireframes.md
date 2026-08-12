# Wireframes (非UI: システムコンテキスト図) — BE-5: services/orcarouter.py によるLLM自動起票の実装

## 目的と方法

本ラフモックは、前段イニシアティブ・ステートメント（`ideation/intent-capture/intent-statement.md`）・スコープ定義書（`ideation/scope-definition/scope-document.md`）・インテント・バックログ（`ideation/scope-definition/intent-backlog.md`）を入力とし、BE-5（Issue #13）の**非UI（API バックエンドのみ）**イニシアティブとして、ステージ本文 Step 5 の非UIパスに従いシステムコンテキスト図を作成します。フロントエンド変更はスコープ外（`scope-document.md` アウトオブスコープ）のため、UI ワイヤーフレーム・画面レベルのアクセシビリティ注記は生成しません。 [intent] [scope-doc] [backlog]

## システムコンテキスト図（System Context Diagram）

```mermaid
flowchart LR
  subgraph Operator[運用スタッフ / デモ評価者]
    REQ[POST /api/v1/alerts/{telemetry_id}/work-order]
  end
  subgraph App[SmartWater Guardian バックエンド]
    ALERTS[routers/alerts.py<br/>501 スタブ → orcarouter.py 呼び出しへ差替]
    ORC[services/orcarouter.py<br/>LLM 自動起票サービス]
    LLMC[services/llm_cost.py<br/>FR-6 原価記録 OR-4]
    PROMPTS[services/prompts.py<br/>プロンプト編成 OR-2]
    WO[schemas/work_order.py<br/>WorkOrder 型 OR-2]
    CACHE[(インメモリキャッシュ<br/>同一 telemetry_id は再呼び出しなし)]
    PARTS[(data/repair_parts.json<br/>フォールバック部材マスタ)]
  end
  subgraph External[外部]
    ORCAPI[Orcarouter API<br/>LLM]
  end
  REQ --> ALERTS
  ALERTS --> ORC
  ORC --> PROMPTS
  ORC --> CACHE
  ORC -->|成功| ORCAPI
  ORC -->|4xx/パース失敗・5xx/ネットワーク 1回リトライ後| PARTS
  ORC --> LLMC
  ORC --> WO
```

（テキスト代替）運用スタッフ/デモ評価者が `POST /api/v1/alerts/{telemetry_id}/work-order` を呼ぶと、`routers/alerts.py`（501 スタブから差替）が `services/orcarouter.py` を呼ぶ。orcarouter.py は `prompts.py`（OR-2）でプロンプトを編成し、キャッシュ未達なら Orcarouter API（LLM）へ呼び出し、成功時は `WorkOrder(source="llm")`、4xx/パース失敗・5xx/ネットワークの1回リトライ後は `repair_parts.json` 由来のフォールバック応答（`source="fallback"`）を生成する。`llm_cost.py`（OR-4）で FR-6 原価を記録し、`schemas/work_order.py`（OR-2）の `WorkOrder` 型で返却する。 [scope-doc] [backlog] [intent]

## 境界と外部契約（Boundaries）

- 外部相互作用は **Orcarouter API への LLM 呼び出し 1 本のみ**であり、認証・権限管理・物理 IoT 通信・リアルタイム通知は Strict Out of Scope（`scope-document.md` アウトオブスコープ）。 [scope-doc]
- Orcarouter API のレスポンス契約（`model` / `usage` / `latency_ms`）は `docs/llm-cost.md` §2（D-2）に規定済み。 [scope-doc]
- フォールバック部材マスタ `repair_parts.json`（D-6）は BE-5 で新規作成し、`@lru_cache(maxsize=1)` で読み込む。 [scope-doc]

## Assumptions & Open Questions

- 非UIイニシアティブのため、UI ワイヤーフレーム・情報階層・ブランドガイドライン・デバイス/フォームファクタ・アクセシビリティ要件は対象外とする。 [assumption]
- その他の未確定項目はなし（None.）

## Sources

- [intent] `ideation/intent-capture/intent-statement.md`（問題定義・成功指標・対象ファイル）
- [scope-doc] `ideation/scope-definition/scope-document.md`（イン/アウト境界・依存関係 D-1〜D-7・実装順序）
- [backlog] `ideation/scope-definition/intent-backlog.md`（単一 proto-Unit PU-1・価値連鎖図・受入条件11件）
