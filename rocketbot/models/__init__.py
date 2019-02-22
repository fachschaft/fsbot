import re
from typing import Any, Dict, Optional, Type, TypeVar, overload

from rocketbot.models.rcdatetime import RcDatetime  # noqa: F401
from rocketbot.models.apiobjects import Message, MessageType, RoleType, Room, RoomRef, RoomRef2, RoomType, UserRef, File, Attachment  # noqa: F401
from rocketbot.models.clientresults import *  # noqa: F401, F403


T = TypeVar('T', Message, Room, UserRef, File, RoomRef2, Attachment)


@overload
def create(ctor: Any, kwargs: None) -> None:
    ...


@overload
def create(ctor: Type[T], kwargs: Dict[str, Any]) -> T:
    ...


@overload
def create(ctor: Type[T], kwargs: T) -> T:
    ...


def create(ctor: Type[T], kwargs: Any) -> Optional[T]:
    if kwargs is None:
        return None
    try:
        return ctor(**kwargs)
    except TypeError as e:
        pattern = r'__init__\(\) got an unexpected keyword argument \'([^\']+)\''
        m = re.match(pattern, e.__str__())
        if not m:
            raise e
        key = m.group(1)
        print(f"Unexpected key '{key}' for {ctor.__name__}. Value was '{kwargs[key]}''")
        del kwargs[key]
        return create(ctor, kwargs)
    except ValueError as e:
        value = e.__str__().split("'")[1]
        key = [k for (k, v) in kwargs.items() if v == value][0]
        print(f"Unexpected value '{value}' for '{key}' in {ctor.__name__}")
        del kwargs[key]
        return create(ctor, kwargs)
