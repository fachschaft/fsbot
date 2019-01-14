import re
import shlex

import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.poll as p


class Poll(c.Prefix):
    def __init__(self, bot: b.BaseBot):
        super().__init__(bot)

        self.poll_manager = p.PollManager(bot)

        self.enable_public_channel = True
        self.enable_private_group = True
        self.prefixes.append((['poll'], self.create_poll))
        self.prefixes.append((['poll_push'], self.push_poll))

    def usage(self) -> str:
        return 'poll <poll_title> <option_1> .. <option_10>\n     - Create a poll\n' +\
            'poll_push\n     - Resend the poll message'

    async def create_poll(self, args: str, message: m.Message) -> bool:
        if message.editedBy:
            # An edited message is handled by the poll directly
            return True
        args_list = shlex.split(self.replace_quotes(args))
        args_list = list(filter(None, args_list))

        if len(args_list) > 1:
            if len(args_list) > 11:
                args_list = args_list[:11]
            await self.poll_manager.new_poll(message.rid, message._id, args_list[0], args_list[1:])
        else:
            await self.bot.send_message(message.rid, f'*Usage:*\n```{self.usage()}```')
        return True

    async def push_poll(self, args: str, message: m.Message) -> bool:
        await self.poll_manager.push_poll(message.rid, message._id)
        return True

    pattern = re.compile(r'(„|“|\'|„|“|”|‘|’)')

    def replace_quotes(self, string: str) -> str:
        """Replace all kinds of obscure quotation marks
        """
        string = Poll.pattern.sub('"', string)
        return string
