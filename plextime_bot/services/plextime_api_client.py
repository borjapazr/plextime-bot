from dataclasses import dataclass
from json import dumps
from typing import Any, Callable, List, Optional, Union, cast

from dataclass_wizard import DatePattern, DateTimePattern, fromdict, fromlist, json_field
from requests import RequestException, Response, Session

from plextime_bot.config.constants import (
    PLEXTIME_API_KEY,
    PLEXTIME_CHECKIN_JOURNAL_OPTION,
    PLEXTIME_CHECKIN_PATH,
    PLEXTIME_CHECKOUT_JOURNAL_OPTION,
    PLEXTIME_CHECKOUT_PATH,
    PLEXTIME_CRYPTO_KEY,
    PLEXTIME_DAY_INFO_PATH,
    PLEXTIME_HOLIDAYS_PATH,
    PLEXTIME_JOURNAL_OPTIONS_PATH,
    PLEXTIME_LOGIN_PATH,
    PLEXTIME_ORIGIN,
    PLEXTIME_TIMETABLE_PATH,
    PLEXTIME_TIMETABLES_PATH,
    PLEXTIME_VACATIONS_PATH,
)
from plextime_bot.utils.aes_cipher import AESCipher
from plextime_bot.utils.date_manager import (
    current_local_date,
    current_utc_datetime,
    end_of_year_local,
    start_of_year_local,
    to_string,
    with_utc_timezone,
)
from plextime_bot.utils.logger import Logger

LOGGER = Logger.get_logger("plextime_api_client")


@dataclass
class LoginData:
    result: str = json_field("result", all=True)
    user_id: int = json_field("user_id", all=True)
    company_id: int = json_field("company_id", all=True)
    locality_id: int = json_field("locality_id", all=True)
    token: str = json_field("token", all=True)


@dataclass
class JournalOption:
    option_id: int = json_field("id", all=True)
    option_type: int = json_field("type", all=True)
    name: str = json_field("name", all=True)
    company_id: int = json_field("company_id", all=True)
    is_break: bool = json_field("is_break", all=True)
    active: bool = json_field("active", all=True)


@dataclass
class PublicHoliday:
    name: str = json_field("name", all=True)
    begins: DatePattern["%Y-%m-%d %H:%M:%S"] = json_field("begins", all=True)
    ends: DatePattern["%Y-%m-%d %H:%M:%S"] = json_field("ends", all=True)


@dataclass
class Holiday:
    begins: DatePattern["%Y-%m-%d %H:%M:%S"] = json_field("init_date", all=True)
    ends: DatePattern["%Y-%m-%d %H:%M:%S"] = json_field("end_date", all=True)
    status: int = json_field("status", all=True)


@dataclass
class TimetableSummary:
    timetable_id: int = json_field("id", all=True)
    begins: Optional[DatePattern["%Y-%m-%d %H:%M:%S"]] = json_field("init_date", all=True)
    ends: Optional[DatePattern["%Y-%m-%d %H:%M:%S"]] = json_field("end_date", all=True)
    status: bool = json_field("status", all=True)


@dataclass
class TimetableEntry:
    week_day: int = json_field("week_day", all=True)
    hour_in: str = json_field("hour_in", all=True)
    hour_out: str = json_field("hour_out", all=True)
    lunch_time: int = json_field("lunch_time", all=True)
    break_time: int = json_field("break_time", all=True)


@dataclass
class Timetable:
    timetable_id: int = json_field("id", all=True)
    name: str = json_field("name", all=True)
    description: str = json_field("description", all=True)
    status: bool = json_field("status", all=True)
    entries: List[TimetableEntry] = json_field("times", all=True)


@dataclass
class Record:
    record_id: int = json_field("id", all=True)
    checkin: DateTimePattern["%Y-%m-%d %H:%M:%S"] = json_field("checkin", all=True)
    checkout: Optional[DateTimePattern["%Y-%m-%d %H:%M:%S"]] = json_field("checkout", all=True)
    checkin_journal_option_id: int = json_field("option_in", all=True)
    checkout_journal_option_id: Optional[int] = json_field("option_out", all=True)

    def __post_init__(self) -> None:
        self.checkin = with_utc_timezone(self.checkin)

        if self.checkout:
            self.checkout = with_utc_timezone(self.checkout)


@dataclass
class CheckInResult:
    result: str = json_field("result", all=True)


@dataclass
class CheckOutResult:
    result: str = json_field("result", all=True)


class PlextimeApiError(Exception):
    def __init__(self, message: str = "An error ocurred in Plextime API Client") -> None:
        super().__init__(message)


class PlextimeApiClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        checkin_journal_option_id: Union[str, int] = PLEXTIME_CHECKIN_JOURNAL_OPTION,
        checkout_journal_option_id: Union[str, int] = PLEXTIME_CHECKOUT_JOURNAL_OPTION,
        origin: Union[str, int] = PLEXTIME_ORIGIN,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self.__checkin_journal_option_id = int(checkin_journal_option_id)
        self.__checkout_journal_option_id = int(checkout_journal_option_id)
        self.__origin = origin
        self.__session = Session()
        self.__headers = {
            "Content-Type": "application/json",
            "api-key": PLEXTIME_API_KEY,
        }
        self.__token: Optional[str] = None
        self.__user_id: Optional[int] = None
        self.__company_id: Optional[int] = None
        self.__locality_id: Optional[int] = None

    @staticmethod
    def __authenticated(method: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(self: "PlextimeApiClient", *args: Any, **kwargs: Any) -> Any:
            self.__retrieve_token_and_user_data()
            return method(self, *args, **kwargs)

        return wrapper

    @__authenticated
    def retrieve_journal_options(self) -> List[JournalOption]:
        journal_options_json = self.__get(
            PLEXTIME_JOURNAL_OPTIONS_PATH.format(company_id=self.__company_id),
        )

        journal_options: List[JournalOption] = fromlist(
            JournalOption,
            journal_options_json["journal_options"],
        )

        return journal_options

    @__authenticated
    def retrieve_current_timetable(self) -> Timetable:
        timetables_json = self.__get(
            PLEXTIME_TIMETABLES_PATH.format(company_id=self.__company_id, user_id=self.__user_id),
        )

        timetables: List[TimetableSummary] = fromlist(TimetableSummary, timetables_json["timetable"])

        today = current_local_date()

        fallback_timetable_id = next(
            (t.timetable_id for t in timetables if t.status and t.begins is None and t.ends is None),
            None,
        )

        active_timetable = next(
            (
                t.timetable_id
                for t in timetables
                if t.status and t.begins is not None and t.ends is not None and t.begins <= today <= t.ends
            ),
            fallback_timetable_id,
        )

        timetable_json = self.__get(
            PLEXTIME_TIMETABLE_PATH.format(company_id=self.__company_id, timetable_id=active_timetable),
        )

        return fromdict(Timetable, timetable_json)

    @__authenticated
    def checkin_if_working_day_and_not_checkedin_before(self) -> bool:
        if self.__is_today_non_working_day():
            return False

        current_day_info_json = self.__get(
            PLEXTIME_DAY_INFO_PATH.format(
                company_id=self.__company_id,
                user_id=self.__user_id,
                target_day=to_string(current_local_date()),
            ),
        )

        current_day_records = fromlist(Record, current_day_info_json["checks"])

        has_record_without_checkout = any(r.checkout is None for r in current_day_records)

        if has_record_without_checkout:
            return False

        checkin_data = {
            "iduser": self.__user_id,
            "date": to_string(current_utc_datetime()),
            "optionId": self.__checkin_journal_option_id,
            "origin": self.__origin,
        }

        checkin_json = self.__put(
            PLEXTIME_CHECKIN_PATH,
            checkin_data,
        )

        checkin_result = fromdict(CheckInResult, checkin_json)

        return checkin_result.result == "OK"

    @__authenticated
    def checkout_if_checkedin_before(self) -> bool:
        if self.__is_today_non_working_day():
            return False

        current_day_info_json = self.__get(
            PLEXTIME_DAY_INFO_PATH.format(
                company_id=self.__company_id,
                user_id=self.__user_id,
                target_day=to_string(current_local_date()),
            ),
        )

        current_day_records = fromlist(Record, current_day_info_json["checks"])

        records_without_checkout = [r for r in current_day_records if r.checkout is None]

        last_record_without_checkout = (
            sorted(records_without_checkout, key=lambda r: r.checkin, reverse=True)[0]
            if records_without_checkout
            else None
        )

        if last_record_without_checkout is None:
            return False

        checkout_data = {
            "id": last_record_without_checkout.record_id,
            "iduser": self.__user_id,
            "date": to_string(current_utc_datetime()),
            "optionId": self.__checkout_journal_option_id,
            "origin": self.__origin,
        }

        checkout_json = self.__put(
            PLEXTIME_CHECKOUT_PATH,
            checkout_data,
        )

        checkout_result = fromdict(CheckOutResult, checkout_json)

        return checkout_result.result == "OK"

    def __is_today_non_working_day(self) -> bool:
        today = current_local_date()
        public_hollidays = self.__retrieve_public_holidays_for_current_year()
        user_hollidays = self.__retrieve_user_hollidays_for_current_year()

        is_today_public_holliday = any(h.begins <= today <= h.ends for h in public_hollidays)
        is_today_user_holliday = any(h.begins <= today <= h.ends for h in user_hollidays)

        return is_today_public_holliday or is_today_user_holliday

    def __retrieve_public_holidays_for_current_year(self) -> List[PublicHoliday]:
        holidays_json = self.__get(
            PLEXTIME_HOLIDAYS_PATH.format(company_id=self.__company_id, locality_id=self.__locality_id),
        )
        holidays: List[PublicHoliday] = fromlist(PublicHoliday, holidays_json)
        return holidays

    def __retrieve_user_hollidays_for_current_year(self) -> List[Holiday]:
        vacations_json = self.__get(
            PLEXTIME_VACATIONS_PATH.format(
                company_id=self.__company_id,
                user_id=self.__user_id,
                date_from=to_string(start_of_year_local()),
                date_to=to_string(end_of_year_local()),
            ),
        )
        vacations: List[Holiday] = fromlist(Holiday, vacations_json["requests"])
        return vacations

    def __retrieve_token_and_user_data(self) -> None:
        login_body = {"email": self._username, "password": self._password}
        login_data_json = self.__put(PLEXTIME_LOGIN_PATH, login_body)

        if login_data_json["result"] != "OK":
            LOGGER.error("Missing or invalid credentials!")
            raise PlextimeApiError("Missing or invalid credentials!")

        login_data = fromdict(LoginData, login_data_json)

        self.__token = login_data.token
        self.__user_id = login_data.user_id
        self.__company_id = login_data.company_id
        self.__locality_id = login_data.locality_id

    def __request(self, method: str, endpoint: str, **kwargs: Any) -> Response:
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": cast(str, self.__token), **self.__headers}

        try:
            response = self.__session.request(method, url, headers=headers, verify=True, **kwargs)
            response.raise_for_status()
        except RequestException as e:
            LOGGER.error("Error ocurring while making request to %s", url)
            raise PlextimeApiError(f"Error ocurring while making request to {url}") from e

        return response

    def __get(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__request("GET", endpoint, **kwargs).json()

    def __put(self, endpoint: str, body: dict, **kwargs: Any) -> Any:
        return self.__request("PUT", endpoint, json=self.__encrypt_body(body), **kwargs).json()

    def __encrypt_body(self, data: dict) -> dict:
        return {"value": AESCipher(PLEXTIME_CRYPTO_KEY).encrypt(dumps(dumps(data))).decode()}
