import rocketbot.bots.accesscontrol as ac
import rocketbot.bots.messagefilter as mf
import rocketbot.bots.messagehandler as mh


class RoomCommandBot(ac.WhitelistRoomMixin, mf.IgnoreOwnMsgMixin, mh.PrefixCommandMixin):
    pass


class RoomTypeCommandBot(ac.RoomTypeMixin, mf.IgnoreOwnMsgMixin, mh.PrefixCommandMixin):
    pass


class RoomTypeMentionCommandBot(ac.RoomTypeMixin, mf.IgnoreOwnMsgMixin, mf.MentionMixin, mh.PrefixCommandMixin):
    pass


class RoomCustomBot(ac.WhitelistRoomMixin, mh.CustomHandlerMixin):
    pass
