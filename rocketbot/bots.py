import abc  # Abstract Base Class
import copy

import rocketbot.master as master
import rocketbot.models as m


def _init_value(cls, kwargs, key, default=None):
    if key in kwargs:
        return kwargs[key]
    if default is not None:
        return default
    raise ValueError(f'{key} missing for {cls.__name__}.')


class BaseBot(abc.ABC):
    def __init__(self, *, master: master.Master, **kwargs):
        self.master = master

    @abc.abstractmethod
    def is_applicable(self, room: m.RoomRef2) -> bool:
        """Check whether the bot is applicable for the room.
        """
        return True

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

    async def handle(self, message: m.Message):
        command = message.msg.split()[0].lower()
        args = message.msg[len(command):].lstrip()

        for com in self._commands:
            if com.can_handle(command):
                await com.handle(command, args, message)
                return
        if self._show_usage_on_unknown:
            await self.master.client.send_message(message.rid, 'Unknown command. Type "usage" for help')


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
