from logging import *
from typing import Sequence


def get_logger(name: Sequence = ("pokeonta",)):
    logger_path_name = ".".join(map(str.lower, name))
    logger = getLogger(logger_path_name)
    logger.name = name[-1].upper()
    return logger
