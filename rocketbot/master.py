from __future__ import annotations

import asyncio
import logging
import re
import signal
from typing import Any, Dict, List, Optional

from rocketchat_API.APIExceptions.RocketExceptions import (
    RocketConnectionException
)

import rocketbot.bots.base as b
import rocketbot.client as client
import rocketbot.exception as exp
import rocketbot.models as m


class Master:
    def __init__(
            self, base_url: str, username: str, password: str, tls: bool = True,
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    ):
        base_url = re.sub('http[s]?://', '', base_url)

        if tls:
            ws_url = f'wss://{base_url}/websocket'
            rest_url = f'https://{base_url}'
        else:
            ws_url = f'ws://{base_url}/websocket'
            rest_url = f'http://{base_url}'

        self.ddp = client.DdpClient(ws_url, loop)
        self.rest = client.RestClient(server_url=rest_url)
        self._username = username
        self._password = password
        self._roomid_cache: Dict[str, m.Room] = {}
        self._roomname_cache: Dict[str, m.Room] = {}
        self._users_cache: Dict[str, m.UserRef] = {}
        self.bots: List[b.BaseBot] = []
        self._active_callbacks: List[asyncio.Task[Any]] = []

        # Add signal handler for graceful stop
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(s, lambda s=s: asyncio.create_task(self.signal_handler(s)))

    async def __aenter__(self) -> 'Master':
        logging.debug(f"Called __aenter__ for user {self._username}")

        async def _login_ddp() -> None:
            """Login ddp by calling connect and login sequential"""
            await self.ddp.connect()
            await self.ddp.login(self._username, self._password)

        # Login rest and ddp in parallel
        await asyncio.gather(
            _login_ddp(),
            self.rest.login(self._username, self._password)
        )

        # Enable bots when both clients are connected/ logged in
        await self.enable_bots()

        return self

    async def __aexit__(self, exception_type: Any, exception_value: Any, traceback: Any) -> None:
        logging.debug(f"Called __aexit__ for user {self._username}")
        await self.shutdown()

    async def room(self, *, room_id: Optional[str] = None, room_name: Optional[str] = None) -> m.Room:
        if room_id is not None:
            if room_id not in self._roomid_cache:
                try:
                    result = (await self.rest.rooms_info(room_id=room_id)).json()
                    if 'room' in result:
                        room = m.create(m.Room, result['room'])
                        self._roomid_cache[room_id] = room
                        if room.name is not None:
                            self._roomname_cache[room.name] = room
                    else:
                        result['roomId'] = room_id
                        raise exp.RocketBotException(result)
                except RocketConnectionException as e:
                    raise exp.RocketClientException(e)
            return self._roomid_cache[room_id]
        if room_name is not None:
            if room_name not in self._roomname_cache:
                try:
                    result = (await self.rest.rooms_info(room_name=room_name)).json()
                    if 'room' in result:
                        room = m.create(m.Room, result['room'])
                        self._roomid_cache[room._id] = room
                        self._roomname_cache[room_name] = room
                    else:
                        result['roomName'] = room_name
                        raise exp.RocketBotException(result)
                except RocketConnectionException as e:
                    raise exp.RocketClientException(e)
            return self._roomname_cache[room_name]
        raise exp.RocketBotException("You have to specify either room_id or room_name.")

    async def user(self, username: str) -> m.UserRef:
        if username not in self._users_cache:
            try:
                user = (await self.rest.users_info(username=username)).json()['user']
                self._users_cache[username] = m.UserRef(_id=user['_id'], username=username, name=user['name'])
            except Exception:
                # Retry next time
                return m.UserRef(_id='id', username=username, name=username)
        return self._users_cache[username]

    async def enable_bots(self) -> None:
        """Enable bots by subscribing the following callback to all messages
        """
        # TODO(parallelize bot.handle)
        async def _callback(result: m.SubscriptionResult) -> None:
            if result.room is None:
                return

            task = asyncio.current_task()
            if task is not None:
                self.add_task(task)

            for bot in self.bots:
                if bot.is_applicable(result.room):
                    await bot.handle(result.message)

        await self.ddp.subscribe_my_messages(_callback)

    async def signal_handler(self, sig: signal.Signals) -> None:
        logging.info(f"{sig.name} received. Shuting down {self._username}")
        await self.shutdown()
        exit(0)

    async def shutdown(self) -> None:
        """Graceful shutdown master by logging out and disconnecting the clients"""
        async def _shutdown_ddp() -> None:
            """Shutdown ddp by calling logout and disconnect sequential"""
            await self.ddp.logout()
            await self.ddp.disconnect()

        await asyncio.gather(
            _shutdown_ddp(),
            self.rest.logout()
        )

    def add_task(self, task: asyncio.Task[Any]) -> None:
        '''Add a task to the master

        All tasks are monitored and can be waited on graceful shutdown
        '''
        # Remove all finished tasks from list
        self._active_callbacks = [t for t in self._active_callbacks if not t.done()]
        self._active_callbacks.append(task)
        logging.debug(f"Task added. Currently {len(self._active_callbacks)} active tasks")

    async def finish_all_tasks(self) -> None:
        while any(x for x in self._active_callbacks if not x.done()):
            await asyncio.wait(self._active_callbacks)
        await asyncio.sleep(.5)
