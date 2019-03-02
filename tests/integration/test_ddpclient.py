import asyncio
from typing import AsyncIterable, Dict

import pytest
from rocketchat_API.rocketchat import RocketChat

import rocketbot.client as c
import rocketbot.models as m

from ..utils import random_string


def setup_module() -> None:
    m.STRICT_MODE = True


def teardown_module() -> None:
    m.STRICT_MODE = False


@pytest.yield_fixture
async def anonym_client(event_loop: asyncio.AbstractEventLoop) -> AsyncIterable[c.Client]:
    client = c.Client('ws://localhost:3000/websocket', event_loop)
    await client.connect()

    yield client

    await client.disconnect()


@pytest.yield_fixture
async def client(anonym_client: c.Client, exisiting_user: Dict[str, str]) -> AsyncIterable[c.Client]:
    await anonym_client.login(exisiting_user['username'], exisiting_user['password'])

    yield anonym_client


@pytest.fixture
def exisiting_user() -> Dict[str, str]:
    rocket = RocketChat()
    username = random_string(10)
    user = {
        'username': username,
        'name': random_string(10),
        'password': random_string(10),
        'email': f'{username}@example.com',
    }
    rocket.users_register(**user).json()
    return user


@pytest.fixture
def exisiting_channel() -> str:
    rocket = RocketChat()
    room = rocket.channels_create(random_string(10)).json()['channel']
    return room['_id']


@pytest.mark.asyncio
async def test_basic_connect_disconnect(event_loop: asyncio.AbstractEventLoop) -> None:
    ws_url = 'ws://localhost:3000/websocket'
    client = c.Client(ws_url, event_loop)

    await client.connect()

    await client.disconnect()


@pytest.mark.asyncio
async def test_login(anonym_client: c.Client, exisiting_user: Dict[str, str]) -> None:
    loginresult = await anonym_client.login(exisiting_user['username'], exisiting_user['password'])
    assert loginresult is not None


@pytest.mark.asyncio
async def test_send_message(client: c.Client, exisiting_channel: str) -> None:
    msg = await client.send_message(exisiting_channel, 'testmessage')
    assert msg is not None
