import asyncio
import os
import re
from typing import Any, List, Tuple

import dmsclient as dms
import rocketbot.commands as c
import rocketbot.models as m


class Dms(c.BaseCommand):
    def __init__(self, token: str, **kwargs: Any):
        super().__init__(**kwargs)
        self._create_dmsclient_config_if_missing(token)

    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('order', 'Orders product in dms for yourself.'),
            ('dms | drink | drinks', 'Access dms client.'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['dms', 'drink', 'drinks', 'order']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        argv = re.split(r'\s+', args.strip())

        if command in ('order'):
            argv = [command, *argv]

        if argv[0] in ('order', 'buy', 'comment'):
            userargv = [arg for arg in argv if arg.startswith('-u') or arg.startswith('--user')]
            if len(userargv) == 0:
                userid = message.created_by.username
                argv.append('--user={}'.format(userid))
        if argv[0] in ('order', 'buy'):
            if '--force' not in argv:
                argv.append('--force')

        proc = await asyncio.create_subprocess_exec(
            'dms', *argv,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        await proc.wait()
        if proc.stdout:
            dms_result = await proc.stdout.read()
            result_str = dms_result.decode('utf-8')
        else:
            result_str = "Done."
        await self.master.ddp.send_message(message.roomid, result_str)

    def _create_dmsclient_config_if_missing(self, token: str) -> None:
        rcfile = os.path.expanduser('~/.dmsrc')
        config = dms.DmsConfig()
        status = config.read(rcfile)
        if status == dms.ReadStatus.NOT_FOUND:
            config._set(dms.Sec.GENERAL, 'token', token)
            config.write(rcfile)
