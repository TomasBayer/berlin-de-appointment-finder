import datetime
import random
import re
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import telegram
from bs4 import BeautifulSoup
from requests import Response, Session

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",  # noqa: E501
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10",  # noqa: E501
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36"
]

LOCATIONS = [122210, 122217, 327316, 122219, 327312, 122227, 122231, 327346, 122238, 122243, 327348, 122252, 329742,
             122260, 329745, 122262, 329748, 122254, 329751, 122271, 327278, 122273, 327274, 122277, 327276, 122280,
             327294, 122282, 327290, 122284, 327292, 122291, 327270, 122285, 327266, 122286, 327264, 122296, 327268,
             150230, 329760, 122301, 327282, 122297, 327286, 122294, 327284, 122312, 329763, 122304, 327330, 122311,
             327334, 122309, 327332, 317869, 324434, 122281, 327352, 122279, 329772, 122276, 327324, 122274, 327326,
             122267, 329766, 122246, 327318, 122251, 327320, 327653, 122257, 327322, 122208, 327298, 122226, 327300]

SERVICES = {
    'wohnungsanmeldung': 120686,
    'personalausweis_antrag': 120703,
    'int_fuehrerschein': 121591,
}


@dataclass
class AppointmentFinder:
    service: str
    telegram_bot_token: str
    telegram_recipients: list[int]

    earliest_datetime: Optional[datetime.datetime] = None
    latest_datetime: Optional[datetime.datetime] = None
    earliest_time: Optional[datetime.time] = None
    latest_time: Optional[datetime.time] = None

    BASE_URL = 'https://service.berlin.de'
    APPOINTMENT_URL_PATTERN = re.compile(r'/terminvereinbarung/termin/time/(\d*)/')

    def __post_init__(self,):
        self.session = Session()
        self.bot = telegram.Bot(token=self.telegram_bot_token)

    def _build_url(self) -> str:
        dienstleister_list = ','.join(map(str, LOCATIONS))
        service_id = SERVICES[self.service]
        return f'{self.BASE_URL}/terminvereinbarung/termin/tag.php?termin=1&anliegen[]={service_id}&dienstleisterlist={dienstleister_list}&herkunft=http%3A%2F%2Fservice.berlin.de%2Fdienstleistung%2F120703%2F'  # noqa: E501

    def _request(self, url) -> Response:
        return self.session.get(url, headers={'User-Agent': random.choice(USER_AGENTS)})

    def find(self) -> Iterator[datetime.date]:
        url = self._build_url()

        response = self._request(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for bookable_day in soup.find_all('td', class_='buchbar'):
            termine_url = bookable_day.find('a').get('href')

            day_timestamp = self.APPOINTMENT_URL_PATTERN.match(termine_url).group(1)
            day = datetime.datetime.utcfromtimestamp(int(day_timestamp)).date()

            time.sleep(random.randint(1000, 3000) / 1000)

            response2 = self._request(self.BASE_URL + termine_url)

            for recipient in self.telegram_recipients:
                self.bot.send_message(
                    chat_id=recipient,
                    text=f"New appointment slots available on <b>{day.strftime('%d/%m')}</b>\n"
                         f"<a href=\"{url}\">Book your appointment here</a>",
                    parse_mode=telegram.ParseMode.HTML,
                    disable_web_page_preview=True
                )

            with open(f'/tmp/termine_{random.randint(0, 10000)}', 'wb') as fh:
                fh.write(response2.content)

            yield day
