from enum import Enum


class MessageType(Enum):
    DISCUSSION_CREATED = 'discussion-created'
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
    WELCOME = 'wm'


class RoleType(Enum):
    NONE = 'none'
    OWNER = 'owner'
    USER = 'user'
    ADMIN = 'admin'
    BOT = 'bot'
    LEADER = 'leader'


class RoomType(Enum):
    PUBLIC = 'c'
    DIRECT = 'd'
    PRIVATE = 'p'
    LIVE = 'l'
