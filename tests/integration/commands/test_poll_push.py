import asyncio
from typing import AsyncIterator, Awaitable, Callable

import pytest

import rocketbot.bots as bots
import rocketbot.commands as com
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as pollutil


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


def expect_message(event: asyncio.Event) -> Callable[[m.Message], Awaitable[None]]:
    async def f(message: m.Message) -> None:
        event.set()
    return f


@pytest.mark.asyncio
async def test_push_to_public(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, public_channel: m.Room, admin: master.Master) -> None:

    await admin.rest.channels_invite(public_channel._id, pollbot.rest.headers['X-User-Id'])
    await admin.rest.channels_invite(public_channel._id, user.rest.headers['X-User-Id'])

    # Register a bot waiting for the poll which resolves a future
    event = asyncio.Event()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[public_channel.name], callback=expect_message(event)))

    async with user:
        roomid = await user.ddp.create_direct_message(pollbot._username)
        await user.ddp.send_message(roomid, 'poll test 1')
        await user.ddp.send_message(roomid, f'poll_push #{public_channel.name}')

        await pollbot.finish_all_tasks()
        assert event.is_set()


@pytest.mark.asyncio
async def test_push_to_private(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, private_group: m.Room, admin: master.Master) -> None:

    await admin.rest.groups_invite(private_group._id, pollbot.rest.headers['X-User-Id'])
    await admin.rest.groups_invite(private_group._id, user.rest.headers['X-User-Id'])
    # Register a bot waiting for the poll which resolves a future
    event = asyncio.Event()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[private_group.name], callback=expect_message(event)))

    async with user:
        roomid = await user.ddp.create_direct_message(pollbot._username)
        await user.ddp.send_message(roomid, 'poll test 1')
        await user.ddp.send_message(roomid, f'poll_push #{private_group.name}')

        await pollbot.finish_all_tasks()
        assert event.is_set()
