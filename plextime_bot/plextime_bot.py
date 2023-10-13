from enum import Enum
from random import randint
from time import sleep
from typing import Optional

from art import text2art
from schedule import clear, every, get_jobs, idle_seconds, run_pending

from plextime_bot.config.constants import (
    APP_NAME,
    AUTHOR,
    DAY_NAMES,
    PLEXTIME_API_URL,
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
from plextime_bot.services.plextime_api_client import PlextimeApiClient, PlextimeApiClientError, Timetable
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
        self.__current_timetable: Optional[Timetable] = None

    def __validate_required_env_vars(self) -> None:
        if not PLEXTIME_USER or not PLEXTIME_PASSWORD:
            LOGGER.error("🚨 'PLEXTIME_USER' and 'PLEXTIME_PASSWORD' environment variables are mandatory")
            raise PlextimeBotError("'PLEXTIME_USER' and 'PLEXTIME_PASSWORD' environment variables are mandatory")

        if PLEXTIME_TELEGRAM_NOTIFICATIONS and (not PLEXTIME_TELEGRAM_BOT_TOKEN or not PLEXTIME_TELEGRAM_CHANNEL_ID):
            LOGGER.error(
                "🚨 'PLEXTIME_TELEGRAM_BOT_TOKEN' and 'PLEXTIME_TELEGRAM_CHANNEL_ID' environment variables are"
                " mandatory",
            )
            raise PlextimeBotError(
                "'PLEXTIME_TELEGRAM_BOT_TOKEN' and 'PLEXTIME_TELEGRAM_CHANNEL_ID' environment variables are mandatory",
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
        except PlextimeApiClientError as e:
            self.__log_and_send_notification_if_enabled(
                f"🚨 An error ocurred while trying to check-in: {e}",
                is_error=True,
            )

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
        except PlextimeApiClientError as e:
            self.__log_and_send_notification_if_enabled(
                f"🚨 An error ocurred while trying to check-out: {e}",
                is_error=True,
            )

    def __log_and_send_notification_if_enabled(self, message: str, is_error: bool = False) -> None:
        LOGGER.info(message) if not is_error else LOGGER.error(message)
        if self.__telegram_notificator:
            self.__telegram_notificator.send_notification(message)

    def __schedule_checks(self) -> None:
        try:
            LOGGER.info("🔂 Scheduling checks")

            new_timetable: Timetable = self.__plextime_api_client.retrieve_current_timetable()

            no_timetable_found = not new_timetable
            timetable_changed = (
                not self.__current_timetable or self.__current_timetable.timetable_id != new_timetable.timetable_id
            )

            if no_timetable_found:
                self.__log_and_send_notification_if_enabled(
                    "🚨 No timetable found for configuring checks",
                    is_error=True,
                )
            elif timetable_changed:
                if self.__current_timetable:
                    self.__log_and_send_notification_if_enabled(
                        "🆕 A new timetable has been detected",
                    )

                self.__current_timetable = new_timetable

                if get_jobs(TaskType.CHECK):
                    LOGGER.info("🧹 Cleaning up old schedulings")
                    clear(TaskType.CHECK)

                self.__log_and_send_notification_if_enabled(
                    "📅 Scheduled check-ins and check-outs based on timetable"
                    f" {new_timetable.name} ({new_timetable.description})",
                )

                sorted_timetable_entries = sorted(new_timetable.entries, key=lambda e: e.week_day)

                for entry in sorted_timetable_entries:
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
                        f"⏰ {day_name.capitalize()}: ➡️ Check-in - {entry.hour_in} | ⬅️ Check-out - {entry.hour_out}",
                    )
            else:
                LOGGER.info("💭 No timetable change detected so it is not necessary to reschedule checks")
        except PlextimeApiClientError as e:
            self.__log_and_send_notification_if_enabled(
                f"🚨 An error ocurred while trying to schedule checks: {e}",
                is_error=True,
            )

    def start(self) -> None:
        LOGGER.info("Hi! I'm %s. Nice to meet you! 🫡\n\n%s", AUTHOR, text2art(APP_NAME))
        self.__log_and_send_notification_if_enabled(
            f"🤖 Plextime Bot is configured to check in and out on behalf of 👤 {PLEXTIME_USER}",
        )

        every().day.at(PLEXTIME_BOT_REFRESH_HOUR, PLEXTIME_TIMEZONE).do(
            self.__schedule_checks,
        ).tag(
            TaskType.SCHEDULE,
        )
        self.__log_and_send_notification_if_enabled(
            f"🔄 Timetable update task is set for every day at {PLEXTIME_BOT_REFRESH_HOUR}",
        )

        self.__schedule_checks()

        while True:
            seconds_until_next_job = idle_seconds()

            if seconds_until_next_job is None:
                break

            if seconds_until_next_job > 0:
                sleep(seconds_until_next_job)

            run_pending()
