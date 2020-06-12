import datetime
import json

import pytz

"""
Adds the ability to send date and datetime objects to the API
Datetime objects will be encoded/ decoded with microseconds
The date and datetime formats from the API are automatically supported and parsed
"""
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
DATE_FORMAT = "%Y-%m-%d"


def _datetime_encoder(obj):
    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is None:  # 3.5
            obj = pytz.utc.localize(obj)
        return datetime.datetime.strftime(obj.astimezone(pytz.utc), DATETIME_FORMAT)
    if isinstance(obj, datetime.date):
        return datetime.datetime.strftime(obj, DATE_FORMAT)
    return None


def _datetime_decoder(dict_):
    for key, value in dict_.items():
        # The built-in `json` library will `unicode` strings, except for empty
        # strings which are of type `str`. `jsondate` patches this for
        # consistency so that `unicode` is always returned.
        if value == "":
            dict_[key] = ""
            continue

        if value is not None and isinstance(value, str):
            try:
                # The api always returns times like this
                # 2014-07-25T09:12:24.735
                datetime_obj = pytz.utc.localize(
                    datetime.datetime.strptime(value, DATETIME_FORMAT)
                )
                dict_[key] = datetime_obj
            except (ValueError, TypeError):
                try:
                    # The api always returns times like this
                    # 2014-07-25T09:12:24.735
                    datetime_obj = pytz.utc.localize(
                        datetime.datetime.strptime(value, DATE_FORMAT)
                    )
                    dict_[key] = datetime_obj.date()
                except (ValueError, TypeError):
                    continue
    return dict_


def dumps(*args, **kwargs):
    kwargs["default"] = _datetime_encoder
    return json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs["object_hook"] = _datetime_decoder
    return json.loads(*args, **kwargs)
