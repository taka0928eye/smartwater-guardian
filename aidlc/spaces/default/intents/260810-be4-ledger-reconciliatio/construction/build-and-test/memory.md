# Build and Test — Diary

> Stage-major (unit-independent) Build and Test for BE-4 配管台帳照合サービス.
> Scope: be4-ledger-reconciliation | Depth: Minimal | Test Strategy: Minimal
> Lead: aidlc-quality-agent (inline) | Support: aidlc-devsecops-agent

## Interpretations

- 2026-08-11T00:35:00Z — Minimal 戦略では統合・性能・セキュリティのテスト指示書をスキップする; produces リストは最大集合で、戦略により絞られる。ビルド&テストはレビューア宣言なし（フィンガープリントゲートなし）で、4 成果物（build-instructions / unit-test-instructions / build-and-test-summary / build-test-results）を生成する。

## Deviations

- 2026-08-11T00:35:00Z — バックエンド Python にコンパイル工程がないため、「ビルド」を依存導入の確認 + アプリ import スモークテスト + 検証スクリプト実行と定義した。フロントエンド（Next.js）は BE-4 変更対象外（pipe_info は従来から AlertDetail スキーマに null 許容で存在、形は不変）のため `npm run build` は対象外と明記した。
- 2026-08-11T00:35:00Z — CLAUDE.md の `venv/Scripts/pytest.exe` 表記は環境に合わない（pytest.exe は cwd を sys.path に挿入せず `app` を import できない）。`venv/Scripts/python.exe -m pytest` を正規コマンドとして指示書に記載した。

## Tradeoffs

- 2026-08-11T00:35:00Z — 統合テスト指示書を生成しない代替案も検討したが、Minimal 戦略の「Unit tests ONLY」規定に従い、alerts 配線の検証は既存の test_alerts.py ユニットテスト（FastAPI TestClient でのエンドポイント検証）が実質カバーするため、追加の統合テスト指示書は不要と判断。

## Open questions

- 2026-08-11T00:35:00Z — 本番で pipes.json 更新時にキャッシュ再読込手段（レビュー Minor #2）が必要になるかは、BE-5 の部材選定利用時に再評価する。
