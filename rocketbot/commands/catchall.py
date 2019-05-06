from typing import Any, Awaitable, Callable, List, Tuple

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m


class CatchAll(c.BaseCommand):
    """This is a catch all command

    It can be used as last command in the chain which is always
    applicable and will call the given function
    """
    def __init__(self, callback: Callable[[master.Master, str, str, m.Message], Awaitable[None]], **kwargs: Any):
        super().__init__(**kwargs)
        self._callback = callback

    def usage(self) -> List[Tuple[str, str]]:
        return []

    def can_handle(self, command: str) -> bool:
        """Catch all is always applicable
        """
        return True

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        await self._callback(self.master, command, args, message)


async def private_message_user(
        master: master.Master, command: str, args: str, message: m.Message) -> None:
    room = await master.ddp.create_direct_message(message.created_by.username)
    await master.ddp.send_message(
        room,
        f"Hey {message.created_by.name}, if you want me to do something contact me right here :)"
    )
