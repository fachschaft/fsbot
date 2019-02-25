from __future__ import annotations

import abc
from typing import Any, List, Tuple

import rocketbot.master as master
import rocketbot.models as m


class BaseBot(abc.ABC):
    def __init__(self, *, master: master.Master, **kwargs: Any):
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

    def _init_value(self, kwargs: Any, key: str, default: Any = None) -> Any:
        if key in kwargs:
            return kwargs[key]
        if default is not None:
            return default
        raise ValueError(f'{key} missing for {self.__class__.__name__}.')
