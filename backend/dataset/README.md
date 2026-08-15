# デモ用音響データの配置

デモ用WAVはライセンス上の理由から、このリポジトリには含めません。また、本プロジェクトはWAVを自動取得せず、外部へのダウンロード処理も実行しません。

プロジェクト管理者から正規の方法で次の4ファイルを取得してください。無許可で再配布しないでください。

- `BE3_demo_no-leak_level0.wav`
- `BE3_demo_leak_level1.wav`
- `BE3_demo_leak_level2.wav`
- `BE3_demo_leak_level3.wav`

各ファイルは、mono・PCM16・8000Hz・1秒のWAVである必要があります。

取得した4ファイルを、このREADMEと同じ `backend/dataset/` ディレクトリへ配置します。配置後にバックエンドとフロントエンドを起動し、画面の「シード投入」ボタンを押してください。ローカル絶対パスの設定は不要です。

CLIやテストで別ディレクトリを使う場合は、既存の `backend/scripts/seed_demo.py --audio-dir <ディレクトリ>` を利用できます。
