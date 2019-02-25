from __future__ import annotations

from typing import List

import rocketbot.master as master
import rocketbot.models as m

PADDING = 5


async def get_message(master: master.Master, room: m.RoomRef2) -> str:
    """Get usage message based on the room
    """
    usage: List[str] = []

    for bot in master.bots:
        if not bot.is_applicable(room):
            continue
        for com, desc in bot.usage():
            usage.append(com)
            usage.append(' ' * PADDING + desc)
    usage_text = '\n'.join(usage)
    msg = f'Usage:\n```{usage_text}```'

    return msg
