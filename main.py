import asyncio

import rocketbot.bots as bots
import rocketbot.commands as com
import rocketbot.master as master

try:
    import bot_config as c
except ModuleNotFoundError:
    raise Exception('Please provide the login credentials in a bot_config.py') from None

loop = asyncio.get_event_loop()


async def go():
    while True:
        masterbot = master.Master(c.SERVER, c.BOTNAME, c.PASSWORD, loop)

        commands = [com.Ping(masterbot), com.Poll(masterbot, c.BOTNAME)]

        # Public command bot
        masterbot.bots.append(
            bots.RoomTypeMentionCommandBot(
                master=masterbot, username=c.BOTNAME, commands=commands,
                enable_public_channel=True, enable_private_groups=True))
        # Direct message bot
        masterbot.bots.append(
            bots.RoomTypeCommandBot(
                master=masterbot, username=c.BOTNAME, commands=commands,
                enable_direct_message=True))
        # Mensa bot
        masterbot.bots.append(
            bots.RoomCommandBot(
                master=masterbot, username=c.BOTNAME,
                rooms=[c.MENSA_ROOM], commands=[com.Mensa(masterbot)],
                show_usage_on_unknown=False
            ))

        async with masterbot:
            print(f'{c.BOTNAME} is ready')
            await masterbot.client.disconnection()

loop.run_until_complete(go())
