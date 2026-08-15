"""DEMO-2: app/services/dataset_sync.py（AWS環境向けS3データセット同期）のテスト。

backend/dataset/（Zenodo由来・ライセンス上git管理外）は、AWS環境ではコンテナに
含まれない。運用者が事前にプライベートS3バケットへ手動アップロードした音源を、
起動時にこのモジュールでコンテナのローカルディレクトリへ同期する。
boto3 は unittest.mock でモックし、実際のAWS接続は行わない。

実行方法（backend ディレクトリで）:

    venv/Scripts/python.exe -m pytest tests/test_dataset_sync.py -v
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.dataset_sync import (
    DatasetSyncError,
    _parse_s3_uri,
    sync_dataset_from_s3,
)


class TestParseS3Uri:
    """s3://bucket/prefix 形式のパース。"""

    def test_parses_bucket_and_prefix(self) -> None:
        bucket, prefix = _parse_s3_uri("s3://my-bucket/demo/dataset/")
        assert bucket == "my-bucket"
        assert prefix == "demo/dataset/"

    def test_parses_bucket_without_prefix(self) -> None:
        bucket, prefix = _parse_s3_uri("s3://my-bucket")
        assert bucket == "my-bucket"
        assert prefix == ""

    def test_rejects_non_s3_scheme(self) -> None:
        with pytest.raises(DatasetSyncError):
            _parse_s3_uri("https://my-bucket/demo/dataset/")

    def test_rejects_missing_bucket(self) -> None:
        with pytest.raises(DatasetSyncError):
            _parse_s3_uri("s3:///demo/dataset/")


class TestSyncDatasetFromS3:
    """sync_dataset_from_s3: S3の.wavファイルをローカルへ同期する。"""

    def test_downloads_only_wav_files(self, tmp_path: Path) -> None:
        target_dir = tmp_path / "dataset"
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "demo/dataset/BE3_demo_no-leak_level0.wav"},
                    {"Key": "demo/dataset/README.txt"},
                    {"Key": "demo/dataset/BE3_demo_leak_level3.wav"},
                ]
            }
        ]

        with patch("boto3.client", return_value=mock_client):
            count = sync_dataset_from_s3("s3://my-bucket/demo/dataset/", target_dir)

        assert count == 2
        assert target_dir.is_dir()
        assert mock_client.download_file.call_count == 2
        downloaded_names = {
            call.args[2].split("\\")[-1].split("/")[-1]
            for call in mock_client.download_file.call_args_list
        }
        assert downloaded_names == {
            "BE3_demo_no-leak_level0.wav",
            "BE3_demo_leak_level3.wav",
        }

    def test_returns_zero_when_bucket_empty(self, tmp_path: Path) -> None:
        target_dir = tmp_path / "dataset"
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{}]

        with patch("boto3.client", return_value=mock_client):
            count = sync_dataset_from_s3("s3://my-bucket/demo/dataset/", target_dir)

        assert count == 0

    def test_wraps_client_error(self, tmp_path: Path) -> None:
        from botocore.exceptions import ClientError

        target_dir = tmp_path / "dataset"
        mock_client = MagicMock()
        mock_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "ListObjectsV2",
        )

        with patch("boto3.client", return_value=mock_client):
            with pytest.raises(DatasetSyncError):
                sync_dataset_from_s3("s3://my-bucket/demo/dataset/", target_dir)

    def test_invalid_uri_raises_before_any_s3_call(self, tmp_path: Path) -> None:
        mock_client = MagicMock()
        with patch("boto3.client", return_value=mock_client):
            with pytest.raises(DatasetSyncError):
                sync_dataset_from_s3("not-an-s3-uri", tmp_path / "dataset")
        mock_client.get_paginator.assert_not_called()
