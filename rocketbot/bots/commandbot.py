import asyncio
from typing import List

import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m


class CommandBot(b.BaseBot):
    """The command bot implements a bot which can react to certain commands.

    Commands can but must not be prefix commands. Simply add commands which
    directly or indirectly inherit from BaseCommand to the _commands list.
    """
    def __init__(self, url, username, password, loop=asyncio.get_event_loop()):
        super().__init__(url, username, password, loop)
        self._commands: List[c.BaseCommand] = [c.Usage(self), c.Ping(self), c.Poll(self)]

    async def __aenter__(self):
        await super().__aenter__()

        await self.activate_commands()

        return self

    async def activate_commands(self) -> None:
        """Activate commands by subscribing the following callback to all messages
        """
        async def command_callback(result: m.SubscriptionResult):
            # Ignore own messages
            if result.message.u.username == self.username:
                return

            # Ignore public unjoined rooms
            room = result.room
            if not room or not room.roomParticipant:
                return

            # Ignore messages without mention for non-direct messages
            if room.roomType != m.RoomType.DIRECT:
                msg = result.message.msg.lstrip()
                if msg.startswith(self.username) or msg.startswith(f'@{self.username}'):
                    result.message.msg = " ".join((msg.split(self.username)[1:])).lstrip()
                else:
                    return

            for com in self._commands:
                if com.is_applicable(room):
                    if await com.handle(result.message):
                        return
            await self.send_message(result.message.rid, 'Unknown command. Type "usage" for help')

        await self.subscribe_my_messages(command_callback)
