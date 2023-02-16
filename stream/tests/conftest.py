import asyncio
import os
import sys
import pytest_asyncio
from uuid import uuid4


from stream import connect


def wrapper(meth):
    async def _parse_response(*args, **kwargs):
        response = await meth(*args, **kwargs)
        assert "duration" in response
        return response

    return _parse_response


@pytest_asyncio.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
def user1(async_client):
    return async_client.feed("user", f"1-{uuid4()}")


@pytest_asyncio.fixture
def user2(async_client):
    return async_client.feed("user", f"2-{uuid4()}")


@pytest_asyncio.fixture
def aggregated2(async_client):
    return async_client.feed("aggregated", f"2-{uuid4()}")


@pytest_asyncio.fixture
def aggregated3(async_client):
    return async_client.feed("aggregated", f"3-{uuid4()}")


@pytest_asyncio.fixture
def topic(async_client):
    return async_client.feed("topic", f"1-{uuid4()}")


@pytest_asyncio.fixture
def flat3(async_client):
    return async_client.feed("flat", f"3-{uuid4()}")
