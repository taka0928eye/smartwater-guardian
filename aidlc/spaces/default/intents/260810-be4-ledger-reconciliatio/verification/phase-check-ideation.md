# フェーズ境界検証: Ideation → Inception

## 検証対象

- BE-4 配管台帳照合サービス（イニシアティブ）
- スコープ: `be4-ledger-reconciliation`（Minimal / 7ステージ）

## 検証項目

### 1. Intent → Scope → Intent Backlog の整合

| 項目 | 状態 | 備考 |
|------|------|------|
| Intent Statement（問題定義・成功指標） | ✅ 存在 | `<record>/ideation/intent-capture/intent-statement.md` |
| Stakeholder Map | ✅ 存在 | `<record>/ideation/intent-capture/stakeholder-map.md` |
| Scope Document | ✅ スコープ外 | 本スコープは intent-capture → approval-handoff → code-generation の最小経路。scope-document はカスタムスコープで意図的に省略 |
| Intent Backlog | ✅ スコープ外 | 同上 |
| Initiative Brief | ✅ 存在 | `<record>/ideation/approval-handoff/initiative-brief.md` |
| Decision Log | ✅ 存在 | `<record>/ideation/approval-handoff/decision-log.md` |

### 2. スコープ項目の実現可能性裏付け

| スコープ項目 | 裏付け | 備考 |
|-------------|--------|------|
| `pipes.json` 10 路線 | ✅ 既存 `hydrants.json` が 10 消火栓・`pipe_id` 参照を保有 | 座標・属性は既存マスタと整合させる方針（D-4） |
| `pipe.py` PipeRecord | ✅ `alert.py` に `PipeInfo` が既存 | Pydantic v2 でスキーマ拡張 |
| `ledger.py` 照合ロジック | ✅ `store.py` の `@lru_cache` パターンが既存 | キャッシュ方針に準拠 |
| `check_ledger.py` | ✅ 受け入れ条件 7 項目で定義 | 検証スクリプトで自動確認 |
| alerts API 配線 | ✅ `alerts.py:72` の `pipe_info=None` が配線点 | スキーマ・配線点ともに既存 |

### 3. 受け入れ条件の実現可能性

- 全 10 消火栓の `find_pipe_by_hydrant()` 解決: `hydrants.json` の `pipe_id` 参照（P-001〜P-010）を直接用いるため整合は確実。
- 未知 ID → `None`: 仕様として明記済み。
- `find_nearest_pipe()`: Haversine 距離で実装可能。
- 欠損/破損時の例外: 明示的例外（FileNotFoundError / ValueError）で実装可能。
- キャッシュ: モジュールロード時の `lru_cache` で実装可能。

## 結論

**✅ 合格。** イデアーション期の成果物はコンストラクション（Code Generation → Build & Test）へ進む準備が整っている。スコープ境界（4ファイル + alerts 配線）はユーザー確認済みであり、実現可能性上のブロッカーはない。
