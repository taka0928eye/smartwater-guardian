# コード生成プラン承認（BE-8 KPI「推定削減コスト」算定ロジックとサマリAPI）

## Plan Approval

TDD（Red → Green → Refactor）で 8 ステップ（スキーマ → 単価計算テスト → 算定サービス → サマリ計算テスト → サマリ組み立て → エンドポイントテスト → ルーター+main.py 登録 → 自走確認）を実行します。新規 4 ファイル + 既存 1 ファイル修正（`main.py` へのルーター登録）です。フロントは変更しません。

- Approve Plan — コード生成を開始します
- Request Changes — プランを修正します

[Answer]: Approve Plan
