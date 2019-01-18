import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m


class Ping(c.Prefix):
    def __init__(self, bot: b.BaseBot):
        super().__init__(bot)

        self.enable_public_channel = True
        self.enable_private_group = True
        self.enable_direct_message = True
        self.prefixes.append((['ping'], self.reply_to_ping))
        self.prefixes.append((['pong'], self.reply_to_pong))

    def usage(self) -> str:
        return 'ping - Reply with "pong"'

    async def reply_to_ping(self, args: str, message: m.Message) -> bool:
        await self.bot.send_message(message.rid, 'Pong')
        return True

    async def reply_to_pong(self, args: str, message: m.Message) -> bool:
        await self.bot.send_message(
            message.rid,
            '[Pong](https://en.wikipedia.org/wiki/Pong) is one of the earliest arcade video games. '
            + 'It is a table tennis sports game featuring simple two-dimensional graphics...')
        return True
