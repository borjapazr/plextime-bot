from requests import RequestException, Session

from plextime_bot.utils.logger import Logger

LOGGER = Logger.get_logger("telegram_notificator")


class TelegramNotificator:
    def __init__(
        self,
        token: str,
        channel_id: str,
    ) -> None:
        self.token = token
        self.channel_id = channel_id
        self.__session = Session()

    def send_notification(self, message: str) -> None:
        if self.token and self.channel_id:
            try:
                response = self.__session.get(
                    f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.channel_id}&text={message}",
                    timeout=30,
                )
                response.raise_for_status()
            except RequestException as e:
                LOGGER.error("🚨 An error ocurred while sending a notification via Telegram - %s", e)
