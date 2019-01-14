import asyncio

import rocketbot.bots as bots

try:
    import bot_config as c
except ModuleNotFoundError as e:
    raise Exception('Please provide the login credentials in a bot_config.py') from None

loop = asyncio.get_event_loop()

async def go():
    while True:
        async with bots.CommandBot(c.SERVER, c.BOTNAME, c.PASSWORD, loop) as bot:
            await bot.disconnection()

loop.run_until_complete(go())
