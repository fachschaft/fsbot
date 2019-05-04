import re
from typing import Any, List, Tuple

import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.poll as pollutil


class Poll(c.BaseCommand):
    def __init__(self, pollmanager: pollutil.PollManager, **kwargs: Any):
        super().__init__(**kwargs)
        self.pollmanager = pollmanager

    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('poll <poll_title> <option_1> .. <option_26>', 'Create a poll'),
            ('poll_push #room', 'Push the poll into #room'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['poll', 'poll_push']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command == 'poll':
            await self.create_poll(args, message)
        if command == 'poll_push':
            match = re.match(r'\s*#(\S+)', args)
            if not match:
                await self.master.ddp.send_message(message.roomid, "Please specify a room")
                return

            room_name = match.groups()[0]

            if message.roomid not in self.pollmanager.polls.last_active_by_roomid:
                await self.master.ddp.send_message(message.roomid, "Please create a poll first")
                return

            poll = self.pollmanager.polls.last_active_by_roomid[message.roomid]
            # Only public rooms are listed in 'channels'
            roomref = [r for r in message.channels if r.name == room_name]
            if len(roomref) != 0:
                await self.pollmanager.push(poll, roomref[0]._id)
                return
            # For private rooms, the id has to be retrieved
            room = await self.master.room(room_name=room_name)
            await self.pollmanager.push(poll, room._id)

    async def create_poll(self, args: str, message: m.Message) -> None:
        args_list = pollutil.parse_args(args)
        if len(args_list) > 1:
            await self.pollmanager.create(message.roomid, message.id, args_list[0], args_list[1:])
        else:
            await self.master.ddp.send_message(message.roomid, f'*Usage:*\n```{self.usage()[0][0]}```')
