import asyncio

import pytest
from rocketchat_API.rocketchat import RocketChat

import rocketbot.master as master


@pytest.fixture
def masterbot(event_loop: asyncio.AbstractEventLoop) -> master.Master:
    rocket = RocketChat()
    username = 'testbot'
    name = 'saBOTeur'
    password = '1234'
    email = 'email@domain.com'
    rocket.users_register(email=email, name=name, password=password, username=username)

    return master.Master('http://localhost:3000', username, password, tls=False, loop=event_loop)


@pytest.mark.asyncio
async def test_basic_connect(masterbot: master.Master) -> None:
    async with masterbot:
        pass
    assert True
