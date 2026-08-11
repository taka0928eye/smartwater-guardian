# Unit of Work Dependency — FE-7 KPIサマリの実データ連携と「試算値」注記

> 単一ユニット（BU-1）のため依存 DAG は自明（単一ノード・依存なし。Q2=A 承認済み）。
> 本成果物は**トポロジーのみ**を記述し、Bolt 順序・臨界経路などの経済的決定は Delivery Planning（2.8）に委ねる。

## 1. 依存 DAG

- 単一ノード `BU-1`。依存エッジなし（`depends_on: []`）。
- 循環依存なし。グラフは DAG（単一ノード）で自明に無閉路。

```
[BU-1]
   (依存なし — 単一ノード)
```

<!-- Text fallback: 単一ノード BU-1 が依存なしで存在する。 -->

## 2. 統合ポイント（Integration Points）

単一ユニットのためユニット間契約は存在しない。外部・内部の統合ポイントは以下に限定される:

| 統合ポイント | 種別 | 内容 |
|---|---|---|
| `GET /api/v1/kpi/summary`（BE-8） | 外部 HTTP（非同期 GET） | `fetchKpiSummary`（`lib/api.ts`）が 5 秒ポーリングで呼び出し。snake_case→camelCase 変換を `lib/api.ts` 境界で 1 回だけ行う |
| `types/api.ts` `KpiSummary` 型 | 内部契約（共有データ） | `DashboardClient` / `useKpiPolling` / `fetchKpiSummary` / `KpiSummary` が参照。コンポーネント内では `KpiSummaryData` エイリアスで同名衝突を回避 |
| `lib/severity.ts` 表示メタ | 内部共有（表示メタ単一ソース） | `SEVERITY_META` / `getSeverityMeta` / `getSeverityColor` の本拠。`types/api.ts` から `SeverityLevel` を re-export |
| `ALERT_POLL_INTERVAL_MS`（=5000） | 内部定数 | `DashboardClient` から `useKpiPolling(intervalMs)` へ引数として渡す（循環依存解消・`useAlertPolling` と対称） |

## 3. 並行開発の機会

- **なし**（単一ユニット）。ユニット間の依存が存在しないため並行開発を構成できる組み合わせはなく、
  すべての実装は BU-1 内で依存順（型 → APIクライアント → 表示 → 状態遷移 → 設定）に行う。
- 複数トポロジカル順序の存在もなし（単一ノードのため順序選択肢は 1 通り）。

## 4. マシン可読エッジブロック（YAML）

```yaml
units:
  - name: BU-1
    kind: ui
    depends_on: []
```

> このブロックは下流のバッチ fan-out（Delivery Planning / Construction）の入力となる。
> `BU-1` は上流 `stories.md` が命名した単一 proto-Unit の識別子を踏襲する
> （uppercase を含む安全なレガシー単一セグメント名としてランタイムが保持）。

## Assumptions & Open Questions

- 単一ユニットのため「依存が解決したら並行実行できる組」は存在せず、Construction は BU-1 の単一 Bolt として扱う前提。
- `BU-1` の名称は上流 `stories.md` の proto-Unit 宣言と整合させ、改名しない（レガシー識別子の保存）。
- その他の未確定項目はなし（None.）

## Sources

- [components] `inception/application-design/components.md`（コンポーネント境界・所有権・依存一覧）
- [component-methods] `inception/application-design/component-methods.md`（公開インターフェース・`useKpiPolling` の戻り値）
- [services] `inception/application-design/services.md`（新規サービスなし・BE-8 利用）
- [component-dependency] `inception/application-design/component-dependency.md`（依存マトリクス・共有リソース・循環なし主張）
- [decisions] `inception/application-design/decisions.md`（ADR-001 `useKpiPolling`・ADR-003 フィクスチャ・ADR-005 ラベル）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-7 / FR-8 / C-1 / C-3）
- [stories] `inception/user-stories/stories.md`（US-1〜4・単一 proto-Unit 宣言・対象ファイル一覧）
