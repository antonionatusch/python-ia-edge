from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class OperatingMode(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL_ON = "manual_on"
    MANUAL_OFF = "manual_off"


class ModeRequest(BaseModel):
    mode: OperatingMode


class RelayRequest(BaseModel):
    enabled: bool


class NotificationDeviceRequest(BaseModel):
    installation_id: str = Field(min_length=8, max_length=128)
    fcm_token: str = Field(min_length=20, max_length=4096)
    platform: Literal["android"] = "android"
    device_name: str | None = Field(default=None, min_length=1, max_length=120)


class NotificationDeviceResponse(BaseModel):
    installation_id: str
    platform: Literal["android"]
    device_name: str | None
    enabled: bool
    created_at: str
    updated_at: str
