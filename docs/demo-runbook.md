# DEMO-1 デモ通しリハーサル & シード投入 ランガイド

> **Issue**: #23（DEMO-1） / **優先度**: P1 / **想定日**: 8/15
> **関連**: `docs/ui-wireframe.md` §5 / `docs/business-model.md` §3.4 / PRD §6.1

デモ当日に「触れて30秒で価値が伝わる」状態を確実に再現するための、シード投入手順・
通しリハーサル手順・トラブル復旧手順をまとめた実行ガイド。

---

## 1. 目的

- **1コマンドでデモ初期状態を構築**する（`seed_demo.py`）
- デモの山場である **Level 1（微小漏水）** と **Level 0（正常）の対比** を画面上に成立させる
  - 訴求文: 「人間には無音・水圧変化もない段階で、AIだけが漏水に気づいた」
- 同一 `--seed` で同じ状態を再現できる（デモの再現性）
- オフライン（`ORCAROUTER_ENABLED=false`）でも通しシナリオが完走する

## 2. 事前チェックリスト（事故防止）

- [ ] `backend/` に `venv` が存在し、依存がインストール済み
- [ ] repo外で受領した `demo_audio/` に、§3記載の実音響WAV 4本が配置済み
      （※ Git 管理外。Zenodo データセットから切り出したファイルを受領して使用する）
- [ ] `frontend/` で `npm install` 済み（初回のみ）
- [ ] `--seed` を固定し、リハーサルと同一の結果が出ることを確認済み（既定 `--seed 42`）
- [ ] `ORCAROUTER_ENABLED=false` でも完走することを確認済み（§6 オフラインリハーサル）
- [ ] KPI「推定削減コスト」が **2,048,400 円（表示「204.8万円」）** になることを確認済み
- [ ] 起票モーダルに「概算であり正式見積ではない」注記と `source` バッジが表示される
- [ ] 同一アラートの再起票がキャッシュを返し、重複課金しないことを確認済み
- [ ] デモに使用するポート（8000 / 3000）が空いている

## 3. セットアップ（3ターミナル）

```powershell
# --- ターミナル 1: バックエンド起動 ---
cd backend
venv/Scripts/uvicorn.exe main:app --reload --port 8000

# --- ターミナル 2: デモ初期状態の投入（1コマンド） ---
cd backend
venv/Scripts/python.exe scripts/seed_demo.py --seed 42 --audio-dir "C:\path\to\demo_audio"
#   [OK] 23 件を http://localhost:8000/api/v1/demo/seed へ投入しました

# --- ターミナル 3: フロントエンド起動 ---
cd frontend
npm run dev
#   http://localhost:3000 をブラウザで開く
```

macOS / Linuxでは、ターミナル2を次のように実行する。

```bash
cd backend
venv/bin/python scripts/seed_demo.py --seed 42 --audio-dir /path/to/demo_audio
```

### 受領する音声ファイル

`--audio-dir`で指定するフォルダには、次の4ファイルを配置する。

```text
demo_audio/
├── BE3_demo_no-leak_level0.wav
├── BE3_demo_leak_level1.wav
├── BE3_demo_leak_level2.wav
└── BE3_demo_leak_level3.wav
```

全ファイル共通の形式は **WAV / mono / PCM16 / 8000Hz / 1.0秒（8000サンプル）**。
ファイル本体はGit管理せず、受領したローカルフォルダを直接指定する。

### シード内容（`--seed 42` の投入内訳）

| 内容 | 件数 | 画面での表現 |
|---|---|---|
| Level 0（正常） | 11（既存1＋追加10） | 地図のグレー（normal）ノード（対比の起点） |
| Level 1（微小漏水） | 8 | 地図の黄緑（watch）＋ アラート一覧上位 |
| Level 2（進行性漏水） | 3 | 地図のオレンジ（warning） |
| Level 3（管路破裂） | 1 | 地図の赤（critical・点滅） |

監視センサーは合計20台、投入するデモアラートは合計23件。4種類の音源をLevelに応じて再利用する。

KPI「推定削減コスト」はこの内訳から **2,048,400 円（204.8万円）** になる
（`docs/business-model.md` §3.4 の式）。

### シードオプション

| オプション | 既定 | 説明 |
|---|---|---|
| `--seed` | （必須） | シーケンス再現用シード。同一値で同一結果（再現性） |
| `--audio-dir` | `backend/dataset` | 受領した実音響WAVのディレクトリ（上記4ファイルを推奨） |
| `--url` | `http://localhost:8000/api/v1/demo/seed` | デモシード API の URL |
| `--dry-run` | off | 送信せず組み立て結果（内訳・割当・音源ファイル）だけを表示 |

```powershell
# 送信せずに確認したい場合
venv/Scripts/python.exe scripts/seed_demo.py --seed 42 --audio-dir "C:\path\to\demo_audio" --dry-run
```

## 4. デモ初期状態の仕様

シードは `scripts/seed_demo.py` の `build_demo_sequence(seed)` が決定的に組み立て、
各ステップで実音響WAVを再生（**BE-2 の `load_audio_file()` 再利用**）して
`POST /api/v1/demo/seed` で1件ずつ投入する。

- **音源は「学習未使用の Zenodo 実音響」**（学習データと同ドメインの held-out カット）。
  `generate_signal()` の人工音は実 SVM が意図レベルに分類できないため DEMO-1 で不採用にした。
  実音響はrepo外で受領し、`--audio-dir`でそのフォルダを明示する
- **ファイル名規約**: `*no-leak*_level{N}.wav` = 正常音 / `*leak*_level{N}.wav` = 漏水音。
  leak / no-leak を判別できないファイル名は投入ミス防止のためエラーにする
- **音源選定は決定論的**: Level 0 は no-leak 音、Level 1〜3 は leak 音を使い、
  ファイル名の `_level{N}` 一致を優先する（無ければ同バケット内から `--seed` で選ぶ）
- **BE-3 MVP 契約の事前検証**: シードAPIは 8000Hz / 1.0秒 / 8000サンプルの WAV のみ受付可能
  （`validate_mvp_contract`）。契約外の WAV は 422 になる前にエラーで停止する
- 各ステップの `hydrant_id` は `hydrants.json` に実在するIDから決定論的に選定
- Level 0の既存ベースライン1台と追加正常10台は異常ステップで再利用しない
  （最新状態が上書きされると「正常」対比が消えるため）
- Level 1 のステップは Level 3 より**必ず先**に投入される（山場は Level 1）
- **深刻度の確定方式**: デモシード専用 API（`POST /api/v1/demo/seed`）が
  `analyze_audio()` で**実スペクトルを算出**しつつ、深刻度を意図レベルに確定する。
  実 no-leak 音は SVM が自然に severity 0（正常）を返すため、
  「Level 0 = 正しい正常」「Level 1+ = AIが気づいた漏水」の対比が実信号で成立する
  - 実測: `BE3_demo_no-leak_level0.wav` → severity 0（honest 正常）/
    `BE3_demo_leak_level2.wav` → severity 2（leak）を確認済み

## 5. 1分間デモタイムライン（`docs/ui-wireframe.md` §5 と整合）

> 事前にシード済みの状態を、審査員へ以下の順に実演する。所要目安は1分以内。

```text
[0:00 - 0:10] 01. 導入 & 正常状態（10秒）
 ├── 画面提示：オペレーションセンター画面（Level 0 のグレー・正常）
 └── 【セリフ】「熟練作業員でも聞き取れない水道管の『微小漏水』。
               水圧の変化もゼロ、地上からは完全に無音の状態です」

[0:10 - 0:30] 02. Level 1 AI即時検知 ★核心（20秒）
 ├── アラート一覧最上部に Level 1（黄緑・AI検知）が並ぶ
 ├── KPI「推定削減コスト」が 204.8万円 に跳ね上がる
 └── 【セリフ】「水圧計は正常のままですが、音響AIだけが異常を検知しました。
               人間には無音の段階で気づける、これがAIである必然性です」

[0:30 - 0:45] 03. 根拠可視化（15秒）
 ├── Level 1 アラートをクリック ➔ 右スライドイン詳細ドロワーが開く
 ├── Recharts による FFT スペクトルグラフ（500〜1500Hzの異常ピーク）を提示
 └── 【セリフ】「500〜1500Hz帯の波形エネルギーピークと布設年数から、
               AIが漏水と判定しています」

[0:45 - 1:00] 04. AI自動起票 & 収支・原価の提示（15秒）
 ├── ドロワー内の「AI自動起票」ボタンを押下
 ├── Orcarouter 生成の「推奨部材・概算見積・作業指示」モーダルが表示される
 └── 【セリフ】「『AI自動起票』を押すと、LLMが最適な補修部材と概算見積を自動生成。
               1起票あたりのAPI原価もわずか【¥X.XX】。現場の調査・手配コストを9割削減します」
```

## 6. シード状態のクリア

デモ中に「正常状態 → Level 1 検知」を何度も実演したい場合、バックエンド再起動不要で
ストアをリセットする。

```powershell
# ターミナル 1（バックエンド起動中）

# --- シード状態をクリア（全アラート削除） ---
cd backend
venv/Scripts/python.exe scripts/clear_demo.py

# 出力例:
# [OK] 23 件のアラートをクリアしました

# --- 別シード、または同じシード 42 で再度投入 ---
venv/Scripts/python.exe scripts/seed_demo.py --seed 42 --audio-dir "C:\path\to\demo_audio"
```

### クリア後の状態

- ストア内の全アラートが削除される
- 地図のマーカーが消える
- アラート一覧が空になる
- KPI もリセットされる
- **バックエンドを再起動する必要なし**（AWS 環境・本番環境でも利用可能）

### トラブル時

```powershell
# backend が起動していない場合
# [ERROR] backend に接続できません: ...

# シード状態を確認したいけど API が見つからない場合
# [ERROR] クリア API が見つかりません（404）
# => backend のルーターが /api/v1/demo/clear エンドポイントを実装していることを確認
```

---

## 7. オフラインリハーサル（`ORCAROUTER_ENABLED=false`）

実キー無し・ネットワーク無しでも通しシナリオが完走することを確認する。

```powershell
# backend/.env に追記（.env は gitignore 対象）
echo "ORCAROUTER_ENABLED=false" >> backend/.env

# バックエンドを再起動してから、シード → フロント
cd backend
venv/Scripts/uvicorn.exe main:app --reload --port 8000
venv/Scripts/python.exe scripts/seed_demo.py --seed 42 --audio-dir "C:\path\to\demo_audio"
cd ..\frontend; npm run dev
```

- 起票は `source == "fallback"` のフォールバック応答が返り、`cost_yen == 0.0`
  （LLM 未使用のため原価計上なし）。**HTTP 呼び出しは行われない**
- リハーサル後は `ORCAROUTER_ENABLED=true`（または削除）に戻して実キーを注入する

## 8. 当日トラブル時の復旧手順

| 症状 | 対処 | 備考 |
|---|---|---|
| アラート・地図が空 / 状態がおかしい | **バックエンド再起動** → ストア（インメモリ）がクリアされる | `Ctrl+C` → uvicorn 再起動 |
| シードをやり直したい | **クリア後に再投入**: `seed_demo.py --seed 42 --audio-dir <受領フォルダ>` | 同一シード・音源で同一状態に復元 |
| LLM が動かない / 実キーが無い | **フォールバック強制**: `backend/.env` に `ORCAROUTER_ENABLED=false` → 再起動 | §6 と同じ手順 |
| フロントが描画されない | **フロント再起動**: `npm run dev`（`Ctrl+C` → 再実行） | ポート3000 が空いているか確認 |
| CORS エラーが出る | `main.py` の `allow_origins` に使用 URL が入っているか確認 | 既定 `http://localhost:3000` |
| スペクトルが表示されない | アラート詳細を開き直す（ドロワー再取得） | 地図連動で選択状態をリセット |
| KPI が 204.8万円 と一致しない | ストアに余計なデータが無いか確認 → **再起動 + シード再投入** | ステップ内訳がずれると変化する |

### ストアの性質

- データは**インメモリストア**（`app/store.py`、保持上限500件）。**バックエンド再起動で
  初期化される**。永続化はしない（デモスコープの設計）。
- シードは投入済みアラートを二重に作らないよう、**再起動後に必ず再投入**する
  （同一シードなら同一状態に復元されるため安全）。

## 9. リハーサル実測記録（通しリハーサル Step 4）

| 日時 | モード | `--seed` | 結果 | 通し所要時間 | 備考 |
|---|---|---|---|---|---|
| （例）2026-08-13 | オンライン（実キー） | 42 | 完了 | — | 実測を記録 |
| （例）2026-08-13 | オフライン（`ENABLED=false`） | 42 | 完了（fallback） | — | 実測を記録 |
