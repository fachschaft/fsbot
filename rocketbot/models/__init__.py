import re
from typing import Any, Callable, TypeVar

from rocketbot.models.rcdatetime import RcDatetime  # noqa: F401
from rocketbot.models.apiobjects import Message, MessageType, RoleType, Room, RoomRef, RoomRef2, RoomType, UserRef  # noqa: F401
from rocketbot.models.clientresults import *  # noqa: F401, F403


T = TypeVar('T')


def create(ctor: Callable[..., T], kwargs: Any) -> T:
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
