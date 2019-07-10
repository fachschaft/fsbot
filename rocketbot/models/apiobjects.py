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

    # Img attachment
    image_dimensions: Optional[Dict[str, int]] = None
    image_preview: Optional[str] = None
    image_type: Optional[str] = None
    image_size: Optional[str] = None

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
    slashes: Optional[bool] = None
    path: Optional[str] = None
    auth: Optional[str] = None
    href: Optional[str] = None


class ApiObject:
    # Must be overwritten in subclass
    mapping: Dict[str, str]

    def asdict(self) -> Dict[str, Any]:
        return {
            key: self.__getattribute__(mapped_key)
            for key, mapped_key in self.__class__.mapping.items()
            if self.__getattribute__(mapped_key) is not None
        }

    def __repr__(self) -> str:
        attr = (f'{key}={value}' for key, value in self.__dict__.items() if value is not None)
        return f'{self.__class__.__name__}({", ".join(attr)})'


class Message(ApiObject):
    mapping = {
        '_id': 'id',
        'rid': 'roomid',
        'msg': 'msg',
        'ts': 'created_at',
        'u': 'created_by',
        '_updatedAt': 'updated_at',
        'editedAt': 'edited_at',
        'editedBy': 'edited_by',
        'pinnedAt': 'pinned_at',
        'pinnedBy': 'pinned_by',
        't': 'message_type',
        'role': 'role_type',
        'attachments': 'attachments',
        'channels': 'channels',
        'mentions': 'mentions',
        'urls': 'urls',
        'reactions': 'reactions',
        'file': 'file',
        'groupable': 'groupable',
        'parseUrls': 'parseUrls',
        'pinned': 'pinned',
    }

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

        self.attachments = [m.create(Attachment, a) for a in kwargs.get('attachments', list())]
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
    unmuted: Optional[List[str]] = None
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
        self.ts = m.try_create(m.RcDatetime, self.ts)
        self.lm = m.try_create(m.RcDatetime, self.lm)
        self.t = m.create(m.RoomType, self.t)
        self.u = m.try_create(UserRef, self.u)
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
class User:
    _id: str
    username: str
    name: str
    active: bool
    status: str
    type: str

    createdAt: Optional[m.RcDatetime] = None
    _updatedAt: Optional[m.RcDatetime] = None
    lastLogin: Optional[m.RcDatetime] = None
    emails: Optional[List[Dict[str, Any]]] = None
    roles: Optional[List[m.RoleType]] = None
    services: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    statusConnection: Optional[str] = None
    utcOffset: Optional[int] = None
    statusDefault: Optional[str] = None
    avatarOrigin: Optional[str] = None
    language: Optional[str] = None
    requirePasswordChange: Optional[bool] = None

    def __post_init__(self) -> None:
        self.createdAt = m.try_create(m.RcDatetime, self.createdAt)
        self._updatedAt = m.try_create(m.RcDatetime, self._updatedAt)
        self.lastLogin = m.try_create(m.RcDatetime, self.lastLogin)
        if self.roles is not None:
            self.roles = [m.create(m.RoleType, r) for r in self.roles]


@dataclasses.dataclass
class UserRef:
    _id: str
    username: str  # Unique name (@...)
    name: Optional[str] = None  # Display name
