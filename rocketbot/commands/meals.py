import rocketbot.bots as b
import rocketbot.commands as c
import rocketbot.models as m
from rocketbot.utils.meals import FoodManager as F


class Meals(c.Prefix):
    def __init__(self, bot: b.BaseBot):
        super().__init__(bot)

        self.enable_public_channel = True
        self.enable_private_group = True
        self.enable_direct_message = True
        self.prefixes.append((['meals'], self.send_meals))

    def usage(self) -> str:
        return 'meals - Reply with todays meals'

    async def send_meals(self, args: str, message: m.Message) -> bool:
        foodmsg = await F.get_food(args)
        await self.bot.send_message(message.rid, foodmsg)
        return True
