import asyncio
import re
from typing import List

from rocketchat_API.rocketchat import RocketChat
from rocketchat_API.APIExceptions.RocketExceptions import RocketConnectionException

import rocketbot.bots as b
import rocketbot.client as client
import rocketbot.models as m


class Master:
    def __init__(self, url, username, password, loop=asyncio.get_event_loop()):
        base_url = re.sub('http[s]?://', '', url)
        self.client = client.Client(f'wss://{base_url}/websocket', loop)
        self.rest_api = RocketChat(user=username, password=password, server_url=url)
        self._username = username
        self._password = password
        self._rooms_cache = {}
        self._users_cache = {}
        self.bots: List[b.BaseBot] = []

    async def __aenter__(self):
        await self.client.connect()
        await self.client.login(self._username, self._password)

        await self.enable_bots()

        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.client.logout()
        self.client.disconnect()

    async def room(self, room_id: str) -> m.Room:
        while room_id not in self._rooms_cache:
            try:
                result = self.rest_api.channels_info(room_id=room_id).json()
                if 'channel' in result:
                    self._rooms_cache[room_id] = m.create(m.Room, result['channel'])
                else:
                    raise client.RocketClientException(result)
            except RocketConnectionException:
                raise
                # await asyncio.sleep(1)
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
        async def _callback(result: m.SubscriptionResult):
            if result.room is None:
                return

            for bot in self.bots:
                if bot.is_applicable(result.room):
                    await bot.handle(result.message)

        await self.client.subscribe_my_messages(_callback)
