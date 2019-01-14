from typing import List, Any

import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m


class Prefix(c.BaseCommand):
    def __init__(self, bot: b.BaseBot):
        self.bot = bot
        self.enable_public_channel = False
        self.enable_private_group = False
        self.enable_direct_message = False
        self.prefixes: List[Any] = []

    def is_applicable(self, room: m.RoomRef2) -> bool:
        if room.roomType == m.RoomType.PUBLIC and self.enable_public_channel:
            return True
        if room.roomType == m.RoomType.PRIVATE and self.enable_private_group:
            return True
        if room.roomType == m.RoomType.DIRECT and self.enable_direct_message:
            return True
        return False

    async def handle(self, message: m.Message) -> bool:
        if not message.msg:
            return True
        command = message.msg.split()[0].lower()
        args = message.msg[len(command):].lstrip()

        for commands, callback in self.prefixes:
            if command in commands:
                result = await callback(args, message)
                if result:
                    return True
        return False
