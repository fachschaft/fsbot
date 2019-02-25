import asyncio

import rocketbot.bots as bots
import rocketbot.commands as com
import rocketbot.master as master
import rocketbot.models as m
import rocketbot.utils.poll as pollutil

try:
    import bot_config as c
except ModuleNotFoundError:
    raise Exception('Please provide the login credentials in a bot_config.py') from None

loop = asyncio.get_event_loop()


async def go() -> None:
    while True:
        masterbot = master.Master(c.SERVER, c.BOTNAME, c.PASSWORD, loop=loop)

        result = masterbot.rest_api.rooms_info(room_name=c.POLL_STATUS_ROOM).json()
        statusroom = m.create(m.Room, result['room'])
        pollmanager = pollutil.PollManager(master=masterbot, botname=c.BOTNAME, statusroom=statusroom.to_roomref())

        usage = com.Usage(master=masterbot)
        ping = com.Ping(master=masterbot)
        poll = com.Poll(master=masterbot, pollmanager=pollmanager)
        dms = com.Dms(master=masterbot, token=c.DMS_TOKEN)
        mensa = com.Mensa(master=masterbot, pollmanager=pollmanager)

        # Public command bot
        masterbot.bots.append(
            bots.RoomTypeMentionCommandBot(
                master=masterbot, username=c.BOTNAME,
                enable_public_channel=True, enable_private_groups=True,
                commands=[usage, ping, poll]))
        # Direct message bot
        masterbot.bots.append(
            bots.RoomTypeCommandBot(
                master=masterbot, username=c.BOTNAME,
                enable_direct_message=True,
                commands=[usage, ping, dms]))
        # Mensa bot
        masterbot.bots.append(
            bots.RoomCommandBot(
                master=masterbot, username=c.BOTNAME,
                whitelist=[c.MENSA_ROOM], commands=[mensa],
                show_usage_on_unknown=False
            ))

        async with masterbot:
            print(f'{c.BOTNAME} is ready')
            await masterbot.client.disconnection()

loop.run_until_complete(go())
