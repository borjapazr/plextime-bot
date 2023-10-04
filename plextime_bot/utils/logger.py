import logging
import logging.handlers
import sys
from pathlib import Path

import coloredlogs

from plextime_bot.config.constants import PLEXTIME_LOG_LEVEL


class Logger:
    __LEVEL = PLEXTIME_LOG_LEVEL
    __LOG_FILE = "./logs/records.log"
    __FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @staticmethod
    def get_logger(service: str) -> logging.Logger:
        logger = logging.getLogger(service)
        logger.setLevel(Logger.__LEVEL)
        logger.addHandler(Logger.__get_console_handler())
        logger.addHandler(Logger.__get_file_handler())
        return logger

    @staticmethod
    def __get_console_handler() -> logging.Handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(coloredlogs.ColoredFormatter(Logger.__FORMAT))
        console_handler.setLevel(Logger.__LEVEL)
        return console_handler

    @staticmethod
    def __get_file_handler() -> logging.Handler:
        Path.mkdir(Path(Logger.__LOG_FILE).parent, parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            Logger.__LOG_FILE,
            maxBytes=500000000,
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(Logger.__FORMAT))
        file_handler.setLevel(Logger.__LEVEL)
        return file_handler
