import dataclasses
from typing import Awaitable, Callable, Dict, Optional, List, Set

import rocketbot.bots as b
import rocketbot.models as m
from rocketbot.client import RocketCancelSubscription


class PollManager:
    """Responsible for polls. Subscribes to rooms, handles active pools, etc.
    """
    def __init__(self, bot: b.BaseBot):
        self.bot = bot
        self.polls: Dict[str, Poll] = {}

    async def new_poll(self, room_id: str, msg_id: str, title: str, options: List[str]) -> None:
        poll = Poll(msg_id, title, options)

        msg = await poll.to_message(self.bot)
        poll.poll_msg = await self.bot.send_message(room_id, msg)
        await self.add_reactions(poll.poll_msg._id, len(options))

        if room_id not in self.polls:
            await self.bot.subscribe_room(room_id, self.poll_callback(room_id))
        self.polls[room_id] = poll

    async def push_poll(self, room_id: str, msg_id: str) -> None:
        if room_id not in self.polls:
            await self.bot.send_message(room_id, 'No active poll found.')
            return

        poll = self.polls[room_id]
        poll.original_msg_id = msg_id
        poll.prev_reactions = dict()

        msg = await poll.to_message(self.bot)
        poll_msg = await self.bot.send_message(room_id, msg)
        await self.add_reactions(poll_msg._id, len(poll.options))

        # Set message after add_reactions so that the callback does not interrupt
        # Results in reactions being lost
        poll.poll_msg = poll_msg

    async def add_reactions(self, msg_id, num_options) -> None:
        # Reactions for options
        for i in range(num_options):
            await self.bot.set_reaction(LETTER_EMOJIS[i], msg_id, True)

        # Reactions for additional people
        for emoji in NUMBER_EMOJI_TO_VALUE.keys():
            await self.bot.set_reaction(emoji, msg_id, True)

    def poll_callback(self, room_id: str) -> Callable[[m.SubscriptionResult], Awaitable]:
        async def _cb(result: m.SubscriptionResult):
            if room_id not in self.polls:
                raise RocketCancelSubscription()

            poll = self.polls[room_id]

            msg = result.message
            msg_id = msg._id
            if msg_id == poll.original_msg_id:
                if result.message.msg:
                    # TODO: update poll
                    pass
                else:
                    del self.polls[room_id]
                    if poll.poll_msg:
                        await self.bot.delete_message(poll.poll_msg._id)
                    raise RocketCancelSubscription()
            if poll.poll_msg and msg_id == poll.poll_msg._id:
                if poll.update(result.message.reactions):
                    msg = await poll.to_message(self.bot)
                    await self.bot.update_message({'_id': poll.poll_msg._id, 'msg': msg})
        return _cb


LETTER_EMOJIS = [
    ':regional_indicator_a:',
    ':regional_indicator_b:',
    ':regional_indicator_c:',
    ':regional_indicator_d:',
    ':regional_indicator_e:',
    ':regional_indicator_f:',
    ':regional_indicator_g:',
    ':regional_indicator_h:',
    ':regional_indicator_i:',
    ':regional_indicator_j:',
]

NUMBER_TO_LETTER_EMOJI = {i: val for i, val in enumerate(LETTER_EMOJIS)}
LETTER_EMOJI_TO_NUMBER = {val: i for i, val in enumerate(LETTER_EMOJIS)}

NUMBER_EMOJI_TO_VALUE = {
    ':plus_one:': 1,
    ':plus_two:': 2,
    ':plus_three:': 3,
    ':plus_four:': 4,
}

VALUE_TO_NUMBER_EMOJI = {val: key for key, val in NUMBER_EMOJI_TO_VALUE.items()}


@dataclasses.dataclass
class PollOption:
    """Poll option"""
    text: str
    _id: int
    emoji: str
    users: Set[str] = dataclasses.field(default_factory=set)


class Poll:
    def __init__(self, msg_id: str, title: str, vote_options: List[str]):
        self.title = title

        self.original_msg_id = msg_id
        self.poll_msg: Optional[m.Message] = None

        self.options: List[PollOption] = list()
        self.prev_reactions: Dict[str, dict] = dict()
        self.user_to_numberemojis: Dict[str, set] = dict()

        for (num, emoji), option_text in zip(NUMBER_TO_LETTER_EMOJI.items(), vote_options):
            option = PollOption(text=option_text, _id=num, emoji=emoji)
            self.options.append(option)

    def update(self, reactions: Optional[dict]) -> bool:
        """Update the poll with new reactions. Return value indicates
        if something changed
        """
        if not reactions:
            reactions = dict()

        update = False
        for option in self.options:
            prev_users = self._get_usernames(self.prev_reactions, option.emoji)
            new_users = self._get_usernames(reactions, option.emoji)

            missing = [u for u in prev_users if u not in new_users]
            new = [u for u in new_users if u not in prev_users]
            if missing or new:
                update = True
                for u in missing:
                    option.users.remove(u)
                for u in new:
                    option.users.add(u)
        for emoji in NUMBER_EMOJI_TO_VALUE.keys():
            prev_users = self._get_usernames(self.prev_reactions, emoji)
            new_users = self._get_usernames(reactions, emoji)

            missing = [u for u in prev_users if u not in new_users]
            new = [u for u in new_users if u not in prev_users]
            if missing or new:
                update = True
                for u in missing:
                    if u in self.user_to_numberemojis:
                        self.user_to_numberemojis[u].discard(emoji)
                for u in new:
                    if u not in self.user_to_numberemojis:
                        self.user_to_numberemojis[u] = set()
                    self.user_to_numberemojis[u].add(emoji)
        self.prev_reactions = reactions
        return update

    def _get_usernames(self, reactions: Optional[dict], key: str) -> List[str]:
        if not reactions or key not in reactions:
            return []
        return reactions[key]['usernames']

    async def to_message(self, bot: b.BaseBot):
        """Create a message representing the poll
        """

        msg = f'*{self.title}* \n\n'

        for option in self.options:
            users = [(await bot.user(u), self._get_number(u)) for u in option.users if u != 'fsbot']
            users_list = ", ".join((f'{u.name}[{val}]' for u, val in users))
            number = sum([val for _, val in users])
            msg += f'*{option.emoji} {option.text} [{number}]* \n\n {users_list} \n\n '

        return msg

    def _get_number(self, user):
        if user not in self.user_to_numberemojis:
            return 1
        sum_ = 1
        for emoji in self.user_to_numberemojis[user]:
            sum_ += NUMBER_EMOJI_TO_VALUE[emoji]
        return sum_
