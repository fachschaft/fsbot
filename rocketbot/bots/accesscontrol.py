from typing import Any

import rocketbot.bots.base as b
import rocketbot.models as m


class WhitelistRoomMixin(b.BaseBot):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.rooms = set(self._init_value(kwargs, 'whitelist'))
        self.whitelist_directmsgs = self._init_value(kwargs, 'whitelist_directmsgs', False)

    def is_applicable(self, room: m.RoomRef2) -> bool:
        # Direct messages do not have a room name
        if room.roomType == m.RoomType.DIRECT:
            if self.whitelist_directmsgs:
                return super().is_applicable(room)
            return False

        if room.roomName in self.rooms:
            return super().is_applicable(room)
        return False


class BlacklistRoomMixin(b.BaseBot):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.rooms = set(self._init_value(kwargs, 'blacklist'))

    def is_applicable(self, room: m.RoomRef2) -> bool:
        if room.roomName and room.roomName in self.rooms:
            return False
        return super().is_applicable(room)


class RoomTypeMixin(b.BaseBot):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.enable_public_channel = self._init_value(kwargs, 'enable_public_channel', False)
        self.enable_private_group = self._init_value(kwargs, 'enable_private_group', False)
        self.enable_direct_message = self._init_value(kwargs, 'enable_direct_message', False)
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
