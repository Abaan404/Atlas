from enum import Enum


class Roles(Enum):
    OWNER = 100  # unused
    ADMINISTRATOR = 70
    MANAGER = 10
    RADIO = 8
    QOTD = 0
    MCUPDATES = 0


class Colour(Enum):
    INFO = 0x12B07C
    WARNING = 0XD2E31C
    ERROR = 0x940023
    QOTD = 0xD3912C
    RADIO = 0x9400D3
    YOUTUBE = 0xFF0000
    SPOTIFY = 0x1DB954
    SOUNDCLOUD = 0xFF8800
    APPLE_MUSIC = 0xFFFFFF
    TWITCH = 0x9146FF

class Module(Enum):
    BLAME = "blame"
    FUN = "fun"
    QOTD = "qotd"
    RADIO = "radio"
    # MCUPDATES = "mcupdates"