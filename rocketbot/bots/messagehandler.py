from typing import List, Tuple

import rocketbot.bots.base as b
import rocketbot.models as m
import rocketbot.utils.usage as usage


class PrefixCommandMixin(b.BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._commands = self._init_value(kwargs, 'commands')
        self._show_usage_on_unknown = self._init_value(kwargs, 'show_usage_on_unknown', default=True)

    def usage(self) -> List[Tuple[str, str]]:
        res: List[Tuple[str, str]] = []
        for c in self._commands:
            res.extend(c.usage())
        return res

    async def handle(self, message: m.Message) -> None:
        if not message.msg:
            return
        command = message.msg.split()[0].lower()
        args = message.msg[len(command):].lstrip()

        for com in self._commands:
            if com.can_handle(command):
                await com.handle(command, args, message)
                return
        if self._show_usage_on_unknown:
            room = await self.master.room(message.rid)
            roomref = room.to_roomref2(True)

            msg = await usage.get_message(self.master, roomref)
            await self.master.client.send_message(message.rid, msg)


class CustomHandlerMixin(b.BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._callback = self._init_value(kwargs, 'callback')

    async def handle(self, message: m.Message) -> None:
        await self._callback(message)
