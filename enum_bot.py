from enum import Enum


class BotStatus(Enum):
    START_FAILED = 1
    LOGIN_FAILED = 2
    ELEMENT_CHANGED = 3
    END_SUCCESS = 4
    USER_NOT_FOUND = 5
    TIME_OUT = 6
