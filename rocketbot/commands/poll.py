import asyncio
import logging
import re
from typing import Any, List, Tuple

import rocketbot.commands as c
import rocketbot.exception as exp
import rocketbot.models as m
import rocketbot.utils.poll as pollutil
import rocketbot.utils.sentry as sentry

logger = logging.getLogger(__name__)


class Poll(c.BaseCommand):
    def __init__(self, pollmanager: pollutil.PollManager, **kwargs: Any):
        super().__init__(**kwargs)
        self.pollmanager = pollmanager
        # This list syncs calls to the handle function since the may depend on each other
        # E.g. poll and subsequent poll_push
        self.active_tasks: List[asyncio.Event] = []

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
        event = await self._check_running_tasks(command)
        try:
            if command == 'poll':
                try:
                    await self.create_poll(args, message)
                except exp.RocketBotPollException as e:
                    await self.master.ddp.send_message(message.roomid, str(e))
                    sentry.exception()

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
                roomref = [r for r in message.channels if r.name == room_name]
                if len(roomref) != 0:
                    try:
                        await self.pollmanager.push(poll, roomref[0]._id)
                    except exp.RocketBotPollException as e:
                        await self.master.ddp.send_message(
                            message.roomid,
                            f"{e} - Am I part of that channel?")
                        sentry.exception()
                    return
                await self.master.ddp.send_message(message.roomid, "No roomref found. Is this a valid room?")
        finally:
            # Set the event will trigger the next queued handle call
            event.set()

    async def create_poll(self, args: str, message: m.Message) -> None:
        args_list = pollutil.parse_args(args)
        if len(args_list) > 1:
            await self.pollmanager.create(message.roomid, message.id, args_list[0], args_list[1:])
        else:
            await self.master.ddp.send_message(message.roomid, f'*Usage:*\n```{self.usage()[0][0]}```')

    async def _check_running_tasks(self, command: str) -> asyncio.Event:
        """Blocks the calling function until all previous calls are finished
        """
        event = asyncio.Event()

        # Filter all finished tasks
        self.active_tasks = [t for t in self.active_tasks if not t.is_set()]
        self.active_tasks.append(event)

        if len(self.active_tasks) == 1:
            return event

        prev_event = self.active_tasks[-2]

        # Block task until prev task is completed
        logger.debug(f"Command {command} has to wait on {len(self.active_tasks) - 1} tasks")
        await prev_event.wait()

        return event
