# Units Generation — 分解方針の質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の Unit 分解方針を確定する。
> 上流成果物（`stories.md`「全ストーリーが単一 proto-Unit（BU-1）で完結」・`requirements.md` C-1〜C-5・
> `application-design` 5 成果物）で確定済みの事項は質問を省略し、**実決定が必要な事項のみ提示**する
> （approval-handoff:c2 / requirements-analysis:c1 / user-stories:c2 学習と整合）。
> 実装順序の優先度（value-first / risk-first / walking-skeleton-first）は Delivery Planning（2.8）の決定事項のため本ステージでは問わない。

## Q1: ユニット境界戦略（粒度の可否も併せて決定）

FE-7 はフロントエンド限定 13 ファイルの相互依存する変更（型 → APIクライアント → 表示 → ポーリング → 設定）で、
`stories.md` は「全ストーリーが単一 proto-Unit（BU-1）に含まれ、分割せず 1 イテレーションで完結する」と規定している。
ユニット境界をどう定義するか？

- A. 単一 proto-Unit（BU-1）として定義する（推奨）— 相互依存する複数ファイルの変更を分割せず 1 ユニットとして扱う
  （scope-definition:c1 学習と整合。kind は `ui`。依存 DAG は単一ノード + `depends_on: []`）
- B. レイヤー分割（契約層・表示層・設定層の 3 ユニット）— 型/APIクライアント/単一ソース化（US-1/US-4）・表示（US-2）・
  ポーリング/設定（US-3/NFR-1）に分ける
- C. ストーリー単位分割（US-1+US-4 / US-2 / US-3 の 3 ユニット）
- X. Other (please specify)

[Answer]: A

## Q2: ユニット間の依存関係・並行開発の扱い

単一ユニットの場合は依存 DAG が自明（依存なし）になる。分割する場合はユニット間の依存エッジと並行開発の可否をどう扱うか？
（分割しない場合、本問は「単一ユニット内の実装順序の根拠」として解釈する）

- A. 単一ユニットとして依存なし（`depends_on: []`）とし、内部の実装順序は scope-definition:c2 学習
  （型 → APIクライアント → 表示）に従う（推奨）
- B. 分割する場合のみ依存 DAG を定義（契約層 → 表示層 → 設定層）
- C. 独立した設定変更（vitest.config.mts / package.json / ci.yml）を別ユニットにして並行開発を許容
- X. Other (please specify)

[Answer]: A

## Q3: デプロイメントモデル

FE-7 はフロントエンド（Next.js）のみの変更で、バックエンド（BE-8）は変更対象外（C-1）。デプロイメントモデルをどう定義するか？

- A. 単一 Next.js アプリへの組み込み（monolithic deploy）として定義する（推奨）— 新規デプロイ対象・独立デプロイ単位は作らない
- B. フロントエンドを独立デプロイ可能な単位として明示する
- C. ハイブリッド（フロント・バックエンドの連携をデプロイ境界とする）
- X. Other (please specify)

[Answer]: A

---

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- Q1: FE-7 は **単一 proto-Unit（BU-1・kind: ui）** として定義する。相互依存する 13 ファイルの変更を分割せず
  1 ユニットで扱う（scope-definition:c1 学習と整合。依存 DAG は単一ノード + `depends_on: []`）。
- Q2: ユニット間の依存は**なし（`depends_on: []`）**。ユニット内部の実装順序は scope-definition:c2 学習
  （型 → APIクライアント → 表示）に従う。並行開発ユニットは作らない。
- Q3: デプロイメントモデルは **単一 Next.js アプリへの組み込み（monolithic deploy）** として定義する。
  新規デプロイ対象・独立デプロイ単位は作らない（C-1: バックエンド BE-8 は変更対象外）。

上記の内容で Unit 分解成果物（unit-of-work.md / unit-of-work-dependency.md / unit-of-work-story-map.md）を確定してよいか？

- Looks correct
- Request changes

[Answer]: Looks correct
