import dataclasses
from typing import Dict, Optional, List, Set

import rocketbot.bots as bots
import rocketbot.master as master
import rocketbot.models as m


class PollManager:
    """Responsible for polls. Subscribes to rooms, handles active pools, etc.
    """
    def __init__(self, master: master.Master):
        self.polls: Dict[str, Poll] = {}
        self.master = master
        self.roomBot = bots.RoomCustomBot(master=master, rooms=[], callback=self.poll_callback)

        self.master.bots.append(self.roomBot)

    async def new_poll(self, room_id: str, msg_id: str, title: str, options: List[str]) -> None:
        poll = Poll(msg_id, title, options)

        msg = await poll.to_message(self.master)
        poll_msg = await self.master.client.send_message(room_id, msg)
        await self.add_reactions(poll_msg._id, len(options))
        poll.poll_msg = poll_msg

        room = await self.master.room(room_id)
        if room.name is not None:
            self.roomBot.rooms.add(room.name)

        self.polls[room_id] = poll

    async def push_poll(self, room_id: str, msg_id: str) -> None:
        """Resend an active poll
        """
        if room_id not in self.polls:
            await self.master.client.send_message(room_id, 'No active poll found.')
            return

        poll = self.polls[room_id]
        poll.original_msg_id = msg_id
        poll.prev_reactions = dict()

        msg = await poll.to_message(self.master)
        poll_msg = await self.master.client.send_message(room_id, msg)
        await self.add_reactions(poll_msg._id, len(poll.options))

        # Set message after add_reactions so that the callback does not interrupt
        # Results in reactions being lost
        poll.poll_msg = poll_msg

    async def add_reactions(self, msg_id, num_options) -> None:
        # Reactions for options
        for i in range(num_options):
            await self.master.client.set_reaction(LETTER_EMOJIS[i], msg_id, True)

        # Reactions for additional people
        for emoji in NUMBER_EMOJI_TO_VALUE.keys():
            await self.master.client.set_reaction(emoji, msg_id, True)

    async def poll_callback(self, message: m.Message) -> None:
        poll = self.polls[message.rid]

        msg_id = message._id
        if msg_id == poll.original_msg_id:
            if message.msg:
                # TODO: update poll
                pass
            else:
                del self.polls[message.rid]

                room = await self.master.room(message.rid)
                if room.name:
                    self.roomBot.rooms.discard(room.name)

                if poll.poll_msg:
                    await self.master.client.delete_message(poll.poll_msg._id)
        if poll.poll_msg and msg_id == poll.poll_msg._id:
            if poll.update(message.reactions):
                msg = await poll.to_message(self.master)
                await self.master.client.update_message({'_id': poll.poll_msg._id, 'msg': msg})


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

    async def to_message(self, master: master.Master):
        """Create a message representing the poll
        """

        msg = f'*{self.title}* \n\n'

        for option in self.options:
            users = [(await master.user(u), self._get_number(u)) for u in option.users if u != 'fsbot']
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
