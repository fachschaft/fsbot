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
            poll = self.pollmanager.polls.last_active_by_room_id[message.roomid]
            if len(message.channels) > 0:
                await self.pollmanager.push(poll, message.channels[0]._id)
            else:
                await self.master.client.send_message(message.roomid, "Please specify a room")

    async def create_poll(self, args: str, message: m.Message) -> None:
        args_list = pollutil.parse_args(args)
        if len(args_list) > 1:
            await self.pollmanager.create(message.roomid, message.id, args_list[0], args_list[1:])
        else:
            await self.master.client.send_message(message.roomid, f'*Usage:*\n```{self.usage()}```')
