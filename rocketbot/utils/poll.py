import collections
import dataclasses
import ejson
import re
import shlex
from typing import Dict, Optional, List, Set

import rocketbot.bots as bots
import rocketbot.exception as exp
import rocketbot.models as m
from rocketbot.master import Master


class PollManager:
    def __init__(self, master: Master, botname: str, statusroomid: str):
        self.master = master
        self.botname = botname
        self.statusroomid = statusroomid
        self.polls: Dict[str, 'Poll'] = {}

        # Pollbot: Responsible for updates made by commands/reactions
        self.roomBot = bots.RoomCustomBot(master=master, whitelist=[], callback=self._poll_callback)
        self.master.bots.append(self.roomBot)

        # Statusbot: Responsible for updates made in the status room
        # TODO

    async def create(self, room_id: str, msg_id: str, title: str, options: List[str]) -> None:
        poll = Poll(self.botname, msg_id, title, options)
        await poll.send_new_message(self.master, room_id)

        room = await self.master.room(room_id)
        if room.name is not None:
            self.roomBot.rooms.add(room.name)

        self.polls[room_id] = poll
        status_msg = await self.master.client.send_message(self.statusroomid, ejson.dumps(poll))
        poll.status_msg_id = status_msg._id

    async def push(self, room_id: str, msg_id: str) -> None:
        """Resend an active poll
        """
        if room_id not in self.polls:
            await self.master.client.send_message(room_id, 'No active poll found.')
            return

        poll = self.polls[room_id]
        poll.original_msg_id = msg_id

        await poll.send_new_message(self.master, room_id)
        await self.master.client.update_message({'_id': poll.status_msg_id, 'msg': ejson.dumps(poll)})

    async def _poll_callback(self, message: m.Message) -> None:
        poll = self.polls[message.rid]

        msg_id = message._id
        if msg_id == poll.original_msg_id:
            if not message.msg:
                del self.polls[message.rid]

                room = await self.master.room(message.rid)
                if room.name:
                    self.roomBot.rooms.discard(room.name)

                if poll.poll_msg:
                    await self.master.client.delete_message(poll.poll_msg._id)
        if poll.poll_msg and msg_id == poll.poll_msg._id:
            if poll.update_reactions(message.reactions):
                msg = await poll.to_message(self.master)
                await self.master.client.update_message({'_id': poll.poll_msg._id, 'msg': msg})
                await self.master.client.update_message({'_id': poll.status_msg_id, 'msg': ejson.dumps(poll)})


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


ejson.REGISTRY[PollOption] = dataclasses.asdict


@dataclasses.dataclass
class Poll:
    botname: str
    original_msg_id: str
    title: str
    vote_options: List[str]

    poll_msg: Optional[m.Message] = None
    status_msg_id: Optional[str] = None
    user_to_number: Dict[str, int] = dataclasses.field(default_factory=lambda: collections.defaultdict(lambda: 1))
    options: List[PollOption] = dataclasses.field(default_factory=list)
    additionl_people: List[PollOption] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        # mypy workaround for https://github.com/python/mypy/issues/5738
        self.options = self.options  # type: List[PollOption]
        self.user_to_number = self.user_to_number  # type: Dict[str, int]

        for emoji, option_text in zip(LETTER_EMOJIS, self.vote_options):
            option = PollOption(text=option_text, emoji=emoji, users=set([self.botname]))
            self.options.append(option)

        self.additionl_people: List[PollOption] = list()
        for emoji in NUMBER_EMOJI_TO_VALUE.keys():
            option = PollOption(text='', emoji=emoji, users=set([self.botname]))
            self.additionl_people.append(option)

    async def send_new_message(self, master: Master, room_id: str) -> None:
        """Send a new message including reactions
        """
        msg = await self.to_message(master)
        self.poll_msg = await master.client.send_message(room_id, msg)
        await master.client.update_message({'_id': self.poll_msg._id, 'reactions': self._get_reactions()})

    async def resend_old_message(self, master: Master) -> None:
        """Resend the old message including reactions
        """
        if self.poll_msg is None:
            raise exp.RocketBotPollException("No old message to resend")

        msg = await self.to_message(master)
        await master.client.update_message({'_id': self.poll_msg._id, 'msg': msg, 'reactions': self._get_reactions()})

    def _get_reactions(self) -> Dict[str, dict]:
        """Get reactions by the current state
        """
        reactions = {}

        # Reactions for options
        for opt in self.options:
            reactions[opt.emoji] = {'usernames': list(opt.users)}

        # Reactions for additional people
        for el in self.additionl_people:
            reactions[el.emoji] = {'usernames': list(el.users)}

        return reactions

    def update_reactions(self, reactions: Optional[dict]) -> bool:
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
        for option in self.additionl_people:
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

    def _get_usernames(self, reactions: Optional[dict], key: str) -> List[str]:
        if not reactions or key not in reactions:
            return []
        return reactions[key]['usernames']

    async def to_message(self, master: Master):
        """Create a message representing the poll
        """

        msg = f'*{self.title}* \n\n'

        for option in self.options:
            users = [(await master.user(u), self.user_to_number[u]) for u in option.users if u != self.botname]
            users_list = ", ".join((f'{u.name}[{val}]' for u, val in users))
            number = sum([val for _, val in users])
            msg += f'*{option.emoji} {option.text} [{number}]* \n {users_list} \n\n '

        return msg

    async def add_option(self, new_option) -> Optional[PollOption]:
        if len(self.options) >= len(LETTER_EMOJIS):
            return None

        if any([opt for opt in self.options if opt.text == new_option]):
            return None

        num = len(self.options)
        emoji = LETTER_EMOJIS[num]
        option = PollOption(text=new_option, emoji=emoji, users=set([self.botname]))
        self.options.append(option)
        return option


@ejson.register_serializer(Poll)
def _serialite_poll(poll: Poll):
    return {
        'additionl_people': poll.additionl_people,
        'options': poll.options,
        'original_msg_id': poll.original_msg_id,
        'title': poll.title,
    }


@ejson.register_serializer(set)
def _serialite_set(set_: Set):
    return list(set_)
