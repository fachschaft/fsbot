import dataclasses
from enum import Enum
from typing import Callable, TypeVar, Optional, List, Any

import ejson

import rocketbot.models as models


def _serialize_dataclass(instance: object) -> dict:
    """Serialize a dataclass"""
    return dataclasses.asdict(instance)


def _serialize_enum(instance: Enum) -> dict:
    """Serialite an enum"""
    return instance.value


T = TypeVar('T')


def _init_list(_list: List[Any], ctor: Callable[..., T]) -> List[T]:
    if _list is None or len(_list) == 0:
        return []
    return [models.create(ctor, el) for el in _list]


# Possible wrapper for dataclasses. Ensures registration with ejson.
# Creates some problems with mypy
# def _dataclass_wrapper(cls_):
#     ejson.REGISTRY[cls_] = _serialize_dataclass
#     return dataclasses.dataclass(cls_)


@dataclasses.dataclass
class UserRef:
    _id: str
    username: str  # Unique name (@...)
    name: Optional[str] = None  # Display name


ejson.REGISTRY[UserRef] = _serialize_dataclass


class RoleType(Enum):
    NONE = 'none'
    OWNER = 'owner'


ejson.REGISTRY[RoleType] = _serialize_enum


class MessageType(Enum):
    MESSAGE_PINNED = 'message_pinned'
    MESSAGE_REMOVED = 'rm'
    MESSAGE_SNIPPETED = 'message_snippeted'
    RENDER_RTC_MESSAGE = 'rtc'
    ROLE_ADDED = 'subscription-role-added'
    ROLE_REMOVED = 'subscription-role-removed'
    ROOM_ARCHIVED = 'room-archived'
    ROOM_CHANGED_ANNOUNCEMENT = 'room_changed_announcement'
    ROOM_CHANGED_DESCRIPTION = 'room_changed_description'
    ROOM_CHANGED_PRIVACY = 'room_changed_privacy'
    ROOM_CHANGED_TOPIC = 'room_changed_topic'
    ROOM_NAME_CHANGED = 'r'
    ROOM_UNARCHIVED = 'room-unarchived'
    STANDARD_MESSAGE = 'message'
    USER_ADDED = 'au'
    USER_JOINED = 'uj'
    USER_LEFT = 'ul'
    USER_MUTED = 'user-muted'
    USER_REMOVED = 'ru'
    USER_UNMUTED = 'user-unmuted'
    WECOME = 'wm'


ejson.REGISTRY[MessageType] = _serialize_enum


@dataclasses.dataclass
class Attachment:
    ts: models.RcDatetime

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
    attachments: List['Attachment'] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        self.ts = models.RcDatetime.from_server(self.ts)
        if len(self.attachments) != 0:
            self.attachments = [models.create(Attachment, a) for a in self.attachments]


ejson.REGISTRY[Attachment] = _serialize_dataclass


@dataclasses.dataclass
class File:
    _id: str
    name: str
    type: str


ejson.REGISTRY[File] = _serialize_dataclass


@dataclasses.dataclass
class Message:
    # Required fields
    _id: str
    _updatedAt: models.RcDatetime  # timestamp when the msg got saved on the server
    rid: str  # roomid
    msg: str
    ts: models.RcDatetime  # msg creation timestamp (on client))
    u: UserRef
    t: MessageType = MessageType.STANDARD_MESSAGE

    # Optional fields
    editedAt: Optional[models.RcDatetime] = None
    editedBy: Optional[UserRef] = None
    # [{'url': 'http://www.spiegel.de/wirtschaft/unternehmen/bierabsatz-steigt-erstmals-seit-jahren-a-1245601.html', 'meta': {'pageTitle': 'Bier: Absatz steigt wegen heißen Sommers erstmals seit Jahren - SPIEGEL ONLINE', 'ogLocale': 'de_DE', 'ogSiteName': 'SPIEGEL ONLINE', 'ogUrl': 'http://www.spiegel.de/wirtschaft/unternehmen/bierabsatz-steigt-erstmals-seit-jahren-a-1245601.html', 'ogType': 'article', 'ogTitle': 'Wegen heißen Sommers: Bierabsatz steigt erstmals seit Jahren - SPIEGEL ONLINE - Wirtschaft', 'ogDescription': 'Jahrelang schwächelte die Nachfrage nach deutschem Bier. Doch in diesem Jahr verkauften die Brauer dank des heißen Sommers wieder etwas mehr.', 'ogImage': 'http://cdn2.spiegel.de/images/image-1198681-860_poster_16x9-hrrg-1198681.jpg', 'twitterImage': 'http://cdn2.spiegel.de/images/image-1198681-860_poster_16x9-hrrg-1198681.jpg', 'description': 'Jahrelang schwächelte die Nachfrage nach deutschem Bier. Doch in diesem Jahr verkauften die Brauer dank des heißen Sommers wieder etwas mehr.'}, 'headers': {'contentType': 'text/html;charset=UTF-8', 'contentLength': '34157'}, 'parsedUrl': {'host': 'www.spiegel.de', 'hash': None, 'pathname': '/wirtschaft/unternehmen/bierabsatz-steigt-erstmals-seit-jahren-a-1245601.html', 'protocol': 'http:', 'port': None, 'query': None, 'search': None, 'hostname': 'www.spiegel.de'}}]
    # [{'url': 'https://www.statistik.uni-freiburg.de/stat/stud', 'meta': {'pageTitle': 'Studierende — Statistik-Web'}, 'headers': {'contentType': 'text/html;charset=utf-8'}, 'parsedUrl': {'host': 'www.statistik.uni-freiburg.de', 'hash': None, 'pathname': '/stat/stud', 'protocol': 'https:', 'port': None, 'query': None, 'search': None, 'hostname': 'www.statistik.uni-freiburg.de'}}]
    # [{'url': 'https://chat.fachschaft.tf/channel/_uni?msg=115737d5-5ad6-485b-8dc7-4ee4fe01b858', 'ignoreParse': True}]
    urls: Optional[Any] = None
    attachments: List[Attachment] = dataclasses.field(default_factory=list)
    alias: Optional[Any] = None
    avatar: Optional[str] = None  # Url to avatar
    emoji: Optional[Any] = None
    customFields: Optional[dict] = None
    reactions: Optional[dict] = None  # E.g. {':tada:': {'usernames': ['sm362']}}
    sandstormSessionId: Optional[Any] = None
    mentions: List[UserRef] = dataclasses.field(default_factory=list)
    channels: List['RoomRef'] = dataclasses.field(default_factory=list)
    role: RoleType = RoleType.NONE
    pinnedAt: Optional[models.RcDatetime] = None
    pinnedBy: Optional[UserRef] = None
    file: Optional[File] = None

    # Flags
    groupable: Optional[bool] = None
    parseUrls: Optional[bool] = None
    pinned: Optional[bool] = None

    def __post_init__(self) -> None:
        self._updatedAt = models.RcDatetime.from_server(self._updatedAt)
        self.ts = models.RcDatetime.from_server(self.ts)
        self.u = models.create(UserRef, self.u)
        self.editedAt = models.RcDatetime.from_server(self.editedAt)
        self.editedBy = models.create(UserRef, self.editedBy)
        self.pinnedAt = models.RcDatetime.from_server(self.pinnedAt)
        self.pinnedBy = models.create(UserRef, self.pinnedBy)
        self.file = models.create(File, self.file)
        if isinstance(self.t, str):
            self.t = MessageType(self.t)
        if isinstance(self.role, str):
            self.role = RoleType(self.role)

        # For later use when reactions actually contain user objects
        # if self.reactions is not None:
        #     self.reactions = {emoji: [UserRef.from_dict(u) for u in users] for emoji, users in self.reactions.items()}
        self.mentions = _init_list(self.mentions, UserRef)
        self.channels = _init_list(self.channels, RoomRef)
        self.attachments = _init_list(self.attachments, Attachment)

        # TEMP
        if self.alias:
            print('Alias arg found:', self.alias)
        if self.emoji:
            print('Emoji arg found:', self.emoji)
        if self.customFields:
            print('CustomFields arg found:', self.customFields)
        if self.sandstormSessionId:
            print('Sandstormsessionid arg found:', self.sandstormSessionId)


ejson.REGISTRY[Message] = _serialize_dataclass


class RoomType(Enum):
    PUBLIC = 'c'
    DIRECT = 'd'
    PRIVATE = 'p'
    LIVE = 'l'


ejson.REGISTRY[RoomType] = _serialize_enum


@dataclasses.dataclass
class RoomRef:
    _id: str
    name: str


ejson.REGISTRY[RoomRef] = _serialize_dataclass


@dataclasses.dataclass
class RoomRef2:
    """Necessary because there is no single way to reference a room"""
    roomType: RoomType
    roomParticipant: bool
    roomName: Optional[str] = None

    def __post_init__(self) -> None:
        self.roomType = RoomType(self.roomType)


ejson.REGISTRY[RoomRef2] = _serialize_dataclass


@dataclasses.dataclass
class Room:
    # Required fields
    _id: str
    _updatedAt: models.RcDatetime
    t: RoomType

    # Optional fields
    name: Optional[str] = None
    fname: Optional[str] = None
    u: Optional[UserRef] = None  # Room owner
    lastMessage: Optional[Message] = None
    topic: Optional[str] = None
    customFields: Optional[dict] = None
    muted: Optional[List[str]] = None
    description: Optional[str] = None
    msgs: Optional[int] = None  # Number of msgs
    usersCount: Optional[int] = None
    ts: Optional[models.RcDatetime] = None  # Creation timestamp
    lm: Optional[models.RcDatetime] = None  # Timestamp of last message
    usernames: Optional[List[str]] = None

    # Flags
    broadcast: Optional[bool] = None
    encrypted: Optional[bool] = None
    ro: Optional[bool] = None  # Read only flag
    sysMes: Optional[bool] = None
    default: Optional[bool] = None
    archived: Optional[bool] = None

    def __post_init__(self) -> None:
        self._updatedAt = models.RcDatetime.from_server(self._updatedAt)
        self.ts = models.RcDatetime.from_server(self.ts)
        self.lm = models.RcDatetime.from_server(self.lm)
        self.t = RoomType(self.t)
        self.u = models.create(UserRef, self.u)
        self.lastMessage = models.create(Message, self.lastMessage)

    def to_roomref(self) -> RoomRef:
        name = self.name if self.name else ""
        return RoomRef(name=name, _id=self._id)

    def to_roomref2(self, is_participant: bool) -> RoomRef2:
        return RoomRef2(roomType=self.t, roomName=self.name, roomParticipant=is_participant)


ejson.REGISTRY[Room] = _serialize_dataclass
