from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.meals as meals
import rocketbot.utils.poll as poll


class Mensa(c.BaseCommand):
    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('essen | food', 'Show meals of the day'),
            ('etm | etlm [<poll_option>...]', 'Shows meal of the day and creates a poll with the given options (default = 11:30) or adds the options to the poll'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['essen', 'food', 'etm', 'etlm']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command in ['essen', 'food']:
            await self.food_command(args, message)
        if command in ['etm', 'etlm']:
            poll_obj = poll.get(message.rid)
            poll_options = poll.parse_args(args)

            if poll_obj and poll_obj.poll_msg and poll_obj.poll_msg.ts.is_today():
                # If its the same day, add the options to the poll
                for option_txt in poll_options:
                    option = await poll_obj.add_option(option_txt)
                    if option:
                        await self.master.client.set_reaction(option.emoji, poll_obj.poll_msg._id, True)
            else:
                if len(poll_options) == 0:
                    poll_options.append('11:30')
                await self.food_command("", message)
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
