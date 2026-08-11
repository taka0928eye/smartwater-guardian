# Application Design — Services

> FE-7「KPIサマリの実データ連携と「試算値」注記の実装」のサービス層設計。
> 本スコープは **フロントエンドのみの変更**（バックエンド BE-8 は実装済み・変更対象外。C-1）のため、
> 新規サービス・データ所有の設計判断は発生しない。本成果物は「既存バックエンド API をフロントから
> 利用する」契約を記録し、オーケストレーション方針を定める。

## 1. サービス一覧

| サービス | 種別 | 状態 | 責務 |
|---|---|---|---|
| `KPI Summary API`（`GET /api/v1/kpi/summary`） | バックエンド API（BE-8 実装済み） | **変更対象外** | KPI サマリ（監視センサー数 / Level 1〜3 件数 / 推定削減コスト）を返す |
| フロント KPI 取得ロジック（`useKpiPolling` + `fetchKpiSummary`） | フロントエンドロジック（本スコープ新規） | **新規実装** | 上記 API を 5 秒ポーリングし、表示用データへ変換・保持 |

> 新規サービスは**発生しない**。デモスコープのため、バックエンドはインメモリストア + JSON マスタで
> 動作する単一 FastAPI モノリス（`requirements.md` Constraints・team-practices と整合）。

## 2. オーケストレーションパターン

| 項目 | 内容 |
|---|---|
| パターン | **オーケストレーション（フロント主導）** |
| 主体 | `DashboardClient`（配下の `useKpiPolling`）がデータ取得を集約し、描画状態を一元的に制御する |
| 根拠 | バックエンドは単一エンドポイントを返すだけで、サービス間の調整は存在しない。フロントの
  `DashboardClient` が「KPI 取得 → スケルトン/実データ切替 → 描画」を束ねる（`components.md` §3.1 と整合） |
| 代替（コレオグラフィ） | バックエンドが複数サービスに分割され、イベント連携が必要な場合のみ検討。現スコープでは該当なし |

## 3. サービス間コミュニケーション契約

| 項目 | 内容 |
|---|---|
| プロトコル | HTTP（REST・`GET`） |
| エンドポイント | `GET /api/v1/kpi/summary` |
| ポーリング周期 | 5 秒（`ALERT_POLL_INTERVAL_MS = 5000`・アラートと同一周期。requirements FR-7） |
| 同期 / 非同期 | ポーリング（定期的な同期 GET）。WebSocket / SSE によるリアルタイム通知はスコープ外 |
| レスポンス形 | `KpiSummary` 型（7 フィールド・`snake_case` → フロント境界 `lib/api.ts` で `camelCase` へ 1 回だけ変換） |
| エラー契約 | 4xx/5xx → `ApiError`（`unwrap<T>`）。非 axios エラー → 透過 |
| 認証 | なし（デモスコープ・認証は Out of Scope。requirements Out of Scope と整合） |

## 4. データフロー

```
[BE-8] GET /api/v1/kpi/summary (snake_case)
   ↓ 5 秒ポーリング
[useKpiPolling] 変換・保持 (camelCase) — 成功時のみ kpiData 更新 / 失敗時 isLoading
   ↓
[DashboardClient] ランドマーク所有・スケルトン/実データ切替（aria-busy）
   ↓
[KpiSummary] 5 カード + 試算値注記（表示専用）
```

## 5. ライフサイクルとスケーリング

| 項目 | 内容 |
|---|---|
| ライフサイクル | デモスコープ（8/10〜8/15）でローカル実行。バックエンドは `uvicorn`、フロントは `npm run dev` / 本番ビルド `npm run build` |
| スケーリング特性 | 単一インスタンス・インメモリストア。負荷・水平スケーリングは想定外（本番用大型 GIS DB は Out of Scope） |
| クラウド | 余裕があれば AWS へデプロイ（team-practices Q7）。本スコープでは環境設計なし |

## 6. 本スコープでのサービス設計判断まとめ

- **新規サービスなし**: BE-8 の既存エンドポイントをフロントから利用するのみ（C-1）。
- **オーケストレーションはフロント主導**: `DashboardClient` が KPI 取得・状態遷移・描画を束ねる。
- **リアルタイム化は行わない**: 5 秒ポーリングを採用。リアルタイム通知は Out of Scope。

## Assumptions & Open Questions

- バックエンド `GET /api/v1/kpi/summary` のレスポンス契約は BE-8 実装済みのものをそのまま利用する
  （本スコープで変更しない）。
- KPI とアラートで同一のポーリング周期（5 秒）を共用する（requirements FR-7）。
- その他の未確定項目はなし（None.）

## Sources

- [requirements] `inception/requirements-analysis/requirements.md`（FR-4〜8 / Constraints / Out of Scope）
- [stories] `inception/user-stories/stories.md`（US-1〜4）
- [architecture] `aidlc/spaces/default/codekb/smartwater-guardian/architecture.md`（レイヤー構造・KPI 配線予定・コンポーネント関係図）
- [component-inventory] `aidlc/spaces/default/codekb/smartwater-guardian/component-inventory.md`（既存 API クライアント・fetch 関数の先例）
- [team-practices] `inception/practices-discovery/team-practices.md`（デモスコープ・ローカル実行・変換境界）
- [business-model] `docs/business-model.md`（§3.4 デモ算出例・§3.5 試算値の扱い）
