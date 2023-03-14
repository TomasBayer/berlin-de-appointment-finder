import argparse
import logging


def build_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--dummy', '-d', metavar='DUMMY', type=str,
        help="dummy",
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
