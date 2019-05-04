from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.usage as usage


class Usage(c.BaseCommand):
    def usage(self) -> List[Tuple[str, str]]:
        return [('help | usage | ?', 'Print all available commands')]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['help', 'usage', '?']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        room = await self.master.room(room_id=message.roomid)
        roomref = room.to_roomref2(True)

        msg = await usage.get_message(self.master, roomref)
        await self.master.ddp.send_message(message.roomid, msg)
