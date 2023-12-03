import asyncio
import logging
from typing import Annotated, Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from berlin_de_appointment_finder.service import Service
from berlin_de_appointment_finder.telegram import AppointmentFinder

app = typer.Typer()
console = Console()


@app.command()
def run(
        service_id: Annotated[int, typer.Argument(
            metavar="SERVICE_ID",
            help="ID of the service which should be monitored. (The ID can be extracted from the URL after clicking"
                 "on the desired service on https://service.berlin.de/dienstleistungen/).",
        )],
        *,
        locations: Annotated[Optional[list[int]], typer.Option(
            '--location', '-l',
            help="ID of a location which should be monitored. This option may be given multiple times. If it is not "
                 "given at all, all available locations are monitored. Use --list-locations to see available "
                 "locations.",
        )] = None,
        telegram_recipients: Annotated[Optional[list[int]], typer.Option(
            '--recipient', '-r',
            help="Telegram IDs of users who should be notified when appointments are found. This option may be given "
                 "multiple times.",
        )] = None,
        telegram_bot_token: Annotated[Optional[str], typer.Option(
            '--token', '-t',
            help="Telegram bot token.",
        )] = None,
        interval: Annotated[int, typer.Option(
            '--interval', '-i',
            help="Interval (in seconds) between successive checks.",
        )] = 300,
        list_locations: Annotated[bool, typer.Option(
            "--list-locations", "-L",
            help="List available locations for the given service and return.",
        )] = False,
        verbose: Annotated[bool, typer.Option(
            "--verbose", "-v",
            help="Verbose mode.",
        )] = False,
):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)-15s %(levelname)-8s %(message)s')

    service = Service(
        service_id=service_id,
    )

    if list_locations:
        table = Table(header_style='bold magenta', box=box.SIMPLE_HEAD)
        table.add_column("ID")
        table.add_column("NAME")

        for location in service.get_available_locations():
            table.add_row(str(location.location_id), location.name)

        console.print(table)

    else:
        finder = AppointmentFinder(
            telegram_bot_token=telegram_bot_token,
            telegram_recipients=telegram_recipients,
            service=service,
            locations=locations if locations else None,
        )

        asyncio.run(finder.run_periodically(interval))
