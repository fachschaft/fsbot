import datetime
import logging
import re
from typing import Any, Awaitable, Callable, Coroutine, List, Optional, Tuple

import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.poll as pollutil
import rocketbot.utils.sentry as sentry
from ftfbroker.producer.rocketchat_mensa import RocketchatMensaProducer

import fsbot.utils.meals as meals

logger = logging.getLogger(__name__)

DEFAULT_TIME = {
    'etm': '11:30',
    'etlm': '12:30',
}


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

            # Normalze poll options or set defaults
            if len(poll_options) == 1 and poll_options[0].strip() == '':
                poll_options = [DEFAULT_TIME[command]]
            else:
                poll_options = [self._normalizeOption(o) for o in poll_options]

            if poll and poll.title == 'ETM' and poll.created_on.is_today():
                # If its the same day, add the options to the poll
                new_options = [
                    await poll.add_option(option_txt)
                    for option_txt in poll_options
                    if option_txt.strip() != '']
                if any(new_options):
                    # Preset sender of message for each option (s)he added
                    for opt in new_options:
                        if opt is not None:
                            opt.users.add(message.created_by.username)
                    poll.options.sort(key=lambda x: x.text)
                    await poll.resend_old_message(self.master)
            else:
                msg = await _food_command("")
                if msg is not None:
                    await self.master.ddp.send_message(message.roomid, msg)
                poll = await self.pollmanager.create(message.roomid, message.id, 'ETM', poll_options)
                # Ignore due to mypy bug: https://github.com/python/mypy/issues/2427
                # poll.resend_old_message = monkeypatch_kafka(poll, poll.resend_old_message)  # type: ignore
                setattr(poll, "resend_old_message", monkeypatch_kafka(poll, poll.resend_old_message))

    pattern = re.compile(r'^[\s]*(1[1-4])[.:]?([0-5][0-9])?[\s]*$')

    @classmethod
    def _normalizeOption(cls, option: str) -> str:
        """Observed cases:

        12:30 -> 12:30
        1230  -> 12:30
        12    -> 12:00
        12.30 -> 12:30
        """
        res = cls.pattern.match(option)
        if res:
            a, b = res.groups()
            if b is None:
                b = '00'
            return f'{a}:{b}'
        return option


def monkeypatch_kafka(
    poll: pollutil.Poll,
    trigger: Callable[..., Awaitable[None]]
) -> Callable[..., Coroutine[Any, Any, None]]:

    # Poll was created -> send first message
    send_kafka_message(poll.options, poll.botname)

    async def wrapper(*args: Any, **kwargs: Any) -> None:
        # Call patched function first
        await trigger(*args, **kwargs)
        # Send kafka message on each trigger function call
        send_kafka_message(poll.options, poll.botname)

    return wrapper


def send_kafka_message(options: List[pollutil.PollOption], botname: str) -> None:
    try:
        kafkaproducer = RocketchatMensaProducer()

        opts = [(o.text, [u for u in o.users if u != botname]) for o in options]
        kafkaproducer.sendV1(opts)
        kafkaproducer.close()
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}", exc_info=True)
        sentry.exception()
