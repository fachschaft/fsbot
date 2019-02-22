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
    raise TypeError(repr(data) + " is not JSON serializable")


ejson._converter = new_converter
