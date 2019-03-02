from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

import rocketbot.models as m


@dataclasses.dataclass
class Attachment:
    ts: m.RcDatetime

    # File attachment
    title: Optional[str] = None
    title_link: Optional[str] = None
    title_link_download: Optional[bool] = None
    image_url: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None

    # Message attachment
    text: Optional[str] = None
    author_name: Optional[str] = None  # Should be user
    author_icon: Optional[str] = None
    message_link: Optional[str] = None
    attachments: List[Attachment] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        self.ts = m.create(m.RcDatetime, self.ts)
        if len(self.attachments) != 0:
            self.attachments = [m.create(Attachment, a) for a in self.attachments]


@dataclasses.dataclass
class File:
    _id: str
    name: str
    type: str


@dataclasses.dataclass
class Link:
    url: str
    ignoreParse: Optional[bool] = None
    meta: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    parsedUrl: Optional[ParsedUrl] = None

    def __post_init__(self) -> None:
        self.parsedUrl = m.try_create(ParsedUrl, self.parsedUrl)


@dataclasses.dataclass
class ParsedUrl:
    host: str
    hostname: str
    protocol: str
    hash: Optional[str] = None
    pathname: Optional[str] = None
    port: Optional[str] = None
    query: Optional[str] = None
    search: Optional[str] = None


class Message:
    def __init__(self, kwargs: Any) -> None:
        self.id: str = kwargs['_id']
        self.roomid: str = kwargs['rid']
        self.msg: str = kwargs['msg']

        self.created_at = m.create(m.RcDatetime, kwargs['ts'])
        self.created_by = m.create(UserRef, kwargs['u'])
        self.updated_at = m.create(m.RcDatetime, kwargs['_updatedAt'])
        self.edited_at = m.try_create(m.RcDatetime, kwargs.get('editedAt'))
        self.edited_by = m.try_create(m.UserRef, kwargs.get('editedBy'))
        self.pinned_at = m.try_create(m.RcDatetime, kwargs.get('pinnedAt'))
        self.pinned_by = m.try_create(m.UserRef, kwargs.get('pinnedBy'))

        self.message_type = m.create(m.MessageType, kwargs.get('t'), default=m.MessageType.STANDARD_MESSAGE)
        self.role_type = m.create(m.RoleType, kwargs.get('role'), default=m.RoleType.NONE)

        self.attachments = [m.create(Attachments, a) for a in kwargs.get('attachments', list())]
        self.channels = [m.create(RoomRef, l) for l in kwargs.get('channels', list())]
        self.mentions = [m.create(UserRef, u) for u in kwargs.get('mentions', list())]
        self.urls = [m.create(Link, l) for l in kwargs.get('urls', list())]

        self.reactions = kwargs.get('reactions', dict())
        self.file = m.try_create(File, kwargs.get('file'))

        self.groupable = kwargs.get('groupable')
        self.parseUrls = kwargs.get('parseUrls')
        self.pinned = kwargs.get('pinned')


@dataclasses.dataclass
class Room:
    # Required fields
    _id: str
    _updatedAt: m.RcDatetime
    t: m.RoomType

    # Optional fields
    name: Optional[str] = None
    fname: Optional[str] = None
    u: Optional[UserRef] = None  # Room owner
    lastMessage: Optional[Message] = None
    topic: Optional[str] = None
    customFields: Optional[Dict[str, Any]] = None
    muted: Optional[List[str]] = None
    description: Optional[str] = None
    msgs: Optional[int] = None  # Number of msgs
    usersCount: Optional[int] = None
    ts: Optional[m.RcDatetime] = None  # Creation timestamp
    lm: Optional[m.RcDatetime] = None  # Timestamp of last message
    usernames: Optional[List[str]] = None

    # Flags
    broadcast: Optional[bool] = None
    encrypted: Optional[bool] = None
    ro: Optional[bool] = None  # Read only flag
    sysMes: Optional[bool] = None
    default: Optional[bool] = None
    archived: Optional[bool] = None

    def __post_init__(self) -> None:
        self._updatedAt = m.create(m.RcDatetime, self._updatedAt)
        self.ts = m.create(m.RcDatetime, self.ts)
        self.lm = m.create(m.RcDatetime, self.lm)
        self.t = m.RoomType(self.t)
        self.u = m.create(UserRef, self.u)
        self.lastMessage = m.try_create(Message, self.lastMessage)

    def to_roomref(self) -> RoomRef:
        name = self.name if self.name else ""
        return RoomRef(name=name, _id=self._id)

    def to_roomref2(self, is_participant: bool) -> RoomRef2:
        return RoomRef2(roomType=self.t, roomName=self.name, roomParticipant=is_participant)


@dataclasses.dataclass
class RoomRef:
    _id: str
    name: str


@dataclasses.dataclass
class RoomRef2:
    """Necessary because there is no single way to reference a room"""
    roomType: m.RoomType
    roomParticipant: bool
    roomName: Optional[str] = None

    def __post_init__(self) -> None:
        self.roomType = m.RoomType(self.roomType)


@dataclasses.dataclass
class UserRef:
    _id: str
    username: str  # Unique name (@...)
    name: Optional[str] = None  # Display name
