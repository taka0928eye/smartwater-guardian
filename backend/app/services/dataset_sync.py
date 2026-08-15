"""DEMO-2: AWS環境でのデモ音源データセット同期（ライセンス配慮）。

``backend/dataset/``（Zenodo由来・ライセンス上再配布不可のため git 管理外。
``.gitignore`` 参照）は、AWS 環境ではコンテナイメージに含まれない。運用者が
事前にプライベート S3 バケットへ手動アップロードした音源を、起動時に
``sync_dataset_from_s3()`` でコンテナのローカルディレクトリへ同期する
（git/CI を経由しないため、ライセンス上の「再配布」に該当しない）。

S3 設定が無い、または取得に失敗した場合も呼び出し側（``main.py`` の
``lifespan``）はアプリ起動を継続する設計を前提とする。この関数自体は
``boto3``/``botocore`` のエラーを ``DatasetSyncError`` に変換して送出する。
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


class DatasetSyncError(Exception):
    """S3からのデータセット同期に失敗した（呼び出し側は起動を継続してよい）。"""


def _parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    """``s3://bucket/prefix`` 形式を (bucket, prefix) に分解する。"""
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise DatasetSyncError(
            f"S3 URI の形式が不正です（s3://bucket/prefix 形式で指定）: {s3_uri}"
        )
    prefix = parsed.path.lstrip("/")
    return parsed.netloc, prefix


def sync_dataset_from_s3(s3_uri: str, target_dir: Path) -> int:
    """S3の音源データセット（.wavのみ）を target_dir へダウンロードする。

    ``s3_uri`` は ``s3://<bucket>/<prefix>/`` 形式。取得できた .wav ファイル数を
    返す。認証・権限・ネットワークエラーは ``DatasetSyncError`` に変換する。
    """
    bucket, prefix = _parse_s3_uri(s3_uri)
    target_dir.mkdir(parents=True, exist_ok=True)

    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        client = boto3.client("s3")
        paginator = client.get_paginator("list_objects_v2")
        downloaded = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if not key.lower().endswith(".wav"):
                    continue
                filename = key.rsplit("/", 1)[-1]
                client.download_file(bucket, key, str(target_dir / filename))
                downloaded += 1
        return downloaded
    except (BotoCoreError, ClientError) as exc:
        raise DatasetSyncError(f"S3からのデータセット同期に失敗しました: {exc}") from exc
