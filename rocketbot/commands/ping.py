from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.models as m


class Ping(c.BaseCommand):
    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('ping', 'Reply with "Pong"'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['ping', 'pong']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command == 'ping':
            await self.master.ddp.send_message(message.roomid, 'Pong')
        if command == 'pong':
            await self.master.ddp.send_message(message.roomid, 'Ping')
