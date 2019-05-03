import datetime
from typing import Any

import pytest

import rocketbot.bots.accesscontrol as ac
import rocketbot.bots.base as base
import rocketbot.bots.messagefilter as mf
import rocketbot.models as m


@pytest.fixture
def message() -> m.Message:
    return m.Message({
        '_id': 'id',
        '_updatedAt': datetime.datetime.now().isoformat(),
        'rid': 'rid',
        'msg': '',
        'ts': datetime.datetime.now().isoformat(),
        'u': {'_id': '_id', 'username': 'username', 'name': 'name'}
    })


class BaseBot(base.BaseBot):
    def __init__(self, **kwargs: Any) -> None:
        self.called_handle = False

    async def handle(self, message: m.Message) -> None:
        self.called_handle = True


class WhiteListBot(ac.WhitelistRoomMixin, BaseBot):
    pass


def test_whitelistbot() -> None:
    bot = WhiteListBot(master=None, whitelist=['room1'])
    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True)

    assert bot.is_applicable(r1) is True
    assert bot.is_applicable(r2) is False
    assert bot.is_applicable(r3) is False


def test_whitelistbot_directmsgs() -> None:
    bot = WhiteListBot(master=None, whitelist=[], whitelist_directmsgs=True)
    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True)

    assert bot.is_applicable(r1) is False
    assert bot.is_applicable(r2) is True


class BlacklistBot(ac.BlacklistRoomMixin, BaseBot):
    pass


def test_blacklistbot() -> None:
    bot = BlacklistBot(master=None, blacklist=['room1'])
    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room2')

    assert bot.is_applicable(r1) is False
    assert bot.is_applicable(r2) is True


class RoomTypeBot(ac.RoomTypeMixin, BaseBot):
    pass


def test_roomtypebot_argsrequired() -> None:
    with pytest.raises(ValueError):
        RoomTypeBot(master=None)


def test_roomtypebot_public() -> None:
    bot = RoomTypeBot(master=None, enable_public_channel=True)

    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PRIVATE, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True, roomName='room3')

    assert bot.is_applicable(r1) is True
    assert bot.is_applicable(r2) is False
    assert bot.is_applicable(r3) is False


def test_roomtypebot_private() -> None:
    bot = RoomTypeBot(master=None, enable_private_group=True)

    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PRIVATE, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True, roomName='room3')

    assert bot.is_applicable(r1) is False
    assert bot.is_applicable(r2) is True
    assert bot.is_applicable(r3) is False


def test_roomtypebot_direct() -> None:
    bot = RoomTypeBot(master=None, enable_direct_message=True)

    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PRIVATE, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True, roomName='room3')

    assert bot.is_applicable(r1) is False
    assert bot.is_applicable(r2) is False
    assert bot.is_applicable(r3) is True


def test_roomtypebot_multiple() -> None:
    bot = RoomTypeBot(master=None, enable_private_group=True, enable_direct_message=True)

    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PRIVATE, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True, roomName='room3')

    assert bot.is_applicable(r1) is False
    assert bot.is_applicable(r2) is True
    assert bot.is_applicable(r3) is True


class IgnoreOwnMsgBot(mf.IgnoreOwnMsgMixin, BaseBot):
    pass


@pytest.mark.asyncio
async def test_ignoreownmsgbot_with_own_msg(message: m.Message) -> None:
    username = 'testuser'
    bot = IgnoreOwnMsgBot(master=None, username=username)
    message.created_by = m.UserRef(_id='id', username=username, name='Test')

    await bot.handle(message)

    assert not bot.called_handle


@pytest.mark.asyncio
async def test_ignoreownmsgbot_with_foreign_msg(message: m.Message) -> None:
    username = 'testuser'
    bot = IgnoreOwnMsgBot(master=None, username=username + '!')
    message.created_by = m.UserRef(_id='id', username=username, name='Test')

    await bot.handle(message)

    assert bot.called_handle
