import asyncio
from typing import List

import rocketbot.bots as b
import rocketbot.commands as c


class FsBot(b.CommandBot):
    """The fsbot is a commandbot with special adoptions:

    - Special commands for room 'mensa'
    """
    def __init__(self, url, username, password, mensa_room, loop=asyncio.get_event_loop()):
        super().__init__(url, username, password, loop)
        self.mensa_command = c.Mensa(self, mensa_room)
        self._commands.append(self.mensa_command)

    async def __aenter__(self):
        await super().__aenter__()

        await self.mensa_command.activate()

        return self
