import asyncio
from typing import AsyncIterable, Dict

import pytest
from rocketchat_API.rocketchat import RocketChat

import rocketbot.client as client
import rocketbot.models as m


def setup_module() -> None:
    m.STRICT_MODE = True


def teardown_module() -> None:
    m.STRICT_MODE = False


@pytest.yield_fixture
async def ddpclient(event_loop: asyncio.AbstractEventLoop) -> AsyncIterable[client.Client]:
    ddpclient = client.Client('ws://localhost:3000/websocket', event_loop)
    await ddpclient.connect()

    yield ddpclient

    await ddpclient.disconnect()


@pytest.fixture
def exisiting_user() -> Dict[str, str]:
    rocket = RocketChat()
    user = {
        'username': 'testbot',
        'name': 'saBOTeur',
        'password': '1234',
        'email': 'email@domain.com',
    }
    rocket.users_register(**user)
    return user


@pytest.mark.asyncio
async def test_basic_connect_disconnect(event_loop: asyncio.AbstractEventLoop) -> None:
    ws_url = 'ws://localhost:3000/websocket'
    ddpclient = client.Client(ws_url, event_loop)

    await ddpclient.connect()

    await ddpclient.disconnect()


@pytest.mark.asyncio
async def test_login(ddpclient: client.Client, exisiting_user: Dict[str, str]) -> None:
    await ddpclient.login(exisiting_user['username'], exisiting_user['password'])
    # TODO check result (esp. if all fields are mapped)
