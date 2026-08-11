# Stakeholder Map — BE-4 配管台帳照合サービス

## Key Stakeholders and Their Interests

| Stakeholder | Interest | Source |
|-------------|----------|--------|
| BE-5（補修部材選定・見積自動起票） | 配管の材質・口径・布設年を渡して部材選定の入力を揃える | [Q2] |
| 監視UIの利用者 | アラート詳細画面で対象管路の材質・口径・布設年・経過年数を確認する | [Q2] |

## Decision-Makers vs. Influencers

| Role | Type | Interest / Authority | Source |
|------|------|----------------------|--------|
| BE-4 / BE-5 / BE-6 実装担当 | Decision-maker | 対象ファイル・受け入れ条件は GitHub Issue に確定記載済み。配線タイミング（BE-4 タスク内で alerts API を接続）を決定した | [desc] [Q4] |

## Communication Requirements

| Requirement | Source |
|-------------|--------|
| 受け入れ条件の通過を `python scripts/check_ledger.py` で検証できること（自動検証スクリプトの提供） | [desc] |

## Assumptions & Open Questions

None.
