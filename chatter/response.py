from enum import StrEnum
from pydantic import BaseModel


class ChatterResponseType(StrEnum):
    REGISTERED = "registered"
    WAITING_MATCH = "waiting_match"
    MATCH_FOUND = "match_found"
    MESSAGE = "message"
    CHAT_ENDED = "chat_ended"


class ChatterResponse(BaseModel):
    type: ChatterResponseType
    payload: str | dict | None = None
