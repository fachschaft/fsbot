import rocketbot.bots.accesscontrol as ac
import rocketbot.bots.base as base
import rocketbot.models as m


class Basebot(base.BaseBot):
    async def handle(self, message: m.Message) -> None:
        return


class WhiteListBot(ac.WhitelistRoomMixin, Basebot):
    pass


def test_whitelistbot() -> None:
    bot = WhiteListBot(master=None, whitelist=['room1'])
    r1 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room1')
    r2 = m.RoomRef2(roomType=m.RoomType.PUBLIC, roomParticipant=True, roomName='room2')

    assert bot.is_applicable(r1) is True
    assert bot.is_applicable(r2) is False
