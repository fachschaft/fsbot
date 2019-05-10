import dataclasses
import enum
import logging
import re
from typing import Any, Dict, Optional, Type, TypeVar, cast, overload

import ejson

import rocketbot.exception as exp
import rocketbot.utils.sentry as sentry
from rocketbot.models.apiobjects import (
    ApiObject, Attachment, File, Message, Room, RoomRef, RoomRef2, User,
    UserRef
)
from rocketbot.models.clientresults import (
    GetRoomsResult, LoadHistoryResult, LoginResult, SubscriptionResult
)
from rocketbot.models.enums import MessageType, RoleType, RoomType
from rocketbot.models.rcdatetime import RcDatetime

logger = logging.getLogger(__name__)


def new_converter(data: Any) -> Dict[str, Any]:
    """Patch the ejson._converter because the data should
    be serialized as dict and not wrapped into

    {
        '__class__': full_name,
        '__value__': handler(data),
    }
    """
    handler = ejson.REGISTRY.get(data.__class__)
    if handler:
        return handler(data)
    # Special case for dataclasses as the already have a designated serialization method
    if dataclasses.is_dataclass(data):
        return dataclasses.asdict(data)
    # Special case for enums
    if isinstance(data, enum.Enum):
        return data.value
    if isinstance(data, ApiObject):
        return data.asdict()
    raise TypeError(repr(data) + " is not JSON serializable")


ejson._converter = new_converter


# This flag controls the object creation mode
# False (default): Ignore additional fields when creating object
# True (e.g. for integration tests): Raise exception on additional fields
STRICT_MODE = False

T = TypeVar('T')


def create(cls_: Type[T], value: Any, *, default: Optional[T] = None) -> T:
    """Create an object if value is not None. Otherwise return default if given or
    raise an exception
    """
    if value is None:
        if default is None:
            raise exp.RocketBotException(f'Unable to create {cls_.__class__.__name__}')
        return default

    if dataclasses.is_dataclass(cls_):
        if STRICT_MODE:
            return cls_(**value)  # type: ignore
        return _save_dataclass_create(cls_, value)

    if STRICT_MODE and isinstance(cls_, ApiObject):
        given = set(value.keys())
        required = set(cls_.mapping.values())
        unexpected = given - required
        if unexpected:
            raise exp.RocketBotException(
                f'Unexpected keys found while creating {cls_.__class__.__name__}: {unexpected}')
    return cls_(value)  # type: ignore


def try_create(cls_: Type[T], value: Any) -> Optional[T]:
    """Try creating an object if value is not None. If value is None return None
    """
    if value is None:
        return None
    return create(cls_, value)


def _save_dataclass_create(cls_: Type[T], kwargs: Dict[str, Any]) -> T:
    try:
        return cls_(**kwargs)  # type: ignore
    except TypeError as e:
        pattern = r'__init__\(\) got an unexpected keyword argument \'([^\']+)\''
        m = re.match(pattern, e.__str__())
        if not m:
            raise e
        key = m.group(1)
        msg = f"Unexpected key '{key}' for {cls_.__name__}. Value was '{kwargs[key]}''"
        logger.warning(msg)
        sentry.message(msg)
        del kwargs[key]
        return _save_dataclass_create(cls_, kwargs)
    except ValueError as e:
        value = e.__str__().split("'")[1]
        key = [k for (k, v) in kwargs.items() if v == value][0]
        msg = f"Unexpected value '{value}' for '{key}' in {cls_.__name__}"
        logger.warning(msg)
        sentry.message(msg)
        del kwargs[key]
        return _save_dataclass_create(cls_, kwargs)
