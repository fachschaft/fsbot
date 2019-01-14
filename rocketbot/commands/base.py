import abc  # Abstract Base Class

import rocketbot.bots as b
import rocketbot.models as m


class BaseCommand(abc.ABC):
    def __init__(self, bot: 'b.BaseBot'):
        self.bot = bot

    @abc.abstractmethod
    def usage(self) -> str:
        pass

    @abc.abstractmethod
    def is_applicable(self, room: m.RoomRef2) -> bool:
        """Check whether the command is applicable for the room.
        """
        pass

    @abc.abstractmethod
    async def handle(self, message: m.Message) -> bool:
        """Handle the incoming message

        The return value should indicate if the command recognized the command or not
        """
        pass
