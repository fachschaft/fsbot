import asyncio
import re

from rocketchat_API.rocketchat import RocketChat
import rocketbot.client as client
import rocketbot.models as m


class BaseBot(client.Client):
    def __init__(self, url, username, password, loop=asyncio.get_event_loop()):
        base_url = re.sub('http[s]?://', '', url)
        super().__init__(f'wss://{base_url}/websocket', loop)
        self.rest_api = RocketChat(user=username, password=password, server_url=url)
        self.username = username
        self.password = password
        self._rooms_cache = {}
        self._users_cache = {}

    async def __aenter__(self):
        await self.connect()
        await self.login(self.username, self.password)

        # TODO: Temp, should be offloaded and retrieved by rest api
        rooms = await self.get_all_rooms()
        self._rooms_cache = {r._id: r for r in rooms}

        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.logout()
        self.disconnect()

    async def room(self, room_id: str) -> m.Room:
        # TODO: Use rest api to retrieve missing rooms
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
