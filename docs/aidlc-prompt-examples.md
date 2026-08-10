# AI-DLC プロンプト例集（SmartWater Guardian）

このプロジェクトの開発は `.claude/skills/aidlc/` で実装された AI-DLC ワークフローに
従う（CLAUDE.md 参照）。仕組みそのものの詳細は `.claude/skills/aidlc/SKILL.md` と
`aidlc/spaces/default/memory/` 配下（`org.md`/`team.md`/`project.md`/`phases/*.md`）が
正であり、ここでは重複させない。このドキュメントは**このプロジェクトで実際に打つ
プロンプトの実例集**（コピペして使えるコマンド帳）。

> `/aidlc` は「何を作りたいか」を文章で渡すだけでスコープを自動判定する。迷ったら
> まず素直に説明文だけを渡し、提示されるスコープ・ステージ構成を確認してから承認する
> のが基本の使い方。

## 基本の型

```
/aidlc <作りたいものの説明>
```

- スコープ（どこまでの工程を回すか）は自動判定される。明示したい場合は
  `/aidlc --scope <name> "<説明>"` のように指定する。
- 迷ったら `/aidlc compose "<やりたいこと>"` で、タスクに合わせたステージ構成の提案を
  受けてから承認する（提案は必ず承認ゲートで止まる）。

AI-DLC全体は **Initialization → Ideation → Inception → Construction → Operation**
の5フェーズ・32ステージで構成される（参考: [AI-DLCワークフロー解説記事](https://zenn.dev/suwash/articles/ai-dlc_20260803)）。
下表の「実行ステージ数/全体」の分母32はこの総数を指し、スコープによって実行される
フェーズ・ステージの範囲が変わる。

## スコープ早見表（このプロジェクトで使う頻度が高いもの）

| スコープ | 用途 | Depth | 実行ステージ数/全体 |
|---|---|---|---|
| `mvp` | **ハッカソンMVPの新機能はまずこれ**（CLAUDE.mdの「最もシンプルでデモ映えする実装」方針と相性が良い） | Standard | 22 / 32 |
| `feature` | 本格的に作り込みたい機能（設計〜運用までフル） | Standard | 32 / 32 |
| `bugfix` | 既存動作の不具合修正 | Minimal | 7 / 32 |
| `poc` | 技術検証だけしたい（Orcarouterの応答形式を試す等） | Minimal | 8 / 32 |
| `refactor` | 挙動を変えない整理 | Minimal | 8 / 32 |

CLAUDE.md の「MVP & Scope Control」原則により、この期間中の新機能はまず
`--scope mvp` を既定候補として考える。運用・監視系ステージまで要る本格実装が
必要になったら `feature` に切り替える。

## 機能別プロンプト例

### 0. 初回はまず疎通確認から（推奨）

いきなりMVP全体（22ステージ）を走らせる前に、`--doctor` でセットアップを確認し、
7番（PoC）のような境界が明確な小さい変更で1回ワークフローをE2E（設計〜実装〜
自走確認）まで通しておくと、本番投入する変更で無駄な手戻りが起きにくい。

```
/aidlc --doctor
```

疎通が確認できたら、以降の本実装（下記1〜）に進む。

### 1. プロジェクト全体のMVPを立ち上げる（最初の1回）

```
/aidlc --scope mvp PRD.mdを参照し、消火栓貼付型IoT音響センサーとハイブリッドAI解析により水道管の微小漏水を
早期検知し、GISマップで可視化した上でOrcarouterにより補修部材選定・見積を自動起票する、
自治体向け単一ダッシュボードのMVPを作りたい。認証機能・実物IoT通信・大型GISDBは対象外。
```

### 2. センサーデータ受信API（バックエンド）

```
/aidlc --scope mvp IoTセンサーから送られてくる音響データ（Base64エンコードされたPCM16、
sensor_id・recorded_at・sample_rate_hz付き）を受け取り検証するFastAPIエンドポイントを
/sensors/readings に作りたい。CORSはNext.jsのローカル開発オリジンを許可する。
```

→ 実装段階では `fastapi-pydantic-v2-patterns` スキルが自動的に参照される。

### 3. 音響解析・深刻度判定ロジック（バックエンド）

```
/aidlc --scope mvp 受信した漏水音の音響データをFFT/周波数解析し、Level1〜3の深刻度に
判定するロジックを backend/app/services/audio.py に実装したい。NumPy/SciPyを使う。
```

→ `numpy-scipy-signal-processing` スキルが自動的に参照される。

### 4. センサー位置・漏水エリアのGISマップ表示（フロントエンド）

```
/aidlc --scope mvp センサーの設置位置と漏水判定エリアをLeafletの地図上に表示する画面を
作りたい。深刻度によってピンの色を変え、クリックで詳細情報をポップアップ表示する。
```

→ `next-app-router-best-practices`（Leaflet SSR回避）と `geojson-leaflet-integration`
（マーカー・GeoJSON設計）の両スキルが自動的に参照される。

### 5. Orcarouterによる補修部材選定・見積自動起票

```
/aidlc --scope mvp 深刻度判定結果と配管台帳データをOrcarouter APIに渡し、補修部材の選定と
見積・修繕指示書を自動生成する処理を backend/app/services/orcarouter.py に実装したい。
APIキーはbackend/.envで管理し、フロントには露出させない。
```

### 6. 既存機能の不具合修正

```
/aidlc --scope bugfix 深刻度Level3のセンサーが地図上で緑色ピンのまま表示される不具合を
修正したい。
```

### 7. 技術検証だけ先にやりたい（実装前のPoC）

```
/aidlc --scope poc Orcarouter APIのレスポンス形式と認証方式を確認するための最小スクリプトを
作りたい。
```

### 8. どのスコープが適切か分からない・複数機能が絡む

```
/aidlc compose センサーデータ受信からOrcarouterでの見積自動起票までを一気通貫で
実装したい。設計〜実装〜簡単な動作確認まで。運用監視は今回は不要。
```

→ アダプティブ・コンポーザーがステージ構成の提案（実行/スキップの理由付き）を出し、
承認ゲートで止まる。承認・編集・却下を選べる。

## よく使う操作コマンド

| コマンド | 用途 |
|---|---|
| `/aidlc --status` | 現在のワークフローの進行状況を確認 |
| `/aidlc --doctor` | セットアップ（bun・AWS Bedrock等）の健全性確認 |
| `/aidlc --stage <slug>` | 特定ステージに直接ジャンプ（例: `--stage application-design`） |
| `/aidlc --phase <name>` | フェーズ単位でジャンプ（`ideation`/`inception`/`construction`/`operation`） |
| `/aidlc --resume` | 中断したワークフローの再開 |
| `/aidlc-code-generation` | コード生成ステージだけを単独実行（メインのワークフロー進行には影響しない） |

## Tips

- 説明文はできるだけ「何を」「誰のために」「スコープ外は何か」まで含めると、
  スコープ自動判定・ステージ構成の精度が上がる（上記の例はすべてその型）。
- 承認ゲートでは `Approve` だけでなく `Request Changes` も選べる。プランの粒度が
  大きすぎる・小さすぎると感じたら遠慮なく差し戻す。
- 1つのアイデアの中に無関係な新機能が混ざっていると気づいたら、新規インテントとして
  分けるかを `/aidlc` 側から確認される（会話を打ち切って進めて構わない）。
- 承認ゲートは内容を読まずに `Approve` を連打しない。計画・成果物を確認せず通すと
  Human-in-the-Loopが単なる待ち時間になり、後工程での手戻りに気づけなくなる。
- 「ビルド/テストが通りました」というAIの報告を鵜呑みにしない。CLAUDE.mdの自走確認
  ステップ通り、`npm run build`（フロント）と `backend/venv/Scripts/python.exe`
  での動作検証（バック）は自分の目でも出力を確認する。
