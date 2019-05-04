import asyncio
from typing import AsyncIterable

import pytest

import rocketbot.client as c
import rocketbot.models as m


def setup_module() -> None:
    # Enable strict mode for ddpclient test to find new fields
    # Strict mode checks if all incoming fields are used by the object model
    m.STRICT_MODE = True


def teardown_module() -> None:
    m.STRICT_MODE = False


@pytest.yield_fixture
async def anonym_client(event_loop: asyncio.AbstractEventLoop) -> AsyncIterable[c.DdpClient]:
    client = c.DdpClient('ws://localhost:3000/websocket', event_loop)
    await client.connect()

    yield client

    await client.disconnect()


@pytest.yield_fixture
async def client(anonym_client: c.DdpClient, user_user: m.User) -> AsyncIterable[c.DdpClient]:
    await anonym_client.login(user_user.username, user_user.username)

    yield anonym_client


@pytest.mark.asyncio
async def test_basic_connect_disconnect(event_loop: asyncio.AbstractEventLoop) -> None:
    ws_url = 'ws://localhost:3000/websocket'
    client = c.DdpClient(ws_url, event_loop)

    await client.connect()

    await client.disconnect()


@pytest.mark.asyncio
async def test_login(anonym_client: c.DdpClient, user_user: m.User) -> None:
    loginresult = await anonym_client.login(user_user.username, user_user.username)
    assert loginresult is not None


@pytest.mark.asyncio
async def test_send_message(client: c.DdpClient, public_channel: m.Room) -> None:
    msg = await client.send_message(public_channel._id, 'testmessage')
    assert msg is not None
