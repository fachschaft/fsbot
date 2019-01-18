import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m
import rocketbot.utils.meals as meals


class Mensa(c.BaseCommand):
    def __init__(self, bot: b.BaseBot, room_name: str):
        self.bot = bot
        self.room_name = room_name

    def is_applicable(self, room: m.RoomRef2) -> bool:
        if room.roomName and room.roomName == self.room_name:
            return True
        return False

    def usage(self) -> str:
        return 'essen | food\n     - Show meals of the day\n'

    async def handle(self, message: m.Message) -> bool:
        """Only receives messages of typ '@bot commmand ...'
        This is not useful for this command
        """
        return False

    async def activate(self) -> None:
        """Activate commands by subscribing the following callback to mensa messages
        """
        async def callback(result: m.SubscriptionResult):
            # Ignore own messages
            if result.message.u.username == self.bot.username:
                return

            command = result.message.msg.split()[0].lower()
            args = result.message.msg[len(command):].lstrip()

            if command == 'essen' or command == 'food':
                return await self.food_command(args, result.message)

            if command.startswith('et'):
                return await self.etx_command(command, args, result.message)

        rid = [r._id for r in self.bot._rooms_cache.values() if r.name == self.room_name][0]
        await self.bot.subscribe_room(rid, callback)

    async def food_command(self, args: str, msg: m.Message):
        """Reply with the meals of the day.

        Possible extentions:
        - args = n \in [1..x]  show meals of n futur days
        - args = 'heute', 'morgen', 'montag', ...
        - after 14:00 -> show meal of next day as default
        - schedule task which sends message with meals every day at 9/10(?)
        """
        foodmsg = await meals.get_food(args)
        await self.bot.send_message(msg.rid, foodmsg)

    async def etx_command(self, etx: str, args: str, msg: m.Message):
        """To be implemented

        Possbile functions
        - ETM/ETLM/ET[whatever] -> start poll if there is none for today. Otherwise add option
        - if poll and option exists, add user to participants (?, to be discussed)
        - scan for ++ (?, to be discussed)
        """
        pass
