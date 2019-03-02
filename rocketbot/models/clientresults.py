from __future__ import annotations

import dataclasses
from typing import Any, List, Optional, cast

import rocketbot.models as models


@dataclasses.dataclass
class LoginResult:
    id: str
    token: str
    tokenExpires: models.RcDatetime
    type: str

    def __post_init__(self) -> None:
        self.tokenExpires = models.create(models.RcDatetime, self.tokenExpires)


@dataclasses.dataclass
class GetRoomsResult:
    update: List[models.Room]
    remove: List[models.Room]

    def __post_init__(self) -> None:
        self.update = [models.create(models.Room, r) for r in self.update]
        self.remove = [models.create(models.Room, r) for r in self.remove]


@dataclasses.dataclass
class LoadHistoryResult:
    messages: List[models.Message]
    unreadNotLoaded: int
    firstUnread: Optional[models.Message] = None

    def __post_init__(self) -> None:
        self.messages = [models.create(models.Message, m) for m in self.messages]
        self.firstUnread = models.create(models.Message, self.firstUnread)


@dataclasses.dataclass
class SubscriptionResult:
    eventName: str
    args: List[Any] = dataclasses.field(repr=False)
    message: models.Message = dataclasses.field(init=False)
    room: Optional[models.RoomRef2] = dataclasses.field(default=None, init=False)

    def __post_init__(self) -> None:
        arg0 = cast(models.Message, self.args[0])  # pylint: disable=E1136
        self.message = models.create(models.Message, arg0)
        if len(self.args) > 1:
            arg1 = cast(models.RoomRef2, self.args[1])  # pylint: disable=E1136
            self.room = models.create(models.RoomRef2, arg1)
