from enum import StrEnum
from pydantic import BaseModel


class ChatterResponseType(StrEnum):
    REGISTERED = "registered"
    WAITING_MATCH = "waiting_match"
    MATCH_FOUND = "match_found"
    MESSAGE = "message"
    CHAT_ENDED = "chat_ended"
    USER_COUNT = "user_count"


class ChatterResponse(BaseModel):
    type: ChatterResponseType
    payload: int | str | dict | None = None
