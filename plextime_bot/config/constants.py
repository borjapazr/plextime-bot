from os import getenv

from dotenv import load_dotenv

load_dotenv()

DAY_NAMES = {
    1: "monday",
    2: "tuesday",
    3: "wednesday",
    4: "thursday",
    5: "friday",
    6: "saturday",
    7: "sunday",
}

APP_NAME = "Plextime Bot"
AUTHOR = "@borjapazr"

PLEXTIME_BOT_REFRESH_DAY = DAY_NAMES[1]
PLEXTIME_BOT_REFRESH_HOUR = "03:00"

PLEXTIME_TIMEZONE = getenv("PLEXTIME_TIMEZONE", "UTC")
PLEXTIME_API_URL = "https://plextime.plexus.services/api/v1/"
PLEXTIME_LOGIN_PATH = "admin/login"
PLEXTIME_CHECKIN_PATH = "checkin_noloc"
PLEXTIME_CHECKOUT_PATH = "checkout_noloc"
PLEXTIME_HOLIDAYS_PATH = "admin/company/{company_id}/locality/{locality_id}/holidays"
PLEXTIME_VACATIONS_PATH = "vacations/company/{company_id}/user/{user_id}?begin={date_from}&end={date_to}"
PLEXTIME_DAY_INFO_PATH = "admin/company/{company_id}/users/{user_id}/day/{target_day}"
PLEXTIME_TIMETABLES_PATH = "admin/company/{company_id}/users/{user_id}/timetable"
PLEXTIME_LAST_TIMETABLE_PATH = "admin/company/{company_id}/users/{user_id}/last-timetable"
PLEXTIME_TIMETABLE_PATH = "admin/company/{company_id}/timetable/{timetable_id}"
PLEXTIME_JOURNAL_OPTIONS_PATH = "admin/company/{company_id}/journal_options"
PLEXTIME_CRYPTO_KEY = "jP=P^=v2AqmNZR6f"
PLEXTIME_API_KEY = "APwXk+7JM7yvqHNNGeeBj8XSRq!$U*@-zKVtQfp_97DJL-bJ3vcW!!AfaTn!eBX47cYk+BPRa94p%e3ZEs2hpV2K=hrwcHsJasZLhX7ycgd6JJ+u4rw?eezAPKUv^TrB2aQXcJSj+Tv#nkL*CF+pm5gx$xGwSznZNZF#VZvfEmnMQ-KuM$D5zADEPS&V*Hah!DgE#-4qB7c25XaDnve_66a=WVBJtjrY^GUMztbuW3_2SdxfUs!TjuBL&Q$5!gHU"
PLEXTIME_USER = getenv("PLEXTIME_USER", None)
PLEXTIME_PASSWORD = getenv("PLEXTIME_PASSWORD", None)
PLEXTIME_CHECKIN_JOURNAL_OPTION = getenv("PLEXTIME_CHECKIN_JOURNAL_OPTION", "8")
PLEXTIME_CHECKOUT_JOURNAL_OPTION = getenv("PLEXTIME_CHECKOUT_JOURNAL_OPTION", "8")
PLEXTIME_CHECKIN_RANDOM_MARGIN = int(getenv("PLEXTIME_CHECKIN_RANDOM_MARGIN", "0"))
PLEXTIME_CHECKOUT_RANDOM_MARGIN = int(getenv("PLEXTIME_CHECKOUT_RANDOM_MARGIN", "0"))
PLEXTIME_ORIGIN = int(getenv("PLEXTIME_ORIGIN", "2"))
PLEXTIME_CHECKIN_MESSAGE = "↘️ Checkin successfully completed on {checkin_datetime}"
PLEXTIME_CHECKOUT_MESSAGE = "↙️ Checkout successfully completed on {checkout_datetime}"
PLEXTIME_TELEGRAM_NOTIFICATIONS = getenv("PLEXTIME_TELEGRAM_NOTIFICATIONS", "false") == "true"
PLEXTIME_TELEGRAM_BOT_TOKEN = getenv("PLEXTIME_TELEGRAM_BOT_TOKEN", None)
PLEXTIME_TELEGRAM_CHANNEL_ID = getenv("PLEXTIME_TELEGRAM_CHANNEL_ID", None)
