import pytest

import rocketbot.bots.accesscontrol as ac
import rocketbot.bots.base as base
import rocketbot.models as m


class BaseBot(base.BaseBot):
    async def handle(self, message: m.Message) -> None:
        return


class WhiteListBot(ac.WhitelistRoomMixin, BaseBot):
    pass


def test_whitelistbot() -> None:
    bot = WhiteListBot(master=None, whitelist=['room1'])
    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room2')

    assert bot.is_applicable(r1) is True
    assert bot.is_applicable(r2) is False


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


def test_roomtypebot() -> None:
    bot = RoomTypeBot(master=None, enable_public_channel=True)

    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PRIVATE, roomParticipant=True, roomName='room2')
    r3 = m.RoomRef2(roomType=m.RoomType.DIRECT, roomParticipant=True, roomName='room3')

    assert bot.is_applicable(r1) is True
    assert bot.is_applicable(r2) is False
    assert bot.is_applicable(r3) is False
