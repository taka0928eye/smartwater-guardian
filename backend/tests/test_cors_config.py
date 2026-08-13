"""INFRA-1: CORS許可オリジンの環境変数化（AWS本番デプロイ対応）。

ALLOWED_ORIGINS 環境変数で CORS 許可オリジンを設定可能にする。
環境変数未設定時は既存のローカル開発向け既定値（http://localhost:3000）を維持し、
ローカル開発（npm run dev / uvicorn --reload）の挙動を変えない。
"""

from main import _get_allowed_origins


def test_get_allowed_origins_defaults_to_localhost_when_unset(monkeypatch):
    """ALLOWED_ORIGINS 未設定時はローカル開発用の既定値のみを返す（既存挙動の維持）。"""
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    assert _get_allowed_origins() == ["http://localhost:3000"]


def test_get_allowed_origins_reads_single_value_from_env(monkeypatch):
    """ALLOWED_ORIGINS に単一URLを設定すると、そのURLのみが許可される。"""
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://smartwater.example.com")
    assert _get_allowed_origins() == ["https://smartwater.example.com"]


def test_get_allowed_origins_splits_comma_separated_values(monkeypatch):
    """ALLOWED_ORIGINS はカンマ区切りで複数オリジンを指定でき、前後の空白は除去される。"""
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "https://smartwater.example.com, http://localhost:3000",
    )
    assert _get_allowed_origins() == [
        "https://smartwater.example.com",
        "http://localhost:3000",
    ]


def test_get_allowed_origins_ignores_empty_entries(monkeypatch):
    """空文字列や余分なカンマは無視される（末尾カンマ等の設定ミスに対する防御）。"""
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://smartwater.example.com,,")
    assert _get_allowed_origins() == ["https://smartwater.example.com"]


def test_default_cors_allows_localhost_origin(client):
    """既定設定（環境変数未設定）で構築されたアプリは、既存どおり localhost:3000 からの
    リクエストに Access-Control-Allow-Origin ヘッダを返す（ローカル開発の回帰防止）。"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
