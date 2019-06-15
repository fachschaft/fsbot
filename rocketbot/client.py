from __future__ import annotations

import asyncio
import functools
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

import aioify
import requests
from ddp_asyncio import DDPClient
from ddp_asyncio.exceptions import RemoteMethodError
from ddp_asyncio.subscription import Subscription
from rocketchat_API.rocketchat import RocketChat

import rocketbot.exception as exp
import rocketbot.models as m
import rocketbot.utils.sentry as sentry

logger = logging.getLogger(__name__)


class DdpClient:
    """RocketChat DdpClient

    Implements all available rocketchat methods and subscriptions
    """
    def __init__(self, address: str, loop: asyncio.AbstractEventLoop) -> None:
        self.logged_in = False
        self.client = DDPClient(address)
        self.subscription_tasks: List[asyncio.Task[Any]] = []
        self.subscriptions: Dict[str, Subscription] = {}
        self.loop = loop

    async def _call(self, method: str, *params: Any) -> Dict[str, Any]:
        while True:
            try:
                return await self.client.call(method, *params)
            except RemoteMethodError as e:
                match = re.match(r'.*?([0-9]+) seconds.*\[too-many-requests\]', e.args[0])
                if match:
                    logger.warning(f"DDPClient: Delay {method} for {match.groups()[0]}s due to rate limiter.")
                    await asyncio.sleep(int(match.groups()[0]))
                else:
                    raise

    async def connect(self) -> None:
        """Connect
        """
        await self.client.connect()

    async def disconnection(self) -> None:
        """Wait until the ddpclient disconnects
        """
        await self.client.disconnection()

    async def disconnect(self) -> None:
        """Disconnect by canceling all running subscription tasks
        """
        for task in self.subscription_tasks:
            task.cancel()
        await self.client.disconnect()

    async def login(self, username: str, password: str) -> m.LoginResult:
        """Login with the given credentials"""
        response = await self._call("login", {"user": {"username": username}, "password": password})
        self.logged_in = True
        return m.create(m.LoginResult, response)

    async def logout(self) -> None:
        """Logout"""
        if self.logged_in:
            await self._call("logout")
            self.logged_in = False

    # async def getUserRoles(self):
    #     """This method call is used to get server-wide special users and their
    #     roles. That information is used to identify key users on the server
    #     (ex.: admins).

    #     (Currently only returns admins)

    #     Returns:
    #         [
    #             {
    #                 '_id': 'noBbWB64vwJ7fgt2q',
    #                 'roles': ['admin'],
    #                 'username': 'admin'
    #             },
    #             ...
    #         ]
    #     """
    #     return await self._call("getUserRoles")

    # async def listEmojiCustom(self):
    #     """Returns a list of custom emoji registered with the server.

    #     Retrieve the custom emoji with:
    #     ${ path }/emoji-custom/${ encoded(name) } }.${ extension }.

    #     Eg.
    #     https://chat.fachschaft.tf/emoji-custom/ersti.png

    #     Returns:
    #         [
    #             {
    #                 '_id': 'GtqC2tbwPZvqir4W5',
    #                 'name': 'ersti',
    #                 'aliases': ['blb', 'bad_luck_brian', 'erstie'],
    #                 'extension': 'png',
    #                 '_updatedAt': {'$date': 1539586118866}
    #             },
    #             ...
    #         ]
    #     """
    #     return await self._call("listEmojiCustom")

    async def load_history(
            self, room_id: str, num_msgs: int = 50,
            until: Optional[m.RcDatetime] = None, from_: Optional[m.RcDatetime] = None) -> m.LoadHistoryResult:
        """Use this method to make the initial load of a room. After the initial
        load you may subscribe to the room messages stream.

        Loads messages starting from the newest until either the until-date is
        reached or num_msgs is exceeded. from_ can be used to specify a start
        date.

        num_msgs: the maximum number of loaded messages

        until: load all messages until this date. May be None.

        from_: load messages starting from this date. Useful for pagination. May be None
        """
        response = await self._call(
            "loadHistory", room_id, from_, num_msgs, until)
        if isinstance(response, dict):
            return m.LoadHistoryResult(**response)
        raise exp.RocketClientException("Cannot access room")

    # async def getRoomRoles(self, *room_ids):
    #     """This method call is used to get room-wide special users and their
    #     roles. You may send a collection of room ids (at least one).
    #     """
    #     return await self._call("getRoomRoles", room_ids)

    async def get_all_rooms(self) -> List[m.Room]:
        """Get all the rooms a user belongs to.
        """
        response = await self._call("rooms/get")
        return [m.create(m.Room, r) for r in response]

    async def get_rooms_since(self, date: m.RcDatetime) -> m.GetRoomsResult:
        """This is the method call used to get all the rooms a user belongs
        to. It accepts a timestamp with the latest client update time in order
        to just send what changed since last call.
        """
        response = await self._call("rooms/get", date)
        return m.GetRoomsResult(**response)

    async def create_direct_message(self, username: str) -> str:
        """Get the room id for a direct message with a user
        """
        response = await self._call("createDirectMessage", username)
        return response['rid']

    async def send_message(self, roomId: str, message: str) -> m.Message:
        """Send a message to a room
        """
        response = await self._call("sendMessage", {"rid": roomId, "msg": message})
        if response is None:
            raise exp.RocketClientException("Could not send message.")
        return m.create(m.Message, response)

    async def update_message(self, message: Union[m.Message, Dict[str, Any]]) -> None:
        """Update a message either by a message object or for partial updates only a
        dict with the relevant fields (_id is required)
        """
        await self._call("updateMessage", message)

    async def delete_message(self, messageId: str) -> None:
        """Delete a message
        """
        await self._call("deleteMessage", {"_id": messageId})

    async def set_reaction(self, emojiId: str, messageId: str, flag: Optional[bool] = None) -> None:
        """React to a message

        Flag:
            True = set reaction
            False = unset reaction
            None = toggle reaction
        """
        await self._call("setReaction", emojiId, messageId, flag)

    async def subscribe_room(
            self, roomId: str,
            callback: Callable[[m.SubscriptionResult], Awaitable[Any]]
    ) -> asyncio.Task[None]:
        """Subscribe for updates for the given room
        """
        col = self.client.get_collection('stream-room-messages')
        col._data['id'] = {}

        col_q = col.get_queue()
        task = self.loop.create_task(_subscription_handler_wrapper(col_q, roomId, callback))

        self.subscription_tasks.append(task)

        if roomId not in self.subscriptions:
            self.subscriptions[roomId] = await self.client.subscribe("stream-room-messages", roomId, True)
        return task

    async def subscribe_my_messages(self, callback: Callable[[m.SubscriptionResult], Awaitable[Any]]) -> Subscription:
        """Subscribe to the personal '__my_messages__' topic which receives updates for:
        - all public channels (joined and unjoined)
        - all joined private groups
        - all direct messages"""
        return await self.subscribe_room('__my_messages__', callback)


def _async_call_wrapper(func: Callable[..., requests.Response]) -> Callable[..., Awaitable[requests.Response]]:
    '''Takes a sync rest call function and wraps it. The returned function is awaitable and has
    a rate limiter protection/ prevention
    '''
    async_func = aioify.aioify(func)
    regex = re.compile(r'([0-9]+) seconds .*\[error-too-many-requests\]')

    @functools.wraps(func)
    async def _async_func_wrapper(*args: Any, **kwargs: Any) -> requests.Response:
        while True:
            response = await async_func(*args, **kwargs)
            if response.status_code != 429:
                return response
            msg = response.json().get('error')
            result = regex.search(msg)
            if result:
                seconds = result.groups()[0]
                await asyncio.sleep(int(seconds))
            else:
                raise exp.RocketClientException(msg)
    return _async_func_wrapper


class RestClient(RocketChat):  # type: ignore
    def _login_patch(self, user: str, password: str) -> requests.Response:
        '''Patch login function because it only returns the status_code on error'''
        login_request = requests.post(self.server_url + self.API_path + 'login',
                                      data={'username': user,
                                            'password': password},
                                      verify=self.ssl_verify,
                                      proxies=self.proxies)
        if login_request.status_code == 200:
            if login_request.json().get('status') == "success":
                self.headers['X-Auth-Token'] = login_request.json().get('data').get('authToken')
                self.headers['X-User-Id'] = login_request.json().get('data').get('userId')
        return login_request

    # Overwrite sync functions with async ones
    login = _async_call_wrapper(_login_patch)
    logout = _async_call_wrapper(RocketChat.logout)

    channels_create = _async_call_wrapper(RocketChat.channels_create)
    channels_info = _async_call_wrapper(RocketChat.channels_info)
    channels_invite = _async_call_wrapper(RocketChat.channels_invite)
    channels_history = _async_call_wrapper(RocketChat.channels_history)

    groups_create = _async_call_wrapper(RocketChat.groups_create)
    groups_info = _async_call_wrapper(RocketChat.groups_info)
    groups_invite = _async_call_wrapper(RocketChat.groups_invite)
    groups_list = _async_call_wrapper(RocketChat.groups_list)
    groups_add_owner = _async_call_wrapper(RocketChat.groups_add_owner)
    groups_delete = _async_call_wrapper(RocketChat.groups_delete)

    users_create = _async_call_wrapper(RocketChat.users_create)
    users_info = _async_call_wrapper(RocketChat.users_info)
    users_list = _async_call_wrapper(RocketChat.users_list)

    rooms_info = _async_call_wrapper(RocketChat.rooms_info)


async def _exception_wrapper(event_name: str, callback: Awaitable[None]) -> None:
    """Wrapper for coroutines to catch and log exceptions"""
    try:
        await callback
    except asyncio.CancelledError:
        logger.info(f'Subscription callback for {event_name} canceled')
    except Exception:
        sentry.exception()
        logger.exception(f'Caught exception in subscription callback')


async def _subscription_handler_wrapper(
        col_q: Any, event_name: str,
        callback: Callable[[m.SubscriptionResult], Awaitable[Any]]
) -> None:
    """Wrapper for a subscription callback providing:
    - Basic error handling and logging
    - Create a task for each incoming message
    """
    logger.debug(f"Subscription handler for {event_name} started")
    while True:
        try:
            event = await col_q.get()
            if event['type'] == 'changed':
                result = m.SubscriptionResult(**event['fields'])
                if event_name == result.eventName:
                    callback_coro = _exception_wrapper(event_name, callback(result))
                    # Offload into task such that new messages can be handled directly
                    asyncio.create_task(callback_coro)
        except asyncio.CancelledError:
            logger.debug(f"Subscription handler for {event_name} stopped")
            return
        except Exception:
            logger.exception(f"Exception in subscription handler for {event_name}.")
            sentry.exception()
