"""センサテレメトリの入出力スキーマ（Pydantic v2）。

BE-1 の段階では ``TelemetryResponse.analysis`` は常に ``None`` を返す。
BE-3（``app/services/audio.py``）が ``AnalysisResult`` を埋めるようになっても、
このレスポンス契約自体は変更しない。
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

# 漏水深刻度。0=正常 / 1=微小漏水（AI検知）/ 2=進行性漏水 / 3=管路破裂
SeverityLevel = Literal[0, 1, 2, 3]

# センサー由来の外部入力は暗黙の型強制を許さず、未知フィールドも拒否する。
STRICT_INPUT_CONFIG = ConfigDict(strict=True, extra="forbid")


class GeoLocation(BaseModel):
    """センサーが貼り付けられた消火栓の位置。"""

    model_config = STRICT_INPUT_CONFIG

    latitude: float = Field(ge=-90.0, le=90.0, description="緯度")
    longitude: float = Field(ge=-180.0, le=180.0, description="経度")


class TelemetryRequest(BaseModel):
    """疑似IoTセンサーから送信される1回分の音響テレメトリ。"""

    model_config = STRICT_INPUT_CONFIG

    sensor_id: str = Field(min_length=1, max_length=64, description="センサー識別子")
    hydrant_id: str = Field(min_length=1, max_length=64, description="消火栓識別子")
    # strict=True のままだと Python の datetime インスタンスしか受け付けず、JSON で
    # 送られてくる ISO 8601 文字列が通らない。このフィールドだけ strict を外し、
    # 代わりに AwareDatetime でタイムゾーン必須を課して緩みを補う
    # （タイムゾーンなしの録音時刻は複数自治体をまたぐ運用で取り違えの原因になる）。
    recorded_at: AwareDatetime = Field(strict=False, description="録音日時（ISO 8601・TZ必須）")
    location: GeoLocation
    sample_rate_hz: int = Field(gt=0, le=192_000, description="サンプリング周波数")
    duration_sec: float = Field(gt=0.0, le=60.0, description="録音長（秒）")
    audio_base64: str = Field(min_length=1, description="PCM16 モノラル音声の Base64")
    battery_pct: int | None = Field(default=None, ge=0, le=100, description="電池残量")

    @field_validator("audio_base64")
    @classmethod
    def _validate_base64(cls, value: str) -> str:
        """Base64 として解読できない音声データを境界で弾く。"""
        try:
            base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("audio_base64 は妥当な Base64 文字列である必要があります") from exc
        return value


class SpectrumPoint(BaseModel):
    """周波数スペクトルの1点（FE-4 のグラフ描画用）。"""

    model_config = ConfigDict(strict=True)

    freq_hz: float = Field(ge=0.0)
    magnitude: float = Field(ge=0.0)


class AnalysisResult(BaseModel):
    """FFT解析（BE-3 / ``app/services/audio.py``）の判定結果。

    BE-1 では生成しない。BE-3 がこの枠を埋める。
    """

    model_config = ConfigDict(strict=True)

    leak_confidence: float = Field(ge=0.0, le=100.0, description="漏水確信度（%）")
    severity_level: SeverityLevel = Field(description="深刻度 Level 1〜3")
    dominant_freq_hz: float = Field(ge=0.0, description="卓越周波数")
    band_energy_ratio: float = Field(ge=0.0, le=1.0, description="漏水帯域のエネルギー比")
    spectrum: list[SpectrumPoint] = Field(default_factory=list, description="スペクトル")


class TelemetryResponse(BaseModel):
    """テレメトリ受信結果。

    ``analysis`` は BE-3 実装までは常に ``None``。
    """

    model_config = ConfigDict(strict=True)

    telemetry_id: str
    sensor_id: str
    received_at: datetime
    status: Literal["accepted"]
    analysis: AnalysisResult | None = None
