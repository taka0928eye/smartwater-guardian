# Build & Test Results — BE-4 配管台帳照合サービス（ledger.py）

> 実行日時: 2026-08-11T00:35–00:36Z | 環境: Windows 11 / Python 3.14.5（backend/venv）| 手法: TDD（Red → Green → Refactor、code-generation で完了済み）

## 1. ビルド結果

| 項目 | 結果 | 出力 |
|------|------|------|
| 依存導入 | ✅ | `requirements.txt` の依存が venv に導入済み（fastapi 0.141.1 / pydantic 2.13.4 / pytest 9.1.1 ほか） |
| import スモーク | ✅ | `import-smoke OK: pipes=10`（`main.app` / `ledger` / `pipe` が import 可能、pipes.json 10 路線読込） |
| フロントエンド build | ⏭ 対象外 | BE-4 はバックエンドのみの変更。`pipe_info` は従来から AlertDetail に null 許容で存在し形は不変 |

## 2. テスト結果

### 単体テスト（pytest）

```text
======================== 107 passed, 1 warning in 1.00s =========================
```

| 指標 | 値 |
|------|-----|
| Total | 107 |
| Passed | 107 |
| Failed | 0 |
| Skipped | 0 |
| 警告 | 1（`StarletteDeprecationWarning`: testclient が httpx2 を推奨 — 本変更とは無関係の既知警告） |

### カバレッジ（app 全体）

```text
TOTAL                      372      0   100%
```

| モジュール | Stmts | Miss | Cover |
|-----------|-------|------|-------|
| `app/services/ledger.py` | 41 | 0 | 100% |
| `app/schemas/pipe.py` | 29 | 0 | 100% |
| `app/routers/alerts.py` | 28 | 0 | 100% |
| その他 app 全体 | — | 0 | 100% |

要求（CLAUDE.md §4: 80% 以上）を大幅超過。

### 独立検証スクリプト（check_ledger.py）

```text
7/7 PASS（A1〜A4 / A6 / D-4 / D-5）· 終了コード 0
```

1. pipes.json が 10 路線（P-001〜P-010）
2. A1: 全 10 消火栓を find_pipe_by_hydrant で解決
3. A2: 未知 hydrant_id → None
4. A3: find_nearest_pipe が既知座標で非 None
5. D-5: get_pipe_age が 2026 - installed_year
6. A4: 欠損→FileNotFoundError / 破損→ValueError
7. A6: モジュールキャッシュ保持（currsize==1）

## 3. 失敗・不具合の詳細

- **失敗なし。** 検証中の一時エラーは 1 件のみ — import スモークの初回実行で `No module named 'app.main'`（エントリポイントは `backend/main.py` の `from main import app`）。コード不具合ではなく実行コマンドの指定誤りで、修正後 Green。build-instructions.md §5 にトラブルシューティングとして記録。
- **既知の Minor（レビュー指摘、ブロックなし）**: 台帳欠損時の API 500、`@lru_cache` の無期限キャッシュ、`REFERENCE_YEAR=2026` 固定、頂点距離ベースの最近接、`PipeInfo` の緩い型 — いずれも MVP 範囲で許容。
