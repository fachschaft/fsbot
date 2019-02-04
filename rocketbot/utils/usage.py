from typing import List

import rocketbot.master as master
import rocketbot.models as m


async def get_message(master: master.Master, room: m.RoomRef2) -> str:
    """Get usage message based on the room
    """
    usage: List[str] = []

    for bot in master.bots:
        if bot.is_applicable(room):
            usage.extend(bot.usage())

    usage_text = '\n'.join(usage)
    msg = f'Usage:\n```{usage_text}```'

    return msg
