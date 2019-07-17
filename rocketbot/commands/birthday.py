import re
from typing import List, Tuple

import rocketbot.commands as c
import rocketbot.models as m


class Birthday(c.BaseCommand):
    def usage(self) -> List[Tuple[str, str]]:
        return [
            ('birthday @user', 'Create a private group with all user except the mentioned one'),
        ]

    def can_handle(self, command: str) -> bool:
        """Check whether the command is applicable
        """
        return command in ['birthday']

    async def handle(self, command: str, args: str, message: m.Message) -> None:
        """Handle the incoming message
        """
        if command == 'birthday':
            if len(message.mentions) == 0:
                await self.master.ddp.send_message(message.roomid, "Please mention a user with `@user`")
                return

            user = message.mentions[0]
            if user.username == message.created_by.username:
                await self.master.ddp.send_message(message.roomid, "Please mention someone other than yourself")
                return

            result = await self.master.rest.users_list(count=0)
            users = [m.create(m.User, u) for u in result.json()['users']]

            username = user.name if user.name is not None else user.username
            username = re.sub(r'\s', '_', username).lower()
            name = f'geburtstag_{username}'
            members = [u.username for u in users if u.username != user.username]
            result = await self.master.rest.groups_create(name=name, members=members)

            if result.status_code != 200:
                await self.master.ddp.send_message(message.roomid, result.json()['error'])
                return
            room = m.create(m.Room, result.json()['group'])
            await self.master.rest.groups_add_owner(room_id=room._id, user_id=message.created_by._id)
