import asyncio
from typing import AsyncIterator

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


@pytest.mark.asyncio
async def test_poll_push_to_public(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, public_channel: m.Room) -> None:
    # Register a bot waiting for the poll which resolves a future
    future = event_loop.create_future()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[public_channel.name], callback=asyncio.coroutine(future.set_result)))

    async with user:
        roomid = await user.client.create_direct_message(pollbot._username)
        await user.client.send_message(roomid, 'poll test 1')
        await user.client.send_message(roomid, f'poll_push #{public_channel.name}')
        assert await asyncio.wait_for(future, 3)


@pytest.mark.asyncio
async def test_poll_push_to_private(
        event_loop: asyncio.AbstractEventLoop, pollbot: master.Master,
        user: master.Master, private_group: m.Room, admin: master.Master) -> None:

    admin.rest_api.groups_invite(private_group._id, pollbot.rest_api.headers['X-User-Id'])
    admin.rest_api.groups_invite(private_group._id, user.rest_api.headers['X-User-Id'])
    # Register a bot waiting for the poll which resolves a future
    future = event_loop.create_future()
    user.bots.append(bots.RoomCustomBot(
        master=user, whitelist=[private_group.name], callback=asyncio.coroutine(future.set_result)))

    async with user:
        roomid = await user.client.create_direct_message(pollbot._username)
        await user.client.send_message(roomid, 'poll test 1')
        await user.client.send_message(roomid, f'poll_push #{private_group.name}')
        assert await asyncio.wait_for(future, 3)
