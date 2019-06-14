import asyncio
import logging
import time
import requests

# Configure logging before importing because some submodule tries to configures the logger
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(name)s]: %(message)s', "%Y-%m-%d %H:%M:%S"))
root = logging.getLogger()
root.handlers.clear()
root.addHandler(console)

# Configure logglevels
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("rocketbot").setLevel(logging.INFO)

from rocketchat_API.APIExceptions.RocketExceptions import RocketConnectionException  # noqa: E402

import rocketbot.bots as bots  # noqa: E402
import rocketbot.commands as com  # noqa: E402
import rocketbot.master as master  # noqa: E402
import rocketbot.models as m  # noqa: E402
import rocketbot.utils.poll as pollutil  # noqa: E402
import rocketbot.utils.sentry as sentry  # noqa: E402

try:
    import bot_config as c
except ModuleNotFoundError:
    raise Exception('Please provide the login credentials in a bot_config.py') from None


async def main() -> None:
    loop = asyncio.get_event_loop()

    masterbot = master.Master(c.SERVER, c.BOTNAME, c.PASSWORD, loop=loop)
    masterbot.rest.login(c.BOTNAME, c.PASSWORD)

    result = masterbot.rest.rooms_info(room_name=c.POLL_STATUS_ROOM).json()
    statusroom = m.create(m.Room, result['room'])
    pollmanager = pollutil.PollManager(master=masterbot, botname=c.BOTNAME, statusroom=statusroom.to_roomref())

    usage = com.Usage(master=masterbot)
    ping = com.Ping(master=masterbot)
    poll = com.Poll(master=masterbot, pollmanager=pollmanager)
    dms = com.Dms(master=masterbot, token=c.DMS_TOKEN)
    etm = com.Etm(master=masterbot, pollmanager=pollmanager)
    food = com.Food(master=masterbot)
    notify = com.CatchAll(master=masterbot, callback=com.private_message_user)

    # Public command bot
    masterbot.bots.append(
        bots.RoomTypeMentionCommandBot(
            master=masterbot, username=c.BOTNAME,
            enable_public_channel=True, enable_private_groups=True,
            commands=[ping, notify]))
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

while True:
    try:
        asyncio.run(main())
        # If run terminates without exception end the while true loop
        break
    except (RocketConnectionException, requests.exceptions.SSLError):
        logging.error("Failed to connect. Retry in 60s")
        time.sleep(60)
    except Exception as e:
        logging.error(f"{type(e).__name__}: {e}", exc_info=True)
        sentry.exception()
