from __future__ import annotations

import datetime
from typing import Any, Dict

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


def _parse_datetime(value: Any) -> datetime.datetime:
    """Try to parse the value into a Datetime, otherwise raise a RocketBotException
    Supported types:
    - iso string
    - datetime
    - { '$date': time_in_milliseconds_since_epoch }
    """
    if isinstance(value, str):
        return dateutil.parser.parse(value)
    if isinstance(value, datetime.datetime):
        return value
    if '$date' in value:
        millis = value['$date']
        return _millis_to_datetime(millis, _server_tz)
    raise exp.RocketBotException(f'Unable to parse Datetime. Value: "{value}"')


class RcDatetime:
    """Datetime wrapper class which handles the timezone and rocketchat
    specific conversion stuff
    """
    def __init__(self, value: datetime.datetime) -> None:
        self.value = _parse_datetime(value)

    def __repr__(self) -> str:
        return self.value.astimezone(_local_tz).isoformat()

    @staticmethod
    def now() -> RcDatetime:
        return RcDatetime(datetime.datetime.now())

    def is_today(self) -> bool:
        return datetime.datetime.today().date() == self.value.date()


@ejson.register_serializer(RcDatetime)
def _serialize_rcdatetime(instance: RcDatetime) -> Dict[str, float]:
    """Returns the value in the rocketchat date format"""
    return {"$date": _datetime_to_millis(instance.value.astimezone(_server_tz))}
