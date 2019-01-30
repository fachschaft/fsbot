import abc  # Abstract Base Class

import rocketbot.models as m


class BaseCommand(abc.ABC):
    @abc.abstractmethod
    def usage(self) -> str:
        pass

    @abc.abstractmethod
    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        pass

    @abc.abstractmethod
    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        pass
