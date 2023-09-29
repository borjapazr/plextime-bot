from enum import Enum
from random import randint
from time import sleep
from typing import Optional

from art import text2art
from schedule import clear, every, get_jobs, run_pending

from plextime_bot.config.constants import (
    APP_NAME,
    AUTHOR,
    DAY_NAMES,
    PLEXTIME_API_URL,
    PLEXTIME_BOT_REFRESH_DAY,
    PLEXTIME_BOT_REFRESH_HOUR,
    PLEXTIME_CHECKIN_MESSAGE,
    PLEXTIME_CHECKIN_RANDOM_MARGIN,
    PLEXTIME_CHECKOUT_MESSAGE,
    PLEXTIME_CHECKOUT_RANDOM_MARGIN,
    PLEXTIME_PASSWORD,
    PLEXTIME_TELEGRAM_BOT_TOKEN,
    PLEXTIME_TELEGRAM_CHANNEL_ID,
    PLEXTIME_TELEGRAM_NOTIFICATIONS,
    PLEXTIME_TIMEZONE,
    PLEXTIME_USER,
)
from plextime_bot.services.plextime_api_client import PlextimeApiClient, PlextimeApiError, Timetable
from plextime_bot.services.telegram_notificator import TelegramNotificator
from plextime_bot.utils.date_manager import current_local_datetime_human_readable
from plextime_bot.utils.logger import Logger

LOGGER = Logger.get_logger("plextime_bot")


class TaskType(Enum):
    CHECK = 0
    CHECK_IN = 1
    CHECK_OUT = 2
    SCHEDULE = 3


class PlextimeBotError(Exception):
    def __init__(self, message: str = "An error ocurred in Plextime Bot") -> None:
        super().__init__(message)


class PlextimeBot:
    def __init__(self) -> None:
        self.__validate_required_env_vars()
        self.__plextime_api_client = PlextimeApiClient(PLEXTIME_API_URL, PLEXTIME_USER, PLEXTIME_PASSWORD)  # type: ignore[arg-type]
        self.__telegram_notificator = self.__get_telegram_notificator_if_enabled()

    def __validate_required_env_vars(self) -> None:
        if not PLEXTIME_USER or not PLEXTIME_PASSWORD:
            LOGGER.error("'PLEXTIME_USER' and 'PLEXTIME_PASSWORD' environment variables are mandatory!")
            raise PlextimeBotError("'PLEXTIME_USER' and 'PLEXTIME_PASSWORD' environment variables are mandatory!")

        if PLEXTIME_TELEGRAM_NOTIFICATIONS and (not PLEXTIME_TELEGRAM_BOT_TOKEN or not PLEXTIME_TELEGRAM_CHANNEL_ID):
            LOGGER.error(
                "'PLEXTIME_TELEGRAM_BOT_TOKEN' and 'PLEXTIME_TELEGRAM_CHANNEL_ID' environment variables are mandatory!",
            )
            raise PlextimeBotError(
                "'PLEXTIME_TELEGRAM_BOT_TOKEN' and 'PLEXTIME_TELEGRAM_CHANNEL_ID' environment variables are mandatory!",
            )

    def __get_telegram_notificator_if_enabled(self) -> Optional[TelegramNotificator]:
        if PLEXTIME_TELEGRAM_NOTIFICATIONS:
            return TelegramNotificator(PLEXTIME_TELEGRAM_BOT_TOKEN, PLEXTIME_TELEGRAM_CHANNEL_ID)  # type: ignore[arg-type]
        return None

    def __sleep_random_time(self, min_val: int, max_val: int) -> None:
        sleep(randint(min_val, max_val))

    def _random_checkin(self) -> None:
        try:
            self.__sleep_random_time(0, PLEXTIME_CHECKIN_RANDOM_MARGIN)
            if self.__plextime_api_client.checkin_if_working_day_and_not_checkedin_before():
                self.__log_and_send_notification_if_enabled(
                    PLEXTIME_CHECKIN_MESSAGE.format(
                        checkin_datetime=current_local_datetime_human_readable(),
                    ),
                )
        except PlextimeApiError as e:
            self.__log_and_send_notification_if_enabled(f"An error ocurred while trying to check-in: {e}")

    def _random_checkout(self) -> None:
        try:
            self.__sleep_random_time(
                PLEXTIME_CHECKIN_RANDOM_MARGIN,
                max(PLEXTIME_CHECKOUT_RANDOM_MARGIN, PLEXTIME_CHECKIN_RANDOM_MARGIN),
            )
            if self.__plextime_api_client.checkout_if_checkedin_before():
                self.__log_and_send_notification_if_enabled(
                    PLEXTIME_CHECKOUT_MESSAGE.format(
                        checkout_datetime=current_local_datetime_human_readable(),
                    ),
                )
        except PlextimeApiError as e:
            self.__log_and_send_notification_if_enabled(f"An error ocurred while trying to check-out: {e}")

    def __log_and_send_notification_if_enabled(self, message: str) -> None:
        LOGGER.info(message)
        if self.__telegram_notificator:
            self.__telegram_notificator.send_notification(message)

    def __schedule_checks(self) -> None:
        try:
            if get_jobs(TaskType.CHECK):
                LOGGER.info("🧹 Cleaning up old schedulings")
                clear(TaskType.CHECK)

            timetable: Timetable = self.__plextime_api_client.retrieve_current_timetable()
            if timetable:
                for entry in timetable.entries:
                    day_name = DAY_NAMES[entry.week_day]
                    getattr(every(), day_name).at(entry.hour_in, PLEXTIME_TIMEZONE).do(self._random_checkin).tag(
                        TaskType.CHECK,
                        TaskType.CHECK_IN,
                    )
                    getattr(every(), day_name).at(entry.hour_out, PLEXTIME_TIMEZONE).do(self._random_checkout).tag(
                        TaskType.CHECK,
                        TaskType.CHECK_OUT,
                    )
                    self.__log_and_send_notification_if_enabled(
                        f"⏰ {day_name.capitalize()} -> check-in at {entry.hour_in} and check-out at {entry.hour_out}",
                    )
        except PlextimeApiError as e:
            self.__log_and_send_notification_if_enabled(f"An error ocurred while trying to schedule checks: {e}")

    def start(self) -> None:
        LOGGER.info("Hi! I'm %s. Nice to meet you! 🫡\n\n%s", AUTHOR, text2art(APP_NAME))
        self.__log_and_send_notification_if_enabled(
            f"🤖 Plextime Bot configured and started to check-in and check-out on behalf of <{PLEXTIME_USER}>",
        )

        getattr(every(), PLEXTIME_BOT_REFRESH_DAY).at(PLEXTIME_BOT_REFRESH_HOUR, PLEXTIME_TIMEZONE).do(
            self.__schedule_checks,
        ).tag(
            TaskType.SCHEDULE,
        )
        self.__log_and_send_notification_if_enabled(
            f"🔄 Timetable updating task enabled for {PLEXTIME_BOT_REFRESH_DAY.capitalize()}s at"
            f" {PLEXTIME_BOT_REFRESH_HOUR}",
        )

        self.__schedule_checks()

        while True:
            run_pending()
            sleep(1)
