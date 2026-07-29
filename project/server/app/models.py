from enum import Enum

from pydantic import BaseModel


class OperatingMode(str, Enum):
    AUTOMATIC = "automatic"
    MANUAL_ON = "manual_on"
    MANUAL_OFF = "manual_off"


class ModeRequest(BaseModel):
    mode: OperatingMode


class RelayRequest(BaseModel):
    enabled: bool
