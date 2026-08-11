# Phase Check — Ideation → Inception（phase-check-ideation）

**Intent**: `260811-be8-kpi-summary`
**スコープ**: `be8-kpi-summary`（mvp相当・単一イテレーション）
**検証日時**: 2026-08-11
**結果**: ✅ PASS（スコープ外ステージは設計により省略のため対象外として判定）

## 1. Intent → Scope → Intent Backlog の整合

| チェック | 結果 | 備考 |
|----------|------|------|
| インテントステートメントの製品境界と選択スコープ（`be8-kpi-summary`）が整合 | ✅ | intent-statement.md の Initial Scope Signal が `be8-kpi-summary` に一致 |
| スコープ文書（scope-document）とインテント・バックログ（intent-backlog）の整合 | ⏭️ 対象外 | 最小スコープでは本ステージは編成されず、成果物自体が存在しない（プロジェクト学習済みルール: 「最小スコープで scope-document / intent-backlog が存在しなくても、イニシアティブ・ブリーフは既存成果物とリポジトリ実態で整合を担保できる」） |
| スコープ内の全項目がリポジトリ実態と整合 | ✅ | バックエンド5ファイル・`hydrants.json`（10件）・インメモリストア・`SeverityLevel` を確認 |

## 2. 全スコープ項目のフィージビリティ裏付け

| スコープ項目 | フィージビリティ根拠 | 結果 |
|--------------|----------------------|------|
| `app/services/kpi.py`（算定ロジック） | `docs/business-model.md` §3 の算定式が根拠。仮説定数ベースである旨を `is_estimate`・`assumption_doc` で明示 | ✅ |
| `app/schemas/kpi.py`（レスポンススキーマ） | Pydantic v2 で定義。`SeverityLevel`（Literal[0,1,2,3]）を再利用 | ✅ |
| `app/routers/kpi.py`（サマリAPI） | 既存ルーター（alerts等）の登録パターンを踏襲。空ストアでも200で返す | ✅ |
| `tests/test_kpi.py`（テスト） | 既存 `tests/test_alerts.py` の TestClient パターンを踏襲し、統合境界をカバー | ✅ |
| `main.py` へのルーター登録 | 既存ルーター登録パターンを踏襲 | ✅ |

## 3. リスク・未解決事項の引き継ぎ

| 事項 | 対応 |
|------|------|
| BE-3 未実装（FFT解析による実漏水検知なし） | Inception・Construction では `scripts/simulate_sensor.py` 投入分を実データ源として扱う（approval-handoff Q2 で対策合意済み） |
| フロント連携時の型不一致（snake_case vs camelCase・`today_detections`） | 後続ストーリー（FE-7 等）で対応。今回のフロント変更はスコープ外（intent-statement.md・approval-handoff Q1 で確定） |
| コミュニケーション要件（報告頻度等）が未確認 | 前提として受け入れ、intent-capture の Assumptions & Open Questions に記載済み |

## 4. 結論

イデエーション段階の成果物（intent-statement.md・stakeholder-map.md）とリポジトリ実態は整合しており、Inception（Requirements Analysis）へ進む準備が整っている。スコープ外ステージの成果物（scope-document・intent-backlog・competitive-analysis・feasibility-assessment・constraint-register・team-assessment・wireframes）は設計により省略されており、欠落ではない。

**Next**: Inception フェーズ（Requirements Analysis）
