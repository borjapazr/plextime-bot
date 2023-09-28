from requests import get


class TelegramNotificator:
    def __init__(
        self,
        token: str,
        channel_id: str,
    ) -> None:
        self.token = token
        self.channel_id = channel_id

    def send_notification(self, message: str) -> None:
        if self.token and self.channel_id:
            get(
                f"https://api.telegram.org/bot{self.token}/sendMessage?chat_id={self.channel_id}&text={message}",
                timeout=30,
            )
