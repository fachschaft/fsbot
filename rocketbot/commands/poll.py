from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as poll


class Poll(c.BaseCommand):
    def __init__(self, master: master.Master, botname: str):
        self.master = master

        poll.init(master, botname)

    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('poll <poll_title> <option_1> .. <option_10>', 'Create a poll'),
            ('poll_push', 'Resend the poll message'),
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
            await poll.push(message.rid, message._id)

    async def create_poll(self, args: str, message: m.Message) -> None:
        args_list = poll.parse_args(args)
        if len(args_list) > 1:
            await poll.create(message.rid, message._id, args_list[0], args_list[1:])
        else:
            await self.master.client.send_message(message.rid, f'*Usage:*\n```{self.usage()}```')
