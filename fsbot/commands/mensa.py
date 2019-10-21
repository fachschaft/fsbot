import datetime
import re
from typing import Any, List, Optional, Tuple

import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.poll as pollutil

import fsbot.utils.meals as meals


async def _food_msg_by_day(day: int) -> str:
    """Return the food msg by day where monday=0, ..."""
    offset = (day - datetime.datetime.today().weekday()) % 7
    return await meals.get_food(offset, 1)


async def _food_command(args: str) -> Optional[str]:
    """Reply with the meals of the specified day

    Possible arguments:
    - empty args -> show meal of today
    - args = n in [1..x]  show meals of n future days
    - args = 'heute', 'morgen', 'montag', ...
    """
    args = args.strip().lower()
    if args.isnumeric():
        foodmsg = await meals.get_food(0, int(args))
    elif len(args) == 0 or args in ['heute', 'today']:
        foodmsg = await meals.get_food(0, 1)
    elif args in ['morgen', 'tomorrow']:
        foodmsg = await meals.get_food(1, 1)
    elif args in ['montag', 'monday']:
        foodmsg = await _food_msg_by_day(0)
    elif args in ['dienstag', 'tuesday']:
        foodmsg = await _food_msg_by_day(1)
    elif args in ['mittwoch', 'wednesday']:
        foodmsg = await _food_msg_by_day(2)
    elif args in ['donnerstag', 'thursday']:
        foodmsg = await _food_msg_by_day(3)
    elif args in ['freitag', 'friday']:
        foodmsg = await _food_msg_by_day(4)
    else:
        return None
    return foodmsg


class Food(c.BaseCommand):
    def usage(self) -> List[Tuple[str, str]]:
        return [
            (
                '<essen | food> [ <n | today | tomorrow | monday .. friday> ]',
                'Show meals of the day, of the next "n" days or on a specific day'
            ),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['essen', 'food']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command in ['essen', 'food']:
            msg = await _food_command(args)
            if msg is None:
                com, desc = self.usage()[0]
                await self.master.ddp.send_message(
                    message.roomid,
                    f'*Usage:*\n```{com}\n    {desc}```')
            else:
                await self.master.ddp.send_message(message.roomid, msg)


class Etm(c.BaseCommand):
    def __init__(self, pollmanager: pollutil.PollManager, **kwargs: Any):
        super().__init__(**kwargs)
        self.pollmanager = pollmanager

    def usage(self) -> List[Tuple[str, str]]:
        return [
            (
                '<etm | etlm> [<poll_option>...]',
                'Shows meal of the day and creates a poll with the given '
                + 'options (default = 11:30) or adds the options to the poll'
            ),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['etm', 'etlm']

    quotemarks = re.compile(r'("|„|“|\'|„|“|”|‘|’)')

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command in ['etm', 'etlm']:
            poll = self.pollmanager.polls.get(roomid=message.roomid)

            poll_options = [args]
            # Parse only if a pair of " is found
            if len(Etm.quotemarks.findall(args)) > 1:
                poll_options = pollutil.parse_args(args)
            if poll and poll.title == 'ETM' and poll.created_on.is_today():
                # If its the same day, add the options to the poll
                if any([await poll.add_option(
                        self._normalizeOption(option_txt))
                        for option_txt in poll_options
                        if option_txt.strip() != '']):
                    poll.options.sort(key=lambda x: x.text)
                    await poll.resend_old_message(self.master)
            else:
                if len(poll_options) == 1 and poll_options[0].strip() == '':
                    poll_options = ['11:30']
                msg = await _food_command("")
                if msg is not None:
                    await self.master.ddp.send_message(message.roomid, msg)
                await self.pollmanager.create(message.roomid, message.id, 'ETM', poll_options)

    pattern = re.compile(r'^[\s]*(1[1-4])[.:]?([0-5][0-9])?[\s]*$')

    def _normalizeOption(self, option: str) -> str:
        """Observed cases:

        12:30 -> 12:30
        1230  -> 12:30
        12    -> 12:00
        12.30 -> 12:30
        """
        res = Etm.pattern.match(option)
        if res:
            a, b = res.groups()
            if b is None:
                b = '00'
            return f'{a}:{b}'
        return option
