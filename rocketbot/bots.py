import abc  # Abstract Base Class
import copy
from typing import List, Tuple

import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.usage as usage


def _init_value(cls, kwargs, key, default=None):
    if key in kwargs:
        return kwargs[key]
    if default is not None:
        return default
    raise ValueError(f'{key} missing for {cls.__name__}.')


class BaseBot(abc.ABC):
    def __init__(self, *, master: master.Master, **kwargs):
        self.master = master

    def is_applicable(self, room: m.RoomRef2) -> bool:
        """Check whether the bot is applicable for the room.
        """
        return True

    def usage(self) -> List[Tuple[str, str]]:
        """Usage text for this bot
        """
        return []

    @abc.abstractmethod
    async def handle(self, message: m.Message) -> None:
        """Handle the incoming message
        """
        pass


class IgnoreOwnMsgMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username: str = _init_value(IgnoreOwnMsgMixin, kwargs, 'username')

    async def handle(self, message: m.Message) -> None:
        if message.u.username != self.username:
            await super().handle(message)


class MentionMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username: str = _init_value(MentionMixin, kwargs, 'username')

    def usage(self) -> List[Tuple[str, str]]:
        return [(f'@{self.username} {command}', desc) for command, desc in super().usage()]

    async def handle(self, message: m.Message) -> None:
        msg = message.msg.lstrip()
        if msg.startswith(self.username) or msg.startswith(f'@{self.username}'):
            message = copy.deepcopy(message)
            message.msg = " ".join((msg.split(self.username)[1:])).lstrip()
            await super().handle(message)


class PrefixCommandMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._commands = _init_value(PrefixCommandMixin, kwargs, 'commands')
        self._show_usage_on_unknown = _init_value(PrefixCommandMixin, kwargs, 'show_usage_on_unknown', default=True)

    def usage(self) -> List[Tuple[str, str]]:
        res: List[Tuple[str, str]] = []
        for c in self._commands:
            res.extend(c.usage())
        return res

    async def handle(self, message: m.Message):
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


class CustomHandlerMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._callback = _init_value(CustomHandlerMixin, kwargs, 'callback')

    async def handle(self, message: m.Message):
        await self._callback(message)


class RoomMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rooms = set(_init_value(RoomMixin, kwargs, 'rooms'))

    def is_applicable(self, room: m.RoomRef2) -> bool:
        if room.roomName and room.roomName in self.rooms:
            return super().is_applicable(room)
        return False


class RoomTypeMixin(BaseBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enable_public_channel = _init_value(RoomTypeMixin, kwargs, 'enable_public_channel', False)
        self.enable_private_group = _init_value(RoomTypeMixin, kwargs, 'enable_private_group', False)
        self.enable_direct_message = _init_value(RoomTypeMixin, kwargs, 'enable_direct_message', False)
        if self.enable_public_channel or self.enable_private_group or self.enable_direct_message:
            pass
        else:
            raise ValueError('Must enable at lease one room type')

    def is_applicable(self, room: m.RoomRef2) -> bool:
        if room.roomType == m.RoomType.PUBLIC and self.enable_public_channel:
            return super().is_applicable(room)
        if room.roomType == m.RoomType.PRIVATE and self.enable_private_group:
            return super().is_applicable(room)
        if room.roomType == m.RoomType.DIRECT and self.enable_direct_message:
            return super().is_applicable(room)
        return False


class RoomCommandBot(IgnoreOwnMsgMixin, RoomMixin, PrefixCommandMixin):
    pass


class RoomTypeCommandBot(IgnoreOwnMsgMixin, RoomTypeMixin, PrefixCommandMixin):
    pass


class RoomTypeMentionCommandBot(IgnoreOwnMsgMixin, RoomTypeMixin, MentionMixin, PrefixCommandMixin):
    pass


class RoomCustomBot(RoomMixin, CustomHandlerMixin):
    pass
