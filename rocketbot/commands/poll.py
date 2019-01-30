import re
import shlex

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as p


class Poll(c.BaseCommand):
    def __init__(self, master: master.Master):
        self.master = master

        self.poll_manager = p.PollManager(master)

    def usage(self) -> str:
        return 'poll <poll_title> <option_1> .. <option_10>\n     - Create a poll\n' +\
            'poll_push\n     - Resend the poll message'

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
            await self.push_poll(args, message)

    async def create_poll(self, args: str, message: m.Message) -> None:
        if message.editedBy:
            # An edited message is handled by the poll directly
            return
        args_list = shlex.split(self.replace_quotes(args))
        args_list = list(filter(None, args_list))

        if len(args_list) > 1:
            if len(args_list) > 11:
                args_list = args_list[:11]
            await self.poll_manager.new_poll(message.rid, message._id, args_list[0], args_list[1:])
        else:
            await self.master.client.send_message(message.rid, f'*Usage:*\n```{self.usage()}```')

    async def push_poll(self, args: str, message: m.Message) -> bool:
        await self.poll_manager.push_poll(message.rid, message._id)
        return True

    pattern = re.compile(r'(„|“|\'|„|“|”|‘|’)')

    def replace_quotes(self, string: str) -> str:
        """Replace all kinds of obscure quotation marks
        """
        string = Poll.pattern.sub('"', string)
        return string
