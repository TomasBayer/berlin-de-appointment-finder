import argparse
import logging
import time

from berlin_de_appointment_finder.finder import AppointmentFinder


def build_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'service', metavar='SERVICE', type=str,
    )
    parser.add_argument(
        '--telegram-recipient', '-t', metavar='TELEGRAM_ID', nargs='+', type=int,
    )
    parser.add_argument(
        '--telegram-bot-token', '-T', metavar='BOT_TOKEN', type=str,
    )
    parser.add_argument('--verbose', '-v', action='store_true', help="verbose mode")

    return parser


def run():
    # Parse arguments
    parser = build_argparser()
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='[%(name)s] %(levelname)-8s %(message)s' if args.verbose else '%(message)s',
    )

    finder = AppointmentFinder(
        service=args.service,
        telegram_bot_token=args.telegram_bot_token,
        telegram_recipients=args.telegram_recipient,
    )

    while True:
        for _appointment in finder.find():
            pass
        time.sleep(60)
