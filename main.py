import asyncio
import logging

import rocketbot.bots as bots
import rocketbot.commands as com
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as pollutil

try:
    import bot_config as c
except ModuleNotFoundError:
    raise Exception('Please provide the login credentials in a bot_config.py') from None

# Configure logging
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s', "%Y-%m-%d %H:%M:%S"))
root = logging.getLogger()
root.handlers.clear()
root.addHandler(console)

# Configure logglevels
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("rocketbot").setLevel(logging.DEBUG)


async def main() -> None:
    loop = asyncio.get_event_loop()

    masterbot = master.Master(c.SERVER, c.BOTNAME, c.PASSWORD, loop=loop)

    result = masterbot.rest.rooms_info(room_name=c.POLL_STATUS_ROOM).json()
    statusroom = m.create(m.Room, result['room'])
    pollmanager = pollutil.PollManager(master=masterbot, botname=c.BOTNAME, statusroom=statusroom.to_roomref())

    usage = com.Usage(master=masterbot)
    ping = com.Ping(master=masterbot)
    poll = com.Poll(master=masterbot, pollmanager=pollmanager)
    dms = com.Dms(master=masterbot, token=c.DMS_TOKEN)
    etm = com.Etm(master=masterbot, pollmanager=pollmanager)
    food = com.Food(master=masterbot)

    # Public command bot
    masterbot.bots.append(
        bots.RoomTypeMentionCommandBot(
            master=masterbot, username=c.BOTNAME,
            enable_public_channel=True, enable_private_groups=True,
            commands=[usage, ping]))
    # Direct message bot
    masterbot.bots.append(
        bots.RoomTypeCommandBot(
            master=masterbot, username=c.BOTNAME,
            enable_direct_message=True,
            commands=[usage, ping, dms, food, poll]))
    # Mensa bot
    masterbot.bots.append(
        bots.RoomCommandBot(
            master=masterbot, username=c.BOTNAME,
            whitelist=[c.MENSA_ROOM], commands=[etm],
            show_usage_on_unknown=False
        ))

    async with masterbot:
        logging.info(f'{c.BOTNAME} is ready')
        await masterbot.ddp.disconnection()

asyncio.run(main())
