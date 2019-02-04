import ejson
from rocketchat_API.rocketchat import RocketChat
from rocketchat_API.APIExceptions.RocketExceptions import RocketMissingParamException


def new_converter(data):
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


def _rooms_info(self, room_id=None, room_name=None, **kwargs):
    """
    WORKAROUND: Patch Restapi until its updated
    """
    if room_id:
        return RocketChat._RocketChat__call_api_get(self, 'rooms.info', roomId=room_id, kwargs=kwargs)
    elif room_name:
        return RocketChat._RocketChat__call_api_get(self, 'rooms.info', roomName=room_name, kwargs=kwargs)
    else:
        raise RocketMissingParamException('roomId or roomName required')


RocketChat.rooms_info = _rooms_info
