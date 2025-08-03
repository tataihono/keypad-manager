"""Constants for keypad_manager."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "keypad_manager"

MIN_TAG_VALUE = 0
MAX_TAG_VALUE = 9999

MIN_USER_NAME_LENGTH = 2
MAX_USER_NAME_LENGTH = 50

MIN_CODE_LENGTH = 4
MAX_CODE_LENGTH = 8
