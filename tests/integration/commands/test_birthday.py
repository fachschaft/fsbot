from typing import AsyncIterator

import pytest
import rocketbot.bots as bots
import rocketbot.master as master
import rocketbot.models as m

import fsbot.commands as com


@pytest.yield_fixture
async def birthdaybot(bot: master.Master) -> AsyncIterator[master.Master]:
    botname = bot._username
    birthday = com.Birthday(master=bot)

    # Direct message bot
    bot.bots.append(
        bots.RoomTypeCommandBot(
            master=bot, username=botname,
            enable_direct_message=True,
            commands=[birthday]))

    async with bot:
        yield bot


async def is_private_group_member(user: master.Master, groupname: str) -> bool:
    result = await user.rest.groups_list()
    groups = [m.create(m.Room, g) for g in result.json()['groups']]

    return any([g for g in groups if g.name is not None and g.name == groupname])


@pytest.mark.asyncio
async def test_birthday(
        birthdaybot: master.Master,
        user: master.Master) -> None:
    groupname = 'geburtstag_administrator'

    # Delete group if already exists
    if await is_private_group_member(user, groupname):
        await user.rest.groups_delete(group=groupname)

    assert not await is_private_group_member(user, groupname)

    async with user:
        roomid = await user.ddp.create_direct_message(birthdaybot._username)
        await user.ddp.send_message(roomid, 'birthday @admin')

        await birthdaybot.finish_all_tasks()
        assert await is_private_group_member(user, groupname)
