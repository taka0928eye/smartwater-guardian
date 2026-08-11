# Accessibility Checklist — FE-7 KPIサマリの実データ連携と「試算値」注記

> WCAG 2.1 Level AA 適合を目標とする（wireframes 承認済み Q4=A）。本スコープは表示変更のみで
> 新規インタラクティブ要素（ボタン・リンク・フォーム）を追加しないため、操作系の要件は
> 既存 UI の維持が中心となる。表示仕様は `mockups.md`、インタラクションは `interaction-spec.md`、
> デザインシステムへの適合は `design-system-mapping.md` を参照。

## 適合宣言

- **対象:** WCAG 2.1 Level AA（統合サマリ確認済み）
- **適用範囲:** KPI サマリセクション（本スコープで変更する部分）。既存 UI（ヘッダー・地図・アラート一覧・
  詳細ドロワー）は変更対象外のため、既存の適合状態を維持する。 [wireframes]

## POUR 原則別チェック

### 1. Perceivable（知覚可能）

| 要件 | 実装 | 根拠 |
|---|---|---|
| 非装飾的画像の代替テキスト | 本スコープで画像を追加しない（N/A） | — |
| 色のコントラスト | 既存 Tailwind トーンを維持: 本文 `text-slate-900` / ラベル `text-slate-500`（対白背景で AA 4.5:1 達成済み）/ アクセント（red / amber / lime の 700 系文字色） | [design-system-mapping] |
| **色だけで情報を伝えない** | Level 1/2/3 カードは色（lime / amber / red）に加えて**ラベル文言**（「Level 1 微小漏水（AI検知）」「Level 2 警告」「Level 3 破裂リスク」）で区別 | [wireframes] |
| 試算値注記の識別 | 「試算値」「前提: docs/business-model.md」の**文字列**で推定値であることを表示（色のみに依存しない） | [mockups] |

### 2. Operable（操作可能）

| 要件 | 実装 | 根拠 |
|---|---|---|
| キーボード操作 | KPI カードは非インタラクティブのため `tabindex` 不要。新規インタラクティブ要素を追加しない | [wireframes] |
| フォーカス表示 | 変更対象外（カードはフォーカスを受けない） | — |
| タイミング | ポーリングによる自動更新は 5 秒間隔で、WCAG の「一時停止できる」要件の対象外（データ監視用途の許容範囲）。画面を自動移動・自動スクロールしない | [interaction-spec] |
| モーション | スケルトンの `animate-pulse` は `prefers-reduced-motion` で無効化 | [interaction-design-patterns] |

### 3. Understandable（理解可能）

| 要件 | 実装 | 根拠 |
|---|---|---|
| 見出し階層 | ページ `h1` → KPI サマリ `h2`「KPI サマリ」→ 各カードは `p`（ラベル）。見出しレベルを飛ばさない | [wireframes] |
| 一貫した識別 | カード構成・ラベルは既存の命名規則（「Level N + 状態」）を踏襲し、初見のユーザーにも意味が通る | [design-system-mapping] |
| 予測可能性 | カードの並び（降順）・注記位置は承認済みワイヤーフレームと一致。操作による予期しない画面変化なし | [mockups] |

### 4. Robust（堅牢）

| 要件 | 実装 | 根拠 |
|---|---|---|
| 妥当な HTML | `section` / `h2` / `p` のネストが妥当。本スコープで独自 role は追加しない | [interaction-spec] |
| 一意な ID | `aria-labelledby` で参照する h2 の ID はページ内で一意（例: `kpi-summary-heading`） | [interaction-spec] |

## ARIA 実装仕様

| 要素 | 属性 | 値 | 条件 |
|---|---|---|---|
| KPI サマリ `section` | `aria-labelledby` | h2「KPI サマリ」の id（例: `kpi-summary-heading`） | 常時 |
| KPI セクションコンテナ | `aria-busy` | `true` / `false` | スケルトン中 `true`・取得成功で `false` |
| KPI セクションコンテナ | `aria-live` | **付与しない** | 5 秒ポーリングでの読上げノイズ回避（ステータス 1 行に限定する場合のみ付与） |
| KPI カード | role | なし（ネイティブ `div` で十分） | 非インタラクティブ |

> `aria-live` の扱いは design agent 指摘 6 / wireframes.md:67 に従う。 [wireframes] [stories US-3 AC6]

## 見出し階層

```
h1  ← ページタイトル（既存）
 └ h2「KPI サマリ」  ← 本スコープで追加（aria-labelledby で section に紐付け）
    └ p（カードラベル: 監視センサー数 / Level 3 破裂リスク / … / 推定削減コスト · 試算値）
```

## スケルトン中のアクセシビリティ

- スケルトン表示中は `aria-busy="true"` で「処理中」を伝える。
- スケルトンは数値テキストを含まないため、読み上げによる誤った数値の告知を防ぐ。
- 取得成功時に `aria-busy="false"` へ戻し、実データを表示する。

## 検証方法

| 手法 | 内容 |
|---|---|
| 自動 | axe DevTools / Lighthouse アクセシビリティ監査（ビルド後のページで実施） |
| 静的コードレビュー | h2・aria-labelledby・aria-busy の実装有無を grep / コードレビューで確認 |
| コンポーネントテスト | `KpiSummary` に h2 が存在・`aria-labelledby` が section を紐付けることをテストで検証 |

## Assumptions & Open Questions

- スケルトン中の読み上げは `aria-busy` で「処理中」を伝え、ポーリングによる数値更新の読上げは
  `aria-live` を付与しないことで回避する（5 秒ごとの読上げノイズが支援技術利用者に悪影響を与えるため）。
- その他の未確定項目はなし（None.）

## Sources

- [wireframes] `ideation/rough-mockups/wireframes.md`（アクセシビリティ注記・h1→h2→p 階層・aria-busy・色依存回避）
- [user-flow] `ideation/rough-mockups/user-flow.md`（スケルトン切替の状態遷移）
- [stories] `inception/user-stories/stories.md`（US-2 AC4 h2・aria-labelledby / US-3 AC6 aria-busy・aria-live）
- [requirements] `inception/requirements-analysis/requirements.md`（FR-8 スケルトン・NFR-5 UI 一貫性）
- [team-practices] `inception/practices-discovery/team-practices.md`（フォールバック Q10・表示メタ単一ソース Q9）
