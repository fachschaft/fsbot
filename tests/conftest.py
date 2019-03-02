import asyncio
import datetime
from typing import Iterable

import pytest
from rocketchat_API.rocketchat import RocketChat

import rocketbot.master as master
import rocketbot.models as m


@pytest.yield_fixture
def event_loop() -> Iterable[asyncio.AbstractEventLoop]:
    """Create an instance of the default event loop for each test case.
    Fixes: https://github.com/pytest-dev/pytest-asyncio/issues/29
    """
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    _close = res.close
    # Ignore mypy bug/limitation -> https://github.com/python/mypy/issues/2427
    res.close = lambda: None  # type: ignore

    yield res

    _close()


@pytest.fixture
def masterbot(event_loop: asyncio.AbstractEventLoop) -> master.Master:
    rocket = RocketChat()
    username = 'testbot'
    name = 'saBOTeur'
    password = '1234'
    email = 'email@domain.com'
    rocket.users_register(email=email, name=name, password=password, username=username)

    return master.Master('http://localhost:3000', username, password, tls=False, loop=event_loop)


@pytest.fixture
def message() -> m.Message:
    return m.Message({
        '_id': 'id',
        '_updatedAt': datetime.datetime.now().isoformat(),
        'rid': 'rid',
        'msg': '',
        'ts': datetime.datetime.now().isoformat(),
        'u': {'_id': '_id', 'username': 'username', 'name': 'name'}
    })
