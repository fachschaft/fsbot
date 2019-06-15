from __future__ import annotations

import collections
import dataclasses
import datetime
import json
import re
import shlex
from typing import Any, Dict, List, Optional, Set

import petname

import rocketbot.bots as bots
import rocketbot.exception as exp
import rocketbot.models as m
from rocketbot.master import Master


class PollCache:
    """A simple cache which lets you access polls by different key properties.
    If a key property changes the pollcache has to be updated manually

    These key properties are:
    - id: Human understandable id
    - original_msg_id: Message id which created the poll
    - poll_msg_id: Message id of the poll
    - status_msg_id: Message id of the status msg which persists the poll in json

    Additional feature:
    - Get last active poll by room id
    """
    def __init__(self) -> None:
        self.by_id: Dict[str, Poll] = {}
        self.by_original_msg_id: Dict[str, Poll] = {}
        self.by_poll_msg_id: Dict[str, Poll] = {}
        self.by_status_msg_id: Dict[str, Poll] = {}
        self.last_active_by_roomid: Dict[str, Poll] = {}

    def new_id(self) -> str:
        """Returns a unique (not used by any active poll) human understandable id
        """
        # List of Tuples:
        # First element is the number of words to try
        # Second element is the number of repetitions (-1 = infinity)
        tries = [(1, 10), (2, -1)]

        for num_words, num_reps in tries:
            cnt = 0
            while cnt != num_reps:
                cnt += 1
                possible_id = petname.generate(words=num_words).lower()
                if possible_id not in self.by_id:
                    return possible_id
        raise exp.RocketBotPollException('Could not find a new id')

    def get(self, *,
            id: Optional[str] = None,
            poll_msg_id: Optional[str] = None,
            original_msg_id: Optional[str] = None,
            status_msg_id: Optional[str] = None,
            roomid: Optional[str] = None) -> Optional['Poll']:
        """Get a poll by a single key property
        """
        if id is not None and id in self.by_id:
            return self.by_id[id]
        if poll_msg_id is not None and poll_msg_id in self.by_poll_msg_id:
            return self.by_poll_msg_id[poll_msg_id]
        if original_msg_id is not None and original_msg_id in self.by_original_msg_id:
            return self.by_original_msg_id[original_msg_id]
        if status_msg_id is not None and status_msg_id in self.by_status_msg_id:
            return self.by_status_msg_id[status_msg_id]
        if roomid is not None and roomid in self.last_active_by_roomid:
            return self.last_active_by_roomid[roomid]
        return None

    def add(self, poll: 'Poll') -> None:
        # Backref so poll can update cache if any key changes
        poll._poll_cache = self
        self.by_id[poll.id] = poll
        self.by_original_msg_id[poll.original_msg_id] = poll
        self.by_poll_msg_id[poll.poll_msg_id] = poll
        self.by_status_msg_id[poll.status_msg_id] = poll
        self.last_active_by_roomid[poll.roomid] = poll

    def remove(self, *,
               id: Optional[str] = None,
               poll_msg_id: Optional[str] = None,
               original_msg_id: Optional[str] = None,
               status_msg_id: Optional[str] = None) -> 'Poll':

        poll = self.get(id=id, poll_msg_id=poll_msg_id, original_msg_id=original_msg_id, status_msg_id=status_msg_id)
        if poll is None:
            raise exp.RocketBotPollException('No poll to remove')

        del self.by_id[poll.id]
        del self.by_original_msg_id[poll.original_msg_id]
        del self.by_poll_msg_id[poll.poll_msg_id]
        del self.by_status_msg_id[poll.status_msg_id]
        room_poll = self.last_active_by_roomid[poll.roomid]
        if poll.id == room_poll.id:
            del self.last_active_by_roomid[poll.roomid]
        return poll


class PollManager:
    """Responsible for the poll creation and overall interaction with the system
    """
    def __init__(self, master: Master, botname: str, statusroom: m.RoomRef):
        self.master = master
        self.botname = botname
        self.statusroom = statusroom
        self.polls = PollCache()

        # Pollbot: Responsible for updates made by commands/reactions
        self.roomBot = bots.RoomCustomBot(
            master=master, whitelist=[],
            whitelist_directmsgs=True, callback=self._poll_callback)
        self.master.bots.append(self.roomBot)

        # Statusbot: Responsible for updates made in the status room
        statusbot = bots.RoomCustomBot(master=master, whitelist=[statusroom.name], callback=self._status_callback)
        self.master.bots.append(statusbot)

    @staticmethod
    async def create_pollmanager(master: Master, botname: str, statusroom: m.RoomRef) -> PollManager:
        ''' Factory function creating a pollmanager and initializing old polls
        '''
        pollmanager = PollManager(master, botname, statusroom)

        # Load history of polls
        roomids = set()
        history = (await master.rest.channels_history(statusroom._id, count=100)).json()
        if 'messages' not in history:
            return pollmanager
        for msg in history['messages'][::-1]:
            try:
                poll = _deserialize_poll(msg['msg'])
                poll.status_msg_id = msg['_id']
                pollmanager.polls.add(poll)
                roomids.add(poll.roomid)
            except json.decoder.JSONDecodeError:
                pass
        for rid in roomids:
            room = (await master.rest.rooms_info(room_id=rid)).json()
            if room['success'] and 'name' in room['room']:
                pollmanager.roomBot.rooms.add(room['room']['name'])
        return pollmanager

    async def create(self, roomid: str, msg_id: str, title: str, options: List[str]) -> None:
        id = self.polls.new_id()
        poll = Poll(
            botname=self.botname, original_msg_id=msg_id,
            title=title, vote_options=options, id=id, roomid=roomid)
        await poll.send_new_poll_message(self.master, roomid, self.statusroom._id)

        room = await self.master.room(room_id=roomid)
        if room.name is not None:
            self.roomBot.rooms.add(room.name)

        self.polls.add(poll)

    async def push(self, poll: Poll, roomid: str) -> None:
        """Resend an active poll
        """
        await poll.send_new_poll_message(self.master, roomid, self.statusroom._id)

        room = await self.master.room(room_id=roomid)
        if room.name is not None:
            self.roomBot.rooms.add(room.name)

    async def _poll_callback(self, message: m.Message) -> None:
        msg_id = message.id
        if msg_id in self.polls.by_original_msg_id:
            if not message.msg:
                poll = self.polls.remove(original_msg_id=msg_id)

                room = await self.master.room(room_id=message.roomid)
                if room.name:
                    self.roomBot.rooms.discard(room.name)

                if poll.poll_msg_id:
                    await self.master.ddp.delete_message(poll.poll_msg_id)
                    await self.master.ddp.delete_message(poll.status_msg_id)
        if msg_id in self.polls.by_poll_msg_id:
            poll = self.polls.by_poll_msg_id[msg_id]
            if poll.update_reactions(message.reactions):
                await poll.resend_old_message(self.master)

    async def _status_callback(self, message: m.Message) -> None:
        # Handle only own messages
        if message.created_by.username != self.botname:
            return
        # Handle only messages edited by someone else
        if not message.edited_by or message.edited_by.username == self.botname:
            return

        poll: Optional[Poll]
        if message.msg:
            try:
                poll = _deserialize_poll(message.msg)
                poll.status_msg_id = message.id

                # We don't know what was changed so readd the poll to the cache and resend it
                self.polls.remove(status_msg_id=message.id)
                self.polls.add(poll)
                await poll.resend_old_message(self.master)
            except json.decoder.JSONDecodeError:
                poll = self.polls.get(status_msg_id=message.id)
                if poll:
                    await self.master.ddp.update_message({'_id': poll.status_msg_id, 'msg': _serialize_poll(poll)})

        else:
            # We don't know what was changed so readd the poll to the cache and resend it
            poll = self.polls.remove(status_msg_id=message.id)
            await self.master.ddp.delete_message(poll.poll_msg_id)


def parse_args(args: str) -> List[str]:
    args_list = shlex.split(_replace_quotes(args))
    return list(filter(None, args_list))


_pattern = re.compile(r'(„|“|\'|„|“|”|‘|’)')


def _replace_quotes(string: str) -> str:
    """Replace all kinds of obscure quotation marks
    """
    return _pattern.sub('"', string)


LETTER_EMOJIS = [f':regional_indicator_{c}:' for c in 'abcdefghijklmnopqrstuvwxyz']

NUMBER_EMOJI_TO_VALUE = {
    ':x1:': 1,
    ':x2:': 2,
    ':x3:': 3,
    ':x4:': 4,
}

VALUE_TO_NUMBER_EMOJI = {val: key for key, val in NUMBER_EMOJI_TO_VALUE.items()}


@dataclasses.dataclass
class PollOption:
    """Poll option"""
    text: str
    emoji: str
    users: Set[str]


def _serialize_polloption(polloption: PollOption) -> Dict[str, Any]:
    dict_ = dataclasses.asdict(polloption)
    dict_['users'] = list(dict_['users'])
    return dict_


def _deserialize_polloption(data: Dict[str, Any]) -> PollOption:
    data['users'] = set(data['users'])
    return PollOption(**data)


class Poll:
    def __init__(self, id: str, roomid: str, original_msg_id: str, botname: str, title: str, vote_options: List[str]):
        self._poll_cache: Optional[PollCache] = None
        self._id = id
        self._roomid = roomid
        self._original_msg_id = original_msg_id
        self.botname = botname
        self.title = title

        self.created_on = m.RcDatetime.now()
        self._poll_msg_id: Optional[str] = None
        self._status_msg_id: Optional[str] = None
        self.user_to_number: Dict[str, int] = collections.defaultdict(lambda: 1)

        self.options: List[PollOption] = list()
        for emoji, option_text in zip(LETTER_EMOJIS, vote_options):
            option = PollOption(text=option_text, emoji=emoji, users=set([self.botname]))
            self.options.append(option)

        self.additional_people: List[PollOption] = list()
        for emoji in NUMBER_EMOJI_TO_VALUE.keys():
            option = PollOption(text='', emoji=emoji, users=set([self.botname]))
            self.additional_people.append(option)

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        if self._poll_cache is not None:
            del self._poll_cache.by_id[self._id]
            self._poll_cache.by_id[value] = self
        self._id = value

    @property
    def original_msg_id(self) -> str:
        return self._original_msg_id

    @original_msg_id.setter
    def original_msg_id(self, value: str) -> None:
        if self._poll_cache is not None:
            del self._poll_cache.by_original_msg_id[self._original_msg_id]
            self._poll_cache.by_original_msg_id[value] = self
        self._original_msg_id = value

    @property
    def poll_msg_id(self) -> str:
        if self._poll_msg_id is None:
            raise exp.RocketBotPollException('poll_msg_id is not set')
        return self._poll_msg_id

    @poll_msg_id.setter
    def poll_msg_id(self, value: str) -> None:
        if self._poll_cache is not None:
            del self._poll_cache.by_poll_msg_id[self.poll_msg_id]
            self._poll_cache.by_poll_msg_id[value] = self
        self._poll_msg_id = value

    @property
    def status_msg_id(self) -> str:
        if self._status_msg_id is None:
            raise exp.RocketBotPollException('status_msg_id is not set')
        return self._status_msg_id

    @status_msg_id.setter
    def status_msg_id(self, value: str) -> None:
        if self._poll_cache is not None:
            del self._poll_cache.by_status_msg_id[self.status_msg_id]
            self._poll_cache.by_status_msg_id[value] = self
        self._status_msg_id = value

    @property
    def roomid(self) -> str:
        return self._roomid

    @roomid.setter
    def roomid(self, value: str) -> None:
        if self._poll_cache is not None:
            if (self._roomid in self._poll_cache.last_active_by_roomid
                    and self._poll_cache.last_active_by_roomid[self._roomid].id == self.id):
                del self._poll_cache.last_active_by_roomid[self._roomid]
            self._poll_cache.last_active_by_roomid[value] = self
        self._roomid = value

    async def send_new_poll_message(self, master: Master, roomid: str, statusroomid: str) -> None:
        """Send a new message including reactions
        """

        old_msg_id = self._poll_msg_id
        msg = await self.to_message(master)

        # Save reactions and clear users in order to avoid a back and forth
        # because the initial message is without reactions and would trigger
        # an update because reactions are missing
        reactions = self._get_reactions()
        if self._poll_cache is not None:
            for o in self.options:
                o.users.clear()
            for o in self.additional_people:
                o.users.clear()

        # Send new poll message
        try:
            poll_msg = await master.ddp.send_message(roomid, msg)
            self.poll_msg_id = poll_msg.id
            self.roomid = roomid
            await master.ddp.update_message({'_id': self.poll_msg_id, 'reactions': reactions})
        except exp.RocketClientException as e:
            raise exp.RocketBotPollException('Could not send poll message/reactions') from e

        # Delete old poll message
        if old_msg_id:
            # Delete old message after the new one is send in case something does not work
            try:
                await master.ddp.delete_message(old_msg_id)
            except exp.RocketClientException:
                # Do nothing if delete fails
                pass

        # Send/Update status message
        try:
            if self._status_msg_id is None:
                status_msg = await master.ddp.send_message(statusroomid, _serialize_poll(self))
                self.status_msg_id = status_msg.id
            else:
                await master.ddp.update_message({'_id': self.status_msg_id, 'msg': _serialize_poll(self)})
        except exp.RocketClientException as e:
            raise exp.RocketBotPollException('Could not send status message') from e

    async def resend_old_message(self, master: Master) -> None:
        """Resend the old message including reactions
        """
        if self.poll_msg_id is None:
            raise exp.RocketBotPollException('No old message to resend')
        if self.status_msg_id is None:
            raise exp.RocketBotPollException('Missing status message')

        msg = await self.to_message(master)
        await master.ddp.update_message({'_id': self.poll_msg_id, 'msg': msg, 'reactions': self._get_reactions()})
        await master.ddp.update_message({'_id': self.status_msg_id, 'msg': _serialize_poll(self)})

    def _get_reactions(self) -> Dict[str, Dict[str, Any]]:
        """Get reactions by the current state
        """
        reactions = {}

        # Reactions for options
        for opt in self.options:
            reactions[opt.emoji] = {'usernames': list(opt.users)}

        # Reactions for additional people
        for el in self.additional_people:
            reactions[el.emoji] = {'usernames': list(el.users)}

        return reactions

    def update_reactions(self, reactions: Optional[Dict[str, Any]]) -> bool:
        """Update the poll with new reactions. Return value indicates
        if something changed
        """
        if not reactions:
            reactions = dict()

        update = False
        for option in self.options:
            prev_users = option.users
            new_users = self._get_usernames(reactions, option.emoji)

            missing = [u for u in prev_users if u not in new_users]
            new = [u for u in new_users if u not in prev_users]
            if missing or new:
                update = True
                for u in missing:
                    option.users.remove(u)
                for u in new:
                    option.users.add(u)
        for option in self.additional_people:
            prev_users = option.users
            new_users = self._get_usernames(reactions, option.emoji)

            missing = [u for u in prev_users if u not in new_users]
            new = [u for u in new_users if u not in prev_users]
            if missing or new:
                update = True
                for u in missing:
                    option.users.remove(u)
                    self.user_to_number[u] -= NUMBER_EMOJI_TO_VALUE[option.emoji]
                for u in new:
                    option.users.add(u)
                    self.user_to_number[u] += NUMBER_EMOJI_TO_VALUE[option.emoji]
        return update

    def _get_usernames(self, reactions: Optional[Dict[str, Any]], key: str) -> List[str]:
        if not reactions or key not in reactions:
            return []
        return reactions[key]['usernames']

    async def to_message(self, master: Master) -> str:
        """Create a message representing the poll
        """

        msg = f'*{self.title}* \n\n'

        for option in self.options:
            users = [(await master.user(u), self.user_to_number[u]) for u in option.users if u != self.botname]
            users_list = ", ".join((f'{u.name}[{val}]' for u, val in users))
            number = sum([val for _, val in users])
            msg += f'*{option.emoji} {option.text} [{number}]* \n {users_list} \n\n '

        return msg

    async def add_option(self, new_option: str) -> Optional[PollOption]:
        if len(self.options) >= len(LETTER_EMOJIS):
            return None

        if any([opt for opt in self.options if opt.text == new_option]):
            return None

        num = len(self.options)
        emoji = LETTER_EMOJIS[num]
        option = PollOption(text=new_option, emoji=emoji, users=set([self.botname]))
        self.options.append(option)
        return option


def _serialize_poll(poll: Poll) -> str:
    return json.dumps({
        'id': poll.id,
        'room_id': poll.roomid,
        'additional_people': [_serialize_polloption(o) for o in poll.additional_people],
        'botname': poll.botname,
        'options': [_serialize_polloption(o) for o in poll.options],
        'original_msg_id': poll.original_msg_id,
        'poll_msg_id': poll.poll_msg_id,
        'title': poll.title,
        'created_on': poll.created_on.value.isoformat()
    })


def _deserialize_poll(strdata: str) -> Poll:
    data = json.loads(strdata)
    poll = Poll(
        id=data['id'],
        roomid=data['room_id'],
        botname=data['botname'],
        original_msg_id=data['original_msg_id'],
        title=data['title'],
        vote_options=[])

    poll.created_on.value = datetime.datetime.strptime(data['created_on'], "%Y-%m-%dT%H:%M:%S.%f")
    poll.poll_msg_id = data['poll_msg_id']
    poll.options = [_deserialize_polloption(d) for d in data['options']]
    poll.additional_people = [_deserialize_polloption(d) for d in data['additional_people']]
    for option in poll.additional_people:
        count = NUMBER_EMOJI_TO_VALUE[option.emoji]
        for user in option.users:
            poll.user_to_number[user] += count

    return poll
