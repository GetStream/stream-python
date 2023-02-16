import os
import re

__author__ = "Thierry Schellenbach"
__copyright__ = "Copyright 2022, Stream.io, Inc"
__credits__ = ["Thierry Schellenbach, mellowmorning.com, @tschellenbach"]
__license__ = "BSD-3-Clause"
__version__ = "5.2.0"
__maintainer__ = "Thierry Schellenbach"
__email__ = "support@getstream.io"
__status__ = "Production"


def connect(
    api_key=None,
    api_secret=None,
    app_id=None,
    version="v1.0",
    timeout=3.0,
    location=None,
    base_url=None,
    use_async=False,
):
    """
    Returns a Client object

    :param api_key: your api key or heroku url
    :param api_secret: the api secret
    :param app_id: the app id (used for listening to feed changes)
    :param use_async: flag to set AsyncClient
    """
    from stream.client import AsyncStreamClient, StreamClient

    stream_url = os.environ.get("STREAM_URL")
    # support for the heroku STREAM_URL syntax
    if stream_url and not api_key:
        pattern = re.compile(
            r"https\:\/\/(\w+)\:(\w+)\@([\w-]*).*\?app_id=(\d+)", re.IGNORECASE
        )
        result = pattern.match(stream_url)
        if result and len(result.groups()) == 4:
            api_key, api_secret, location, app_id = result.groups()
            location = None if location in ("getstream", "stream-io-api") else location
        else:
            raise ValueError("Invalid api key or heroku url")

    if use_async:
        return AsyncStreamClient(
            api_key,
            api_secret,
            app_id,
            version,
            timeout,
            location=location,
            base_url=base_url,
        )

    return StreamClient(
        api_key,
        api_secret,
        app_id,
        version,
        timeout,
        location=location,
        base_url=base_url,
    )
