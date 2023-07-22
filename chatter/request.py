from enum import StrEnum
from pydantic import BaseModel

from chatter.payloads import RegisterPayload


class ChatterRequestType(StrEnum):
    REGISTER = "register"
    MESSAGE = "message"
    END_CHAT = "end_chat"
    REQUEST_MATCH = "request_match"


class ChatterRequest(BaseModel):
    type: ChatterRequestType
    payload: str | dict | RegisterPayload | None = None
