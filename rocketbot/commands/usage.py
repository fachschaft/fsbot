import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m


class Usage(c.Prefix):
    def __init__(self, bot: 'b.CommandBot'):
        super().__init__(bot)
        self.bot: b.CommandBot = bot

        self.enable_public_channel = True
        self.enable_private_group = True
        self.enable_direct_message = True
        self.prefixes.append((['help', 'usage', '?'], self.send_usage))

    def usage(self) -> str:
        return 'help | usage | ?\n     - Print all available commands'

    async def send_usage(self, args: str, message: m.Message) -> bool:
        room = await self.bot.room(message.rid)
        roomref = room.to_roomref2(True)
        command_usage = [c.usage() for c in self.bot._commands if c.is_applicable(roomref)]
        usage = '*Usage:*\n```' + '\n'.join(command_usage) + '```'
        await self.bot.send_message(message.rid, usage)
        return True
