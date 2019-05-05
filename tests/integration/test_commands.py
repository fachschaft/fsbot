import asyncio
from typing import AsyncIterator, Awaitable, Callable

import pytest
from asynctest import MagicMock

import rocketbot.bots as bots
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as pollutil

from ..utils import patch_module

mock_bot_config = MagicMock()
mock_bot_config.MENSA_CACHE_URL = 'https://www.mensa_dummy.de/api'
with patch_module('bot_config', mock_bot_config):
    import rocketbot.commands as com


@pytest.yield_fixture
async def pollbot(bot: master.Master, statusroom: m.Room) -> AsyncIterator[master.Master]:
    botname = bot._username
    pollmanager = pollutil.PollManager(
        master=bot,
        botname=botname,
        statusroom=statusroom.to_roomref())

    poll = com.Poll(master=bot, pollmanager=pollmanager)

    # Direct message bot
    bot.bots.append(
        bots.RoomTypeCommandBot(
            master=bot, username=botname,
            enable_direct_message=True,
            commands=[poll]))

    async with bot:
        yield bot


def num_tasks() -> int:
    return len(asyncio.all_tasks())


async def finish_all_tasks(num_tasks: int) -> None:
    # TODO(Change to context manager?)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    # +1 for current task
    tasks_left = len(tasks) - num_tasks + 1
    for t in asyncio.as_completed(tasks):
        await t
        tasks_left -= 1
        if tasks_left == 0:
            break


def expect_message(event: asyncio.Event) -> Callable[[m.Message], Awaitable[None]]:
    async def f(message: m.Message) -> None:
        event.set()
    return f


@pytest.mark.asyncio
async def test_poll_push_to_public(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, public_channel: m.Room) -> None:
    # Register a bot waiting for the poll which resolves a future
    event = asyncio.Event()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[public_channel.name], callback=expect_message(event)))

    async with user:
        tasks = num_tasks()
        roomid = await user.ddp.create_direct_message(pollbot._username)
        await user.ddp.send_message(roomid, 'poll test 1')
        await user.ddp.send_message(roomid, f'poll_push #{public_channel.name}')

        await finish_all_tasks(tasks)
        assert event.is_set()


@pytest.mark.asyncio
async def test_poll_push_to_private(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, private_group: m.Room, admin: master.Master) -> None:

    admin.rest.groups_invite(private_group._id, pollbot.rest.headers['X-User-Id'])
    admin.rest.groups_invite(private_group._id, user.rest.headers['X-User-Id'])
    # Register a bot waiting for the poll which resolves a future
    future = event_loop.create_future()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[private_group.name], callback=asyncio.coroutine(future.set_result)))

    async with user:
        tasks = num_tasks()

        roomid = await user.ddp.create_direct_message(pollbot._username)
        await user.ddp.send_message(roomid, 'poll test 1')
        await user.ddp.send_message(roomid, f'poll_push #{private_group.name}')

        await finish_all_tasks(tasks)
        assert await asyncio.wait_for(future, 3)
