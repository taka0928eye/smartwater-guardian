# Build and Test Summary — BE-4 配管台帳照合サービス（ledger.py）

| 項目 | 内容 |
|------|------|
| スコープ | be4-ledger-reconciliation（バックエンドのみ） |
| テスト戦略 | Minimal（Nyquist）— ユニットテストのみ |
| リード | aidlc-quality-agent（inline）／支援: aidlc-devsecops-agent |
| 上流成果物 | `construction/be4-ledger/code-generation/code-generation-plan.md`・`code-summary.md` |

## 1. ビルド状態と前提条件

- **状態: ✅ ビルド成功**（Python にコンパイル工程なし → import スモーク + 依存導入確認で検証）
- 前提条件: `backend/venv` に依存導入済み、`backend/app/data/pipes.json` 配置済み（cwd 非依存で解決）
- フロントエンドは変更対象外（`pipe_info` のスキーマ形状は不変）のため対象外

## 2. テスト種別インベントリ

| テスト種別 | 生成状況 | 理由 |
|-----------|----------|------|
| ユニットテスト | ✅ `unit-test-instructions.md` | Minimal 戦略の要求駆動テスト（A1〜A7 / D-4 / D-5） |
| 統合テスト | ⏭ スキップ | Minimal 戦略で対象外。alerts 配線は TestClient のエンドポイントテスト（test_alerts.py）が実質カバー |
| 性能テスト | ⏭ スキップ | NFR 要求が存在しない（nfr-requirements はスコープ外） |
| セキュリティテスト | ⏭ スキップ | NFR 要求なし。入力境界は Pydantic v2 スキーマ検証が担保（`any` 禁止） |
| E2E | ⏭ スキップ | Minimal 戦略で対象外 |

## 3. カバレッジ期待値（ユニット別）

| コンポーネント | 期待値（CLAUDE.md 基準 80%） | 実績 |
|----------------|------------------------------|------|
| `app/services/ledger.py` | 80% 以上 | **100%**（41/41） |
| `app/schemas/pipe.py` | 80% 以上 | **100%**（29/29） |
| `app/routers/alerts.py` | 80% 以上 | **100%**（28/28） |
| app 全体 | 80% 以上 | **100%**（372/372） |

## 4. レディネス評価

| 評価項目 | 状態 |
|----------|------|
| Build-ready | ✅ import スモーク・依存導入 OK |
| Test-ready | ✅ pytest 107 passed / カバレッジ 100% / check_ledger.py 7/7 PASS |
| Demo-ready（8/10〜8/15 デモ） | ✅ 受け入れ条件 A1〜A7・決定 D-4/D-5 すべて実装・検証済み。alerts 詳細 API が配管情報を返す（BE-6 配線完了） |

## 5. 既知の制限・未解決事項

- **`pytest.exe` 表記の不一致**: CLAUDE.md §4 の `venv/Scripts/pytest.exe --cov=...` は環境で動作しない（`app` を import できない）。正規コマンドは `venv/Scripts/python.exe -m pytest --cov=app --cov-report=term-missing`。→ CLAUDE.md の表記更新を検討（build-and-test で発見した学習として §13 に候補化）。
- **レビュー Minor 5 件**（code-generation のアドバイザリレビュー）: 台帳欠損時の API 500、`@lru_cache` 無期限キャッシュ、`REFERENCE_YEAR=2026` 固定、頂点距離ベースの最近接、`PipeInfo` の緩い型。いずれも MVP デモ範囲ではブロックしない。
- **`REFERENCE_YEAR=2026`**: 仕様（D-5）どおり固定。2026 年を過ぎると実時間から乖離する（BE-5 着手時の可搬化を検討）。
