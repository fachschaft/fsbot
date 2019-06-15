import asyncio
from typing import Iterable, List

import pytest
from rocketchat_API.rocketchat import RocketChat

import rocketbot.master as master
import rocketbot.models as m

from ..utils import random_string

_admin_user = None


@pytest.fixture(scope="module", autouse=True)
def setup_admin() -> None:
    """This function is executed before any integration test is run.

    The admin is created here because the first user is by default admin
    """

    global _admin_user

    # This function uses the default RocketChat Client because it cannot be async and
    # since this is the first function it cannot break due to the ratelimiter
    rest = RocketChat()
    result = rest.users_register(
        username='admin',
        name='Administrator',
        email='admin@example.com',
        password='admin').json()
    if result['success']:
        _admin_user = m.create(m.User, result['user'])
    else:
        rest.login(user='admin', password='admin')
        result = rest.users_info(username='admin').json()
        _admin_user = m.create(m.User, result['user'])


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
def admin_user() -> m.User:
    if _admin_user is None:
        raise Exception("Admin user is not set up correctly")
    return _admin_user


@pytest.fixture
async def admin(admin_user: m.User, event_loop: asyncio.AbstractEventLoop) -> master.Master:
    _admin = master.Master(
        'http://localhost:3000', admin_user.username,
        admin_user.username, tls=False, loop=event_loop)
    await _admin.rest.login(admin_user.username, admin_user.username)
    return _admin


@pytest.fixture
async def bot_user(admin: master.Master) -> m.User:
    return await _get_or_create_user(admin, 'bot', 'saBOTeur', roles=['bot'])


@pytest.fixture
async def bot(bot_user: m.User, event_loop: asyncio.AbstractEventLoop) -> master.Master:
    _bot = master.Master('http://localhost:3000', bot_user.username, bot_user.username, tls=False, loop=event_loop)
    await _bot.rest.login(bot_user.username, bot_user.username)
    return _bot


@pytest.fixture
async def user_user(admin: master.Master) -> m.User:
    return await _get_or_create_user(admin, 'user', 'FirstUser')


@pytest.fixture
async def user(user_user: m.User, event_loop: asyncio.AbstractEventLoop) -> master.Master:
    _user = master.Master('http://localhost:3000', user_user.username, user_user.username, tls=False, loop=event_loop)
    await _user.rest.login(user_user.username, user_user.username)
    return _user


@pytest.fixture
async def public_channel(admin: master.Master) -> m.Room:
    return await _get_or_create_public_room(admin, random_string(10))


@pytest.fixture
async def statusroom(admin: master.Master) -> m.Room:
    return await _get_or_create_public_room(admin, 'pollstatusroom')


@pytest.fixture
async def private_group(admin: master.Master) -> m.Room:
    return await _get_or_create_private_group(admin, random_string(10))


async def _get_or_create_user(
        master: master.Master,
        username: str,
        displayname: str,
        *,
        roles: List[str] = ['user']) -> m.User:

    result = (await master.rest.users_info(username=username)).json()
    if not result['success']:
        result = (await master.rest.users_create(
            username=username,
            name=displayname,
            email=f'{username}@example.com',
            password=username,
            roles=roles
        )).json()

    return m.create(m.User, result['user'])


async def _get_or_create_public_room(master: master.Master, roomname: str) -> m.Room:
    result = (await master.rest.channels_info(channel=roomname)).json()
    if not result['success']:
        result = (await master.rest.channels_create(name=roomname)).json()

    return m.create(m.Room, result['channel'])


async def _get_or_create_private_group(master: master.Master, roomname: str) -> m.Room:
    result = (await master.rest.groups_info(room_name=roomname)).json()
    if not result['success']:
        result = (await master.rest.groups_create(name=roomname)).json()

    return m.create(m.Room, result['group'])
