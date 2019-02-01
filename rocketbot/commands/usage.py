from typing import List

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m


class Usage(c.BaseCommand):
    def __init__(self, master: master.Master):
        self.master = master

    def usage(self) -> List[str]:
        return ['help | usage | ?     - Print all available commands']

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['help', 'usage', '?']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        usage: List[str] = []
        room = await self.master.room(message.rid)
        roomref = room.to_roomref2(True)

        for bot in self.master.bots:
            if bot.is_applicable(roomref):
                usage.extend(bot.usage())

        usage_text = '\n'.join(usage)
        msg = f'Usage:\n```{usage_text}```'
        await self.master.client.send_message(message.rid, msg)
