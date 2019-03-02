import dataclasses
import enum
from typing import Any, Dict

import ejson


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
    raise TypeError(repr(data) + " is not JSON serializable")


ejson._converter = new_converter
