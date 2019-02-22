import datetime
import pytz
import pytz.tzinfo
from typing import Any

import ejson
import tzlocal

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

    @staticmethod
    def from_server(value: Any) -> 'RcDatetime':
        """Factory function for date objects from the server.
        Dateobjects from rocketchat look like this:
        date = { '$date': time_in_milliseconds_since_epoch}
        """
        millis = value['$date']
        return RcDatetime(_millis_to_datetime(millis, _server_tz))

    @staticmethod
    def now() -> 'RcDatetime':
        return RcDatetime(datetime.datetime.now())

    def is_today(self) -> bool:
        return datetime.datetime.today().date() == self.value.date()


@ejson.register_serializer(RcDatetime)
def _serialize_rcdatetime(instance: RcDatetime) -> dict:
    """Returns the value in the rocketchat date format"""
    return {"$date": _datetime_to_millis(instance.value.astimezone(_server_tz))}
