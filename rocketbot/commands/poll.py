import re
import shlex

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as poll


class Poll(c.BaseCommand):
    def __init__(self, master: master.Master, botname: str):
        self.master = master

        poll.init(master, botname)

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
            await poll.push(message.rid, message._id)

    async def create_poll(self, args: str, message: m.Message) -> None:
        args_list = shlex.split(self.replace_quotes(args))
        args_list = list(filter(None, args_list))

        if len(args_list) > 1:
            if len(args_list) > 11:
                args_list = args_list[:11]
            await poll.create(message.rid, message._id, args_list[0], args_list[1:])
        else:
            await self.master.client.send_message(message.rid, f'*Usage:*\n```{self.usage()}```')

    pattern = re.compile(r'(„|“|\'|„|“|”|‘|’)')

    def replace_quotes(self, string: str) -> str:
        """Replace all kinds of obscure quotation marks
        """
        string = Poll.pattern.sub('"', string)
        return string
