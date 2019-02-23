import abc  # Abstract Base Class
from typing import List, Tuple

import rocketbot.master as master
import rocketbot.models as m


class BaseCommand(abc.ABC):
    def __init__(self, *, master: master.Master):
        self.master = master

    @abc.abstractmethod
    def usage(self) -> List[Tuple[str, str]]:
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
