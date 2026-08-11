# User Stories — ステージ評価

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の User Stories ステージ実施要否の判定。
> 判定基準は stage-protocol / user-stories.md Step 2 に基づく。

## Decision: **Execute**

## Rationale

FE-7 はユーザー向けダッシュボードの表示変更であり、以下の条件に該当するため User Stories を実施する。

- **ユーザー向け機能**: KPI カードの表示構成変更（本日の検知数→レベル1、試算値注記、スケルトン切替）は
  水道事業者の監視画面に直接影響する（user-facing）。
- **ペルソナ**: 一次顧客「水道事業者オペレータ（監視担当）」と、最終確認者「デモ評価者」という
  複数ペルソナが関与する。
- **受入条件の検証可能性**: 「試算値注記の常時表示」「スケルトン表示」等は Given/When/Then 形式の
  受入条件で明確に検証できる。
- **複雑なビジネスロジックは無い**が、表示仕様の明確化（カード順・注記配置・失敗時挙動）に
  ストーリーが価値を発揮する。

## Factors Considered

| 因子 | 評価 | 影響 |
|---|---|---|
| プロジェクト種別 | Brownfield / feature | 実施（ユーザー向け変更） |
| ユーザー向けスコープ | ダッシュボード KPI 表示 | 実施 |
| 複雑性シグナル | 低（フロント6ファイル・依存先順） | ストーリーは小規模で十分 |
| ペルソナ数 | 2（オペレータ + 評価者） | 実施 |
| 表示仕様の未確定 | カード順・注記配置・失敗時挙動 | ストーリーで確定 |

## Key Areas Where Stories Add Value

1. KPI カード構成の変更（本日の検知数 → レベル1）がユーザーに伝える価値の明確化
2. 「試算値」注記の透明性（根拠のない金額を断定的に見せない）のストーリー化
3. バックエンド停止時のスケルトン表示（白画面回避）の受入条件の明確化
4. `SeverityLevel` 二重定義解消の内部品質ストーリー（開発者視点の価値: 型の単一ソース）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-1〜8 / NFR / Constraints）
- [business-overview] `aidlc/spaces/default/codekb/smartwater-guardian/business-overview.md`（ドメイン・ペルソナ・KPI 概要）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（対象コンポーネント実態）
- [team-practices] `inception/practices-discovery/team-practices.md`（TDD・テストポスチャ・品質ゲート）
