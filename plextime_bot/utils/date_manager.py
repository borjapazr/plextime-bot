from datetime import date, datetime, timezone
from typing import Union

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
HUMAN_READABLE_DATETIME_FORMAT = "%d/%m/%Y at %H:%M:%S"


def current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)


def current_utc_date() -> date:
    return current_utc_datetime().date()


def current_local_datetime() -> datetime:
    return current_utc_datetime().astimezone()


def current_local_date() -> date:
    return current_local_datetime().date()


def start_of_year_local() -> date:
    return date(current_local_datetime().year, 1, 1)


def end_of_year_local() -> date:
    return date(current_local_datetime().year, 12, 31)


def with_utc_timezone(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def to_string(value: Union[datetime, date]) -> str:
    format_str = DATETIME_FORMAT if isinstance(value, datetime) else DATE_FORMAT
    return value.strftime(format_str)


def current_local_datetime_human_readable() -> str:
    return current_local_datetime().strftime(HUMAN_READABLE_DATETIME_FORMAT)
