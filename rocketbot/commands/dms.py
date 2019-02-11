from typing import List, Tuple
import subprocess
import os

import dmsclient as dms

import rocketbot.commands as c
import rocketbot.master as master
import rocketbot.models as m
import bot_config


class DMSClient(c.BaseCommand):
    def __init__(self, master: master.Master):
        self._create_dmsclient_config_if_missing()
        self.master = master

    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('order <product name>', 'Orders product in dms for yourself.'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['order']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command == 'order':
            userid = message.u.username
            dms_result = subprocess.run(['dms', 'order', *args,
                                         '--force', '--user={}'.format(userid)],
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            result_str = dms_result.stdout.decode('utf-8')
            await self.master.client.send_message(message.rid, result_str)

    def _create_dmsclient_config_if_missing():
        rcfile = os.path.expanduser('~/.dmsrc')
        config = dms.DmsConfig()
        status = config.read(rcfile)
        if status == dms.ReadStatus.NOT_FOUND:
            config._set(dms.Sec.GENERAL, 'token', bot_config.DMS_TOKEN)
            config.write(rcfile)
