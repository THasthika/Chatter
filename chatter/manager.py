from fastapi import WebSocket
import asyncio
from chatter.user import User
from chatter.response import ChatterResponse, ChatterResponseType
from chatter.request import ChatterRequestType
from chatter.payloads import RegisterPayload
from chatter.utils import Preference


class ChatterManager:

    websocket_map: dict[WebSocket, User]
    users: set[User]
    waiting_match_set: set[User]

    def __init__(self) -> None:
        self.websocket_map = {}
        self.users = set()
        self.waiting_match_set = set()

    def get_user_count(self) -> int:
        return len(self.users)

    async def handle_websocket(self, websocket: WebSocket):
        user = User(websocket)
        self.users.add(user)
        self.websocket_map[websocket] = user

        await self.__broadcase_user_count()

        while True:
            data = await websocket.receive_json()
            if 'type' not in data:
                raise ValueError("Invalid Request")
            user.update_ping()
            match data['type']:
                case ChatterRequestType.REGISTER:
                    await self.__register(user, data['payload'])
                case ChatterRequestType.REQUEST_MATCH:
                    await self.__request_match(user)
                case ChatterRequestType.MESSAGE:
                    await self.__send_message(user, data['payload'])
                case ChatterRequestType.END_CHAT:
                    await self.__end_chat(user)

    async def remove_user(self, user: User):
        if user in self.users:
            if not user.is_free:
                await self.__end_chat(user)
            self.users.remove(user)
            await self.__broadcase_user_count()

    async def remove_websocket(self, websocket: WebSocket):
        if websocket in self.websocket_map:
            user = self.websocket_map[websocket]
            if user in self.waiting_match_set:
                self.waiting_match_set.remove(user)
            await self.remove_user(user)
            del self.websocket_map[websocket]

    async def close(self):
        callbacks = []
        for user in self.users:
            callbacks.append(self.remove_user(user))
        await asyncio.gather(*callbacks)

    async def __broadcase_user_count(self):
        # broadcast user count change
        callbacks = []
        for uc in self.users:
            callbacks.append(uc.send_response(ChatterResponse(
                type=ChatterResponseType.USER_COUNT, payload=self.get_user_count())))
        await asyncio.gather(*callbacks)

    async def __register(self, user: User, payload: dict):
        payload_m = RegisterPayload.model_validate(payload)
        if payload_m.preference is None:
            payload_m.preference = Preference()
        user.register(payload_m.age, payload_m.gender, payload_m.preference)
        response = ChatterResponse(type=ChatterResponseType.REGISTERED)
        await user.send_response(response)

    async def __request_match(self, user: User):
        if not user.is_registered:
            print("User should be registered!")
            return

        if user in self.waiting_match_set:
            print("Already in waiting list")
            return

        # check waiting users
        for other_user in self.waiting_match_set:
            try:
                if user.is_free and \
                    other_user.is_free and \
                    user.check_match(other_user) and \
                        other_user.check_match(user):

                    # match found
                    user.set_active_peer(other_user)
                    other_user.set_active_peer(user)

                    # remove other user from the set
                    self.waiting_match_set.remove(other_user)

                    # notify users
                    await asyncio.gather(
                        user.send_response(
                            ChatterResponse(
                                type=ChatterResponseType.MATCH_FOUND,
                                payload={
                                    "age": other_user.age,
                                    "gender": other_user.gender
                                }
                            )
                        ),
                        other_user.send_response(
                            ChatterResponse(
                                type=ChatterResponseType.MATCH_FOUND,
                                payload={
                                    "age": user.age,
                                    "gender": user.gender
                                }
                            )
                        )
                    )

                    return

            except Exception:
                user.unset_active_peer()

        # add to waiting list
        self.waiting_match_set.add(user)
        await user.send_response(
            ChatterResponse(
                type=ChatterResponseType.WAITING_MATCH
            )
        )

    async def __send_message(self, user: User, message: str):
        if not user.is_registered:
            return

        if user.is_free:
            return

        other_user = user.active_peer
        await other_user.send_response(
            ChatterResponse(
                type=ChatterResponseType.MESSAGE,
                payload=message
            )
        )

    async def __end_chat(self, user: User):
        if not user.is_registered:
            return

        if user.is_free:
            return

        other_user = user.active_peer
        user.unset_active_peer()
        other_user.unset_active_peer()

        try:
            await asyncio.gather(
                other_user.send_response(
                    ChatterResponse(
                        type=ChatterResponseType.CHAT_ENDED,
                    )
                ),
                user.send_response(
                    ChatterResponse(
                        type=ChatterResponseType.CHAT_ENDED,
                    )
                )
            )
        except Exception:
            pass
