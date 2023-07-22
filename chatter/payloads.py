from pydantic import BaseModel

from chatter.utils import Gender, Preference


class RegisterPayload(BaseModel):
    age: int | None
    gender: Gender | None
    preference: Preference | None
