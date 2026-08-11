# Delivery Planning — Bolt 計画の質問

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」の Bolt 分解と実行順序を確定する。
> **ユーザー指示（2026-08-11）: 作業タスクはGitHubのISSUESを正とし、Unit Generationステージは実施しない**。
> したがってタスク分解は units-generation 成果物ではなく **GitHub Issue #19（FE-7）** を正とする。
> 上流成果物（`requirements.md` FR-1〜8 / `stories.md` US-1〜4 / `components.md`・`component-methods.md`・
> `services.md`・`component-dependency.md`・`decisions.md` / `team-practices.md`）で確定済みの事項は
> 質問を省略し、**実決定が必要な事項のみ提示**する（approval-handoff:c2 学習と整合）。
>
> **用語**: **Bolt** とは、Construction（実装フェーズ）で 1 つの作業塊を一通り作り上げて動作する状態に
> する 1 回のビルド工程（ステージ 3.1〜3.7 を 1 周すること）を指す。**モブ** とは、1 つの Bolt を担当する
> 作業チームのこと。

## Q1: Bolt 分解の単位（分割するか否か）

FE-7 は GitHub Issue #19 に定義された単一のフロントエンド作業（変更予定 6 ファイル、実態は
stories でスコープ確定済みの相互依存する 13 ファイル）で、バックエンド（BE-8）は実装済み・変更対象外。
Bolt 分解をどうするか？

- A. 単一 Bolt として扱う（推奨）— Issue 単位で 1 つの Bolt にまとめ、1 回の Construction
  （設計 → 実装 → テスト → CI 整備）で完結させる。相互依存する変更の分割利益が小さく
  （scope-definition:c1 学習と整合）、デモ 8/12 に向けた最短経路になる
- B. 内部工程で分割（型・API クライアント → 表示 → ポーリング/スケルトン → 設定の 4 Bolt）—
  各工程を別 Bolt にし、それぞれで動作確認する
- C. リスク領域（SeverityLevel 単一ソース化 + 循環依存解消）と表示領域（KPI 実データ + 試算値注記）の
  2 Bolt に分割
- X. Other (please specify)

[Answer]:

## Q2: 単一 Bolt 内の構築順序の根拠（ヒューリスティック）

単一 Bolt の場合でも、内部の作業順序には根拠が必要。FE-7 の作業をどの順で組み立てるか？

- A. 依存先順（型・単一ソース化 → API クライアント → 表示 → ポーリング/スケルトン → 設定）— TDD
  （Red → Green → Refactor）と整合し、scope-definition:c2 学習の既定
- B. リスク先行（SeverityLevel 単一ソース化と循環依存解消を最初に行い、表示はその後）— 型の二重定義
  （`1|2|3` vs `0|1|2|3`）という既知の不整合を最優先で解消する
- C. 価値先行（KPI 実データ表示と試算値注記を先に作り、リファクタリングは後）— デモ評価軸 3 の
  可視化を最優先で届ける
- X. Other (please specify)

[Answer]:

## Q3: 並行実行の扱い

複数 Bolt を同時進行させるか？ それとも 1 つずつ直列に進めるか？

- A. 直列（推奨）— 単一 Bolt のため並行対象なし。1 つの作業塊を順に完成させる
- B. 並行 — 分割した場合の各 Bolt を並行開発する（単一 Bolt の場合は選択肢なし）
- X. Other (please specify)

[Answer]:

## Q4: 外部依存の有無

FE-7 を進めるにあたり、外部（別チーム・API・データ・承認）で待たされるものはあるか？

- A. 外部依存なし（推奨）— BE-8 の `GET /api/v1/kpi/summary` は実装済みで即利用可能。
  依存タスク（BE-8 / FE-1 / FE-2）は完了済み
- B. 一部依存あり（詳細を Other で指定）
- X. Other (please specify)

[Answer]:

## Q5: 最大の懸念（最優先で取り組むべきリスク）

この作業で最も心配なことは何か？（Bolt 内の作業順序・テスト計画に反映する）

- A. カバレッジゲート恒久化（NFR-1）— フロントの lines/functions/branches/statements 各 80% を
  ローカルと CI で一致させる整備が未実施で、既存テストがゲートを満たせるか未検証
- B. 型の二重定義と循環依存 — `SeverityLevel` の不整合（`1|2|3` vs `0|1|2|3`）と
  `DashboardClient ↔ useKpiPolling` の循環依存が実装の早い段階で問題になりうる
- C. モック値の残置 — `MOCK_KPI_DATA`（`1_420_000` / `1240`）が実データで埋められるカードに
  残らないか（受け入れ条件の grep 検証で担保）
- X. Other (please specify)

[Answer]:

---

## Consolidated Summary Confirmation

**回答の統合サマリ**:

- （未回答 — このセクションは回答後に確定します）

上記の内容で Bolt 計画成果物（bolt-plan.md / team-allocation.md / risk-and-sequencing-rationale.md /
external-dependency-map.md）を生成してよいか？

- Looks correct
- Request changes

[Answer]:
