from uuid import UUID, uuid4
from fastapi import WebSocket
from typing import Self
from threading import Lock
from datetime import datetime

from chatter.utils import Gender, Preference
from chatter.response import ChatterResponse


class User:
    _id: UUID
    _websocket: WebSocket
    _age: int | None
    _gender: Gender | None
    _preference: Preference
    _active_peer: Self | None
    _last_ping: float
    _lock: Lock
    _registered: bool

    def __init__(self, websocket: WebSocket) -> None:
        self._id = uuid4()
        self._websocket = websocket
        self._age = None
        self._gender = None
        self._preference = Preference()
        self._active_peer = None
        self._registered = False
        self._lock = Lock()
        self.update_ping()

    def __hash__(self):
        return hash((self._id, self._websocket))

    @property
    def is_free(self):
        return self._active_peer is None

    @property
    def age(self):
        return self._age

    @property
    def gender(self):
        return self._gender

    @property
    def websocket(self):
        return self._websocket

    @property
    def is_registered(self):
        return self._registered

    @property
    def active_peer(self):
        return self._active_peer

    def register(self, age: int | None, gender: Gender | None, preference: Preference):
        with self._lock:
            self._age = age
            self._gender = gender
            self._preference = preference
            self._registered = True

    def __check_age_match(self, other: Self):
        checks = [False, False]
        if self._preference.age.min is None:
            checks[0] = True
        if self._preference.age.max is None:
            checks[1] = True
        if other.age is not None:
            if self._preference.age.min is not None and other.age >= self._preference.age.min:
                checks[0] = True
            if self._preference.age.max is not None and other.age <= self._preference.age.max:
                checks[1] = True
        return all(checks)

    def __check_gender_match(self, other: Self):
        check = False
        if self._preference.gender is None:
            check = True
        if other.gender is not None and self._preference.gender is not None:
            if isinstance(self._preference.gender, Gender):
                if other.gender == self._preference.gender:
                    check = True
            else:
                if other.gender in self._preference.gender:
                    check = True
        return check

    def check_match(self, other: Self):
        with self._lock:
            return self.__check_age_match(other) and self.__check_gender_match(other)

    def set_active_peer(self, other: Self):
        with self._lock:
            if not self.is_free:
                raise Exception("User is not free!")
            self._active_peer = other

    def unset_active_peer(self):
        with self._lock:
            self._active_peer = None

    def update_ping(self):
        self.last_ping = datetime.now().timestamp()

    async def send_response(self, response: ChatterResponse):
        await self._websocket.send_json(response.model_dump())
