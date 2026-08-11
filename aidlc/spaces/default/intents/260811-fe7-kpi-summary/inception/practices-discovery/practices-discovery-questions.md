# Practices Discovery — インタビュー質問

> Step 4（Interview）の質問記録。Brownfield のため、リードドラフトと 3 盲検レビューが
> 確定できなかった事項のみを人間に確認する。回答は `## 回答` に記録する。

## Way of Working

1. **ブランチ戦略の使い分け基準** — 現状は main への直接コミットが主軸で、大規模・他者レビューが必要な変更のみ短命フィーチャーブランチ + PR でマージしている。この使い分けを明文化するか？

- A. main 直コミット中心を明文化（短命ブランチ + PR は大規模変更・共同作業時のみ） — 実態と一致
- B. 全変更をフィーチャーブランチ + PR に統一 — レビューゲートを強制
- C. 現状のまま明文化しない — 習慣に委ねる
- X. Other (please specify)

回答: A

## Walking Skeleton

2. **Walking Skeleton の扱い** — 本スコープ（feature / Brownfield、アプリは end-to-end 動作済み）ではスケルトン・セレモニーを実施しない、という記述でよいか？

- A. 実施しない（既存の動くアプリに薄い縦スライス検証は不要） — ドラフトのまま
- B. 軽量な確認（1 本の縦スライス検証）を実施
- C. 未確定のまま明文化しない
- X. Other (please specify)

回答: A

## Testing Posture

3. **カバレッジゲートの固定** — CI のみに存在する 80% ゲートを、ローカル実行でも再現可能にする（vitest.config.mts の coverage.thresholds 設定・pytest-cov の requirements-dev.txt ピン・backend/.coverage の .gitignore 追加）ことを承認するか？

- A. 承認（ローカルと CI を一致させる） — ゲートの再現性が向上
- B. 80% 閾値の固定のみ承認（CI は現状のまま）
- C. 変更しない（スコープ外）
- X. Other (please specify)

回答: A

4. **バックエンドの branch カバレッジ** — 現状 backend は行カバレッジのみ（frontend は 4 指標）。backend にも branch カバレッジを要求するか？

- A. 要求しない（現状の行のみ維持） — Minimal 戦略に整合
- B. 要求する（branch も 80%） — 分岐の多い KPI 集計に有効
- C. 未確定のまま
- X. Other (please specify)

回答: B

5. **E2E テストの扱い** — デモまで E2E 層（Playwright / Cypress）を導入しない方針でよいか？（TestClient エンドポイントテスト + component テストを統合境界の上限とする）

- A. 導入しない（現状のまま） — デモスコープに整合
- B. E2E を導入する
- C. 未確定のまま
- X. Other (please specify)

回答: A

6. **Python リント導入意向** — 現状 BE は ruff / mypy 未導入（Pydantic ランタイムテストで型安全性を代替）。導入するか？

- A. 導入しない（現状維持） — デモスコープで追加負荷なし
- B. ruff のみ導入（CI ゲート追加）
- C. ruff + mypy 導入
- D. 導入は別 Issue / スコープ外として記録のみ
- X. Other (please specify)

回答: C

## Deployment

7. **デモ受け渡し方法** — デモ成果物（8/10〜8/15）の受け渡しはどうするか？

- A. ローカル実行のまま（uvicorn / npm run dev でデモ） — 現状と一致
- B. 何らかのホスティング（Vercel 等）を検討
- C. 未確定のまま明文化しない
- X. Other (please specify)

回答: X ひとまずローカル実行のまま、余裕があればAWSにデプロイ

## Code Style

8. **エラーハンドリング / レイヤー境界の規約化** — 実コードに存在する一貫パターン（BE: ハンドラは 500 にせず状態コード整理・例外を明確に上げる / FE: `lib/api.ts` で ApiError 変換・取得失敗時は最終状態を据え置き）を Code Style に明文化するか？

- A. 明文化する（チーム規約として確定） — developer 提案を統合
- B. 明文化しない（暗黙規約のまま）
- C. 未確定のまま
- X. Other (please specify)

回答: A

9. **`SeverityLevel` 単一ソースの表記** — これは現行規約ではなく FE-7 で実施する確定方針なので、「FE-7 で `lib/severity.ts` に集約し `types/api.ts` から re-export」と明記してよいか？

- A. 「FE-7 で実施予定」と明記 — 現状の二重定義と区別
- B. 現行規約としての表記を維持
- C. 未確定のまま
- X. Other (please specify)

回答: A

10. **フォールバック規則の限定** — 「バックエンド停止時のフォールバック」はスケルトン / 実マスタ由来データに限定し、固定 KPI 数値モック（MOCK_KPI_DATA）を実データの代わりに表示する用途には使わない、と明記してよいか？

- A. 限定を明記（スケルトン / 実マスタ由来のみ） — モック非残置と整合
- B. 限定しない（現状の文言）
- C. 未確定のまま
- X. Other (please specify)

回答: A

## セキュリティ統制（Code Style / Deployment 横断）

11. **依存脆弱性スキャン** — デモスコープで依存脆弱性スキャン（Dependabot または npm audit / pip-audit）を導入するか？

- A. Dependabot のみ有効化（GitHub ネイティブ・ゼロコスト） — 最小導入
- B. Dependabot + CI に npm audit / pip-audit ゲート追加
- C. 導入しない（スコープ外・既知負債として記録のみ）
- X. Other (please specify)

回答: A

12. **シークレット検知** — シークレット検知（gitleaks 等 / GitHub secret scanning）を導入するか？

- A. 導入しない（現状の .gitignore 依存を維持） — デモスコープで十分
- B. GitHub secret scanning 有効化（手間ゼロ）
- C. CI に gitleaks 追加
- X. Other (please specify)

回答: B

## Consolidated Summary Confirmation

**統合サマリ**: Step 4 インタビューで 5領域12問に回答済み。Step 5 リード統合で 3 contribution と回答を反映し、4 宣言成果物（team-practices.md / discovered-rules.md / evidence.md / practices-discovery-timestamp.md）を最終化した。主な確定事項は、ブランチ戦略（main直コミット中心）・カバレッジ80%固定（ローカル/CI一致・backend branch80%）・ruff+mypy 導入・E2E非導入・デモはローカル実行のまま（余裕時AWS）・エラーハンドリング/レイヤー境界の規約化・`SeverityLevel` 単一ソースは FE-7 実施予定・フォールバック限定・Dependabot 有効化・GitHub secret scanning 有効化。

この内容で成果物を生成・承認ゲートへ進んでよいか？

- Looks correct
- Request changes

[Answer]: Looks correct
