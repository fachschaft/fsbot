import datetime
import pytz
import pytz.tzinfo

import ejson
import tzlocal

# Rocketchat uses the server timezone as reference
_server_tz = pytz.timezone("Europe/Berlin")
_local_tz = tzlocal.get_localzone()
_epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.UTC)


def _datetime_to_millis(dt: datetime.datetime):
    return (dt - _epoch.astimezone(dt.tzinfo)).total_seconds() * 1000


def _millis_to_datetime(millis: int, tz: pytz.tzinfo.DstTzInfo):
    return datetime.datetime.fromtimestamp(millis / 1000, _server_tz)


class RcDatetime:
    """Datetime wrapper class which handles the timezone and rocketchat
    specific conversion stuff
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value.astimezone(_local_tz).isoformat()

    @staticmethod
    def from_server(value):
        """Factory function for date objects from the server.
        Dateobjects from rocketchat look like this:
        date = { '$date': time_in_milliseconds_since_epoch}
        """
        if value is None or '$date' not in value:
            return None
        millis = value['$date']
        return RcDatetime(_millis_to_datetime(millis, _server_tz))


@ejson.register_serializer(RcDatetime)
def _serialize_rcdatetime(instance) -> dict:
    """Returns the value in the rocketchat date format"""
    return {"$date": _datetime_to_millis(instance.value.astimezone(_server_tz))}
