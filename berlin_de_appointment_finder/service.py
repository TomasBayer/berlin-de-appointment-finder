import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests import Response, Session
from zoneinfo import ZoneInfo

ua = UserAgent()


@dataclass
class Location:
    location_id: int
    name: str


@dataclass
class AppointmentSearchResult:
    service_id: int
    available_days: list[date]

    def has_appointments(self) -> bool:
        return bool(self.available_days)


@dataclass
class Service:
    service_id: int

    BASE_URL = 'https://service.berlin.de'
    APPOINTMENT_URL_PATTERN = re.compile(r'/terminvereinbarung/termin/time/(\d*)/')

    def __post_init__(self):
        self.session = Session()

    def build_service_info_url(self) -> str:
        return f'{self.BASE_URL}/dienstleistung/{self.service_id}/'

    def build_appointment_search_url(self, locations: Iterable[Location | int]) -> str:
        query_parameters = {
            'termin': 1,
            'anliegen[]': self.service_id,
            'dienstleisterlist': ','.join(
                str(location.location_id if isinstance(location, Location) else location)
                for location in locations
            ),
            'herkunft': quote_plus(self.build_service_info_url()),
        }
        query_string = "&".join(f'{key}={value}' for key, value in query_parameters.items())

        return f'{self.BASE_URL}/terminvereinbarung/termin/tag.php?{query_string}'

    def _request(self, url) -> Response:
        return self.session.get(url, headers={'User-Agent': ua.firefox})

    def get_available_locations(self) -> list[Location]:
        response = self._request(self.build_service_info_url())
        soup = BeautifulSoup(response.text, 'html.parser')

        locations = []

        for e in soup.find_all('input', {'name': 'dienstleister[]'}):
            location_id = e['value']
            name = e.parent.find('label').get_text().strip()
            locations.append(Location(location_id, name))

        return sorted(locations, key=lambda location: location.name)

    def search_appointments(
            self,
            locations: Iterable[Location | int],
            *,
            earliest_day: Optional[date] = None,
            latest_day: Optional[date] = None,
    ) -> AppointmentSearchResult:
        response = self._request(self.build_appointment_search_url(locations))
        soup = BeautifulSoup(response.text, 'html.parser')

        days = []

        for bookable_day in soup.find_all('td', class_='buchbar'):
            termine_url = bookable_day.find('a').get('href')

            timestamp = self.APPOINTMENT_URL_PATTERN.match(termine_url).group(1)
            # This timestamp points at 12 a.m. (Berlin time) of the day with available appointments
            day = datetime.fromtimestamp(int(timestamp), tz=ZoneInfo('Europe/Berlin')).date()

            if earliest_day is not None and day < earliest_day:
                continue

            if latest_day is not None and day > latest_day:
                continue

            days.append(day)

        return AppointmentSearchResult(
            service_id=self.service_id,
            available_days=days,
        )
