import datetime
import json
import six

'''
Adds the ability to send date and datetime objects to the API
The date and datetime formats from the API are automatically supported and parsed
'''


def _datetime_encoder(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()


def _datetime_decoder(dict_):
    for key, value in dict_.items():
        # The built-in `json` library will `unicode` strings, except for empty
        # strings which are of type `str`. `jsondate` patches this for
        # consistency so that `unicode` is always returned.
        if value == '':
            dict_[key] = u''
            continue

        if value is not None and isinstance(value, six.string_types):
            try:
                # The api always returns times like this
                # 2014-07-25T09:12:24.735
                datetime_obj = datetime.datetime.strptime(
                    value, "%Y-%m-%dT%H:%M:%S.%f")
                dict_[key] = datetime_obj
            except (ValueError, TypeError):
                try:
                    # The api always returns times like this
                    # 2014-07-25T09:12:24.735
                    datetime_obj = datetime.datetime.strptime(
                        value, "%Y-%m-%d")
                    dict_[key] = datetime_obj.date()
                except (ValueError, TypeError):
                    continue
    return dict_


def dumps(*args, **kwargs):
    kwargs['default'] = _datetime_encoder
    return json.dumps(*args, **kwargs)


def loads(*args, **kwargs):
    kwargs['object_hook'] = _datetime_decoder
    return json.loads(*args, **kwargs)
