import asyncio
import traceback
from typing import Awaitable, Callable, List, Optional, Union, Dict

from ddp_asyncio import DDPClient
from ddp_asyncio.subscription import Subscription

import rocketbot.exception as exp
import rocketbot.models as m


async def _subscription_cb_wrapper(col_q: asyncio.Queue, event_name: str, callback: Callable[[m.SubscriptionResult], Awaitable]):
    """Wrapper for a subscription callback with handles incoming messages and adds a basic errorhandling
    """
    while True:
        event = await col_q.get()
        try:
            if event['type'] == 'changed':
                result = m.SubscriptionResult(**event['fields'])
                if event_name == result.eventName:
                    await callback(result)
        except exp.RocketCancelSubscription:
            break
        except Exception:
            traceback.print_exc()


class Client:
    """RocketChat Client

    Implements all available rocketchat methods and subscriptions
    """
    def __init__(self, address, loop):
        self.client = DDPClient(address)
        self.tasks: List[asyncio.Task] = []
        self.subscriptions: Dict[str, Subscription] = {}
        self.loop = loop

    async def connect(self) -> None:
        """Connect
        """
        await self.client.connect()

    async def disconnection(self) -> None:
        """Wait until the ddpclient disconnects
        """
        await self.client.disconnection()

    def disconnect(self) -> None:
        """Disconnect by caneling all running tasks
        """
        for task in self.tasks:
            task.cancel()

    async def login(self, username: str, password: str) -> m.LoginResult:
        """Login with the given credentials"""
        response = await self.client.call("login", {"user": {"username": username}, "password": password})
        return m.LoginResult(**response)

    async def logout(self) -> None:
        """Logout"""
        await self.client.call("logout")

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
    #     return await self.client.call("getUserRoles")

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
    #     return await self.client.call("listEmojiCustom")

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
        response = await self.client.call(
            "loadHistory", room_id, from_, num_msgs, until)
        if isinstance(response, dict):
            return m.LoadHistoryResult(**response)
        raise exp.RocketClientException("Cannot access room")

    # async def getRoomRoles(self, *room_ids):
    #     """This method call is used to get room-wide special users and their
    #     roles. You may send a collection of room ids (at least one).
    #     """
    #     return await self.client.call("getRoomRoles", room_ids)

    async def get_all_rooms(self) -> List[m.Room]:
        """Get all the rooms a user belongs to.
        """
        response = await self.client.call("rooms/get")
        return [m.create(m.Room, r) for r in response]

    async def get_rooms_since(self, date: m.RcDatetime) -> m.GetRoomsResult:
        """This is the method call used to get all the rooms a user belongs
        to. It accepts a timestamp with the latest client update time in order
        to just send what changed since last call.
        """
        response = await self.client.call("rooms/get", date)
        return m.GetRoomsResult(**response)

    async def create_direct_message(self, username: str) -> str:
        """Get the room id for a direct message with a user
        """
        response = await self.client.call("createDirectMessage", username)
        return response['rid']

    async def send_message(self, roomId: str, message: str) -> m.Message:
        """Send a message to a room
        """
        response = await self.client.call("sendMessage", {"rid": roomId, "msg": message})
        return m.create(m.Message, response)

    async def update_message(self, message: Union[m.Message, dict]) -> None:
        """Update a message either by a message object or for partial updates only a
        dict with the relevant fields (_id is required)
        """
        return await self.client.call("updateMessage", message)

    async def delete_message(self, messageId: str) -> None:
        """Delete a message
        """
        await self.client.call("deleteMessage", {"_id": messageId})

    async def set_reaction(self, emojiId: str, messageId: str, flag: Optional[bool] = None) -> None:
        """React to a message

        Flag:
            True = set reaction
            False = unset reaction
            None = toggle reaction
        """
        await self.client.call("setReaction", emojiId, messageId, flag)

    async def subscribe_room(self, roomId: str, callback: Callable[[m.SubscriptionResult], Awaitable]) -> Subscription:
        """Subscribe for updates for the given room
        """
        col = self.client.get_collection('stream-room-messages')
        col._data['id'] = {}

        col_q = col.get_queue()
        task = self.loop.create_task(_subscription_cb_wrapper(col_q, roomId, callback))
        self.tasks.append(task)

        if roomId not in self.subscriptions:
            self.subscriptions[roomId] = await self.client.subscribe("stream-room-messages", roomId, True)
        return self.subscriptions[roomId]

    async def subscribe_my_messages(self, callback: Callable[[m.SubscriptionResult], Awaitable]) -> Subscription:
        """Subscribe to the personal '__my_messages__' topic which receives updates for:
        - all public channels (joined and unjoined)
        - all joined private groups
        - all direct messages"""
        return await self.subscribe_room('__my_messages__', callback)
