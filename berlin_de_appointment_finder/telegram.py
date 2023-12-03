import asyncio
from dataclasses import dataclass
from typing import Iterable

import telegram

from berlin_de_appointment_finder.service import Location, Service


def human_join(words: Iterable[str]) -> str:
    words = list(words)

    if len(words) == 0:
        return ''
    elif len(words) == 1:
        return words[0]
    else:
        return ', '.join(words[:-1]) + ' and ' + words[-1]


@dataclass
class AppointmentFinder:
    telegram_bot_token: str
    telegram_recipients: list[int]

    service: Service
    locations: list[Location | int] | None

    def __post_init__(self):
        self.telegram_bot = telegram.Bot(token=self.telegram_bot_token)

        if self.locations is None:
            self.locations = self.service.get_available_locations()

    async def find_appointments_and_notify(self):
        result = self.service.search_appointments(self.locations)

        if result.has_appointments():
            message = (
                f"New appointment slots available on "
                f"<b>{human_join(day.strftime('%d/%m') for day in result.available_days)}</b>\n"
                f"<a href=\"{self.service.build_appointment_search_url(self.locations)}\">"
                f"Book your appointment here"
                f"</a>"
            )

            await asyncio.gather(
                *(self.telegram_bot.send_message(
                    chat_id=recipient,
                    text=message,
                    parse_mode=telegram.constants.ParseMode.HTML,
                    disable_web_page_preview=True,
                ) for recipient in self.telegram_recipients),
            )

    async def run_periodically(self, interval: int):
        while True:
            await self.find_appointments_and_notify()
            await asyncio.sleep(interval)
