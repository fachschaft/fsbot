import copy
from typing import List, Tuple

import rocketbot.bots.base as b
import rocketbot.models as m


class IgnoreOwnMsgMixin(b.BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username: str = self._init_value(kwargs, 'username')

    async def handle(self, message: m.Message) -> None:
        if message.u.username != self.username:
            await super().handle(message)


class MentionMixin(b.BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username: str = self._init_value(kwargs, 'username')

    def usage(self) -> List[Tuple[str, str]]:
        return [(f'@{self.username} {command}', desc) for command, desc in super().usage()]

    async def handle(self, message: m.Message) -> None:
        msg = message.msg.lstrip()
        if msg.startswith(self.username) or msg.startswith(f'@{self.username}'):
            message = copy.deepcopy(message)
            message.msg = " ".join((msg.split(self.username)[1:])).lstrip()
            await super().handle(message)