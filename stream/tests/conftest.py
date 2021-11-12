import asyncio
import os
import sys

import pytest

from stream import connect


def wrapper(meth):
    async def _parse_response(*args, **kwargs):
        response = await meth(*args, **kwargs)
        assert "duration" in response
        return response

    return _parse_response


@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    key = os.getenv("STREAM_KEY")
    secret = os.getenv("STREAM_SECRET")
    if not key or not secret:
        print(
            "To run the tests the STREAM_KEY and STREAM_SECRET variables "
            "need to be available. \n"
            "Please create a pull request if you are an external "
            "contributor, because these variables are automatically added "
            "by Travis."
        )
        sys.exit(1)

    client = connect(key, secret, location="qa", timeout=30, use_async=True)
    wrapper(client._parse_response)
    yield client


@pytest.fixture
def user1(async_client):
    return async_client.feed("user", "1")


@pytest.fixture
def user2(async_client):
    return async_client.feed("user", "2")


@pytest.fixture
def aggregated2(async_client):
    return async_client.feed("aggregated", "2")


@pytest.fixture
def aggregated3(async_client):
    return async_client.feed("aggregated", "3")


@pytest.fixture
def topic(async_client):
    return async_client.feed("topic", "1")


@pytest.fixture
def flat3(async_client):
    return async_client.feed("flat", "3")
