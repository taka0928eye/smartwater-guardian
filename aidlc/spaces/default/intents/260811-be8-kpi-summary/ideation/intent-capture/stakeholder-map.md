# Stakeholder Map — BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI

## Key Stakeholders and Their Interests

| Stakeholder | Interest | Source |
|-------------|----------|--------|
| ダッシュボード表示層（フロント `page.tsx` / `KpiSummary`） | 算出済みの推定削減コストと実データ由来の内訳カウントを受け取って表示する | [Q1] [Q3] |
| デモ参加者（8/15 デモ） | 算定根拠のあるKPIを確認する（デモ完了が最優先） | [Q4] |

## Decision-Makers vs. Influencers

| Role | Type | Interest / Authority | Source |
|------|------|----------------------|--------|
| 本ワークフローの実装担当（ユーザー） | Decision-maker | スコープ境界（対象バックエンド5ファイル・フロント変更なし）を Q1 で確認・確定した | [Q1] |

## Communication Requirements

| Requirement | Source |
|-------------|--------|
| Unknown (open question) — 報告頻度・報告対象・連絡体制は未確認（前提として受け入れ、Assumptions & Open Questions に記載） | 前提（§ Assumptions & Open Questions 参照） |

## Assumptions & Open Questions

- コミュニケーション要件（報告頻度・報告対象・連絡体制）は確認されていない。 [assumption]
