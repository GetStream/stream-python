import asyncio

import pytest
from stream import connect


def wrapper(meth):
    async def _parse_response(*args, **kwargs):
        response = await meth(*args, **kwargs)
        assert "duration" in response
        return response

    return _parse_response


@pytest.fixture(scope="module")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    key = "n8udba92h9hf"
    secret = "5mjaw2a5bynt3fzdnxy2pwxh7fw89gg2dq3mm4jy56vhrwnadfst7yssatmaxhkv"
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
