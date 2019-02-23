import datetime
from typing import Any, Dict, Optional, overload

import dateutil.parser
import ejson
import pytz
import pytz.tzinfo
import tzlocal

import rocketbot.exception as exp

# Rocketchat uses the server timezone as reference
_server_tz = pytz.timezone("Europe/Berlin")
_local_tz = tzlocal.get_localzone()
_epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.UTC)


def _datetime_to_millis(dt: datetime.datetime) -> float:
    return (dt - _epoch.astimezone(dt.tzinfo)).total_seconds() * 1000


def _millis_to_datetime(millis: int, tz: pytz.tzinfo.DstTzInfo) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(millis / 1000, tz)


class RcDatetime:
    """Datetime wrapper class which handles the timezone and rocketchat
    specific conversion stuff
    """
    def __init__(self, value: datetime.datetime) -> None:
        self.value = value

    def __repr__(self) -> str:
        return self.value.astimezone(_local_tz).isoformat()

    @overload  # noqa: F811, see https://github.com/PyCQA/pyflakes/issues/434
    @staticmethod
    def from_server(value: 'RcDatetime') -> 'RcDatetime':
        pass

    @overload  # noqa: F811
    @staticmethod
    def from_server(value: None) -> None:
        pass

    @staticmethod  # noqa: F811
    def from_server(value: Any) -> Optional['RcDatetime']:
        """Factory function for date objects from the server.
        Dateobjects from rocketchat look like this:
        date = { '$date': time_in_milliseconds_since_epoch}
        """
        if value is None:
            return None
        if type(value) == str:
            return RcDatetime(dateutil.parser.parse(value))
        # tmp = cast(Dict[str, int], value)
        if '$date' in value:
            millis = value['$date']
            return RcDatetime(_millis_to_datetime(millis, _server_tz))
        raise exp.RocketBotException(f'Unkown RcDatetime format: "{value}"')

    @staticmethod
    def now() -> 'RcDatetime':
        return RcDatetime(datetime.datetime.now())

    def is_today(self) -> bool:
        return datetime.datetime.today().date() == self.value.date()


@ejson.register_serializer(RcDatetime)
def _serialize_rcdatetime(instance: RcDatetime) -> Dict[str, float]:
    """Returns the value in the rocketchat date format"""
    return {"$date": _datetime_to_millis(instance.value.astimezone(_server_tz))}
