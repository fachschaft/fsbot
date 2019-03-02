import dataclasses

from typing import Any, Dict, Optional, Type, TypeVar, overload

import rocketbot.exception as exp
from rocketbot.models.enums import (MessageType, RoleType, RoomType)

from rocketbot.models.apiobjects import (
    Attachment, File, Message, Room, RoomRef, RoomRef2,
    UserRef
)
from rocketbot.models.clientresults import (
    GetRoomsResult, LoadHistoryResult, LoginResult, SubscriptionResult
)
from rocketbot.models.rcdatetime import RcDatetime

T = TypeVar('T')


def create(cls_: Type[T], value: Any, *, default: Optional[T] = None) -> T:
    """Create an object if value is not None. Otherwise return default if given or
    raise an exception
    """
    print(f'In create: {value}')
    if value is not None:
        if dataclasses.is_dataclass(cls_):
            return cls_(**value)
        else:
            return cls_(value)
    if default is not None:
        return default
    raise exp.RocketBotException(f'Unable to create {cls_.__class__.__name__}')


def try_create(cls_: Type[T], value: Any) -> Optional[T]:
    """Try creating an object if value is not None. If value is None return None
    """
    if value is None:
        return None
    return create(cls_, value)
