import asyncio
import re
from typing import Any, Dict, List

from rocketchat_API.rocketchat import RocketChat
from rocketchat_API.APIExceptions.RocketExceptions import RocketConnectionException

import rocketbot.bots.base as b
import rocketbot.client as client
import rocketbot.exception as exp
import rocketbot.models as m


class Master:
    def __init__(self, url: str, username: str, password: str, loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()):
        base_url = re.sub('http[s]?://', '', url)
        self.client = client.Client(f'wss://{base_url}/websocket', loop)
        self.rest_api = RocketChat(user=username, password=password, server_url=url)
        self._username = username
        self._password = password
        self._rooms_cache: Dict[str, m.Room] = {}
        self._users_cache: Dict[str, m.UserRef] = {}
        self.bots: List[b.BaseBot] = []

    async def __aenter__(self) -> 'Master':
        await self.client.connect()
        await self.client.login(self._username, self._password)

        await self.enable_bots()

        return self

    async def __aexit__(self, exception_type: Any, exception_value: Any, traceback: Any) -> None:
        await self.client.logout()
        self.client.disconnect()

    async def room(self, room_id: str) -> m.Room:
        if room_id not in self._rooms_cache:
            try:
                result = self.rest_api.rooms_info(room_id=room_id).json()
                if 'room' in result:
                    self._rooms_cache[room_id] = m.create(m.Room, result['room'])
                else:
                    result['roomId'] = room_id
                    raise exp.RocketBotException(result)
            except RocketConnectionException as e:
                raise exp.RocketClientException(e)
        return self._rooms_cache[room_id]

    async def user(self, username: str) -> m.UserRef:
        if username not in self._users_cache:
            try:
                user = self.rest_api.users_info(username=username).json()['user']
                self._users_cache[username] = m.UserRef(_id=user['_id'], username=username, name=user['name'])
            except Exception:
                # Retry next time
                return m.UserRef(_id='id', username=username, name=username)
        return self._users_cache[username]

    async def enable_bots(self) -> None:
        """Enable bots by subscribing the following callback to all messages
        """
        async def _callback(result: m.SubscriptionResult) -> None:
            if result.room is None:
                return

            for bot in self.bots:
                if bot.is_applicable(result.room):
                    await bot.handle(result.message)

        await self.client.subscribe_my_messages(_callback)
