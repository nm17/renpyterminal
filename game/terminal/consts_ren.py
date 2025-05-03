"""renpy
init -999 python:
"""

from enum import IntEnum
import logging

# Just a random unique number
ENUM_START = 777123

class RTSpecial(IntEnum):
    PTYHANDLER__PREVENT_DEFAULT = ENUM_START
    CMDHANDLER__PREVENT_DEFAULT = ENUM_START + 1
    PTYEVENT__ENTER = ENUM_START + 2

rt_logger = logging.getLogger("RenPyTerminal")
rt_qth_logger = rt_logger.getChild("QueueThreadHandler")
rt_cmdhandler_logger = rt_logger.getChild("CommandHandler")