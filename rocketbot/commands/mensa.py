from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.meals as meals
import rocketbot.utils.poll as poll


class Mensa(c.BaseCommand):
    def __init__(self, master: master.Master):
        self.master = master

    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('essen | food', 'Show meals of the day'),
            ('etm [<option_1> ... <option_10]', 'Shows meal of the day and creates a poll with the given options (default = 11:30)'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['essen', 'food', 'etm']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command in ['essen', 'food']:
            await self.food_command(args, message)
        if command == 'etm':
            await self.food_command("", message)
            poll_options = args.split()
            if len(poll_options) == 0:
                poll_options.append('11:30')
            await poll.create(message.rid, message._id, command, poll_options)

    async def food_command(self, args: str, msg: m.Message):
        """Reply with the meals of the day.

        Possible extentions:
        - args = n in [1..x]  show meals of n futur days
        - args = 'heute', 'morgen', 'montag', ...
        - after 14:00 -> show meal of next day as default
        - schedule task which sends message with meals every day at 9/10(?)
        """
        try:
            foodmsg = await meals.get_food(int(args))
        except ValueError:
            foodmsg = await meals.get_food()
        await self.master.client.send_message(msg.rid, foodmsg)

    async def etx_command(self, etx: str, args: str, msg: m.Message):
        """To be implemented

        Possbile functions
        - ETM/ETLM/ET[whatever] -> start poll if there is none for today. Otherwise add option
        - if poll and option exists, add user to participants (?, to be discussed)
        - scan for ++ (?, to be discussed)
        """
        pass
