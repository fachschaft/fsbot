import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m


class Ping(c.BaseCommand):
    def __init__(self, master: master.Master):
        self.master = master

    def usage(self) -> str:
        return 'ping - Reply with "pong"'

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['ping', 'pong']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command == 'ping':
            await self.master.client.send_message(message.rid, 'Pong')
        if command == 'pong':
            await self.master.client.send_message(message.rid, 'Ping')
