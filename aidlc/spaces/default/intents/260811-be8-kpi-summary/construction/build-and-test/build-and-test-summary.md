# Build and Test Summary — SmartWater Guardian（BE-8 KPI サマリ）

> ステージ: build-and-test（Construction）| テスト戦略: **Minimal** | 対象ユニット: `be8-kpi-summary`
> インプット: コード生成プラン / コードサマリ（`construction/be8-kpi-summary/code-generation/`）

## 生成した指示書・成果物

| ファイル | 種別 | 内容 |
|----------|------|------|
| `build-instructions.md` | ビルド指示 | 依存導入確認 / import スモーク / 起動確認 / テスト実行 / トラブルシュート |
| `unit-test-instructions.md` | テスト指示（Minimal） | 受け入れ条件（S-1〜S-6, D-1〜D-3）を要求駆動で検証するユニットテスト仕様 |
| `build-test-results.md` | 実行結果 | 実測ビルド/テスト/カバレッジの結果レポート |
| 本ファイル | サマリ | ビルド状態・テスト種別棚卸・対応可否 |

> **Minimal 戦略のため、統合・性能・セキュリティのテスト指示書は生成しない。**
> 統合境界は TestClient のエンドポイントテスト（`test_kpi.py` `TestKpiSummaryEndpoint`）が実質カバーする
> （プロジェクト学習済みルール c1 / c4）。NFR 要件（性能・セキュリティ）は本スコープでスキップ済みのため
> 該当する性能/セキュリティテストも不要。

## ビルド状態

| 項目 | 結果 |
|------|------|
| 依存パッケージ | ✅ 導入済み（`requirements.txt` / venv） |
| import スモーク | ✅ 成功（`OK: 9 routes` — `kpi` ルーター登録確認） |
| ビルド | ✅ 成立（Python はコンパイル工程なし） |

## テスト種別棚卸

| テスト種別 | 生成 | 実行 | 件数 | 備考 |
|-----------|:----:|:----:|-----:|------|
| ユニット（`test_kpi.py`） | ✅ | ✅ | 14 | 単価計算4 / サマリ集計3 / エンドポイント3 / スキーマ型4 |
| プロジェクト全体 | ✅ | ✅ | 123 | 全 Green |
| 統合 | —（Minimal スキップ） | — | — | TestClient エンドポイントテストで代替 |
| 性能 | —（Minimal スキップ） | — | — | NFR 要件なし |
| セキュリティ | —（Minimal スキップ） | — | — | 認証等は実装禁止（スコープ外） |

## カバレッジ期待値 / 実績

| 単位 | 期待（基準） | 実績 |
|------|-------------|------|
| プロジェクト全体 | 80% 以上 | **99%**（431/1） |

## レディネス評価

| 観点 | 評価 | 根拠 |
|------|------|------|
| build-ready | ✅ | import スモーク成功、依存整合 |
| test-ready | ✅ | 123 passed / カバレッジ99%（基準80%超） |
| deployment-ready | ✅（バックエンド単体） | ルーター登録・エンドポイント検証済み。フロント連携は FE-7 で別途 |

## 既知の制限・保留事項

- `app/services/kpi.py` L52 の `raise ValueError` はデッドコード（コード生成レビュー Minor #1）。
  修正の要否は承認ゲートで判断する。品質基準は満たしている。
- フロントエンド（`MOCK_KPI_DATA` の実API置換）は本スコープ外（FE-7 等で対応）。
- `StarletteDeprecationWarning`（httpx テストクライアント）は既存・無害のため放置。
